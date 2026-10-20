# BIRD Analysis

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

## 2. Autonomous Agent Evaluation: Claude Code on BIRD ($N=1,534$)

Full development benchmark evaluated using headless sandboxed Claude Code (`claude -p`, max 15 turns) served by `Qwen/Qwen3.6-27B-FP8` via SGLang + Anthropic adapter. The agent had access to bash tools to run `sqlite3` CLI commands directly on dev databases.

### 2.1 Performance by Database

| Database | Evaluated (N) | Correct | Execution Accuracy (EX) | Mean Latency (s) | Mean Turns |
|---|---:|---:|---:|---:|---:|
| `california_schools` | 89 | 39 | **43.8%** | 88.0s | 6.0 |
| `card_games` | 191 | 70 | **36.6%** | 57.4s | 6.3 |
| `codebase_community` | 186 | 100 | **53.8%** | 42.7s | 5.5 |
| `debit_card_specializing` | 64 | 31 | **48.4%** | 57.5s | 6.4 |
| `european_football_2` | 129 | 71 | **55.0%** | 53.8s | 5.2 |
| `financial` | 106 | 47 | **44.3%** | 94.9s | 5.1 |
| `formula_1` | 174 | 76 | **43.7%** | 47.6s | 5.2 |
| `student_club` | 158 | 88 | **55.7%** | 42.2s | 5.5 |
| `superhero` | 129 | 96 | **74.4%** | 27.6s | 4.7 |
| `thrombosis_prediction` | 163 | 29 | **17.8%** | 106.9s | 6.1 |
| `toxicology` | 145 | 77 | **53.1%** | 52.6s | 6.6 |
| **Overall Benchmark Total** | **1,534** | **724** | **47.20%** | **59.3s** | **5.7** |

### 2.2 Performance by Query Difficulty

| Difficulty | Evaluated (N) | Correct | Claude Code EX | Shipped Pipeline EX | Delta vs. Ours |
|---|---:|---:|---:|---:|---:|
| **Simple** | 924 | 474 | **51.30%** | 70.59% | -19.29pp |
| **Moderate** | 464 | 195 | **42.03%** | 57.11% | -15.08pp |
| **Challenging** | 145 | 55 | **37.93%** | 51.03% | -13.10pp |
| **Total** | **1,534** | **724** | **47.20%** | **64.67%** | **-17.47pp** |

### 2.3 Failure & Error Profile
- **Clean Execution / Verification Rate**: Claude Code's interactive tool loop verifies SQL execution before returning, achieving a **99.93% syntax validity rate** (only 1 runtime syntax crash / 0.07%).
- **Timeouts / Missing Predictions**: 141 queries (9.19%) exceeded execution limits or turn caps (primarily on large databases such as `financial` and `thrombosis_prediction` where exploratory queries without indexed filters stalled).
- **Latency & Turn Overhead**: Average latency was **59.3s** per query with **5.7 interactive tool turns**, compared to **23.9s** for the single-pass compiled pipeline.

---

## 3. Backbone Model Comparison: Older vs. Newer Qwen on Our Pipeline ($N=1,534$)

Comparison of our latest compiled pipeline running across two generations of open-weight models evaluated on the official BIRD development set ($N=1,534$):
- **Older Model**: `Qwen/Qwen2.5-Coder-32B-Instruct` (served with TP=2 on 2x RTX A6000)
- **Newer Model**: `Qwen/Qwen3.6-27B-FP8` (served locally on RTX PRO 6000 Blackwell)

### 3.1 Overall & Difficulty Breakdown

| Difficulty Class | Questions ($N$) | Older Model (`Qwen2.5-Coder-32B`) | Newer Model (`Qwen3.6-27B-FP8`) | Generational Delta |
|---|---:|---:|---:|---:|
| **Simple** | 924 | 376 (40.69%) | **653 (70.59%)** | **+29.90pp** |
| **Moderate** | 464 | 150 (32.33%) | **265 (57.11%)** | **+24.78pp** |
| **Challenging** | 145 | 54 (37.24%) | **74 (51.03%)** | **+13.79pp** |
| **Overall Benchmark Total** | **1,534** | **580 (37.81%)** | **992 (64.67%)** | **+26.86pp** |
| **Execution Crashes** | 1,534 | 99 (6.45%) | **23 (1.50%)** | **-4.95pp crashes** |
| **Mean Latency** | 1,534 | 39.97s / query | **23.90s / query** | **1.67x faster** |

### 3.2 Performance by Database

| Database | Questions ($N$) | Older Model EX (`Qwen2.5-Coder-32B`) | Newer Model EX (`Qwen3.6-27B-FP8`) | Delta (pp) | Older Latency | Newer Latency |
|---|---:|---:|---:|---:|---:|---:|
| `california_schools` | 89 | 23.6% (21 / 89) | **64.0%** (57 / 89) | +40.4pp | 41.9s | 24.3s |
| `card_games` | 191 | 29.3% (56 / 191) | **63.4%** (121 / 191) | +34.1pp | 36.3s | 18.2s |
| `codebase_community` | 186 | 44.1% (82 / 186) | **69.4%** (129 / 186) | +25.3pp | 34.3s | 21.0s |
| `debit_card_specializing` | 64 | 32.8% (21 / 64) | **56.2%** (36 / 64) | +23.4pp | 48.6s | 23.1s |
| `european_football_2` | 129 | 45.0% (58 / 129) | **68.2%** (88 / 129) | +23.2pp | 40.4s | 24.8s |
| `financial` | 106 | 28.3% (30 / 106) | **57.5%** (61 / 106) | +29.2pp | 44.1s | 31.5s |
| `formula_1` | 174 | 35.1% (61 / 174) | **64.4%** (112 / 174) | +29.3pp | 42.5s | 25.1s |
| `student_club` | 158 | 45.6% (72 / 158) | **73.4%** (116 / 158) | +27.8pp | 38.7s | 20.4s |
| `superhero` | 129 | 54.3% (70 / 129) | **79.8%** (103 / 129) | +25.5pp | 34.6s | 19.8s |
| `thrombosis_prediction` | 163 | 34.4% (56 / 163) | **50.3%** (82 / 163) | +15.9pp | 40.8s | 33.2s |
| `toxicology` | 145 | 36.6% (53 / 145) | **60.0%** (87 / 145) | +23.4pp | 45.9s | 25.6s |
| **Total** | **1,534** | **37.81% (580 / 1,534)** | **64.67% (992 / 1,534)** | **+26.86pp** | **39.97s** | **23.90s** |

