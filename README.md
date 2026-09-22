# CrossDB: Cross-Paradigm Text-to-Database Benchmark Engine

CrossDB is a benchmark engine for natural language database interfaces.
The engine supports relational databases (SQLite / BIRD) and document databases (MongoDB / TEND).

---

## 1. Prerequisites

Install the required software:
- Python 3.10 or newer.
- SQLite 3.38 or newer.
- MongoDB 6.0 or newer (for document evaluation).
- An OpenAI-compatible LLM inference server (vLLM, SGLang, or NIM).

---

## 2. Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/cross-db-benchmark.git
   cd cross-db-benchmark
   ```

2. Create a virtual environment and install the package:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

---

## 3. Configuration

Set the environment variables:
```bash
# URL of your LLM inference server
export LM_BASE_URL="http://localhost:30000/v1"

# API key if required (use EMPTY for local servers)
export LM_API_KEY="EMPTY"

# Model name
export LM_MODEL="Qwen/Qwen3.6-27B-FP8"
```

---

## 4. Run Smoke Tests

Verify the installation with the smoke test suite:
```bash
bash scripts/smoke_test.sh
```

---

## 5. Run Evaluations

### Relational Benchmark (BIRD / SQLite)
Run the full BIRD benchmark across all 1,534 development queries:
```bash
export BIRD_DATA_DIR="/path/to/bird/data"
export BIRD_DB_DIR="/path/to/bird/databases"

# Run turnkey runner:
bash scripts/run_bird.sh

# Or invoke directly via Python CLI:
python3 -m crossdb.evaluate --backend sqlite --data-dir "$BIRD_DATA_DIR" --db-dir "$BIRD_DB_DIR"
```

### Document Benchmark (TEND / MongoDB)
Run the full TEND benchmark across all 1,210 queries:
```bash
export TEND_DATA_DIR="/path/to/tend/data"
export MONGO_URI="mongodb://localhost:27017"

# Run turnkey runner:
bash scripts/run_tend.sh

# Or invoke directly via Python CLI:
python3 -m crossdb.evaluate --backend mongodb --data-dir "$TEND_DATA_DIR" --mongo-uri "$MONGO_URI"
```

---

## 6. Run Ablation Studies

Execute specific architectural and generation ablation configurations using command-line switches:

### 6.1 Schema Discovery Routing Ablations
```bash
# Disable 588-edge Field Knowledge Graph:
python3 -m crossdb.evaluate --backend sqlite --no-kg

# Disable value catalog statistics matching:
python3 -m crossdb.evaluate --backend sqlite --no-values

# Disable adaptive depth routing and property reranking (flat top-K):
python3 -m crossdb.evaluate --backend sqlite --no-adaptive --no-rerank

# Disable dense semantic embeddings (pure lexical discovery):
python3 -m crossdb.evaluate --backend sqlite --no-embedding
```

### 6.2 Generation & Refinement Ablations
```bash
# Direct query generation without Intermediate Representation (A1):
python3 -m crossdb.evaluate --backend sqlite --no-ir

# Disable refinement loop entirely (single turn, A3 Arm C):
python3 -m crossdb.evaluate --backend sqlite --no-refine

# Force multi-turn refinement unconditionally on all queries (A3 Arm B):
python3 -m crossdb.evaluate --backend sqlite --ungated
```

---

## 7. Documentation

Read the technical documents:
- [Architecture Details](docs/ARCHITECTURE.md)
- [Canonical Benchmark Results](docs/RESULTS.md)
