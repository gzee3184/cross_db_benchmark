"""Relational BIRD benchmark execution and evaluation runner."""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from crossdb.backends.sqlite.evaluator import BIRDEvaluator
from crossdb.backends.sqlite.executor import SQLiteExecutor
from crossdb.core.client import LLMClient
from crossdb.core.pipeline import DualCandidatePipeline
from crossdb.core.refine_gate import RefinementGate
from crossdb.discovery.kg import FieldKnowledgeGraph
from crossdb.discovery.retrieval import SchemaRetriever


def _remap_table_names(sql: str, table_map: Dict[str, str]) -> str:
    """Remap PascalCase or aliased collection names to actual SQLite table names."""
    if not sql or not table_map:
        return sql
    # Sort keys by length descending to avoid partial prefix collisions
    for old_name, new_name in sorted(table_map.items(), key=lambda x: len(x[0]), reverse=True):
        sql = re.sub(rf"\b{re.escape(old_name)}\b", new_name, sql, flags=re.IGNORECASE)
    return sql


def run_bird_benchmark(
    data_dir: Path,
    db_dir: Path,
    output_dir: Path,
    concurrency: int = 8,
    split: str = "all",
    limit: Optional[int] = None,
    db_id_filter: Optional[str] = None,
    # Ablation flags:
    no_ir: bool = False,
    no_refine: bool = False,
    ungated: bool = False,
    no_kg: bool = False,
    no_embedding: bool = False,
    no_rerank: bool = False,
    no_values: bool = False,
    no_adaptive: bool = False,
    no_multi_hop: bool = False,
    no_lexical: bool = False,
    # Client settings:
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Execute the full BIRD benchmark evaluation across target queries.

    Args:
        data_dir: Directory containing dev.json, dev_tables.json, etc.
        db_dir: Directory containing SQLite databases (<db_id>/<db_id>.sqlite).
        output_dir: Directory to save summary.json and results.json.
        concurrency: Number of parallel evaluation threads.
        split: Query split ('all', 'dev', 'test').
        limit: Optional maximum number of queries to evaluate.
        db_id_filter: Optional single database filter.
        no_ir: Ablation A1 - Disable IR compilation.
        no_refine: Ablation A3 - Disable refinement loop.
        ungated: Ablation A3 - Force refinement unconditionally.
        no_kg: Ablation A2 - Disable Knowledge Graph.
        no_embedding: Disable dense semantic embeddings.
        no_rerank: Disable property token reranking.
        no_values: Disable value catalog statistics.
        no_adaptive: Disable adaptive candidate depth routing.
        no_multi_hop: Disable multi-hop graph traversal.
        no_lexical: Disable lexical overlap scoring.
        client: Optional custom LLMClient instance.

    Returns:
        Summary metrics dictionary.
    """
    data_dir = Path(data_dir)
    db_dir = Path(db_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load questions (dev.json)
    dev_json_path = data_dir / "dev.json"
    if not dev_json_path.exists():
        # Check subdirectories
        candidates = list(data_dir.glob("**/dev.json"))
        if candidates:
            dev_json_path = candidates[0]
        else:
            raise FileNotFoundError(f"Could not find dev.json in {data_dir}")

    with open(dev_json_path, "r", encoding="utf-8") as f:
        all_queries = json.load(f)

    # 2. Load schemas (dev_tables.json)
    tables_json_path = data_dir / "dev_tables.json"
    if not tables_json_path.exists():
        candidates = list(data_dir.glob("**/dev_tables.json"))
        if candidates:
            tables_json_path = candidates[0]

    tables_metadata = []
    if tables_json_path and tables_json_path.exists():
        with open(tables_json_path, "r", encoding="utf-8") as f:
            tables_metadata = json.load(f)

    # Build schema lookup: db_id -> {table_name: [column_names]}
    table_schemas: Dict[str, Dict[str, List[str]]] = {}
    table_remap: Dict[str, Dict[str, str]] = {}
    for db in tables_metadata:
        d_id = db.get("db_id", "")
        t_names = db.get("table_names_original", [])
        c_entries = db.get("column_names_original", [])

        schema: Dict[str, List[str]] = {t: [] for t in t_names}
        for tbl_idx, col_name in c_entries:
            if 0 <= tbl_idx < len(t_names):
                schema[t_names[tbl_idx]].append(col_name)

        table_schemas[d_id] = schema

        # Map normalized / PascalCase table names to raw SQLite table name
        remap = {}
        for t in t_names:
            remap[t.lower()] = t
            remap[re.sub(r"[_]+", "", t.lower())] = t
            remap[f"{d_id}_{t}".lower()] = t
            remap[re.sub(r"[_]+", "", f"{d_id}_{t}".lower())] = t
        table_remap[d_id] = remap

    # 3. Load Knowledge Graph & Value Catalog
    kg = FieldKnowledgeGraph(enabled=not no_kg)
    if not no_kg and tables_metadata:
        kg.build_from_schemas(tables_metadata)

    # Check for precomputed join paths
    join_paths_file = data_dir / "join_paths.json"
    if join_paths_file.exists() and not no_kg:
        try:
            with open(join_paths_file, "r", encoding="utf-8") as f:
                kg.load_precomputed_join_paths(json.load(f))
        except Exception:
            pass

    value_catalog = None
    if not no_values:
        vc_path = data_dir / "bird_sqlite_value_catalog.json"
        if vc_path.exists():
            try:
                with open(vc_path, "r", encoding="utf-8") as f:
                    value_catalog = json.load(f)
            except Exception:
                value_catalog = None

    # Initialize Retriever & Pipeline
    retriever = SchemaRetriever(
        kg=kg,
        value_catalog=value_catalog,
        use_kg=not no_kg,
        use_embedding=not no_embedding,
        use_rerank=not no_rerank,
        use_values=not no_values,
        use_adaptive=not no_adaptive,
        use_multi_hop=not no_multi_hop,
        use_lexical=not no_lexical,
    )

    pipeline = DualCandidatePipeline(
        client=client or LLMClient(),
        refine_gate=RefinementGate(enabled=not ungated),
        no_ir=no_ir,
        no_refine=no_refine,
        ungated=ungated,
    )

    executor = SQLiteExecutor(db_dir=db_dir)

    # 4. Filter queries
    queries_to_run = all_queries
    if db_id_filter:
        queries_to_run = [q for q in queries_to_run if q.get("db_id") == db_id_filter]
    if limit is not None and limit > 0:
        queries_to_run = queries_to_run[:limit]

    total_n = len(queries_to_run)
    print(f"\nEvaluating BIRD ({total_n} queries, concurrency={concurrency})...")

    # 5. Worker function for parallel execution
    def _eval_one(q: Dict[str, Any]) -> Dict[str, Any]:
        q_id = q.get("question_id", q.get("id", 0))
        db_id = q.get("db_id", "")
        question = q.get("question", "")
        evidence = q.get("evidence", "")
        gold_sql = q.get("SQL", q.get("query", ""))

        db_path = executor.resolve_db_path(db_id)
        if not db_path:
            return {
                "question_id": q_id,
                "db_id": db_id,
                "error": f"Database file not found for {db_id}",
                "correct": False,
            }

        # Gold execution
        gold_rows, gold_err = executor.execute(db_path, gold_sql)

        # Candidate table discovery
        schemas_for_db = table_schemas.get(db_id, {})
        cand_tables = retriever.retrieve_tables(
            db_id=db_id,
            question=question,
            evidence=evidence,
            table_schemas=schemas_for_db,
        )
        filtered_schemas = {t: schemas_for_db.get(t, []) for t in cand_tables}

        # Join path hints from KG
        join_hints = []
        if not no_kg and len(cand_tables) >= 2:
            for i in range(len(cand_tables)):
                for j in range(i + 1, len(cand_tables)):
                    hops = kg.find_join_path(db_id, cand_tables[i], cand_tables[j])
                    if hops:
                        for hop in hops:
                            join_hints.append(f"{hop[0]}.{hop[1]} = {hop[2]}.{hop[3]}")

        # Run pipeline
        res = pipeline.run_relational(
            db_path=db_path,
            question=question,
            evidence=evidence,
            table_schemas=filtered_schemas,
            executor=executor,
            join_hints=join_hints,
        )

        # Apply table remapping if needed
        pred_sql = res.get("final_sql", "")
        remap_dict = table_remap.get(db_id, {})
        remapped_sql = _remap_table_names(pred_sql, remap_dict)
        pred_rows = res.get("rows")
        if remapped_sql != pred_sql:
            pred_rows, err2 = executor.execute(db_path, remapped_sql)
            if not err2:
                res["final_sql"] = remapped_sql
                res["rows"] = pred_rows
                res["error"] = None

        # Compare results using official set-equality
        is_correct = BIRDEvaluator.compare_results(gold_rows, pred_rows) if not gold_err else False

        return {
            "question_id": q_id,
            "db_id": db_id,
            "question": question,
            "gold_sql": gold_sql,
            "pred_sql": res.get("final_sql", ""),
            "correct": is_correct,
            "error": res.get("error"),
            "branch_used": res.get("branch_used"),
            "latency_s": res.get("latency_s", 0.0),
            "refine_rounds": res.get("refine_rounds", 0),
        }

    results = []
    correct_count = 0
    crash_count = 0

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_eval_one, q): q for q in queries_to_run}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if res.get("correct"):
                correct_count += 1
            if res.get("error"):
                crash_count += 1

            completed = len(results)
            if completed % 50 == 0 or completed == total_n:
                curr_ex = (correct_count / completed) * 100
                print(f"  [{completed}/{total_n}] Correct: {correct_count} ({curr_ex:.2f}% EX) | Crashes: {crash_count}")

    # Compute final metrics
    ex_score = (correct_count / total_n * 100) if total_n > 0 else 0.0
    crash_rate = (crash_count / total_n * 100) if total_n > 0 else 0.0
    latencies = [r.get("latency_s", 0.0) for r in results]
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0

    summary = {
        "backend": "sqlite",
        "benchmark": "BIRD",
        "total_queries": total_n,
        "correct_queries": correct_count,
        "execution_accuracy": round(ex_score, 2),
        "execution_crashes": crash_count,
        "crash_rate": round(crash_rate, 2),
        "mean_latency_s": round(mean_latency, 2),
        "ablations": {
            "no_ir": no_ir,
            "no_refine": no_refine,
            "ungated": ungated,
            "no_kg": no_kg,
            "no_embedding": no_embedding,
            "no_rerank": no_rerank,
            "no_values": no_values,
            "no_adaptive": no_adaptive,
            "no_multi_hop": no_multi_hop,
            "no_lexical": no_lexical,
        },
    }

    # Save outputs
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(output_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 65)
    print(f"BIRD EVALUATION COMPLETE: {correct_count}/{total_n} ({ex_score:.2f}% EX)")
    print(f"Crashes: {crash_count} ({crash_rate:.2f}%) | Mean Latency: {mean_latency:.2f}s")
    print(f"Results saved to: {output_dir}")
    print("=" * 65)

    return summary
