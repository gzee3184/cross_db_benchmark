"""Official TEND benchmark evaluator for MongoDB document results."""

from typing import Any, Dict, List, Optional


def document_to_key(doc: Dict[str, Any]) -> str:
    """Serialize a document into a deterministic canonical string for set comparison."""
    import json
    def _clean(obj):
        if isinstance(obj, dict):
            # Omit internal _id if present
            return {k: _clean(v) for k, v in sorted(obj.items()) if k != "_id"}
        if isinstance(obj, list):
            return [_clean(x) for x in obj]
        if isinstance(obj, float):
            return round(obj, 4)
        return str(obj)

    cleaned = _clean(doc)
    return json.dumps(cleaned, sort_keys=True)


class TENDEvaluator:
    """Computes official Execution Accuracy (EXC) and Execution F1 (EXF1) for TEND."""

    @staticmethod
    def compare_documents(
        gold_docs: Optional[List[Dict[str, Any]]],
        pred_docs: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, float]:
        """Compute match metrics between gold and predicted document sets.

        Returns:
            Dictionary with 'exact_match', 'precision', 'recall', and 'f1'.
        """
        if gold_docs is None or pred_docs is None:
            return {"exact_match": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

        gold_keys = [document_to_key(d) for d in gold_docs]
        pred_keys = [document_to_key(d) for d in pred_docs]

        set_gold = set(gold_keys)
        set_pred = set(pred_keys)

        # Exact match
        exact_match = 1.0 if set_gold == set_pred else 0.0

        # Set-based F1
        if not set_pred and not set_gold:
            return {"exact_match": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
        if not set_pred or not set_gold:
            return {"exact_match": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

        intersection = len(set_gold.intersection(set_pred))
        precision = intersection / len(set_pred)
        recall = intersection / len(set_gold)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "exact_match": exact_match,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
