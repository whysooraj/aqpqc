# Design Specification: AQPQC Empirical Benchmark and Evaluation Suite

## Goal
Quantify performance gains and cryptographic agility benefits of the AQPQC Selector against static baselines (Static-Max and Static-Min) across 1,000 heterogeneous contexts (Edge IoT, Mobile WAN, Cloud Datacenter), and render visual graphs for technical validation.

## Baselines
1. **Static-Max**: Hardcoded to highest security algorithms (ML-KEM-1024 for KEM, ML-DSA-87 for signatures). High latency, packet fragmentation on edge links.
2. **Static-Min**: Hardcoded to minimal footprint algorithms (ML-KEM-512 for KEM, ML-DSA-44 for signatures). Violates high-assurance security requirements.
3. **AQPQC Selector**: Dynamic context-adaptive selection combining XGBoost classification and Pareto post-filtering.

## Metrics
- **Security Requirement Satisfaction Rate (%)**: Percentage of contexts where selected algorithm security level >= required security level.
- **Average Latency (ms)**: Total transmission and cryptographic execution duration.
- **Packet Fragmentation Rate (%)**: Percentage of transactions requiring more than 1 MTU packet.
- **Memory Violation Rate (%)**: Transactions exceeding 20% of available memory on host.
- **Mean Pareto Utility**: Overall composite fitness score.

## Components
1. `experiments/benchmark_evaluation.py`:
   - Runs evaluation on N test scenarios.
   - Computes statistical summaries per strategy.
   - Exports CSV to `experiments/results/benchmark_summary.csv`.
2. `experiments/plot_results.py`:
   - Generates `figures/static_vs_aqpqc_comparison.png`.
   - Generates `figures/feature_importance.png`.
3. `tests/test_evaluation.py`:
   - Fast pytest check verifying evaluation logic, metrics calculation, and CSV output.
