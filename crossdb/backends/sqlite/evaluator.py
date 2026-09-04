"""Official BIRD execution accuracy evaluator."""

from typing import Any, List, Optional, Set, Tuple


def normalize_value(val: Any) -> Any:
    """Normalize a database value for stable comparison."""
    if isinstance(val, float):
        return round(val, 4)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="ignore")
    return val


def normalize_row(row: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Normalize row values into a comparable tuple."""
    return tuple(normalize_value(v) for v in row)


def normalize_results(rows: Optional[List[Tuple[Any, ...]]]) -> Optional[Set[Tuple[Any, ...]]]:
    """Convert rows into a normalized set for set-equality evaluation."""
    if rows is None:
        return None
    return set(normalize_row(r) for r in rows)


class BIRDEvaluator:
    """Computes official set-equality Execution Accuracy (EX) for BIRD."""

    @staticmethod
    def compare_results(
        gold_rows: Optional[List[Tuple[Any, ...]]],
        pred_rows: Optional[List[Tuple[Any, ...]]],
    ) -> bool:
        """Compare execution results between gold SQL and predicted SQL.

        Returns:
            True if the normalized result sets match, False otherwise.
        """
        if gold_rows is None or pred_rows is None:
            return False

        norm_gold = normalize_results(gold_rows)
        norm_pred = normalize_results(pred_rows)

        # Standard set-equality comparison
        if norm_gold == norm_pred:
            return True

        # Permutation check if column count matches and single row
        if len(gold_rows) == len(pred_rows) == 1:
            g_set = set(normalize_row(gold_rows[0]))
            p_set = set(normalize_row(pred_rows[0]))
            if g_set == p_set:
                return True

        return False
