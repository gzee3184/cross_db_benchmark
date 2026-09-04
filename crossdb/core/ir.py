"""Intermediate Representation (IR) schemas for relational and document queries."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdditionalCollection(BaseModel):
    """Secondary collection joined to the primary collection."""
    collection_name: str
    join_type: Optional[str] = "INNER"
    join_condition: Optional[str] = None


class RelationalQueryArgs(BaseModel):
    """Intermediate representation for a relational (SQL) query."""
    collection_name: str = Field(..., description="Primary table or collection name")
    additional_collections: Optional[List[AdditionalCollection]] = Field(
        default_factory=list, description="Joined tables"
    )
    filter_criteria: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Key-value or operator-based WHERE filters"
    )
    projection: Optional[List[str]] = Field(
        default_factory=list, description="Columns to project in SELECT"
    )
    group_by: Optional[List[str]] = Field(
        default_factory=list, description="Columns for GROUP BY clause"
    )
    order_by: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, description="List of dicts specifying column and direction"
    )
    limit: Optional[int] = Field(None, description="Maximum number of rows to return")
    raw_reference_sql: Optional[str] = Field(
        None, description="Optional raw reference SQL emitted by dual-generator"
    )


class DocumentQueryArgs(BaseModel):
    """Intermediate representation for a document (MongoDB) query."""
    collection_name: str = Field(..., description="Target MongoDB collection")
    match_criteria: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Filter for $match stage"
    )
    pipeline_stages: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Ordered list of MongoDB aggregation stages"
    )
    projection: Optional[Dict[str, int]] = Field(
        default_factory=dict, description="Field inclusion/exclusion specification"
    )
    limit: Optional[int] = Field(None, description="Maximum number of documents")
