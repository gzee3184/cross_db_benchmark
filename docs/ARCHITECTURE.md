# System Architecture: Cross-Paradigm Text-to-Database Engine

This document explains the architecture of the CrossDB engine.
The engine translates natural language questions into database queries across two paradigms:
1. Relational databases (SQLite / BIRD).
2. Document databases (MongoDB / TEND).

---

## 1. Relational Architecture (SQLite / BIRD)

The relational pipeline converts natural language to SQLite SQL through five sequential stages:

```
[Natural Language Question + Evidence]
                 │
                 ▼
     1. Schema Linking & Knowledge Graph
                 │
                 ▼
     2. Zero-Shot Tool-Call IR Generation
                 │
                 ▼
     3. Relational Compiler (IR to SQLite SQL)
                 │
                 ▼
     4. Execution-Gated Refinement Loop
                 │
                 ▼
     5. Multi-Candidate Consensus Voting
                 │
                 ▼
          [Final SQLite SQL]
```

### Stage 1: Schema Linking and Knowledge Graph
- The engine extracts referenced entities from the user question.
- A schema knowledge graph links related tables through declared and inferred foreign keys.
- A dynamic value catalog identifies candidate literal matches for string filters.

### Stage 2: Tool-Call Intermediate Representation (IR) Generation
- The model receives the database schema and question.
- The model emits a structured JSON tool call (`RelationalQueryArgs`).
- The JSON call separates table selection, join relationships, filter predicates, and projections into explicit fields.

### Stage 3: Relational Compiler
- The compiler translates `RelationalQueryArgs` into valid SQLite SQL.
- Reserved keywords (such as `order`, `group`, and `by`) are escaped with backticks.
- Table aliases (`T1`, `T2`) and foreign key paths are resolved automatically.
- Float casting (`CAST(x AS REAL)`) is applied to division operations to prevent integer truncation.

### Stage 4: Execution-Gated Refinement Loop
- The compiled SQL executes against the SQLite database using a 30-second progress handler timeout.
- The `RefinementGate` evaluates the result:
  - If execution fails with an error, the model refines the query.
  - If execution returns zero rows, the model refines the query.
  - If execution returns one or more rows cleanly, refinement is skipped.
- Gating skips 90.2% of redundant model calls and eliminates regression errors.

### Stage 5: Multi-Candidate Consensus Voting
- Diverse prompt styles propose candidate queries.
- Candidates execute against the database.
- Results cluster into equivalence sets.
- The majority consensus cluster provides the final SQL.

---

## 2. Document Architecture (MongoDB / TEND)

The document pipeline converts natural language to MongoDB aggregation pipelines through four stages:

```
[Natural Language Question]
            │
            ▼
1. Dynamic Key Introspection
            │
            ▼
2. Document Tool-Call IR Generation
            │
            ▼
3. Aggregation Pipeline Compiler
            │
            ▼
4. PyMongo Execution & Metric Scorer
            │
            ▼
     [Final Result Documents]
```

### Stage 1: Dynamic Key Introspection
- MongoDB documents have flexible, semi-structured schemas.
- The engine introspects collection documents to extract nested keys and field value types.

### Stage 2: Document Tool-Call IR Generation
- The model emits `DocumentQueryArgs`.
- The call specifies the target collection, match filters, and pipeline transformation stages.

### Stage 3: Aggregation Pipeline Compiler
- The compiler translates `DocumentQueryArgs` into an ordered list of MongoDB aggregation stages:
  - `$match`: Filters documents matching criteria.
  - `$lookup`: Performs left outer joins to other collections.
  - `$unwind`: Deconstructs arrays into individual documents.
  - `$project`: Selects and renames fields.
  - `$limit`: Restricts output document counts.

### Stage 4: PyMongo Execution and Metric Scorer
- The aggregation pipeline executes against MongoDB using a 15-second timeout.
- The evaluator computes Execution Accuracy (EXC) and Execution F1 (EXF1) by comparing canonical document sets.

---

## 3. The Representational Boundary

The experimental results identify a representational boundary between relational and document pipelines:

1. **Relational Success (SQLite, 63.88% EX)**:
   - Relational queries map cleanly to flat tool arguments (FROM, JOIN, WHERE, SELECT).
   - The compiler resolves join trees and foreign keys deterministically.

2. **Document Expression Gap (MongoDB, 32.23% EXC)**:
   - Collection discovery succeeds at 99.1%.
   - Execution accuracy drops to 32.23%.
   - Flat function parameters cannot express multi-stage nested transformations (`$lookup` followed by `$unwind` and `$group`) without value distortion.
   - 55.5% of failures stem from literal value mismatches in nested documents.
