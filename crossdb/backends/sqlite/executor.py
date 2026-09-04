"""Thread-safe SQLite query execution engine with native progress handler timeout."""

import sqlite3
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple


class SQLiteExecutor:
    """Executes SQL queries against SQLite databases safely."""

    def __init__(self, db_dir: Optional[Path] = None, timeout_sec: int = 30):
        """Initialize the executor.

        Args:
            db_dir: Path to directory containing SQLite database subfolders.
            timeout_sec: Maximum execution duration per query in seconds.
        """
        self.db_dir = Path(db_dir) if db_dir else None
        self.timeout_sec = timeout_sec

    def resolve_db_path(self, db_id: str) -> Optional[Path]:
        """Find the SQLite file for a given database identifier."""
        if not self.db_dir:
            return None
        candidate = self.db_dir / db_id / f"{db_id}.sqlite"
        if candidate.exists():
            return candidate
        candidate2 = self.db_dir / f"{db_id}.sqlite"
        if candidate2.exists():
            return candidate2
        return None

    def execute(
        self,
        db_path: Path,
        sql: str,
        timeout_sec: Optional[int] = None,
    ) -> Tuple[Optional[List[Tuple[Any, ...]]], Optional[str]]:
        """Execute a SQL string against a database file.

        Args:
            db_path: Path to the SQLite database file.
            sql: SQL query string to run.
            timeout_sec: Optional query timeout override.

        Returns:
            A tuple of (rows, error_message). On success, error_message is None.
            On failure, rows is None and error_message contains the error reason.
        """
        if not db_path.exists():
            return None, f"Database file not found: {db_path}"

        limit = timeout_sec or self.timeout_sec
        deadline = time.time() + limit

        def _check_timeout() -> int:
            return 1 if time.time() > deadline else 0

        try:
            conn = sqlite3.connect(str(db_path))
            conn.text_factory = str
            # Check every 10,000 SQLite VM opcodes for thread-safe timeout
            conn.set_progress_handler(_check_timeout, 10000)

            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()

            conn.set_progress_handler(None, 0)
            conn.close()
            return rows, None

        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if "interrupted" in msg:
                return None, "timeout"
            return None, f"OperationalError: {e}"
        except Exception as e:
            return None, f"Error: {e}"
