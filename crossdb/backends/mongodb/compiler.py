"""Document query compiler for MongoDB.

Converts DocumentQueryArgs intermediate representation to MongoDB aggregation pipelines.
"""

from typing import Any, Dict, List
from crossdb.core.ir import DocumentQueryArgs


class MongoCompiler:
    """Compiles structured document tool arguments to MongoDB aggregation pipelines."""

    def __init__(self):
        pass

    def compile(self, args: DocumentQueryArgs) -> List[Dict[str, Any]]:
        """Translate DocumentQueryArgs to an aggregation pipeline list.

        Args:
            args: The structured document query arguments.

        Returns:
            A list of dictionary stages for collection.aggregate().
        """
        pipeline: List[Dict[str, Any]] = []

        # 1. Match stage if match_criteria provided
        if args.match_criteria:
            pipeline.append({"$match": args.match_criteria})

        # 2. Add custom pipeline stages ($lookup, $unwind, $group, etc.)
        if args.pipeline_stages:
            for stage in args.pipeline_stages:
                if isinstance(stage, dict):
                    pipeline.append(stage)

        # 3. Project stage if projection provided
        if args.projection:
            pipeline.append({"$project": args.projection})

        # 4. Limit stage if limit provided
        if args.limit is not None and args.limit > 0:
            pipeline.append({"$limit": args.limit})

        return pipeline
