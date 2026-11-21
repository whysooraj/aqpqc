"""Benchmark evaluation runner comparing AQPQC Selector against static baselines across 1,000 contexts."""

import csv
import os
import sys
from pathlib import Path

from aqpqc.evaluator import evaluate_strategies

def main(n_contexts: int = 1000):
    print(f"Executing empirical benchmark across {n_contexts} heterogeneous operational contexts...")
    summary = evaluate_strategies(n_contexts=n_contexts, random_state=42)

    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = results_dir / "benchmark_summary.csv"

    fieldnames = [
        "strategy",
        "security_satisfaction_pct",
        "mean_latency_ms",
        "mean_packets",
        "severe_fragmentation_pct",
        "memory_violation_pct",
        "mean_utility",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for strat, metrics in summary.items():
            row = {"strategy": strat, **metrics}
            writer.writerow(row)

    print(f"\nSaved CSV summary to: {csv_path}\n")

    # Console display table
    print(f"{'STRATEGY':<14} {'SEC SATISFIED':<16} {'LATENCY (ms)':<14} {'AVG PKTS':<10} {'SEVERE FRAG':<14} {'UTILITY':<10}")
    print("-" * 80)
    for strat, metrics in summary.items():
        print(
            f"{strat:<14} "
            f"{metrics['security_satisfaction_pct']:>13.1f}% "
            f"{metrics['mean_latency_ms']:>12.2f} "
            f"{metrics['mean_packets']:>9.2f} "
            f"{metrics['severe_fragmentation_pct']:>12.1f}% "
            f"{metrics['mean_utility']:>9.2f}"
        )


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    main(n)
