# tests/test_evaluation.py
import pytest
from aqpqc.evaluator import evaluate_strategies

def test_evaluate_strategies():
    results = evaluate_strategies(n_contexts=100, random_state=42)
    assert "static_max" in results
    assert "static_min" in results
    assert "aqpqc" in results

    aqpqc_metrics = results["aqpqc"]
    static_max = results["static_max"]
    static_min = results["static_min"]

    # AQPQC should satisfy security much better than static_min (100% vs ~39%)
    assert aqpqc_metrics["security_satisfaction_pct"] > static_min["security_satisfaction_pct"]
    # AQPQC should have lower severe packet fragmentation than static_max
    assert aqpqc_metrics["severe_fragmentation_pct"] <= static_max["severe_fragmentation_pct"]
    assert aqpqc_metrics["mean_packets"] < static_max["mean_packets"]
    # AQPQC should have higher overall utility than both static approaches
    assert aqpqc_metrics["mean_utility"] > static_max["mean_utility"]
    assert aqpqc_metrics["mean_utility"] > static_min["mean_utility"]
