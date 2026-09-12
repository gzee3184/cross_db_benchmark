# Publication-Grade Architecture Diagram Specification and Generation Prompt

This document provides the complete prompt and technical specifications for generating a publication-grade (NeurIPS / VLDB / SIGMOD / ICDE) system architecture diagram for the **Cross-Database Benchmark Engine**.

---

## 1. Executive Visual Brief

* **Figure Title**: Unified Cross-Paradigm Text-to-Query Benchmarking Framework and Representational Boundary.
* **Aspect Ratio / Format**: Double-column landscape figure (width: 175–180 mm / 7.0 inches, aspect ratio ~ 16:9 or 21:9, vector SVG or 300+ DPI PDF/PNG).
* **Color Palette (Publication-Grade, Colorblind Safe, WCAG AAA compliant)**:
  * **Relational / SQLite Stream**: Deep Navy / Slate Blue (`#1E293B` text, `#0284C7` primary borders, `#F0F9FF` fill).
  * **Document / MongoDB Stream**: Emerald Green (`#065F46` text, `#059669` primary borders, `#ECFDF5` fill).
  * **Compiler / Deterministic Core**: Vibrant Violet / Indigo (`#4338CA` borders, `#EEF2FF` fill).
  * **Execution & Arbitration Gate**: Coral / Amber (`#D97706` warning/gate borders, `#FEF3C7` fill).
  * **Novelty Badges ([N1]–[N4])**: High-contrast Crimson / Ruby badges (`#BE123C` fill, `#FFFFFF` bold text).
  * **Background & Canvas**: Crisp white (`#FFFFFF`) with subtle grid or container bounding boxes (`#F8FAFC` fill, `#E2E8F0` stroke).
* **Typography**: Clean sans-serif (Inter, SF Pro, or Helvetica Neue) for all titles and descriptions; monospace (Fira Code, JetBrains Mono) for code tokens, table names, and JSON/MQL snippets.

---

## 2. Text-to-Image / Visual Diffusion Model Prompt

Use the following master prompt for generative visual engines (e.g., Midjourney v6, DALL-E 3, Recraft Vector, Ideogram 2.0):

```text
A clean, publication-grade academic system architecture diagram for a top-tier computer science conference (VLDB / SIGMOD / NeurIPS), vector illustration style, ultra-high resolution, sharp edges, white background, no photorealism, no 3D rendered bevels, crisp flat vector UI.

The diagram is organized into two horizontal parallel workflows (Relational on top, Document on bottom) with a central contrasting boundary banner:

TOP WORKFLOW (Relational Pipeline - SQLite / BIRD, cool blue palette):
1. Input block: "Natural Language Question + Evidence Hint" pointing into "Schema Discovery & 588-Edge KG".
2. Pre-Gen block: "Task Understanding & Shape Prediction" predicting expected row/col counts.
3. Generation block: "Dual-Representation LLM Generator" with a red callout badge "[N3] Dual-Gen", splitting into two parallel branches:
   - Branch A: "Typed Relational JSON IR" pointing to a violet box "Deterministic Relational Compiler [N1]" which emits "Compiled SQL Query".
   - Branch B: "Free-Text Reference SQL" emitting raw SQL text.
4. Execution & Arbitration block: Both queries run against a "Live SQLite Database", their row sets feed into "Dual-Execution Arbitration" comparing multiset equivalence.
5. Gating block: Diamond decision node "Refinement Gate [N2]" with two paths:
   - Clean path (90.2% queries): Directly ships to "Verified Output SQL (64.67% Official EX)".
   - Error/Empty path (9.8% queries): Loops through "Bounded Diagnostic Repair Loop (6 DB tools, 2 rounds max)".

BOTTOM WORKFLOW (Document Pipeline - MongoDB / TEND, forest emerald palette):
1. Input block: "Natural Language Question" pointing into "Schema Introspection (8-doc sampling, depth 14)".
2. Discovery block: "Hybrid Discovery (Dense 0.75 + BM25 0.25)" pointing to "Top-3 LLM Reranker & Prompt Assembly (Value Hints)".
3. Generation block: "Native MQL Aggregation Generator" emitting multi-stage aggregation pipeline ($match, $unwind, $group, $project).
4. Execution block: "PyMongo Live Execution Engine (15s Timeout)".
5. Retry block: Diamond decision node "Single-Shot Gated Retry" with error feedback loop.
6. Evaluator block: "Set-Based Output Evaluator (32.23% EXC)".

CENTRAL AXIS (The Representational Boundary [N4]):
A bold, modern horizontal comparison divider between the two workflows with badge "[N4] Representational Boundary":
Contrasts "Relational Flat Invariance (Single-level IR prevents 99% syntax crashes)" vs "Document Tree Restructuring ($unwind / $group requires native MQL + gated retry)".

Visual details: Professional minimalist conference paper figure, clean arrows with clear semantic labels, distinct dashed bounding boxes for pipeline stages, elegant rounded rectangles, sharp black labels, no garbled text, high contrast, readable at 0.5x zoom.
```

---

## 3. Structural Specification for Figma / Illustrator / Draw.io

For manual or programmatically rendered vector figures, implement the following exact grid layout:

```
+-------------------------------------------------------------------------------------------------------------------------------+
| FIGURE 1: UNIFIED CROSS-PARADIGM BENCHMARKING ENGINE & REPRESENTATIONAL BOUNDARY                                              |
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                               |
|  [RELATIONAL PIPELINE: BIRD / SQLITE] (Theme: Slate Blue / Indigo)                                                            |
|  +--------------------+     +------------------------+     +---------------------------------------------------------------+  |
|  | NLQ + Evidence     | --> | 1. Schema Discovery    | --> | 2. Task Understanding                                         |  |
|  | "How many schools  |     | - Dense Embedding      |     | - Extract Literals & Entities                                 |  |
|  |  in Fresno..."     |     | - 588-Edge Field KG    |     | - Predict Shape: 1 row x 1 col                                |  |
|  +--------------------+     +------------------------+     +---------------------------------------------------------------+  |
|                                                                    |                                                          |
|                                                                    v                                                          |
|                             +-----------------------------------------------------------------------------------------------+ |
|                             | 3. Dual-Representation Generator [N3] (1 Model Call, Suppressed Thinking)                     | |
|                             |  +---------------------------------------+  +----------------------------------------------+  | |
|                             |  | Branch A: Typed Relational JSON IR    |  | Branch B: Free-Text Reference SQL            |  | |
|                             |  | { collection, select, filters... }   |  | SELECT COUNT(DISTINCT T1.CDSCode)...         |  | |
|                             |  +---------------------------------------+  +----------------------------------------------+  | |
|                             +-----------------------------------------------------------------------------------------------+ |
|                                              |                                            |                                   |
|                                              v                                            |                                   |
|                             +-----------------------------------+                         |                                   |
|                             | 4. Deterministic Compiler [N1]    |                         |                                   |
|                             | - Keyword escaping (`col`)        |                         |                                   |
|                             | - Div CAST(x AS REAL) injection   |                         |                                   |
|                             | - Collate NOCASE normalization    |                         |                                   |
|                             +-----------------------------------+                         |                                   |
|                                              |                                            |                                   |
|                                              v (Compiled SQL)                             v (Reference SQL)                   |
|                             +-----------------------------------------------------------------------------------------------+ |
|                             | 5. Live SQLite Database Execution & Dual-Execution Arbitration                                 | |
|                             | Run both queries -> Compare row multiset -> Pick candidate using arbitration matrix           | |
|                             +-----------------------------------------------------------------------------------------------+ |
|                                                                    |                                                          |
|                                                                    v (Candidate Query)                                        |
|                                                     +------------------------------+                                          |
|                                                     | 6. Refinement Gate [N2]       |                                          |
|                                                     | (Error? 0 rows? Bad shape?)  |                                          |
|                                                     +------------------------------+                                          |
|                                                       /                          \                                            |
|                                     Pass: 90.2%      /                            \ Trigger: 9.8%                             |
|                                                     v                              v                                          |
|                                      +--------------------------+    +------------------------------------------+             |
|                                      | FINAL SQL OUTPUT         |    | Bounded Diagnostic Repair Loop           |             |
|                                      | Official EX: 64.67%      |    | - 6 DB diagnostic tools (describe, probe)|             |
|                                      | (992 / 1,534 correct)    |    | - Max 2 rounds, fallback protection      |             |
|                                      +--------------------------+    +------------------------------------------+             |
|                                                                                                                               |
|  ===========================================================================================================================  |
|  [N4] THE REPRESENTATIONAL BOUNDARY (Cross-Paradigm Structural Divergence)                                                   |
|  Relational Invariance: Flat rectangular schemas -> JSON IR decoupling eliminates 99% syntax crashes (+17.89pp EX).         |
|  Document Complexity: Nested tree structures ($unwind, $group, $lookup) -> IR collapses -> Native MQL + Gated Retry.       |
|  ===========================================================================================================================  |
|                                                                                                                               |
|  [DOCUMENT PIPELINE: TEND / MONGODB] (Theme: Emerald / Teal)                                                                 |
|  +--------------------+     +------------------------+     +------------------------+     +--------------------------------+  |
|  | NLQ Question       | --> | 1. Schema Introspect   | --> | 2. Hybrid Discovery    | --> | 3. Top-3 LLM Reranking & Hints |  |
|  | "Calculate total   |     | - 8 docs/col sample    |     | - Dense (0.75)         |     | - LLM Ordinal Selector         |  |
|  |  repayments..."    |     | - Depth-14 tree walk   |     | - BM25 Lexical (0.25)  |     | - Value Hints & `_id` Guard    |  |
|  +--------------------+     +------------------------+     +------------------------+     +--------------------------------+  |
|                                                                                                    |                          |
|                                                                                                    v                          |
|  +--------------------------+     +--------------------------+     +-------------------------------------------------------+  |
|  | 7. Set-Based Scorer      | <-- | 6. Gated Retry Engine    | <-- | 4. Native MQL Pipeline Generator                      |  |
|  | - Name-insensitive tuples|     | - Exception / 0 rows     |     | db.loans.aggregate([                                  |  |
|  | - Tolerance: 2 fields    |     | - 1-shot retry w/ values |     |   { $match }, { $unwind }, { $group }, { $project }   |  |
|  | Official EXC: 32.23%     |     | - No-regression guard    |     | ])                                                    |  |
|  +--------------------------+     +--------------------------+     +-------------------------------------------------------+  |
|                                                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. TikZ / LaTeX Specification for Paper Ingestion

For LaTeX / Overleaf submission, use this PGF/TikZ specification:

```latex
\begin{figure*}[t]
\centering
\resizebox{\textwidth}{!}{%
\begin{tikzpicture}[
    node distance=0.8cm and 1.2cm,
    font=\sffamily\footnotesize,
    box/.style={draw=slate!80, fill=slate!5, rounded corners=3pt, text width=2.4cm, align=center, minimum height=1.0cm, line width=0.8pt},
    rel_box/.style={draw=blue!70!black, fill=blue!5, rounded corners=3pt, text width=2.6cm, align=center, minimum height=1.0cm, line width=0.8pt},
    doc_box/.style={draw=emerald!70!black, fill=emerald!5, rounded corners=3pt, text width=2.6cm, align=center, minimum height=1.0cm, line width=0.8pt},
    comp_box/.style={draw=violet!80, fill=violet!5, rounded corners=3pt, text width=2.4cm, align=center, minimum height=1.0cm, line width=0.8pt},
    gate_box/.style={draw=amber!90!black, fill=amber!10, diamond, aspect=2, align=center, line width=0.8pt, inner sep=1pt},
    badge/.style={fill=crimson!90!black, text=white, font=\bfseries\tiny, rounded corners=2pt, inner sep=2pt},
    arrow/.style={-stealth, thick, color=gray!80!black}
]

% Top Row: Relational
\node[rel_box] (q_rel) {\textbf{Input}\\NLQ + Evidence};
\node[rel_box, right=of q_rel] (disco_rel) {\textbf{1. Schema Discovery}\\Dense + 588-Edge KG};
\node[rel_box, right=of disco_rel] (tu_rel) {\textbf{2. Task Understanding}\\Literals \& Shape};
\node[rel_box, right=of tu_rel, text width=3.2cm] (gen_rel) {\textbf{3. Dual Generator \tikz\node[badge]{N3};}\\Typed IR + Reference SQL};
\node[comp_box, below=0.6cm of gen_rel] (comp_rel) {\textbf{4. Compiler \tikz\node[badge]{N1};}\\SQLite Dialect Rules};
\node[rel_box, below=0.6cm of comp_rel, text width=3.4cm] (exec_rel) {\textbf{5. Live Execution \& Arb}\\SQLite Run + Multiset Compare};
\node[gate_box, left=1.2cm of exec_rel] (gate_rel) {\textbf{6. Gate \tikz\node[badge]{N2};}\\Err/0?};
\node[rel_box, left=1.2cm of gate_rel, fill=blue!15] (out_rel) {\textbf{Verified SQL}\\64.67\% Official EX};
\node[comp_box, above=0.6cm of gate_rel, text width=2.6cm] (loop_rel) {\textbf{Diagnostic Loop}\\6 DB Tools, 2 Rounds};

% Relational Connections
\draw[arrow] (q_rel) -- (disco_rel);
\draw[arrow] (disco_rel) -- (tu_rel);
\draw[arrow] (tu_rel) -- (gen_rel);
\draw[arrow] (gen_rel.south -| comp_rel.north) -- (comp_rel.north);
\draw[arrow] (comp_rel) -- (exec_rel);
\draw[arrow] (gen_rel.south east) to[out=270, in=0] (exec_rel.east);
\draw[arrow] (exec_rel) -- (gate_rel);
\draw[arrow] (gate_rel) -- node[below, font=\tiny]{Pass (90.2\%)} (out_rel);
\draw[arrow] (gate_rel) -- node[right, font=\tiny]{Trigger (9.8\%)} (loop_rel);
\draw[arrow] (loop_rel) -| (out_rel);

% Central Boundary
\node[draw=gray!50, fill=gray!10, rounded corners=4pt, text width=16.5cm, align=center, below=1.0cm of exec_rel, xshift=-4.5cm] (bound) {
    \textbf{\tikz\node[badge]{N4}; The Representational Boundary}: \textit{Relational Invariance} (flat tables) enables zero-SFT IR compilation ($+17.89$pp EX, 99\% syntax crash reduction). \textit{Document Hierarchy} (nested arrays) causes representation collapse in flat IR, requiring Native MQL + Gated Retry.
};

% Bottom Row: Document
\node[doc_box, below=1.0cm of bound.south west, xshift=1.4cm] (q_doc) {\textbf{Input}\\NLQ Question};
\node[doc_box, right=of q_doc] (intro_doc) {\textbf{1. Introspection}\\8-doc sample, depth 14};
\node[doc_box, right=of intro_doc] (disco_doc) {\textbf{2. Hybrid Discovery}\\Dense 0.75 + BM25 0.25};
\node[doc_box, right=of disco_doc] (rerank_doc) {\textbf{3. Reranking}\\Top-3 LLM + Value Hints};
\node[doc_box, right=of rerank_doc, text width=2.8cm] (gen_doc) {\textbf{4. Native MQL Gen}\\Aggregate Pipeline};
\node[doc_box, below=0.6cm of gen_doc] (exec_doc) {\textbf{5. PyMongo Exec}\\15s Timeout};
\node[gate_box, left=1.2cm of exec_doc] (gate_doc) {\textbf{6. Gated Retry}\\1-Shot Retry};
\node[doc_box, left=1.2cm of gate_doc, fill=emerald!15] (out_doc) {\textbf{Output Evaluator}\\32.23\% Official EXC};

% Document Connections
\draw[arrow] (q_doc) -- (intro_doc);
\draw[arrow] (intro_doc) -- (disco_doc);
\draw[arrow] (disco_doc) -- (rerank_doc);
\draw[arrow] (rerank_doc) -- (gen_doc);
\draw[arrow] (gen_doc) -- (exec_doc);
\draw[arrow] (exec_doc) -- (gate_doc);
\draw[arrow] (gate_doc) -- node[below, font=\tiny]{Pass / Scored} (out_doc);
\draw[arrow] (gate_doc.north) to[out=90, in=180] node[above, font=\tiny]{Retry} (gen_doc.west);

\end{tikzpicture}
}
\caption{\textbf{System Architecture and the Representational Boundary.} Top: The relational pipeline executes schema discovery, predicts answer shape, compiles typed IR into dialect SQL (\textbf{[N1]}), executes dual-representation queries (\textbf{[N3]}), and isolates defects via the execution-gated refinement loop (\textbf{[N2]}). Bottom: The document pipeline introspects nested structures and generates native MQL pipelines with gated retries. Middle: The representational boundary (\textbf{[N4]}) demarcates where intermediate representations succeed versus where native AST generation is required.}
\label{fig:crossdb_architecture}
\end{figure*}
```

---

## 5. Key Callout Elements to Verify in Generated Figures

1. **Novelty Badges**:
   * **[N1]**: Typed Relational IR Decoupling (attached to Compiler box).
   * **[N2]**: Execution-Gated Refinement Loop (attached to Gate diamond).
   * **[N3]**: Dual-Representation Generation (attached to Model Gen box).
   * **[N4]**: The Representational Boundary (attached to central cross-paradigm divider).
2. **Quantitative Checkpoints**:
   * Relational Discovery: 588 KG edges, Cosine similarity.
   * Relational Arbitration Gate: 90.2% Pass rate, 9.8% Trigger rate.
   * Relational Benchmark Result: 64.67% Official EX (992 / 1,534).
   * Document Discovery Formula: $\text{Score} = 0.75 \times \text{Dense} + 0.25 \times \text{BM25}$.
   * Document Benchmark Result: 32.23% Official EXC (390 / 1,210).
3. **No Stylistic Clutter**:
   * No 3D drop-shadows, no photorealistic textures, no decorative robot heads or anthropomorphic LLM icons.
   * All arrows must clearly indicate directionality of data flow.
