"""Tests for SQLiteCompiler and in-memory SQLite execution."""

import sqlite3
from crossdb.core.ir import RelationalQueryArgs, AdditionalCollection
from crossdb.backends.sqlite.compiler import SQLiteCompiler


def test_basic_select_compilation():
    compiler = SQLiteCompiler()
    args = RelationalQueryArgs(
        collection_name="users",
        projection=["id", "name"],
        filter_criteria={"age": 25},
        order_by=[{"column": "name", "direction": "ASC"}],
        limit=10,
    )
    sql = compiler.compile(args)
    assert "SELECT id, name FROM users AS T1" in sql
    assert "WHERE age = 25" in sql
    assert "ORDER BY name ASC" in sql
    assert "LIMIT 10" in sql


def test_join_compilation_and_execution():
    compiler = SQLiteCompiler()
    args = RelationalQueryArgs(
        collection_name="orders",
        additional_collections=[
            AdditionalCollection(
                collection_name="customers",
                join_type="INNER",
                join_condition="T1.customer_id = T2.id",
            )
        ],
        projection=["T1.order_id", "T2.customer_name"],
        filter_criteria={"T2.country": "USA"},
    )
    sql = compiler.compile(args)
    assert "INNER JOIN customers AS T2 ON T1.customer_id = T2.id" in sql
    assert "WHERE T2.country = 'USA'" in sql

    # Test executing against in-memory SQLite database
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE orders (order_id INT, customer_id INT)")
    cur.execute("CREATE TABLE customers (id INT, customer_name TEXT, country TEXT)")
    cur.execute("INSERT INTO customers VALUES (1, 'Alice', 'USA'), (2, 'Bob', 'UK')")
    cur.execute("INSERT INTO orders VALUES (101, 1), (102, 2)")
    conn.commit()

    cur.execute(sql)
    rows = cur.fetchall()
    assert rows == [(101, "Alice")]
    conn.close()
