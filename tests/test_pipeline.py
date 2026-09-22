"""Tests for DualCandidatePipeline, cleaning helpers, and arbitration."""

import sqlite3
from crossdb.core.pipeline import DualCandidatePipeline
from crossdb.backends.sqlite.executor import SQLiteExecutor


def test_clean_sql_block():
    markdown_sql = "```sql\nSELECT * FROM users WHERE age > 20;\n```"
    assert DualCandidatePipeline._clean_sql_block(markdown_sql) == "SELECT * FROM users WHERE age > 20;"

    raw_sql = "SELECT id, name FROM orders\n-- comment\nORDER BY id ASC"
    cleaned = DualCandidatePipeline._clean_sql_block(raw_sql)
    assert "SELECT id, name FROM orders" in cleaned
    assert "-- comment" not in cleaned


def test_clean_mql_pipeline():
    raw_mql = "db.users.aggregate([\n  {\"$match\": {\"age\": {\"$gt\": 25}}},\n  {\"$limit\": 5}\n]);"
    pipeline = DualCandidatePipeline._clean_mql_pipeline(raw_mql)
    assert pipeline is not None
    assert len(pipeline) == 2
    assert "$match" in pipeline[0]
    assert "$limit" in pipeline[1]


def test_pipeline_ablation_flags():
    pipe_baseline = DualCandidatePipeline()
    assert pipe_baseline.no_ir is False
    assert pipe_baseline.no_refine is False
    assert pipe_baseline.ungated is False

    pipe_ablation = DualCandidatePipeline(no_ir=True, no_refine=True, ungated=True)
    assert pipe_ablation.no_ir is True
    assert pipe_ablation.no_refine is True
    assert pipe_ablation.ungated is True
