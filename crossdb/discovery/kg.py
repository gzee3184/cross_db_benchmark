"""Field-Level Knowledge Graph for relational schema discovery and join path resolution."""

import re
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


def normalize_col_key(name: str) -> str:
    """Normalize a column or property name for case/delimiter-invariant matching."""
    s = re.sub(r"[_\s\-]+", "", name.lower())
    # Strip common prefixes/suffixes like tbl_ or id
    return s


class FieldKnowledgeGraph:
    """Graph representation of table relationships, foreign keys, and semantic linkages."""

    def __init__(self, enabled: bool = True):
        """Initialize the knowledge graph.

        Args:
            enabled: If False, graph features and join-path lookups are bypassed (ablation).
        """
        self.enabled = enabled
        # Adjacency: db_id -> source_table -> list of (target_table, source_col, target_col, relation_type)
        self._adj: Dict[str, Dict[str, List[Tuple[str, str, str, str]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # Precomputed join paths: (db_id, table_a, table_b) -> join_clause_string
        self._precomputed_paths: Dict[Tuple[str, str, str], str] = {}

    def add_edge(
        self,
        db_id: str,
        table_a: str,
        col_a: str,
        table_b: str,
        col_b: str,
        relation_type: str = "FK_REFERENCE",
    ) -> None:
        """Add a bidirectional relationship between two table columns."""
        if not self.enabled:
            return
        t_a = table_a.lower()
        t_b = table_b.lower()
        self._adj[db_id][t_a].append((t_b, col_a, col_b, relation_type))
        self._adj[db_id][t_b].append((t_a, col_b, col_a, relation_type))

    def build_from_schemas(self, tables_list: List[Dict[str, Any]]) -> None:
        """Populate graph edges from standard schema metadata (e.g. BIRD tables.json).

        Args:
            tables_list: List of database schema definitions containing:
                'db_id', 'table_names_original', 'column_names_original', 'foreign_keys'
        """
        if not self.enabled:
            return

        for db in tables_list:
            db_id = db.get("db_id", "")
            table_names = db.get("table_names_original", [])
            col_entries = db.get("column_names_original", [])
            fks = db.get("foreign_keys", [])

            # 1. Foreign key edges (FK_REFERENCE)
            for src_idx, tgt_idx in fks:
                if src_idx < len(col_entries) and tgt_idx < len(col_entries):
                    src_tbl_id, src_col = col_entries[src_idx]
                    tgt_tbl_id, tgt_col = col_entries[tgt_idx]
                    if 0 <= src_tbl_id < len(table_names) and 0 <= tgt_tbl_id < len(table_names):
                        src_tbl = table_names[src_tbl_id]
                        tgt_tbl = table_names[tgt_tbl_id]
                        self.add_edge(db_id, src_tbl, src_col, tgt_tbl, tgt_col, "FK_REFERENCE")

            # 2. Shared identifier columns (SHARED_KEY)
            cols_by_norm: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
            for tbl_id, col_name in col_entries:
                if tbl_id >= 0 and tbl_id < len(table_names):
                    tbl_name = table_names[tbl_id]
                    norm = normalize_col_key(col_name)
                    if norm.endswith("id") or norm.endswith("code") or norm.endswith("key"):
                        cols_by_norm[norm].append((tbl_name, col_name))

            for norm_key, occurrences in cols_by_norm.items():
                if 1 < len(occurrences) <= 5:
                    for i in range(len(occurrences)):
                        for j in range(i + 1, len(occurrences)):
                            t1, c1 = occurrences[i]
                            t2, c2 = occurrences[j]
                            if t1.lower() != t2.lower():
                                self.add_edge(db_id, t1, c1, t2, c2, "SHARED_KEY")

    def load_precomputed_join_paths(self, paths_dict: Dict[str, Any]) -> None:
        """Load precomputed BFS join paths for fast lookup."""
        if not self.enabled:
            return
        for key, val in paths_dict.items():
            # key format: "db_id:table_a:table_b" or similar
            parts = key.split(":")
            if len(parts) == 3:
                db_id, t_a, t_b = parts
                self._precomputed_paths[(db_id, t_a.lower(), t_b.lower())] = val
                self._precomputed_paths[(db_id, t_b.lower(), t_a.lower())] = val

    def find_join_path(
        self,
        db_id: str,
        start_table: str,
        end_table: str,
        max_hops: int = 3,
        allow_multi_hop: bool = True,
    ) -> Optional[List[Tuple[str, str, str, str]]]:
        """Find the shortest join path between two tables using BFS.

        Args:
            db_id: Database identifier.
            start_table: Origin table name.
            end_table: Destination table name.
            max_hops: Maximum traversal depth.
            allow_multi_hop: If False, only 1-hop direct relationships are accepted.

        Returns:
            List of (from_tbl, from_col, to_tbl, to_col) hops, or None if no path found.
        """
        if not self.enabled:
            return None

        s_tbl = start_table.lower()
        e_tbl = end_table.lower()

        if s_tbl == e_tbl:
            return []

        # Check precomputed paths
        pre = self._precomputed_paths.get((db_id, s_tbl, e_tbl))
        if pre and isinstance(pre, list):
            return pre

        adj = self._adj.get(db_id, {})
        if s_tbl not in adj or e_tbl not in adj:
            return None

        hops_limit = 1 if not allow_multi_hop else max_hops

        queue: deque = deque([(s_tbl, [])])
        visited: Set[str] = {s_tbl}

        while queue:
            curr_tbl, path = queue.popleft()
            if len(path) >= hops_limit:
                continue

            for next_tbl, src_col, tgt_col, rel in adj.get(curr_tbl, []):
                new_hop = (curr_tbl, src_col, next_tbl, tgt_col)
                if next_tbl == e_tbl:
                    return path + [new_hop]
                if next_tbl not in visited:
                    visited.add(next_tbl)
                    queue.append((next_tbl, path + [new_hop]))

        return None

    def get_related_tables(self, db_id: str, table_name: str) -> List[str]:
        """Return all tables directly connected to the specified table."""
        if not self.enabled:
            return []
        t = table_name.lower()
        adj = self._adj.get(db_id, {})
        neighbors = set()
        for next_tbl, _, _, _ in adj.get(t, []):
            neighbors.add(next_tbl)
        return sorted(list(neighbors))
