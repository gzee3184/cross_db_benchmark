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

## 3. End-to-End Generation & Translation Ablations ($N=1,315$)

Evaluated on the test split queries of the BIRD development benchmark:

| Ablation Configuration | Execution Accuracy (EX) | Execution Crashes | Latency / Query | Token Factor | Architectural Finding |
|---|---:|---:|---:|---:|---|
| **1. Direct SQL (No IR)** | **44.71%** (588 / 1,315) | 344 (26.16%) | ~3.2s | 0.21x | Open-weight models suffer severe syntax collapse |
| **2. Single-Candidate Base** | **62.60%** (823 / 1,315) | 3 (0.23%) | 40.7s | 0.95x | Deterministic IR compiler eliminates 99% of crashes (+17.89pp) |
| **3. Shipped Ensemble (Gated)** | **63.88%** (840 / 1,315) | 3 (0.23%) | 42.1s | 1.00x | Multi-candidate arbitration adds +1.28pp accuracy |
| **4. Ungated Refinement** | **63.88%** (840 / 1,315) | 22 (1.67%) | 160.4s | 3.85x | 0.0pp gain; burns 3.85x compute without gating |
| **5. No Refinement Loop** | **63.80%** (839 / 1,315) | 21 (1.60%) | 38.5s | 0.92x | Gated refinement recovers targeted execution failures safely |

---

## 4. Comparison with State-of-the-Art on Qwen-27B-FP8 ($N=1,534$)

Comparison against external SOTA systems running on the identical Qwen3.6-27B-FP8 model across all 1,534 BIRD development set questions:

| System | BIRD Dev EX ($N=1,534$) | Latency / Query | Total Benchmark Time | Total Tokens / Query | Efficiency Profile |
|---|---:|---:|---:|---:|---|
| **DAIL-SQL** (ICDE'24) | **53.46%** (820 / 1,534) | 2.99s | ~1.3 hours | 1,088 tokens | Fast single-turn baseline |
| **Ours** (Shipped Pipeline) | **64.67%** (992 / 1,534) | 23.9s | ~10.2 hours | 17,290 tokens | High-throughput compiled pipeline |
| **DeepEye-SQL** (sota fork) | **65.65%** (1,007 / 1,534) | 1,506.5s (~25 min) | ~642.0 hours | 64,264 tokens | Unbounded test-time tree search |

* **vs. DAIL-SQL**: +11.21pp higher execution accuracy (992 vs. 820 queries correct).
* **vs. DeepEye-SQL**: Within 0.98pp of SOTA (15 queries difference) at **63.0x lower latency** and **3.7x fewer tokens**.

---

## 5. TEND (Document MongoDB) Benchmark Results ($N=1,210$)

Full development benchmark evaluated on Qwen3.6-27B-FP8 across 11 MongoDB databases:

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
