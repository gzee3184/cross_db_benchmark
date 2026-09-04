"""Tests for RefinementGate invariant rules."""

from crossdb.core.refine_gate import RefinementGate


def test_refine_gate_rules():
    gate = RefinementGate(enabled=True)

    # 1. Error occurs -> MUST refine
    assert gate.should_refine(rows=None, error="Syntax error") is True

    # 2. Empty result set -> MUST refine
    assert gate.should_refine(rows=[], error=None) is True

    # 3. Clean execution with valid rows -> SKIP refinement
    assert gate.should_refine(rows=[(1, "Alice"), (2, "Bob")], error=None) is False

    # 4. Gating disabled -> ALWAYS refine
    ungated = RefinementGate(enabled=False)
    assert ungated.should_refine(rows=[(1, "Alice")], error=None) is True
