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
