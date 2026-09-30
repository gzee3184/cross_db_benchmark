# TEND (Document MongoDB) Analysis (N=1,210)

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
