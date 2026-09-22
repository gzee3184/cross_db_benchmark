"""Unified command-line interface for CrossDB evaluations and ablations."""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from crossdb.core.client import LLMClient
from crossdb.benchmarks.bird import run_bird_benchmark
from crossdb.benchmarks.tend import run_tend_benchmark


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="CrossDB: Unified Text-to-Database Benchmark Engine"
    )
    parser.add_argument(
        "--backend",
        choices=["sqlite", "mongodb"],
        required=True,
        help="Database backend to evaluate (sqlite for BIRD, mongodb for TEND)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing benchmark dataset files (BIRD data or TEND.json)",
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=None,
        help="Directory containing SQLite database files (for sqlite backend)",
    )
    parser.add_argument(
        "--mongo-uri",
        type=str,
        default=None,
        help="MongoDB connection URI (for mongodb backend, defaults to MONGO_URI env var)",
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Optional directory containing pre-extracted schema JSON files",
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test", "all"],
        default="all",
        help="Dataset split to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of queries to evaluate (useful for smoke tests)",
    )
    parser.add_argument(
        "--db-id",
        type=str,
        default=None,
        help="Evaluate only a specific database (e.g., 'card_games')",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Number of concurrent worker threads",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to save output evaluation reports",
    )

    # LLM Serving Overrides
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="LLM inference server base URL (overrides LM_BASE_URL)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model identifier (overrides LM_MODEL)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for inference server (overrides LM_API_KEY)",
    )

    # Core Generation Ablations
    parser.add_argument(
        "--no-ir",
        action="store_true",
        help="Ablation A1: Direct query generation without Intermediate Representation",
    )
    parser.add_argument(
        "--no-refine",
        action="store_true",
        help="Ablation A3 Arm C: Disable refinement loop entirely (single turn)",
    )
    parser.add_argument(
        "--ungated",
        action="store_true",
        help="Ablation A3 Arm B: Force multi-turn refinement unconditionally on all queries",
    )

    # Schema Discovery Ablations (Task 3)
    parser.add_argument(
        "--no-kg",
        action="store_true",
        help="Ablation A2: Disable Field Knowledge Graph edges and join path resolution",
    )
    parser.add_argument(
        "--no-embedding",
        action="store_true",
        help="Ablation: Disable dense semantic embeddings (fallback to lexical)",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Ablation: Disable property match token overlap reranker",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        help="Ablation: Disable value statistics catalog matching",
    )
    parser.add_argument(
        "--no-adaptive",
        action="store_true",
        help="Ablation: Disable adaptive depth routing (flat top-K candidate retrieval)",
    )
    parser.add_argument(
        "--no-multi-hop",
        action="store_true",
        help="Ablation: Disable multi-hop graph path traversal (1-hop only)",
    )
    parser.add_argument(
        "--no-lexical",
        action="store_true",
        help="Ablation: Disable lexical token matching",
    )

    return parser


def main():
    """Main execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("CROSS-DB BENCHMARK ENGINE")
    print(f"Backend:     {args.backend.upper()}")
    print(f"Split:       {args.split} (limit={args.limit}, db_id={args.db_id})")
    print(f"Concurrency: {args.concurrency}")
    print(f"Output dir:  {args.output_dir}")

    # Active ablations summary
    active_ablations = [
        name for name in [
            "no_ir", "no_refine", "ungated", "no_kg", "no_embedding",
            "no_rerank", "no_values", "no_adaptive", "no_multi_hop", "no_lexical"
        ] if getattr(args, name, False)
    ]
    if active_ablations:
        print(f"Ablations:   {', '.join(active_ablations)}")
    else:
        print("Ablations:   None (Full Pipeline Baseline)")
    print("=" * 70)

    # Initialize client with optional CLI overrides
    client = LLMClient(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
    )

    if args.backend == "sqlite":
        # Resolve data directory
        data_dir = args.data_dir or Path(os.environ.get("BIRD_DATA_DIR", "data/bird"))
        db_dir = args.db_dir or Path(os.environ.get("BIRD_DB_DIR", "data/bird/dev_databases"))

        if not data_dir.exists():
            print(f"Error: BIRD data directory not found at {data_dir}. Specify --data-dir.", file=sys.stderr)
            sys.exit(1)

        run_bird_benchmark(
            data_dir=data_dir,
            db_dir=db_dir,
            output_dir=args.output_dir,
            concurrency=args.concurrency,
            split=args.split,
            limit=args.limit,
            db_id_filter=args.db_id,
            no_ir=args.no_ir,
            no_refine=args.no_refine,
            ungated=args.ungated,
            no_kg=args.no_kg,
            no_embedding=args.no_embedding,
            no_rerank=args.no_rerank,
            no_values=args.no_values,
            no_adaptive=args.no_adaptive,
            no_multi_hop=args.no_multi_hop,
            no_lexical=args.no_lexical,
            client=client,
        )

    elif args.backend == "mongodb":
        # Resolve data directory
        data_dir = args.data_dir or Path(os.environ.get("TEND_DATA_DIR", "data/tend"))

        if not data_dir.exists():
            print(f"Error: TEND data directory not found at {data_dir}. Specify --data-dir.", file=sys.stderr)
            sys.exit(1)

        run_tend_benchmark(
            data_dir=data_dir,
            output_dir=args.output_dir,
            mongo_uri=args.mongo_uri,
            schema_dir=args.schema_dir,
            concurrency=args.concurrency,
            limit=args.limit,
            db_id_filter=args.db_id,
            no_ir=args.no_ir,
            no_refine=args.no_refine,
            ungated=args.ungated,
            client=client,
        )


if __name__ == "__main__":
    main()
