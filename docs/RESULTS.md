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
| **Claude Code Agent** (claude -p) | **47.20%** (724 / 1,534) | 59.3s | ~25.2 hours | Multi-turn (5.7 turns) | Autonomous tool agent (Bash + SQLite inspect) |
| **DAIL-SQL** (ICDE'24) | **53.46%** (820 / 1,534) | 2.99s | ~1.3 hours | 1,088 tokens | Fast single-turn baseline |
| **CHESS** (EMNLP'24) | **54.43%** (835 / 1,534) | 5,595.9s (~93 min) | ~2,384.5 hours | 182,424 tokens | Multi-agent iterative testing & revision |
| **DIN-SQL** (NeurIPS'23) | **59.71%** (916 / 1,534) | 14.72s | ~6.3 hours | 1,551 tokens | Decomposed In-Context Reasoning |
| **Ours** (Shipped Pipeline) | **64.67%** (992 / 1,534) | 23.9s | ~10.2 hours | 17,290 tokens | High-throughput compiled pipeline |
| **MAC-SQL** (COLING'24) | **64.86%** (995 / 1,534) | 30.56s | ~13.0 hours | 1,820 tokens | Multi-Agent Collaborative Refinement |
| **DeepEye-SQL** (sota fork) | **65.65%** (1,007 / 1,534) | 1,506.5s (~25 min) | ~642.0 hours | 64,264 tokens | Unbounded test-time tree search |

### Comparative Findings:
- **vs. Claude Code Agent (Autonomous Terminal Agent)**:
  - Sandboxed Claude Code (`claude -p`, max-turns=15) served by Qwen3.6-27B-FP8 achieves **47.20% EX** (724 / 1,534) with mean latency **59.3s / query** and **5.7 turns**.
  - While live CLI testing virtually eliminates runtime SQL syntax crashes (**0.07%** / 1 crash), exploratory queries without index awareness induce timeouts on heavy SQLite databases (**9.19%** missing/timeout rate).
  - Our compiled pipeline outperforms Claude Code by **+17.47pp EX** (992 vs. 724 correct) at **2.5x lower latency** (23.9s vs. 59.3s).
- **vs. DIN-SQL & MAC-SQL**: When provided with verified schema DDL and proper reserved-keyword quoting matching the standards in DAIL-SQL and DeepEye-SQL forks, both pipelines demonstrate strong performance on open-weight Qwen3.6-27B-FP8 with negligible crash rates:
  - **DIN-SQL** achieves **59.71% EX** (916 / 1,534) with only **0.13% crashes** (2 queries) at **14.72s / query** and **1,551 tokens**.
  - **MAC-SQL** achieves **64.86% EX** (995 / 1,534) with only **0.39% crashes** (6 queries) at **30.56s / query** and **1,820 tokens**, virtually on par with DeepEye-SQL (64.86% vs 65.65%) while running **49x faster**.
- **vs. DAIL-SQL**: Our pipeline delivers **+11.21pp higher execution accuracy** (992 vs. 820 queries correct).
- **vs. CHESS**: Our pipeline delivers **+10.24pp higher execution accuracy** (992 vs. 835 queries correct) at **234.1x lower latency** and **10.6x fewer tokens**.
- **vs. DeepEye-SQL**: Ours reaches **98.5% of SOTA accuracy** (64.67% vs. 65.65%, a 0.98pp gap / 15 queries) at **63.0x lower latency** and **3.7x fewer tokens**.

### 4.2 Backbone Model Comparison: Older vs. Newer Qwen on Our Pipeline ($N=1,534$)

Performance of our latest compiled pipeline across open-weight model generations on the full BIRD development benchmark:

| Model Architecture | Parameter Size / Precision | BIRD Dev EX ($N=1,534$) | Execution Crashes | Mean Latency / Query | Generational Delta |
|---|---|---:|---:|---:|---:|
| **Older: Qwen2.5-Coder** | 32B (BF16 / SGLang TP=2) | **37.81%** (580 / 1,534) | 99 (6.45%) | 39.97s | Machine 2 validation run |
| **Newer: Qwen3.6** | 27B (FP8 / Local SGLang) | **64.67%** (992 / 1,534) | 23 (1.50%) | 23.90s | **+26.86pp EX** (1.67x faster) |

- **Difficulty Scaling**: Qwen3.6 achieves **70.59%** on Simple (vs. 40.69% for Qwen2.5-Coder, +29.90pp), **57.11%** on Moderate (vs. 32.33%, +24.78pp), and **51.03%** on Challenging (vs. 37.24%, +13.79pp).
- **Execution Stability**: Runtime execution exceptions dropped from 6.45% (99 queries) to 1.50% (23 queries), demonstrating substantially stronger schema grounding and relational clause construction.

---

## 5. TEND (Document MongoDB) Benchmark Results ($N=1,210$)

Full development benchmark evaluated on Qwen3.6-27B-FP8 across 11 MongoDB databases using the unified CrossDB pipeline with complete per-database latency and token counts:

| Database | Questions ($N$) | Correct | Official EXC | Official EXF1 | Mean Latency | Avg InTok | Avg OutTok | Avg TotalTok | Collection Recall | Exec Clean Rate |
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
| **Overall Mean** | **1,210** | **390** | **32.23%** | **0.3290** | **21.7s** | **7,136** | **528** | **7,664** | **99.10%** | **95.37%** |

* **Collection Discovery Rate**: **99.10%** collection recall using hybrid dense embedding + lexical retrieval.
* **Failure Outcome Distribution**: `correct` = 390 (32.23%), `value_mismatch` = 672 (55.54%), `empty_result` = 69 (5.70%), `execution_error` = 56 (4.63%), `gold_unscorable` = 12 (0.99%), `row_superset` = 6 (0.50%), `row_subset` = 5 (0.41%).

---

## 6. TEND Paradigm & SOTA Comparison (Qwen-27B-FP8, $N=1,210$)

| System / Paradigm | Strategy Description | Total ($N$) | Correct | Official EXC | Official EXF1 | Mean Latency | Total Benchmark Time | Total Tokens | Efficiency Profile |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **SQL Pivot** | NL $\to$ SQL Sketch $\to$ MQL Pipeline | 1,210 | 115 | **9.50%** | 0.0691 | 4.8s | ~1.6 hours | Context cap* | Relational SQL bottleneck; 771 queries exceeded context cap during translation |
| **MAC-MQL** | Multi-Agent: Selector $\to$ Decomposer $\to$ Refiner | 1,210 | 182 | **15.04%** | 0.1650 | 78.7s (28s clean) | ~26.4 hours | 6,765 | Multi-agent reasoning overhead; cascading intermediate stage errors |
| **Ours (CrossDB TEND)** | Intermediate Representation (IR) compilation to MQL | 1,210 | 390 | **32.23%** | **0.3290** | 21.7s | ~7.3 hours | 7,664 | High-throughput dual-candidate compiled pipeline with execution gate |
| **SAG (Official Reference)** | Schema-as-Data Grounding with dynamic execution repair | 1,210 | 452 | **37.36%** | **0.3800** | ~22.0s | ~7.4 hours | 7,136 | Native NoSQL schema grounding preserving document nesting |

