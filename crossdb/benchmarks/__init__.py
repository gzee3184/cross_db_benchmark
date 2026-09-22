"""Benchmark runners for relational (BIRD) and document (TEND) evaluations."""

from crossdb.benchmarks.bird import run_bird_benchmark
from crossdb.benchmarks.tend import run_tend_benchmark

__all__ = ["run_bird_benchmark", "run_tend_benchmark"]
