# Implementation Plan: Full End-to-End Pipeline & Ablation Engine for CrossDB

This plan specifies the technical architecture and file-by-file changes to integrate the complete end-to-end evaluation pipeline for both relational (**BIRD / SQLite**) and document (**TEND / MongoDB**) benchmarks into [`cross_db_benchmark`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark).

---

## 1. Architectural Strategy: Zero Duplication & Modular Design

The repository already contains high-quality implementations of:
* **IR Schemas**: [`crossdb/core/ir.py`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/crossdb/core/ir.py)
* **LLM Client**: [`crossdb/core/client.py`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/crossdb/core/client.py)
* **Refinement Gate**: [`crossdb/core/refine_gate.py`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/crossdb/core/refine_gate.py)
* **SQLite Backend**: [`crossdb/backends/sqlite/`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/crossdb/backends/sqlite/) (`compiler.py`, `executor.py`, `evaluator.py`)
* **MongoDB Backend**: [`crossdb/backends/mongodb/`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/crossdb/backends/mongodb/) (`compiler.py`, `executor.py`, `evaluator.py`)

We will **strictly avoid duplicating** any of these existing modules. Instead, we will add only the missing functional layers:
1. **Schema Discovery (`crossdb/discovery/`)**:
   - `kg.py`: Clean, typed Field-Level Knowledge Graph (588 edges: foreign keys, shared keys, name patterns).
   - `retrieval.py`: Dense semantic retrieval (MiniLM embeddings / cosine similarity), property token reranker, value catalog matcher, and adaptive depth table routing.
   - Fully supports all 8 schema discovery ablation dimensions.
2. **End-to-End Pipeline Orchestration (`crossdb/core/pipeline.py`)**:
   - Executes Module 1 (Discovery) $\rightarrow$ Module 2 (Literal & Task Understanding) $\rightarrow$ Module 3 (Dual Candidate Generation) $\rightarrow$ Module 4 (Compilation via existing compilers) $\rightarrow$ Module 5 (Execution via existing executors & arbitration) $\rightarrow$ Module 6 (Gated Refinement via existing `RefinementGate`).
   - Supports generation ablations: `--no-ir`, `--no-refine`, `--ungated`.
3. **Benchmark Orchestrators (`crossdb/benchmarks/`)**:
   - `bird.py`: Loads BIRD questions/schemas, executes the pipeline with configurable concurrency, handles SQLite table remapping, and evaluates set-equality EX via `BIRDEvaluator`.
   - `tend.py`: Loads TEND questions (`TEND.json`), introspects/retrieves Mongo collections, executes aggregation pipelines via `MongoExecutor`, and evaluates EXC / EXF1 via `TENDEvaluator`.
4. **CLI Dispatcher (`crossdb/evaluate.py`)**:
   - Wires up the CLI arguments and dispatches to either the BIRD or TEND runner with all ablation flags, real-time progress logging, and saving `results/summary.json`.
5. **Documentation (`README.md`)**:
   - Minimally update `README.md` to document how to run the full BIRD/TEND benchmarks and ablations from the repository alone.

---

## 2. Proposed Changes

### Discovery Layer

#### [NEW] `crossdb/discovery/__init__.py`
Exports `FieldKnowledgeGraph`, `SchemaRetriever`, and discovery helper functions.

#### [NEW] `crossdb/discovery/kg.py`
Machine-agnostic, polished implementation of the Field-Level Knowledge Graph:
* Graph edges: `FK_REFERENCE`, `SHARED_KEY`, `NAME_PATTERN`.
* Case- and whitespace-insensitive property normalization (`_normalize_col_key`).
* BFS path-finding between candidate collections to supply foreign-key join paths.
* Zero internal paths or environment assumptions.

#### [NEW] `crossdb/discovery/retrieval.py`
Unified schema retriever supporting both relational tables (BIRD) and document collections (TEND):
* Dense embedding retrieval with cosine similarity (using `sentence-transformers/all-MiniLM-L6-v2` or lightweight cosine matrix).
* Property-name token overlap reranker (weight factor 0.15).
* Value catalog statistics matcher for question literal matching.
* Adaptive search depth routing.
* Switchable ablation flags:
  - `no_kg`: Disables knowledge graph edges.
  - `no_embedding`: Disables dense embeddings, falls back to lexical overlap.
  - `no_rerank`: Disables property token overlap reranking.
  - `no_values`: Disables value catalog literal boost.
  - `no_adaptive`: Disables adaptive candidate depth cutoff.
  - `no_multi_hop`: Disables multi-hop graph traversals.
  - `no_lexical`: Disables lexical overlap matching.

---

### Core Pipeline Layer

#### [NEW] `crossdb/core/pipeline.py`
Unified query generation and multi-candidate arbitration pipeline:
* **Task Understanding**: Extracts literals and target attributes from question & evidence hints.
* **Candidate Generation**:
  - Branch A: Generates structured IR tool call (`RelationalQueryArgs` / `DocumentQueryArgs`) using `client.generate_tool_call()`.
  - Branch B: Generates free-text reference query using `client.generate()`.
* **Compilation**: Invokes existing `SQLiteCompiler.compile()` or `MongoCompiler.compile()`.
* **Execution & Arbitration**:
  - Runs compiled query and reference query on live database using existing `SQLiteExecutor` or `MongoExecutor`.
  - Compares execution results; arbitrates on agreement or disagreement.
* **Gated Refinement Loop**:
  - If execution fails with syntax error or returns 0 rows, queries `RefinementGate.should_refine()`.
  - If triggered, performs bounded multi-turn diagnostic self-repair (respecting `--no-refine` and `--ungated`).

---

### Benchmark Layer

#### [NEW] `crossdb/benchmarks/__init__.py`
Exports `run_bird_benchmark` and `run_tend_benchmark`.

#### [NEW] `crossdb/benchmarks/bird.py`
Relational BIRD benchmark execution harness:
* Loads BIRD `dev.json`, `dev_tables.json`, and database `.sqlite` files.
* Executes the pipeline across queries using `concurrent.futures.ThreadPoolExecutor`.
* Performs table remapping to guarantee compiled queries match target SQLite table names without PascalCase collection mismatches.
* Evaluates execution correctness against gold SQL results using existing `BIRDEvaluator.compare_results()`.
* Records latency, token counts, and error classifications.

#### [NEW] `crossdb/benchmarks/tend.py`
Document TEND benchmark execution harness:
* Loads TEND `TEND.json` records across 11 MongoDB databases.
* Connects to MongoDB via standard `MONGO_URI` (default: `mongodb://localhost:27017`).
* Compiles document IR to aggregation pipelines, executes via `MongoExecutor`.
* Evaluates exact match and F1 score against gold reference results using existing `TENDEvaluator.compare_documents()`.
* Records latency and execution metrics.

---

### Entrypoint & Documentation

#### [MODIFY] `crossdb/evaluate.py`
* Expand `build_parser()` to include all 8 schema discovery ablation flags (`--no-kg`, `--no-embedding`, `--no-rerank`, `--no-values`, `--no-adaptive`, etc.) and execution options (`--limit`, `--db-id`, `--model`, `--base-url`).
* Connect `main()` to invoke `run_bird_benchmark()` or `run_tend_benchmark()` with the parsed arguments.
* Output rich summary tables and save `summary.json` and `results.json` into `--output-dir`.

#### [MODIFY] `README.md`
* Minimal updates to Section 5 (Run Evaluations) and Section 6 (Run Ablation Studies) to document exact turnkey commands for running the full BIRD pipeline, full TEND pipeline, and all ablation switches.
* Ensure all code snippets and examples are completely machine-agnostic.

---

## 3. Verification Plan

### Automated Tests
1. **Existing Unit Tests**:
   ```bash
   cd cross_db_benchmark && PYTHONPATH=. pytest -v tests/
   ```
   Ensure 100% of existing tests continue to pass.
2. **New Discovery & Pipeline Tests**:
   Create and run `tests/test_discovery.py` to verify:
   * Knowledge graph edge lookup and join path BFS.
   * Schema retriever candidate ranking and ablation flag toggling.
   * End-to-end pipeline compilation and refinement gate triggering.
3. **Smoke Run**:
   Run a fast, offline 5-query smoke test for both backends:
   ```bash
   python3 -m crossdb.evaluate --backend sqlite --limit 5 --output-dir results/smoke_bird
   ```

### Manual Verification
* Inspect all modified and new files to ensure zero hardcoded machine paths (`/export/scratch/...`) and clean, publication-grade docstrings.
* Confirm git status is clean and changes are staged locally without pushing (`git status`).
