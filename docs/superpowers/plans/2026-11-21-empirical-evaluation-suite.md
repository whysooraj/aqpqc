# Empirical Benchmark and Evaluation Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement empirical benchmarking suite that compares AQPQC Selector against static baselines across 1,000 heterogeneous contexts, exports CSV metrics, and renders comparison charts.

**Architecture:** An evaluation runner module that generates test contexts, scores Static-Max, Static-Min, and AQPQC Selector across 5 metrics, saves structured CSV reports, and a plotting module that renders figures via matplotlib.

**Tech Stack:** Python 3.12+, Matplotlib, Pandas, NumPy, Scikit-learn, XGBoost, Pytest.

## Global Constraints

- No emojis anywhere in code, comments, documentation, or commit messages.
- Clean design with zero unrequested abstractions.
- Non-trivial logic must have a runnable pytest check.
- Matplotlib rendering must run headlessly (`matplotlib.use('Agg')`).

---

### Task 1: Evaluation Engine & Metrics Collector

**Files:**
- Create: `aqpqc/evaluator.py`
- Test: `tests/test_evaluation.py`

**Interfaces:**
- Produces: `EvaluationMetric`, `evaluate_strategies(n_contexts: int = 500, random_state: int = 42) -> dict`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to make sure it fails**
- [ ] **Step 3: Implement `aqpqc/evaluator.py`**
- [ ] **Step 4: Run test and verify it passes**
- [ ] **Step 5: Git commit**

---

### Task 2: Experiment Runner Script & CSV Export

**Files:**
- Create: `experiments/benchmark_evaluation.py`
- Test: integration run via pytest

**Interfaces:**
- Produces: `experiments/results/benchmark_summary.csv`

- [ ] **Step 1: Write script to run evaluation across 1,000 contexts**
- [ ] **Step 2: Execute runner and verify CSV generation**
- [ ] **Step 3: Git commit**

---

### Task 3: Visualization & Plotting Pipeline

**Files:**
- Create: `experiments/plot_results.py`
- Produces: `figures/static_vs_aqpqc_comparison.png`, `figures/feature_importance.png`

- [ ] **Step 1: Implement plotting script with Matplotlib Agg backend**
- [ ] **Step 2: Run script and verify generated PNG images**
- [ ] **Step 3: Update README with evaluation instructions**
- [ ] **Step 4: Full test suite verification**
- [ ] **Step 5: Git commit**
