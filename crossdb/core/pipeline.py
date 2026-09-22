"""End-to-end multi-candidate generation, arbitration, and refinement pipeline."""

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from crossdb.core.client import LLMClient
from crossdb.core.ir import DocumentQueryArgs, RelationalQueryArgs
from crossdb.core.refine_gate import RefinementGate
from crossdb.backends.sqlite.compiler import SQLiteCompiler
from crossdb.backends.sqlite.executor import SQLiteExecutor
from crossdb.backends.mongodb.compiler import MongoCompiler
from crossdb.backends.mongodb.executor import MongoExecutor


# Relational Tool Definition for Branch A
RELATIONAL_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "execute_relational_query",
        "description": "Execute a structured relational query compiled to SQLite.",
        "parameters": {
            "type": "object",
            "properties": {
                "collection_name": {
                    "type": "string",
                    "description": "Primary table name (e.g., 'customers')",
                },
                "projection": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to select (e.g., ['T1.id', 'T2.name'])",
                },
                "additional_collections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "collection_name": {"type": "string"},
                            "join_type": {"type": "string", "enum": ["INNER", "LEFT", "RIGHT"]},
                            "join_condition": {"type": "string"},
                        },
                        "required": ["collection_name", "join_condition"],
                    },
                    "description": "Joined tables and join conditions",
                },
                "filter_criteria": {
                    "type": "object",
                    "description": "Column filter conditions (e.g., {'T1.status': 'active'})",
                },
                "order_by": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string"},
                            "direction": {"type": "string", "enum": ["ASC", "DESC"]},
                        },
                        "required": ["column"],
                    },
                    "description": "Sort ordering",
                },
                "limit": {"type": "integer", "description": "Maximum rows to return"},
                "distinct": {"type": "boolean", "description": "Whether to return distinct rows"},
            },
            "required": ["collection_name", "projection"],
        },
    },
}

# Document Tool Definition for Branch A
DOCUMENT_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "execute_document_query",
        "description": "Execute a structured document query compiled to MongoDB aggregation pipeline.",
        "parameters": {
            "type": "object",
            "properties": {
                "collection_name": {
                    "type": "string",
                    "description": "Target collection name",
                },
                "match_criteria": {
                    "type": "object",
                    "description": "Initial $match filter criteria",
                },
                "pipeline_stages": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Sequential aggregation pipeline stages ($unwind, $lookup, $group)",
                },
                "projection": {
                    "type": "object",
                    "description": "$project stage specifications",
                },
                "limit": {"type": "integer", "description": "Maximum documents to return"},
            },
            "required": ["collection_name"],
        },
    },
}


class DualCandidatePipeline:
    """Orchestrates dual-candidate generation, cross-execution, and gated refinement."""

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        refine_gate: Optional[RefinementGate] = None,
        # Ablation flags:
        no_ir: bool = False,
        no_refine: bool = False,
        ungated: bool = False,
        max_refine_rounds: int = 2,
    ):
        """Initialize the pipeline with clients and ablation settings."""
        self.client = client or LLMClient()
        self.refine_gate = refine_gate or RefinementGate(enabled=not ungated)
        self.no_ir = no_ir
        self.no_refine = no_refine
        self.ungated = ungated
        self.max_refine_rounds = max_refine_rounds

        self.sqlite_compiler = SQLiteCompiler()
        self.mongo_compiler = MongoCompiler()

    def _build_relational_prompt(
        self,
        question: str,
        evidence: str,
        table_schemas: Dict[str, List[str]],
        join_hints: Optional[List[str]] = None,
    ) -> str:
        """Construct the prompt for relational Text-to-SQL generation."""
        schema_lines = []
        for t_name, cols in table_schemas.items():
            schema_lines.append(f"Table {t_name} (\n  " + ",\n  ".join(cols) + "\n)")

        hint_block = f"\nEvidence: {evidence}" if evidence else ""
        join_block = ""
        if join_hints:
            join_block = "\nCandidate Join Paths:\n" + "\n".join(f"- {h}" for h in join_hints)

        return (
            f"You are an expert SQL engineer. Given the database schema and question, "
            f"write a valid SQLite SQL query to answer the user's request.\n\n"
            f"Database Schema:\n" + "\n\n".join(schema_lines) +
            hint_block + join_block +
            f"\n\nQuestion: {question}\n\n"
            f"Generate the exact SQL query required. If tool calling is available, call the function."
        )

    def _build_document_prompt(
        self,
        question: str,
        collection_name: str,
        schema_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Construct the prompt for document Text-to-MQL generation."""
        schema_desc = ""
        if schema_info and "fields" in schema_info:
            fields = [f"  {f}: {t}" for f, t in list(schema_info["fields"].items())[:30]]
            schema_desc = f"\nCollection Schema for '{collection_name}':\n" + "\n".join(fields)

        return (
            f"You are an expert MongoDB engineer. Write a MongoDB aggregation pipeline "
            f"for collection '{collection_name}' to answer the following question.\n"
            f"{schema_desc}\n\n"
            f"Question: {question}\n\n"
            f"Return the aggregation pipeline as a JSON array of stages or call execute_document_query."
        )

    def run_relational(
        self,
        db_path: Any,
        question: str,
        evidence: str,
        table_schemas: Dict[str, List[str]],
        executor: SQLiteExecutor,
        join_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the full relational pipeline for a BIRD question.

        Returns:
            Dictionary with 'final_sql', 'rows', 'branch_used', 'latency_s', 'rounds'.
        """
        t0 = time.time()
        prompt = self._build_relational_prompt(question, evidence, table_schemas, join_hints)

        cand_a_sql = None
        cand_b_sql = None

        # Branch A: Structured IR Tool Call (omitted if --no-ir)
        if not self.no_ir:
            tool_call = self.client.generate_tool_call(
                prompt=prompt,
                tools=[RELATIONAL_TOOL_SPEC],
                system_prompt="You are a precise relational intermediate representation compiler.",
            )
            if tool_call and "collection_name" in tool_call:
                try:
                    args = RelationalQueryArgs(**tool_call)
                    cand_a_sql = self.sqlite_compiler.compile(args)
                except Exception:
                    cand_a_sql = None

        # Branch B: Free-Text Reference SQL
        ref_resp = self.client.generate(
            prompt=prompt,
            system_prompt="Return only the executable SQLite SQL query inside a ```sql ... ``` block.",
        )
        # Extract SQL from markdown or raw text
        cand_b_sql = self._clean_sql_block(ref_resp)

        # Primary selection and live execution
        sql_to_run = cand_a_sql or cand_b_sql
        branch = "ir" if cand_a_sql else "direct_sql"

        rows, err = executor.execute(db_path, sql_to_run) if sql_to_run else (None, "No SQL generated")

        # Dual-Execution Arbitration (if both candidates available)
        if cand_a_sql and cand_b_sql and cand_a_sql != cand_b_sql:
            rows_b, err_b = executor.execute(db_path, cand_b_sql)
            if err and not err_b:
                sql_to_run = cand_b_sql
                rows, err = rows_b, err_b
                branch = "arbitrated_ref"
            elif rows == rows_b and not err:
                branch = "consensus"

        # Bounded Refinement Loop (Module 6)
        rounds = 0
        if not self.no_refine and sql_to_run:
            while rounds < self.max_refine_rounds:
                should_refine = self.ungated or self.refine_gate.should_refine(err, rows)
                if not should_refine:
                    break

                rounds += 1
                refine_prompt = (
                    f"The previously generated SQL failed during execution:\n"
                    f"Query: {sql_to_run}\n"
                    f"Execution Error: {err or 'Query returned empty result (0 rows)'}\n\n"
                    f"Please fix the SQL query to resolve this error for question: {question}"
                )
                fixed_resp = self.client.generate(prompt=refine_prompt)
                fixed_sql = self._clean_sql_block(fixed_resp)
                if fixed_sql:
                    new_rows, new_err = executor.execute(db_path, fixed_sql)
                    if not new_err:
                        sql_to_run = fixed_sql
                        rows, err = new_rows, new_err
                        branch = f"refined_round_{rounds}"
                        break

        total_latency = time.time() - t0
        return {
            "final_sql": sql_to_run or "",
            "rows": rows,
            "error": err,
            "branch_used": branch,
            "latency_s": round(total_latency, 3),
            "refine_rounds": rounds,
        }

    def run_document(
        self,
        db_name: str,
        collection_name: str,
        question: str,
        schema_info: Optional[Dict[str, Any]],
        executor: MongoExecutor,
    ) -> Dict[str, Any]:
        """Execute the document pipeline for a TEND question."""
        t0 = time.time()
        prompt = self._build_document_prompt(question, collection_name, schema_info)

        pipeline = None
        branch = "direct_mql"

        # Branch A: Document IR (omitted if --no-ir)
        if not self.no_ir:
            tool_call = self.client.generate_tool_call(
                prompt=prompt,
                tools=[DOCUMENT_TOOL_SPEC],
                system_prompt="You are a precise document intermediate representation compiler.",
            )
            if tool_call and "collection_name" in tool_call:
                try:
                    args = DocumentQueryArgs(**tool_call)
                    pipeline = self.mongo_compiler.compile(args)
                    branch = "ir"
                except Exception:
                    pipeline = None

        # Fallback / Direct MQL
        if pipeline is None:
            raw_resp = self.client.generate(prompt=prompt)
            pipeline = self._clean_mql_pipeline(raw_resp)
            branch = "direct_mql"

        docs, err = executor.execute(db_name, collection_name, pipeline or []) if pipeline else (None, "No pipeline generated")

        # Refinement loop
        rounds = 0
        if not self.no_refine and pipeline:
            while rounds < self.max_refine_rounds:
                should_refine = self.ungated or (err is not None or (docs is not None and len(docs) == 0))
                if not should_refine:
                    break
                rounds += 1
                fix_prompt = (
                    f"The MongoDB pipeline failed or returned 0 documents:\n"
                    f"Error: {err}\n\n"
                    f"Please repair the aggregation pipeline for: {question}"
                )
                fixed = self._clean_mql_pipeline(self.client.generate(prompt=fix_prompt))
                if fixed:
                    new_docs, new_err = executor.execute(db_name, collection_name, fixed)
                    if not new_err:
                        docs, err = new_docs, new_err
                        pipeline = fixed
                        branch = f"refined_round_{rounds}"
                        break

        return {
            "pipeline": pipeline,
            "docs": docs,
            "error": err,
            "branch_used": branch,
            "latency_s": round(time.time() - t0, 3),
            "refine_rounds": rounds,
        }

    @staticmethod
    def _clean_sql_block(text: str) -> str:
        """Extract clean SQL string from model completion."""
        import re
        m = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("--")]
        return " ".join(lines).strip()

    @staticmethod
    def _clean_mql_pipeline(text: str) -> Optional[List[Dict[str, Any]]]:
        """Extract aggregation pipeline list from model completion."""
        import json
        import re
        m = re.search(r"\[\s*\{.*\}\s*\]", text, flags=re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        return None
