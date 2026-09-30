# Comparison with State-of-the-Art on BIRD (Qwen-27B-FP8, N=1,534)

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
