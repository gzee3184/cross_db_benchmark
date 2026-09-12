# Implementation Plan: BIRD Pipeline Telemetry Breakdown (Task 1) & Full Ablation Suite (Task 3)

This plan specifies the technical execution for **Task 1** (Latency, Token Usage, and Pipeline Accuracy Funnel Analysis on the full $N=1,534$ BIRD dev set) and **Task 3** (Full BIRD Pipeline Ablation Suite).

Per user instruction:
- **Tasks 2 and 4 are COMPLETED**:
  * Task 2: [`cross_db_benchmark/docs/ARCHITECTURE.md`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/docs/ARCHITECTURE.md) (Restructured ASD-STE100 technical documentation, Mermaid flowcharts, worked NLQ examples, and representational boundary).
  * Task 4: [`cross_db_benchmark/docs/DIAGRAM_PROMPT.md`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/docs/DIAGRAM_PROMPT.md) (Publication-grade NeurIPS/VLDB/SIGMOD diagram prompt, ASCII layout, and TikZ/LaTeX specification).
- **Tasks 1 and 3 are PLANNED below and will launch only upon user approval**.

---

## 1. Key Insights & Constraints

### Task 1 (Latency, Token Usage & Pipeline Accuracy Funnel)
* **Data Status**: We already possess the complete, uncorrupted $N=1,534$ telemetry dataset from the shipped run:
  * `pipeline_nim_v2_n135.json` (10.3 MB): Stores per-query latency (`latency_s`, `total_latency_s`), token counts (`input_tokens`, `output_tokens`, `total_input_tokens`, `total_output_tokens`), multi-candidate breakdown (`qwen-v2`, `qwen-plain`, `qwen-cot`), and refinement metadata (`refine_meta`, `rounds_used`, `tool_calls`).
  * `official_scored.json` (2.4 MB): Official set-equality match verdicts (992 / 1,534 = 64.67%), translation failure flags (1 / 1,534), execution error flags (23 / 1,534), and gold error flags (2 / 1,534).
* **Execution Advantage**: We do **not** need to spend 19 GPU hours re-running inference. We can execute an offline telemetry parser that computes exact statistical distributions (mean, median, p50, p90, p99, min, max, total) across every single pipeline phase and builds the publication accuracy funnel.

### Task 3 (Full BIRD Pipeline Ablations)
* **The 8 Ablation Dimensions**:
  1. `No structural self-correction` (`--no-correction` / `--no-exec-retry` / `--refine-loop`)
  2. `No value stat` (`--no-values` - value-aware linking / value catalog boost)
  3. `No property reranking` (`--no-rerank` - token overlap property match reranker)
  4. `No adaptive depth routing` (`--no-adaptive` - adaptive search depth)
  5. `No KG features` (`--no-kg` - 588-edge field knowledge graph)
  6. `No multi-hop traversal` (`--no-multi-hop` - multi-hop graph path traversal)
  7. `No embedding retrieval` (`--no-embedding` - dense semantic MiniLM embeddings)
  8. `No BM25 keywords` (Lexical property matching ablation; BM25 is MongoDB/TEND hybrid discovery, while BIRD uses Dense + KG + Property Reranking + Value Stats).
* **Execution Strategy**:
  * Running 8 complete LLM generation passes on all 1,534 queries would require ~150 GPU hours.
  * We propose a 3-tier execution structure:
    * **Tier 3.1 (Full $N=1,534$ Schema Discovery Routing Benchmark)**: Run all 8 ablation configurations across all 1,534 dev queries through the discovery engine (pure CPU / embedding, takes ~5 minutes total). Measures Top-1 Collection Accuracy, Table Recall@K, Table Precision, and Candidate Set Size.
    * **Tier 3.2 (Stratified $N=200$ End-to-End Generation Matrix)**: Run the standard official $N=200$ stratified dev benchmark across each ablation condition to measure the exact Execution Accuracy (EX) deltas.
    * **Tier 3.3 (Full $N=1,315$ Existing Baselines)**: Cross-reference and incorporate the completed full-scale $N=1,315$ generation ablations already recorded in the repository (`ablation_no_ir_n1315`, `ablation_refine_ungated_n1315`, `ablation_no_refine_n1315`).

---

## 2. Detailed Technical Plan

### Phase 1: Task 1 Implementation (Latency & Accuracy Funnel)

1. **Create Telemetry Parser Script**:
   * File: [`cross_db_benchmark/benchmarks/analyze_bird_pipeline.py`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/benchmarks/analyze_bird_pipeline.py)
   * Reads:
     - `/export/scratch/abrar008/llm_rag/path_a_bird_improvement/gorilla/eval/results/shipped_ensemble_full_dev_n1534/pipeline_nim_v2_n135.json`
     - `/export/scratch/abrar008/llm_rag/path_a_bird_improvement/gorilla/eval/results/shipped_ensemble_full_dev_n1534/official_scored.json`
   * Computes:
     - **Latency Breakdown**:
       * Overall end-to-end per query (mean, median, p90, p95, p99).
       * Per-candidate generation latency (`qwen-v2-t0.1`, `qwen-plain-t0.2`, `qwen-cot-t0.3`).
       * Arbitration & execution time.
       * Refinement loop latency for triggered queries (9.8%) vs bypassed queries (90.2%).
     - **Token Usage Breakdown**:
       * Input prompt tokens vs output completion tokens per query.
       * Total tokens across all 1,534 queries.
       * Token cost comparison: full-schema prompt vs schema-discovery filtered prompt.
       * Marginal token cost of multi-candidate arbitration and refinement loop.
     - **Pipeline Accuracy Funnel**:
       * **Level 0 (Total Questions)**: 1,534 (100.0%).
       * **Level 1 (Schema Discovery Coverage)**: Percentage of queries where all gold tables were successfully retrieved in the candidate set.
       * **Level 2 (Valid Query Representation)**: Queries producing valid, parseable JSON IR (1,533 / 1,534 = 99.93%; only 1 translation failure).
       * **Level 3 (Database Executability)**: Queries executing cleanly on SQLite without runtime syntax crashes (1,510 / 1,534 = 98.44%; 23 execution errors).
       * **Level 4 (Refinement Gate Resolution)**: Clean execution bypass (1,384 queries / 90.2%) vs gated diagnostic repair (150 queries / 9.8%, with recovered queries).
       * **Level 5 (Official Set-Equality Match)**: 992 / 1,534 = 64.67% Official EX.
       * Funnel breakdown sliced by difficulty: Easy (N=457), Medium (N=682), Hard (N=395).

2. **Generate Documentation Artifact**:
   * File: [`cross_db_benchmark/docs/LATENCY_AND_FUNNEL_ANALYSIS.md`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/docs/LATENCY_AND_FUNNEL_ANALYSIS.md)
   * Formatted Markdown tables, summary metrics, and a publication-ready Mermaid/ASCII funnel diagram.

---

### Phase 2: Task 3 Implementation (Ablation Suite)

1. **Create Discovery Ablation Engine**:
   * File: [`cross_db_benchmark/benchmarks/run_discovery_ablations.py`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/benchmarks/run_discovery_ablations.py)
   * Implements automated sweeps across all 1,534 BIRD dev queries with ablation flags:
     * `baseline`: Default discovery (MiniLM dense embeddings + 588-edge KG + property rerank + value stats + adaptive depth).
     * `no_kg`: `--no-kg` (disables all 588 KG edges).
     * `no_embedding`: `--no-embedding` (disables dense embedding search).
     * `no_rerank`: `--no-rerank` (disables token-overlap property reranker).
     * `no_values`: `--no-values` (disables value statistics linking).
     * `no_adaptive`: `--no-adaptive` (disables adaptive depth routing).
     * `no_multi_hop`: `--no-multi-hop` (disables multi-hop KG traversal).
     * `no_lexical`: Lexical / BM25 property matching ablation.
   * Outputs: Top-1 Collection Hit Rate, Target Table Recall, Candidate Set Cardinality, Runtime per query.

2. **Execute Generation Ablation Matrix**:
   * Run stratified dev evaluation ($N=200$) for the generation-level ablations:
     * `--no-correction` (disables structural self-correction / refinement).
     * `--no-exec-retry` (disables execution feedback retry).
     * `--no-values` (disables value hint injections into prompt).
     * `--no-kg` (end-to-end impact of KG omission).
   * Integrate results with the established $N=1,315$ generation ablation baselines:
     * `no_ir_n1315`: 44.71% EX (26.16% syntax crash).
     * `refine_ungated_n1315`: 63.88% EX (3.85x latency/token inflation).
     * `no_refine_n1315`: 63.80% EX.

3. **Generate Ablation Report**:
   * File: [`cross_db_benchmark/docs/ABLATION_STUDY.md`](file:///export/scratch/abrar008/llm_rag/cross_db_benchmark/docs/ABLATION_STUDY.md)
   * Unified ablation tables comparing discovery metrics ($N=1,534$) and end-to-end execution accuracy deltas ($N=200$ & $N=1,315$).

---

## 3. Launch & Execution Protocol

1. **User Review**: Present this plan to the user.
2. **Approval Gate**: Wait for explicit user confirmation before running execution scripts.
3. **Execution**: Upon approval, run Phase 1 (Task 1 telemetry analysis), then Phase 2 (Task 3 ablation suite), and commit documentation to the repository.
