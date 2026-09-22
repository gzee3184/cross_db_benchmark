"""Tests for FieldKnowledgeGraph and SchemaRetriever."""

from crossdb.discovery.kg import FieldKnowledgeGraph, normalize_col_key
from crossdb.discovery.retrieval import SchemaRetriever


def test_normalize_col_key():
    assert normalize_col_key("CustomerID") == "customerid"
    assert normalize_col_key("customer_id") == "customerid"
    assert normalize_col_key("Customer ID") == "customerid"


def test_kg_edges_and_join_paths():
    kg = FieldKnowledgeGraph(enabled=True)
    db_id = "ecommerce"

    # Add edges: customers -> orders -> line_items
    kg.add_edge(db_id, "customers", "id", "orders", "customer_id", "FK_REFERENCE")
    kg.add_edge(db_id, "orders", "order_id", "line_items", "order_id", "FK_REFERENCE")

    # 1-hop path
    path_1hop = kg.find_join_path(db_id, "customers", "orders")
    assert path_1hop is not None
    assert len(path_1hop) == 1
    assert path_1hop[0] == ("customers", "id", "orders", "customer_id")

    # 2-hop path
    path_2hop = kg.find_join_path(db_id, "customers", "line_items")
    assert path_2hop is not None
    assert len(path_2hop) == 2

    # Multi-hop disabled
    path_no_multihop = kg.find_join_path(db_id, "customers", "line_items", allow_multi_hop=False)
    assert path_no_multihop is None

    # KG disabled (ablation)
    disabled_kg = FieldKnowledgeGraph(enabled=False)
    disabled_kg.add_edge(db_id, "customers", "id", "orders", "customer_id")
    assert disabled_kg.find_join_path(db_id, "customers", "orders") is None


def test_schema_retriever_ranking_and_ablations():
    table_schemas = {
        "customers": ["id", "first_name", "last_name", "email", "country"],
        "orders": ["order_id", "customer_id", "order_date", "total_amount"],
        "products": ["product_id", "product_name", "category", "unit_price"],
        "inventory": ["warehouse_id", "product_id", "stock_count"],
    }

    # Baseline retriever
    retriever = SchemaRetriever(use_embedding=False, use_rerank=True, use_adaptive=True)
    ranked = retriever.retrieve_tables(
        db_id="shop",
        question="What is the total amount of orders placed by customer email test@example.com?",
        table_schemas=table_schemas,
        top_k=2,
    )
    assert "orders" in ranked or "customers" in ranked

    # Ablation: no reranking
    retriever_no_rerank = SchemaRetriever(use_embedding=False, use_rerank=False)
    ranked_no_rerank = retriever_no_rerank.retrieve_tables(
        db_id="shop",
        question="List all product names and unit prices",
        table_schemas=table_schemas,
        top_k=2,
    )
    assert "products" in ranked_no_rerank


def test_tend_collection_retrieval():
    retriever = SchemaRetriever()
    colls = ["users", "card_print_dossiers", "tournaments", "logs"]
    schema = {
        "card_print_dossiers": {"fields": {"card_id": "int", "print_identity.name": "str"}},
        "tournaments": {"fields": {"tournament_id": "int", "location": "str"}},
    }
    cands = retriever.retrieve_collections(
        db_id="card_games",
        question="What is the print identity name of the card with ID 50?",
        available_collections=colls,
        schema_dict=schema,
        top_k=2,
    )
    assert cands[0] == "card_print_dossiers"
