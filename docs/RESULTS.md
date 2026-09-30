# Benchmark and Ablation Results

This document contains canonical experimental results on the open-weight **Qwen3.6-27B-FP8** model across relational (BIRD / SQLite) and document (TEND / MongoDB) database benchmarks.

---

## 1. Full BIRD Dev Set Stratification and Accuracy Funnel ($N=1,534$)

### 1.1 Performance by Query Difficulty
Evaluated on the full official BIRD 2024-06-27 development set:

| Difficulty Class | Total Queries (N) | Correct Queries | Execution Accuracy (EX) | Mean Latency (s) | Mean Total Tokens |
|---|---:|---:|---:|---:|---:|
| **Simple** | 925 | 653 | **70.59%** | 20.3s | 17,251 |
| **Moderate** | 464 | 265 | **57.11%** | 28.3s | 17,437 |
| **Challenging** | 145 | 74 | **51.03%** | 32.5s | 17,070 |
| **Overall Dev Set** | **1,534** | **992** | **64.67%** | **23.9s** | **17,290** |

### 1.2 Pipeline Accuracy Funnel
Query retention rate across each sequential module of the relational engine:

| Funnel Stage | Successful Queries | Retention (%) | Failure Mode |
|---|---:|---:|---|
| **1. Input Questions** | 1,534 | 100.00% | Initial natural language questions and evidence hints |
| **2. Schema Discovery** | 1,149 | 74.90% | Missing required tables in candidate universe (385 queries) |
| **3. Valid IR Compilation** | 1,534 | 100.00% | JSON IR syntax or translation failure (0 queries) |
| **4. Live SQLite Execution** | 1,511 | 98.50% | Runtime database execution exceptions (23 queries) |
| **5. Refinement Gate Bypass** | 1,534 | 100.00% | Queries passing error and shape verification gates |
| **6. Official Set-Equality EX** | **992** | **64.67%** | Scored correct against ground truth database results |

---

## 2. Schema Discovery Routing Ablations ($N=1,534$)

All 8 architectural discovery configurations evaluated across all 1,534 BIRD development set questions:

| Configuration | Top-1 Hit (%) | Recall@3 (%) | Recall@5 (%) | Table Recall (%) | Latency (ms/q) |
|---|---:|---:|---:|---:|---:|
| **Full Pipeline (Baseline)** | **77.97%** | **97.07%** | **99.61%** | **98.82%** | 0.56 ms |
| **No KG Features (`--no-kg`)** | 76.66% (-1.30%) | 96.68% | 99.28% | 93.03% (-5.79%) | 0.42 ms |
| **No Dense Embedding (`--no-embedding`)** | 77.25% (-0.72%) | 95.50% | 98.96% | 98.78% | 0.54 ms |
| **No Property Rerank (`--no-rerank`)** | 77.71% (-0.26%) | 96.94% | 99.35% | 98.72% | 0.41 ms |
| **No Value Statistics (`--no-values`)** | 78.94% (+0.98%) | 97.52% | 99.74% | 98.94% | 0.20 ms |
| **No Adaptive Depth (`--no-adaptive`)** | 77.51% (-0.46%) | 96.87% | 99.35% | 98.72% | 0.41 ms |
| **No Multi-Hop (`--no-multi-hop`)** | 77.97% (0.00%) | 97.07% | 99.61% | 98.82% | 0.50 ms |
| **No Lexical Overlap (`--no-lexical`)** | 77.97% (0.00%) | 97.07% | 99.61% | 98.82% | 0.55 ms |

---

## 3. End-to-End Generation & Architectural Ablations

Evaluated across the full official BIRD development benchmark ($N=1,534$):

| Ablation Configuration | Evaluated $N$ | Execution Accuracy (EX) | Execution Crashes | Latency / Query | Architectural Finding |
|---|---:|---:|---:|---:|---|
| **Full Pipeline (Shipped Reference)** | 1,534 | **64.67%** (992 / 1,534) | 23 (1.50%) | 23.9s | Canonical multi-candidate compiled baseline |
| **No Value Catalog (`--no-values`)** | 1,533 | **52.77%** (809 / 1,533) | 215 (14.02%) | 23.5s | Loss of value statistics distorts column-literal alignment (-11.90pp) |
| **No Knowledge Graph (`--no-kg`)** | 1,533 | **51.34%** (787 / 1,533) | 243 (15.85%) | 23.8s | Schema retrieval starvation drops multi-table join recall (-13.33pp) |
| **No Adaptive Depth (`--no-adaptive`)** | 1,534 | **54.37%** (834 / 1,534) | 284 (18.51%) | 241.3s | Fixed exploration depth limits candidate discovery in complex schemas (-10.30pp) |
| **Direct SQL (No IR) (`--no-ir`)** | 1,534 | **50.33%** (772 / 1,534) | 388 (25.29%) | 152.7s | Direct SQL generation without structured IR induces severe syntax collapse (-14.34pp) |
| **No Lexical Overlap (`--no-lexical`)** | 1,534 | **47.26%** (725 / 1,534) | 365 (23.79%) | 198.2s | Disabling lexical matching impedes exact-match table and column identification (-17.41pp) |
| **No Refinement Loop (`--no-refine`)** | 1,534 | **46.81%** (718 / 1,534) | 355 (23.14%) | 147.7s | Disabling execution feedback prevents recovery from schema and runtime errors (-17.86pp) |
| **No Multi-Hop (`--no-multi-hop`)** | 1,534 | **46.48%** (713 / 1,534) | 383 (24.97%) | 197.6s | Restricting schema expansion to direct links starves multi-table relational joins (-18.19pp) |
| **No Dense Embedding (`--no-embedding`)** | 1,534 | **45.57%** (699 / 1,534) | 410 (26.73%) | 196.3s | Dense embedding removal causes catastrophic candidate recall failure (-19.10pp) |
| **Single-Candidate Base (`--single-candidate`)** | 1,534 | **46.94%** (720 / 1,534) | 366 (23.86%) | 188.3s | Disabling dual arbitration causes -17.73pp accuracy loss vs full reference |
| **Compound Knockout (`--no-values --no-multi-hop --no-lexical`)** | 1,534 | *Aborted* | — | — | Run cancelled to free GPU compute |
| **Ungated Refinement (`--ungated`)** | 1,534 | *Offloaded* | — | — | Unconditionally forced multi-turn refinement (remote Blackwell RTX 6000 sweep) |

---

## 4. Comparison with State-of-the-Art on Qwen-27B-FP8 ($N=1,534$)

Comparison against external SOTA systems running on the identical Qwen3.6-27B-FP8 model across all 1,534 BIRD development set questions:

| System | BIRD Dev EX ($N=1,534$) | Latency / Query | Total Benchmark Time | Total Tokens / Query | Efficiency Profile |
|---|---:|---:|---:|---:|---|
| **DAIL-SQL** (ICDE'24) | **53.46%** (820 / 1,534) | 2.99s | ~1.3 hours | 1,088 tokens | Fast single-turn baseline |
| **CHESS** (EMNLP'24) | **54.43%** (835 / 1,534) | 5,595.9s (~93 min) | ~2,384.5 hours | 182,424 tokens | Multi-agent iterative testing & revision |
| **DIN-SQL** (NeurIPS'23) | **59.71%** (916 / 1,534) | 14.72s | ~6.3 hours | 1,551 tokens | Decomposed In-Context Reasoning |
| **Ours** (Shipped Pipeline) | **64.67%** (992 / 1,534) | 23.9s | ~10.2 hours | 17,290 tokens | High-throughput compiled pipeline |
| **MAC-SQL** (COLING'24) | **64.86%** (995 / 1,534) | 30.56s | ~13.0 hours | 1,820 tokens | Multi-Agent Collaborative Refinement |
| **DeepEye-SQL** (sota fork) | **65.65%** (1,007 / 1,534) | 1,506.5s (~25 min) | ~642.0 hours | 64,264 tokens | Unbounded test-time tree search |

### Comparative Findings:
- **vs. DIN-SQL & MAC-SQL**: When provided with verified schema DDL and proper reserved-keyword quoting matching the standards in DAIL-SQL and DeepEye-SQL forks, both pipelines demonstrate strong performance on open-weight Qwen3.6-27B-FP8 with negligible crash rates:
  - **DIN-SQL** achieves **59.71% EX** (916 / 1,534) with only **0.13% crashes** (2 queries) at **14.72s / query** and **1,551 tokens**.
  - **MAC-SQL** achieves **64.86% EX** (995 / 1,534) with only **0.39% crashes** (6 queries) at **30.56s / query** and **1,820 tokens**, virtually on par with DeepEye-SQL (64.86% vs 65.65%) while running **49x faster**.
- **vs. DAIL-SQL**: Our pipeline delivers **+11.21pp higher execution accuracy** (992 vs. 820 queries correct).
- **vs. CHESS**: Our pipeline delivers **+10.24pp higher execution accuracy** (992 vs. 835 queries correct) at **234.1x lower latency** and **10.6x fewer tokens**.
- **vs. DeepEye-SQL**: Ours reaches **98.5% of SOTA accuracy** (64.67% vs. 65.65%, a 0.98pp gap / 15 queries) at **63.0x lower latency** and **3.7x fewer tokens**.

---

## 5. TEND (Document MongoDB) Benchmark Results ($N=1,210$)

Full development benchmark evaluated on Qwen3.6-27B-FP8 across 11 MongoDB databases using the unified CrossDB pipeline:

| Database | Questions (N) | Correct Queries | Official EXC | Official EXF1 | Latency / Query (s) |
|---|---:|---:|---:|---:|---:|
| `card_games` | 110 | 50 | **45.5%** | 0.466 | 18.3s |
| `financial` | 110 | 47 | **43.1%** | 0.451 | 25.2s |
| `california_schools` | 110 | 44 | **41.1%** | 0.420 | 24.0s |
| `student_club` | 110 | 41 | **37.3%** | 0.352 | 19.4s |
| `toxicology` | 110 | 39 | **35.5%** | 0.298 | 21.3s |
| `codebase_community` | 110 | 34 | **30.9%** | 0.245 | 18.2s |
| `formula_1` | 110 | 32 | **29.1%** | 0.293 | 24.4s |
| `debit_card_specializing` | 110 | 30 | **27.3%** | 0.218 | 20.9s |
| `superhero` | 110 | 26 | **23.6%** | 0.178 | 23.3s |
| `thrombosis_prediction` | 110 | 25 | **22.7%** | 0.172 | 19.4s |
| `european_football_2` | 110 | 22 | **20.0%** | 0.150 | 24.9s |
| **Overall Mean** | **1,210** | **390** | **32.23%** | **0.295** | **21.7s** |

* **Schema Discovery Rate**: **99.1%** collection recall.
* **Dominant Failure Mode**: `value_mismatch` (55.5% of errors caused by nested literal distortions in `$unwind`/`$group`).

---

## 6. TEND Paradigm Comparison (Qwen-27B-FP8)

| Paradigm / Baseline | Strategy Description | Status / Accuracy ($N=1,210$) | Efficiency Profile |
|---|---|---|---|
| **Ours (CrossDB TEND)** | Intermediate Representation compilation to MongoDB pipelines | **Validated (32.23% EXC)** | 21.7s / 7,136 tokens |
| **SAG (Official Reference)** | Schema-as-Data Grounding with execution repair | **Validated (37.36% EXC)** | ~22.0s / 7,136 tokens |
| **MAC-MQL (Multi-Agent Modular)** | Zero-shot Selector $\to$ Decomposer $\to$ Execution Refiner | **Completed (15.04% EXC)** | 78.7s (28s clean) / 6,765 tokens |
| **SQL Pivot** | Natural Language $\to$ SQL Sketch $\to$ MQL Pipeline | **Completed (9.50% EXC)** | 0.0691 EXF1 / 429 predictions (771 context overflow) |
