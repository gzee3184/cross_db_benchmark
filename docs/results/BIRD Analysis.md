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
