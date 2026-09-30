# TEND Paradigm Comparison (Qwen-27B-FP8)

| Paradigm / Baseline | Strategy Description | Status / Accuracy ($N=1,210$) | Efficiency Profile |
|---|---|---|---|
| **Ours (CrossDB TEND)** | Intermediate Representation compilation to MongoDB pipelines | **Validated (32.23% EXC)** | 21.7s / 7,136 tokens |
| **SAG (Official Reference)** | Schema-as-Data Grounding with execution repair | **Validated (37.36% EXC)** | ~22.0s / 7,136 tokens |
| **MAC-MQL (Multi-Agent Modular)** | Zero-shot Selector $\to$ Decomposer $\to$ Execution Refiner | **Completed (15.04% EXC)** | 78.7s (28s clean) / 6,765 tokens |
| **SQL Pivot** | Natural Language $\to$ SQL Sketch $\to$ MQL Pipeline | **Completed (9.50% EXC)** | 0.0691 EXF1 / 429 predictions (771 context overflow) |
