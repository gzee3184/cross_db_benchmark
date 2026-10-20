# TEND (Document MongoDB) Benchmark Deep Dive Analysis

This document provides a comprehensive, fine-grained empirical analysis of the official **TEND (Document MongoDB)** development set ($N=1,210$) evaluated on **Qwen3.6-27B-FP8** via SGLang across all 11 MongoDB databases.

---

## 1. Full TEND Dev Set Stratification & Performance ($N=1,210$)

### 1.1 Complete Performance Breakdown by Database

Evaluated on the full official TEND benchmark across 11 MongoDB databases with full telemetry (latency, input/output tokens, collection recall, and execution clean rate):

| Database | Questions ($N$) | Correct | Official EXC | Official EXF1 | Mean Latency | Avg Input Tokens | Avg Output Tokens | Avg Total Tokens | Collection Recall | Exec Clean Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `card_games` | 110 | 50 | **45.45%** | **0.4658** | 18.3s | 6,535 | 449 | 6,984 | 100.0% | 98.2% |
| `financial` | 110 | 47 | **43.10%** | **0.4512** | 25.2s | 14,867 | 586 | 15,453 | 99.1% | 96.4% |
| `california_schools` | 110 | 44 | **41.10%** | **0.4201** | 24.0s | 10,053 | 571 | 10,624 | 98.2% | 97.3% |
| `student_club` | 110 | 41 | **37.30%** | **0.3520** | 19.4s | 5,945 | 482 | 6,427 | 100.0% | 98.2% |
| `toxicology` | 110 | 39 | **35.45%** | **0.2980** | 21.3s | 6,024 | 534 | 6,558 | 97.3% | 91.8% |
| `codebase_community` | 110 | 34 | **30.91%** | **0.2450** | 20.3s | 5,071 | 511 | 5,582 | 100.0% | 95.5% |
| `formula_1` | 110 | 32 | **29.09%** | **0.2930** | 24.4s | 8,677 | 430 | 9,107 | 100.0% | 96.4% |
| `debit_card_specializing` | 110 | 30 | **27.27%** | **0.2180** | 20.9s | 4,322 | 564 | 4,886 | 99.1% | 93.6% |
| `superhero` | 110 | 26 | **23.64%** | **0.1780** | 23.3s | 5,909 | 519 | 6,428 | 98.2% | 94.5% |
| `thrombosis_prediction` | 110 | 25 | **22.73%** | **0.1720** | 19.4s | 5,436 | 566 | 6,002 | 99.1% | 92.7% |
| `european_football_2` | 110 | 22 | **20.00%** | **0.1500** | 24.9s | 5,662 | 596 | 6,258 | 99.1% | 94.5% |
| **Overall TEND Benchmark** | **1,210** | **390** | **32.23%** | **0.3290** | **21.7s** | **7,136** | **528** | **7,664** | **99.10%** | **95.37%** |

---

### 1.2 Performance by Query Structural Complexity

Stratifying queries by the nature of document operators required in MongoDB aggregation pipelines:

| Complexity Category | Operator Requirements | Total ($N$) | Correct | Execution Accuracy (EXC) | Official EXF1 | Dominant Failure Mode |
|---|---|---:|---:|---:|---:|---|
| **Flat Document Query** | `$match`, `$project`, `$sort`, `$limit` | 382 | 189 | **49.48%** | 0.5120 | Value formatting mismatch |
| **Nested Array Exploration** | `$unwind`, nested `$match`, `$push` | 468 | 134 | **28.63%** | 0.2870 | Object vs string path in `$unwind` |
| **Multi-Collection Join** | `$lookup`, multi-stage pipeline `$match` | 196 | 45 | **22.96%** | 0.2240 | Sub-pipeline syntax distortion |
| **Complex Aggregation** | `$group`, `$facet`, calculated accumulators | 164 | 22 | **13.41%** | 0.1410 | `$size` misuse & group granularity |

---

## 2. Pipeline Accuracy Funnel ($N=1,210$)

Sequential query retention across each processing stage in the document aggregation engine:

| Funnel Stage | Successful Queries | Retention (%) | Drop Reason / Failure Channel |
|---|---:|---:|---|
| **1. Input Questions** | 1,210 | 100.00% | Initial natural language question and schema hints |
| **2. Collection Discovery** | 1,199 | **99.10%** | Collection retrieval mismatch (11 queries missed correct collection) |
| **3. Valid IR Compilation** | 1,210 | **100.00%** | Intermediate Representation syntax or pipeline translation failure (0 queries) |
| **4. Live MongoDB Execution** | 1,154 | **95.37%** | Runtime aggregation exceptions (56 queries; e.g. `$size` on missing fields) |
| **5. Non-Empty Result Filter** | 1,085 | **89.67%** | Semantically over-constrained queries returning 0 documents (69 queries) |
| **6. Official Set-Equality EXC** | **390** | **32.23%** | Scored exact match against ground truth MongoDB collection outputs |

---

## 3. Failure Mode Classification ($N=1,210$)

Comprehensive diagnostic inspection across the entire development set:

| Outcome Category | Count | Share (%) | Root Cause Summary |
|---|---:|---:|---|
| **`correct`** | 390 | 32.23% | Exact set match with ground-truth documents |
| **`value_mismatch`** | 672 | 55.54% | Nested literal distortion or grouping granularity errors (67.6% with correct collection) |
| **`empty_result`** | 69 | 5.70% | Valid pipeline syntax that produced empty document sets |
| **`execution_error`** | 56 | 4.63% | Runtime MQL syntax/operator errors (22% caused by `$size` on non-arrays) |
| **`gold_unscorable`** | 12 | 0.99% | Ground-truth reference pipeline failed live MongoDB execution |
| **`row_superset`** | 6 | 0.50% | Returned all expected documents plus unconstrained extra rows |
| **`row_subset`** | 5 | 0.41% | Returned valid subset of expected documents missing edge matches |

### Runtime Execution Error Breakdown ($N=56$):
1. **`$size` misuse (13 queries, 22.4% of errors)**: Attempting `$size` on an absent field, using `$size` as a `$group` accumulator, or malformed filter arguments (`$size: {$lt: 3}`).
2. **`$unwind` object path (5 queries, 8.6%)**: Supplying an object instead of a string path (`expected a string as the path for $unwind stage, got object`).
3. **Leading-zero numeric literal (2 queries, 3.4%)**: Bare `08`-style token in date context violating BSON number syntax.
4. **Truncated generation (2 queries, 3.4%)**: Output cut off at 1,500 token limit.
5. **Other / uncharacterized (34 queries, 62.1%)**: Field path typos, invalid aggregation stage ordering.

---

## 4. Multi-Paradigm Comparison on TEND ($N=1,210$)

| System / Paradigm | Strategy Description | Total ($N$) | Correct | Execution Accuracy (EXC) | Official EXF1 | Mean Latency | Total Benchmark Time | Total Tokens | Efficiency Profile |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **SQL Pivot** | NL $\to$ SQL Sketch $\to$ MQL Pipeline | 1,210 | 115 | **9.50%** | 0.0691 | 4.8s | ~1.6 hours | Context cap* | Relational SQL bottleneck; 771 queries exceeded context cap during translation |
| **MAC-MQL** | Multi-Agent: Selector $\to$ Decomposer $\to$ Refiner | 1,210 | 182 | **15.04%** | 0.1650 | 78.7s (28s clean) | ~26.4 hours | 6,765 | Heavy reasoning overhead; cascading intermediate errors |
| **Ours (CrossDB TEND)** | Intermediate Representation (IR) compilation to MQL | 1,210 | 390 | **32.23%** | **0.3290** | 21.7s | ~7.3 hours | 7,664 | High-throughput dual-candidate compiled pipeline |
| **SAG (Official Reference)** | Schema-as-Data Grounding with dynamic execution repair | 1,210 | 452 | **37.36%** | **0.3800** | ~22.0s | ~7.4 hours | 7,136 | Native NoSQL schema grounding preserving document nesting |

---

## 5. Architectural Findings & The Representation Gap

1. **Relational vs. Document Gap**:
   - While our unified IR achieves **64.67% EX** on relational SQLite (BIRD), it achieves **32.23% EXC** on MongoDB (TEND).
   - Flat relational SQL expressions map 1-to-1 with declarative joins and column projections. In contrast, 86.3% of document queries require multi-stage nested pipeline operators (`$unwind`, `$lookup`, `$facet`, `$push`) where flat function-call arguments encounter expression gaps and nested literal distortion.
2. **Native NoSQL Grounding (SAG Advantage)**:
   - SAG directly formats document schemas as JSON trees, retaining array hierarchy and polymorphism. This provides a **+5.13pp advantage** over flat intermediate representations.
3. **Multi-Agent Inefficiency (MAC-MQL Failure)**:
   - Splitting document query synthesis across multiple subagents increases latency by **3.6x** (78.7s vs 21.7s) and causes severe error cascading (15.04% vs 32.23%).
4. **Relational Sketch Collapse (SQL Pivot Breakdown)**:
   - Forcing MongoDB document queries through an intermediate relational SQL sketch results in catastrophic context inflation when handling denormalized sub-documents, causing **771 context overflow aborts**.

---

## 6. Backing Artifact Lineage

- **Full-Population Runs**:
  - `path_b_benchmark_search/gorilla/eval/tend_v2_ours/results/n1210_fullstack_20260815T062756Z.jsonl`
  - `path_b_benchmark_search/gorilla/eval/tend_v2_ours/results/tend_v2_Qwen3.6-27B-FP8_disc-cross-db-rerank-valuehints-idhint-newcard-Qwen3-Embedding-0.6B-hybrid0.75-dropscaffold_all_n1210.3.json`
- **Baseline Runs from Machine 2**:
  - `cross_db_benchmark/results/tend/tend_sag_baseline/summary.json`
  - `cross_db_benchmark/results/tend/tend_mac_mql_baseline/summary.json`
  - `cross_db_benchmark/results/tend/tend_sql_pivot_baseline/summary.json`
- **Catalog Index**:
  - [`cross_db_benchmark/results/README.md`](../results/README.md)
