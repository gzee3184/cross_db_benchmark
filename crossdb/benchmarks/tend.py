"""Document TEND benchmark execution and evaluation runner."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from crossdb.backends.mongodb.evaluator import TENDEvaluator
from crossdb.backends.mongodb.executor import MongoExecutor
from crossdb.core.client import LLMClient
from crossdb.core.pipeline import DualCandidatePipeline
from crossdb.discovery.retrieval import SchemaRetriever


def run_tend_benchmark(
    data_dir: Path,
    output_dir: Path,
    mongo_uri: Optional[str] = None,
    schema_dir: Optional[Path] = None,
    concurrency: int = 8,
    limit: Optional[int] = None,
    db_id_filter: Optional[str] = None,
    # Ablations:
    no_ir: bool = False,
    no_refine: bool = False,
    ungated: bool = False,
    # Client:
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Execute the full TEND benchmark evaluation across MongoDB collections.

    Args:
        data_dir: Path to directory containing TEND.json.
        output_dir: Path to directory to save results.
        mongo_uri: MongoDB connection URI (defaults to MONGO_URI env var or mongodb://localhost:27017).
        schema_dir: Optional directory with pre-extracted schema JSON files.
        concurrency: Number of concurrent worker threads.
        limit: Optional maximum number of queries to evaluate.
        db_id_filter: Optional database name filter (e.g., 'card_games').
        no_ir: Disable IR compilation (Ablation A1).
        no_refine: Disable refinement loop (Ablation A3).
        ungated: Force refinement loop on all queries.
        client: Optional custom LLMClient instance.

    Returns:
        Summary metrics dictionary.
    """
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load TEND.json
    tend_json_path = data_dir / "TEND.json"
    if not tend_json_path.exists():
        candidates = list(data_dir.glob("**/TEND.json"))
        if candidates:
            tend_json_path = candidates[0]
        else:
            raise FileNotFoundError(f"Could not find TEND.json in {data_dir}")

    with open(tend_json_path, "r", encoding="utf-8") as f:
        all_records = json.load(f)

    # Filter records
    if db_id_filter:
        all_records = [r for r in all_records if r.get("db_id") == db_id_filter]
    if limit is not None and limit > 0:
        all_records = all_records[:limit]

    total_n = len(all_records)
    print(f"\nEvaluating TEND ({total_n} queries, concurrency={concurrency})...")

    # 2. Initialize Executor & Components
    executor = MongoExecutor(uri=mongo_uri)
    pipeline = DualCandidatePipeline(
        client=client or LLMClient(),
        no_ir=no_ir,
        no_refine=no_refine,
        ungated=ungated,
    )
    retriever = SchemaRetriever()

    # 3. Load pre-extracted schemas if schema_dir provided
    cached_schemas: Dict[str, Dict[str, Any]] = {}
    if schema_dir and Path(schema_dir).exists():
        for p in Path(schema_dir).glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    db_name = data.get("db_id", p.stem)
                    cached_schemas[db_name] = data.get("collections", {})
            except Exception:
                pass

    # 4. Worker function for parallel execution
    def _eval_one(record: Dict[str, Any]) -> Dict[str, Any]:
        rec_id = record.get("record_id", 0)
        db_id = record.get("db_id", "")
        # Normalize DB name for Mongo (e.g. tend_v2_<db_id> or <db_id>)
        mongo_db_name = f"tend_v2_{db_id}"

        question = record.get("NLQ", record.get("question", ""))
        if not question and "nl_queries" in record and record["nl_queries"]:
            question = record["nl_queries"][0]

        gold_mql = record.get("MQL", "")

        # Available collections from schema cache or live introspection
        schema_dict = cached_schemas.get(db_id, {})
        available_colls = list(schema_dict.keys()) if schema_dict else []

        if not available_colls:
            try:
                client_conn = executor.get_client()
                available_colls = client_conn[mongo_db_name].list_collection_names()
            except Exception:
                available_colls = ["default"]

        # Discover primary collection
        cand_colls = retriever.retrieve_collections(
            db_id=db_id,
            question=question,
            available_collections=available_colls,
            schema_dict=schema_dict,
        )
        target_coll = cand_colls[0] if cand_colls else "default"
        coll_schema = schema_dict.get(target_coll)

        # Run pipeline
        res = pipeline.run_document(
            db_name=mongo_db_name,
            collection_name=target_coll,
            question=question,
            schema_info=coll_schema,
            executor=executor,
        )

        pred_docs = res.get("docs")
        err = res.get("error")

        # Execute gold MQL for comparison
        gold_docs = None
        if gold_mql:
            gold_pipeline = DualCandidatePipeline._clean_mql_pipeline(gold_mql)
            if gold_pipeline:
                gold_docs, _ = executor.execute(mongo_db_name, target_coll, gold_pipeline)

        # Score with TENDEvaluator
        metrics = TENDEvaluator.compare_documents(gold_docs, pred_docs) if gold_docs is not None else {
            "exact_match": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0
        }

        return {
            "record_id": rec_id,
            "db_id": db_id,
            "collection": target_coll,
            "question": question,
            "gold_mql": gold_mql,
            "pred_pipeline": res.get("pipeline"),
            "exact_match": metrics.get("exact_match", 0.0),
            "f1": metrics.get("f1", 0.0),
            "error": err,
            "latency_s": res.get("latency_s", 0.0),
            "branch_used": res.get("branch_used"),
            "refine_rounds": res.get("refine_rounds", 0),
        }

    results = []
    exact_matches = 0
    f1_sum = 0.0
    crashes = 0

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_eval_one, r): r for r in all_records}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            em = res.get("exact_match", 0.0)
            f1 = res.get("f1", 0.0)
            exact_matches += int(em == 1.0)
            f1_sum += f1
            if res.get("error"):
                crashes += 1

            completed = len(results)
            if completed % 25 == 0 or completed == total_n:
                curr_exc = (exact_matches / completed) * 100
                curr_f1 = (f1_sum / completed)
                print(f"  [{completed}/{total_n}] EXC: {curr_exc:.2f}% | EXF1: {curr_f1:.3f} | Crashes: {crashes}")

    exc_score = (exact_matches / total_n * 100) if total_n > 0 else 0.0
    mean_f1 = (f1_sum / total_n) if total_n > 0 else 0.0
    latencies = [r.get("latency_s", 0.0) for r in results]
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0

    summary = {
        "backend": "mongodb",
        "benchmark": "TEND",
        "total_queries": total_n,
        "exact_matches": exact_matches,
        "official_exc": round(exc_score, 2),
        "official_exf1": round(mean_f1, 3),
        "execution_crashes": crashes,
        "mean_latency_s": round(mean_latency, 2),
        "ablations": {
            "no_ir": no_ir,
            "no_refine": no_refine,
            "ungated": ungated,
        },
    }

    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(output_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 65)
    print(f"TEND EVALUATION COMPLETE: EXC = {exc_score:.2f}% | EXF1 = {mean_f1:.3f}")
    print(f"Crashes: {crashes} | Mean Latency: {mean_latency:.2f}s")
    print(f"Results saved to: {output_dir}")
    print("=" * 65)

    return summary
