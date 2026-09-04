# Benchmark and Ablation Results

This document contains canonical experimental results on the open-weight **Qwen3.6-27B-FP8** model.

---

## 1. BIRD Development Benchmark Ablations ($N=1,315$)

All ablations evaluated on the 1,315 test split queries of the BIRD development benchmark:

| Ablation Configuration | Execution Accuracy (EX) | Execution Crashes | Latency / Query | Token Factor | Key Finding |
|---|---:|---:|---:|---:|---|
| **1. Direct SQL (No IR)** | **44.71%** (588 / 1,315) | 344 (26.16%) | ~3.2s | 0.21x | Model collapses without structured IR |
| **2. Single-Candidate Base** | **62.60%** (823 / 1,315) | 3 (0.23%) | 40.7s | 0.95x | Structured IR fixes 99% of crashes (+17.89pp) |
| **3. Shipped Ensemble (Gated)** | **63.88%** (840 / 1,315) | 3 (0.23%) | 42.1s | 1.00x | Schema diversity adds +1.28pp |
| **4. Ungated Refinement** | **63.88%** (840 / 1,315) | 22 (1.67%) | 160.4s | 3.85x | 0.0pp gain; burns 3.8x compute |
| **5. No Refinement Loop** | **63.80%** (839 / 1,315) | 21 (1.60%) | 38.5s | 0.92x | Close to gated; gating adds stability |

---

## 2. Comparison with State-of-the-Art on Qwen-27B-FP8 ($N=1,534$)

Comparison against external SOTA systems running on the identical Qwen3.6-27B-FP8 model across all 1,534 BIRD development set questions:

| System | BIRD Dev EX ($N=1,534$) | Latency / Query | Total Benchmark Time | Total Tokens / Query | Efficiency Profile |
|---|---:|---:|---:|---:|---|
| **DAIL-SQL** (ICDE'24) | **53.46%** (820 / 1,534) | 2.99s | ~1.3 hours | 1,088 tokens | Fast single-turn baseline |
| **Ours** (Shipped Ensemble) | **64.67%** (992 / 1,534) | 44.4s | ~18.9 hours | 17,117 tokens | High-throughput compiled pipeline |
| **DeepEye-SQL** (sota fork) | **65.65%** (1,007 / 1,534) | 1,506.5s (~25 min) | ~642.0 hours | 64,264 tokens | Unbounded test-time tree search |

### Summary:
- **vs. DAIL-SQL**: Ours delivers **+11.21pp higher execution accuracy** (992 vs. 820 queries correct).
- **vs. DeepEye-SQL**: Ours reaches **98.5% of SOTA accuracy** (64.67% vs. 65.65%, a 0.98pp gap / 15 queries) at **34.0x lower latency** and **3.8x fewer tokens**.


---

## 3. TEND (Document MongoDB) Benchmark Results ($N=1,210$)

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

- **Schema Discovery Rate**: **99.1%** (correct collection identified).
- **Dominant Failure Mode**: `value_mismatch` (**55.5%** of errors due to nested literal distortions).
