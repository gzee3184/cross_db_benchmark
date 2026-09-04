"""Tests for BIRDEvaluator and TENDEvaluator."""

from crossdb.backends.sqlite.evaluator import BIRDEvaluator
from crossdb.backends.mongodb.evaluator import TENDEvaluator


def test_bird_evaluator():
    # Identical sets
    gold = [(1, 25.0), (2, 30.0)]
    pred = [(2, 30.0), (1, 25.0)]
    assert BIRDEvaluator.compare_results(gold, pred) is True

    # Float rounding tolerance
    gold_f = [(1, 3.14159)]
    pred_f = [(1, 3.1416)]
    assert BIRDEvaluator.compare_results(gold_f, pred_f) is True

    # Mismatch
    mismatch = [(1, 25.0), (3, 40.0)]
    assert BIRDEvaluator.compare_results(gold, mismatch) is False


def test_tend_evaluator():
    gold_docs = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
    pred_docs = [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]

    metrics = TENDEvaluator.compare_documents(gold_docs, pred_docs)
    assert metrics["exact_match"] == 1.0
    assert metrics["f1"] == 1.0

    # Partial overlap
    pred_partial = [{"name": "Alice", "age": 25}, {"name": "Charlie", "age": 40}]
    partial_metrics = TENDEvaluator.compare_documents(gold_docs, pred_partial)
    assert partial_metrics["exact_match"] == 0.0
    assert 0.0 < partial_metrics["f1"] < 1.0
