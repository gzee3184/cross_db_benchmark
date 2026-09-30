# BIRD Ablations

## Schema Discovery Routing Ablations ($N=1,534$)

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

## End-to-End Generation & Architectural Ablations ($N=1,534$)

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
| **Single-Candidate Base (`--single-candidate`)** | 1,534 | *In Progress* | — | ~100s | Evaluating deterministic single-turn IR compiler without dual arbitration (test split: 62.60%, 823/1,315) |
| **Compound Knockout (`--no-values --no-multi-hop --no-lexical`)** | 1,534 | *In Progress* | — | ~195s | Joint knockout isolating minimal routing components |
| **Ungated Refinement (`--ungated`)** | 1,533 | **61.58%** (944 / 1,533) | 30 (1.96%) | 160.4s | Unconditional refinement induces over-correction (-3.09pp vs Shipped) at 3.85x compute |
