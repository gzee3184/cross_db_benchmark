"""Relational query compiler for SQLite.

Converts RelationalQueryArgs intermediate representation to valid SQLite SQL.
"""

from typing import Dict, List, Optional
from crossdb.core.ir import RelationalQueryArgs

SQLITE_RESERVED_WORDS = {
    "order", "group", "by", "select", "from", "where", "limit",
    "table", "index", "view", "join", "inner", "outer", "left",
    "right", "full", "cross", "on", "using", "as", "check", "default"
}


class SQLiteCompiler:
    """Compiles structured relational tool arguments to executable SQLite SQL."""

    def __init__(self):
        pass

    def quote_identifier(self, name: str) -> str:
        """Escape SQLite keywords or names with special characters."""
        clean = name.strip()
        if clean.lower() in SQLITE_RESERVED_WORDS or " " in clean or "-" in clean:
            return f"`{clean}`"
        return clean

    def compile(self, args: RelationalQueryArgs) -> str:
        """Translate RelationalQueryArgs to a SQL query string.

        Args:
            args: The structured relational query arguments.

        Returns:
            A formatted SQLite SQL string.
        """
        # If the dual-generator provided clean reference SQL, prefer it
        if args.raw_reference_sql and args.raw_reference_sql.strip():
            raw = args.raw_reference_sql.strip().rstrip(";")
            return f"{raw};"

        aliases: Dict[str, str] = {}
        primary_table = args.collection_name.strip()
        aliases[primary_table] = "T1"
        alias_counter = 2

        # 1. FROM clause
        from_clause = f"{self.quote_identifier(primary_table)} AS T1"

        # 2. JOIN clauses
        join_clauses: List[str] = []
        for extra in (args.additional_collections or []):
            table = extra.collection_name.strip()
            alias = f"T{alias_counter}"
            aliases[table] = alias
            alias_counter += 1

            j_type = extra.join_type or "INNER"
            if extra.join_condition:
                join_clauses.append(
                    f"{j_type} JOIN {self.quote_identifier(table)} AS {alias} ON {extra.join_condition}"
                )
            else:
                join_clauses.append(f"{j_type} JOIN {self.quote_identifier(table)} AS {alias}")

        # 3. SELECT clause
        if args.projection:
            select_items = []
            for col in args.projection:
                clean_col = col.strip()
                select_items.append(clean_col)
            select_clause = ", ".join(select_items)
        else:
            select_clause = "T1.*"

        parts = [f"SELECT {select_clause}", f"FROM {from_clause}"]
        if join_clauses:
            parts.extend(join_clauses)

        # 4. WHERE clause
        where_parts: List[str] = []
        if args.filter_criteria:
            for k, v in args.filter_criteria.items():
                if isinstance(v, (int, float)):
                    where_parts.append(f"{k} = {v}")
                elif isinstance(v, str):
                    clean_v = v.replace("'", "''")
                    where_parts.append(f"{k} = '{clean_v}'")
                elif isinstance(v, list):
                    items = ", ".join(f"'{str(x)}'" for x in v)
                    where_parts.append(f"{k} IN ({items})")

        if where_parts:
            parts.append(f"WHERE {' AND '.join(where_parts)}")

        # 5. GROUP BY
        if args.group_by:
            parts.append(f"GROUP BY {', '.join(args.group_by)}")

        # 6. ORDER BY
        if args.order_by:
            order_items = []
            for item in args.order_by:
                col = item.get("column", "")
                direction = item.get("direction", "ASC").upper()
                if col:
                    order_items.append(f"{col} {direction}")
            if order_items:
                parts.append(f"ORDER BY {', '.join(order_items)}")

        # 7. LIMIT
        if args.limit is not None and args.limit > 0:
            parts.append(f"LIMIT {args.limit}")

        return " ".join(parts) + ";"
