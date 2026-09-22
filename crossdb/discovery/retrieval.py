"""Unified schema retriever supporting relational tables and document collections."""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from crossdb.discovery.kg import FieldKnowledgeGraph, normalize_col_key


def _tokenize(text: str) -> Set[str]:
    """Tokenize a string into lowercase alphanumeric words."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    # Filter common stopwords
    stopwords = {"what", "is", "the", "are", "of", "and", "in", "to", "for", "a", "an", "how", "many", "which"}
    return {w for w in words if len(w) > 1 and w not in stopwords}


class SchemaRetriever:
    """Discovers, scores, and ranks candidate tables/collections for a query."""

    def __init__(
        self,
        kg: Optional[FieldKnowledgeGraph] = None,
        value_catalog: Optional[Dict[str, Any]] = None,
        embedding_model_name: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2",
        # Ablation switches:
        use_kg: bool = True,
        use_embedding: bool = True,
        use_rerank: bool = True,
        use_values: bool = True,
        use_adaptive: bool = True,
        use_multi_hop: bool = True,
        use_lexical: bool = True,
    ):
        """Initialize the retriever with components and ablation configurations."""
        self.kg = kg if use_kg else None
        self.value_catalog = value_catalog if use_values else None
        self.embedding_model_name = embedding_model_name
        self._embedder = None

        # Ablation flags
        self.use_kg = use_kg
        self.use_embedding = use_embedding
        self.use_rerank = use_rerank
        self.use_values = use_values
        self.use_adaptive = use_adaptive
        self.use_multi_hop = use_multi_hop
        self.use_lexical = use_lexical

    def _get_embedder(self):
        """Lazy-load the sentence transformer embedder if embeddings are enabled."""
        if not self.use_embedding:
            return None
        if self._embedder is None and self.embedding_model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.embedding_model_name)
            except Exception:
                # Fallback gracefully to lexical scoring if model cannot be downloaded/loaded
                self._embedder = None
        return self._embedder

    def score_lexical_overlap(self, question_tokens: Set[str], candidates: List[str]) -> float:
        """Compute token overlap score between question and candidate terms."""
        if not self.use_lexical or not question_tokens or not candidates:
            return 0.0
        cand_tokens = set()
        for c in candidates:
            cand_tokens.update(_tokenize(c))
        intersection = question_tokens.intersection(cand_tokens)
        return len(intersection) / math.sqrt(len(question_tokens) * max(1, len(cand_tokens)))

    def score_value_match(self, db_id: str, table_name: str, question: str) -> float:
        """Check if any literal value in question matches known catalog statistics."""
        if not self.use_values or not self.value_catalog:
            return 0.0
        # Check value catalog entries for this table
        db_catalog = self.value_catalog.get(db_id, {})
        table_catalog = db_catalog.get(table_name, {})
        if not table_catalog:
            return 0.0

        q_lower = question.lower()
        score = 0.0
        for col_name, stats in table_catalog.items():
            samples = stats.get("samples", [])
            for sample in samples:
                if str(sample).lower() in q_lower and len(str(sample)) > 2:
                    score += 0.3
                    break
        return min(score, 1.0)

    def retrieve_tables(
        self,
        db_id: str,
        question: str,
        evidence: str = "",
        table_schemas: Optional[Dict[str, List[str]]] = None,
        top_k: int = 5,
    ) -> List[str]:
        """Rank and return candidate tables for a relational database question.

        Args:
            db_id: Target database identifier.
            question: Natural language user question.
            evidence: Evidence hint or schema constraint notes.
            table_schemas: Dict of {table_name: [column_names]}.
            top_k: Nominal candidate count.

        Returns:
            List of ranked candidate table names.
        """
        if not table_schemas:
            return []

        all_tables = list(table_schemas.keys())
        if len(all_tables) <= top_k:
            return all_tables

        q_text = f"{question} {evidence}".strip()
        q_tokens = _tokenize(q_text)

        # 1. Base semantic or lexical scores
        scores: Dict[str, float] = {}
        embedder = self._get_embedder()

        if embedder is not None:
            try:
                table_texts = [
                    f"{t} {' '.join(cols[:15])}"
                    for t, cols in table_schemas.items()
                ]
                q_emb = embedder.encode(q_text, normalize_embeddings=True)
                t_embs = embedder.encode(table_texts, normalize_embeddings=True)
                for idx, t_name in enumerate(all_tables):
                    scores[t_name] = float(q_emb @ t_embs[idx])
            except Exception:
                embedder = None

        if embedder is None:
            # Fallback lexical scoring
            for t_name, cols in table_schemas.items():
                t_tokens = [t_name] + cols[:20]
                scores[t_name] = self.score_lexical_overlap(q_tokens, t_tokens)

        # 2. Property match rerank boost (Module 1, factor 0.15)
        if self.use_rerank:
            for t_name, cols in table_schemas.items():
                rerank_boost = self.score_lexical_overlap(q_tokens, cols) * 0.15
                scores[t_name] = scores.get(t_name, 0.0) + rerank_boost

        # 3. Value statistics catalog boost
        if self.use_values and self.value_catalog:
            for t_name in all_tables:
                v_boost = self.score_value_match(db_id, t_name, q_text)
                scores[t_name] = scores.get(t_name, 0.0) + v_boost

        # Sort candidate tables by total score
        ranked_tables = sorted(all_tables, key=lambda t: scores.get(t, 0.0), reverse=True)

        # 4. Adaptive depth routing or fixed top-K
        if self.use_adaptive and len(ranked_tables) > 1:
            top_score = scores.get(ranked_tables[0], 0.0)
            # Retain tables within 35% margin of top score, with minimum 2 and maximum top_k
            selected = [ranked_tables[0]]
            for t in ranked_tables[1:top_k]:
                if scores.get(t, 0.0) >= top_score * 0.65 or len(selected) < 2:
                    selected.append(t)
        else:
            selected = ranked_tables[:top_k]

        # 5. Knowledge Graph expansion (add necessary join path bridging tables)
        if self.use_kg and self.kg:
            expanded = list(selected)
            for i in range(len(selected)):
                for j in range(i + 1, len(selected)):
                    path = self.kg.find_join_path(
                        db_id,
                        selected[i],
                        selected[j],
                        allow_multi_hop=self.use_multi_hop,
                    )
                    if path:
                        for hop in path:
                            for t in (hop[0], hop[2]):
                                if t not in expanded and t in table_schemas:
                                    expanded.append(t)
            selected = expanded

        return selected

    def retrieve_collections(
        self,
        db_id: str,
        question: str,
        available_collections: List[str],
        schema_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> List[str]:
        """Rank and return candidate collections for a document (MongoDB/TEND) question.

        Args:
            db_id: Target database identifier.
            question: Natural language question.
            available_collections: List of collection names.
            schema_dict: Optional dict of {collection: {field_paths...}}.
            top_k: Maximum candidate collections to return.

        Returns:
            List of ranked collection names.
        """
        if len(available_collections) <= top_k:
            return available_collections

        q_tokens = _tokenize(question)
        scores: Dict[str, float] = {}

        for coll in available_collections:
            terms = [coll]
            if schema_dict and coll in schema_dict:
                # Add top-level fields
                c_schema = schema_dict[coll]
                if isinstance(c_schema, dict):
                    fields = list(c_schema.get("fields", {}).keys())
                    terms.extend(fields[:20])
            scores[coll] = self.score_lexical_overlap(q_tokens, terms)

        ranked = sorted(available_collections, key=lambda c: scores.get(c, 0.0), reverse=True)
        return ranked[:top_k]
