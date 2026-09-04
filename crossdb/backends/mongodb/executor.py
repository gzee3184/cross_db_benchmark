"""MongoDB query execution engine."""

import os
from typing import Any, Dict, List, Optional, Tuple


class MongoExecutor:
    """Executes MongoDB aggregation pipelines against a database."""

    def __init__(self, uri: Optional[str] = None, timeout_ms: int = 15000):
        """Initialize the executor.

        Args:
            uri: MongoDB connection URI. Defaults to MONGO_URI or mongodb://localhost:27017.
            timeout_ms: Maximum execution timeout in milliseconds.
        """
        self.uri = uri or os.environ.get("MONGO_URI", "mongodb://localhost:27017")
        self.timeout_ms = timeout_ms
        self._client = None

    def get_client(self):
        """Get or initialize the MongoClient."""
        if self._client is None:
            from pymongo import MongoClient
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout_ms,
            )
        return self._client

    def execute(
        self,
        db_name: str,
        collection_name: str,
        pipeline: List[Dict[str, Any]],
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Run an aggregation pipeline against a MongoDB collection.

        Args:
            db_name: Target database name.
            collection_name: Target collection name.
            pipeline: List of aggregation pipeline stages.

        Returns:
            Tuple of (documents, error_message).
        """
        try:
            client = self.get_client()
            db = client[db_name]
            coll = db[collection_name]
            cursor = coll.aggregate(pipeline, maxTimeMS=self.timeout_ms)
            docs = list(cursor)
            return docs, None
        except Exception as e:
            return None, str(e)
