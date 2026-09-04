"""Refinement loop gating invariant engine.

This module decides if a query needs refinement.
It prevents regression errors and reduces unnecessary inference costs.
"""

from typing import Any, List, Optional


class RefinementGate:
    """Evaluates query execution results to gate refinement loops."""

    def __init__(self, enabled: bool = True):
        """Initialize the gate.
        
        Args:
            enabled: If False, refinement triggers unconditionally for all queries.
        """
        self.enabled = enabled

    def should_refine(
        self,
        rows: Optional[List[Any]],
        error: Optional[str],
    ) -> bool:
        """Decide if the model must refine the generated query.

        Rules:
        1. When gating is disabled, always refine (returns True).
        2. When an execution error occurs, refine (returns True).
        3. When a query returns zero rows, refine (returns True).
        4. When a query executes cleanly with rows, skip refinement (returns False).

        Args:
            rows: The result rows returned from the database execution.
            error: The error string if execution failed, or None.

        Returns:
            True if refinement is required, False otherwise.
        """
        if not self.enabled:
            return True

        # Rule 1: Execution error occurred
        if error is not None:
            return True

        # Rule 2: Execution succeeded but produced an empty result set
        if rows is not None and len(rows) == 0:
            return True

        # Rule 3: Valid non-empty result set - skip refinement
        return False
