"""Unified command-line interface for CrossDB evaluations and ablations."""

import argparse
import json
import os
from pathlib import Path
from crossdb.core.client import LLMClient
from crossdb.core.refine_gate import RefinementGate
from crossdb.backends.sqlite import SQLiteCompiler, SQLiteExecutor, BIRDEvaluator
from crossdb.backends.mongodb import MongoCompiler, MongoExecutor, TENDEvaluator


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="CrossDB: Unified Text-to-Database Benchmark Engine"
    )
    parser.add_argument(
        "--backend",
        choices=["sqlite", "mongodb"],
        required=True,
        help="Database backend to evaluate",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory containing benchmark dataset files",
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=None,
        help="Directory containing SQLite database files (for sqlite backend)",
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test", "all"],
        default="all",
        help="Dataset split to evaluate",
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

    # Core Ablation Switches
    parser.add_argument(
        "--no-ir",
        action="store_true",
        help="Ablation A1: Direct query generation without Intermediate Representation",
    )
    parser.add_argument(
        "--no-refine",
        action="store_true",
        help="Ablation A3 Arm C: Disable refinement loop entirely",
    )
    parser.add_argument(
        "--ungated",
        action="store_true",
        help="Ablation A3 Arm B: Force multi-turn refinement unconditionally on all queries",
    )

    return parser


def main():
    """Main execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("CROSS-DB BENCHMARK ENGINE")
    print(f"Backend:     {args.backend}")
    print(f"Split:       {args.split}")
    print(f"Ablations:   no_ir={args.no_ir}, no_refine={args.no_refine}, ungated={args.ungated}")
    print(f"Output dir:  {args.output_dir}")
    print("=" * 70)

    # Initialize components
    client = LLMClient()
    refine_gate = RefinementGate(enabled=not args.ungated)

    if args.backend == "sqlite":
        compiler = SQLiteCompiler()
        executor = SQLiteExecutor(db_dir=args.db_dir)
        evaluator = BIRDEvaluator()
        print("Initialized SQLite Relational Backend.")
    else:
        compiler = MongoCompiler()
        executor = MongoExecutor()
        evaluator = TENDEvaluator()
        print("Initialized MongoDB Document Backend.")


if __name__ == "__main__":
    main()
