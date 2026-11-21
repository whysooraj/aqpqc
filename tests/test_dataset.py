# tests/test_dataset.py
import numpy as np
import pytest
from aqpqc.dataset import generate_synthetic_dataset, calculate_pareto_utility

def test_generate_synthetic_dataset():
    X, y, class_names, feature_names = generate_synthetic_dataset(n_samples=200, random_state=42)
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.shape[0] == 200
    assert X.shape[1] == len(feature_names)
    assert len(y) == 200
    assert len(class_names) >= 6
    # Ensure all labels in y correspond to valid class indices
    assert np.all(y >= 0) and np.all(y < len(class_names))

def test_pareto_utility_selection():
    # Constrained edge context: tiny RAM (32MB), low MTU (576B), high loss (5%)
    # ML-KEM-512 should have higher utility than ML-KEM-1024 due to packet fragmentation risk & memory
    score_512 = calculate_pareto_utility(
        algo_name="ML-KEM-512",
        cpu_usage_pct=85.0,
        mem_available_mb=32.0,
        network_rtt_ms=100.0,
        network_bandwidth_mbps=1.0,
        packet_loss_pct=5.0,
        mtu_bytes=576,
        required_security=1,
    )
    score_1024 = calculate_pareto_utility(
        algo_name="ML-KEM-1024",
        cpu_usage_pct=85.0,
        mem_available_mb=32.0,
        network_rtt_ms=100.0,
        network_bandwidth_mbps=1.0,
        packet_loss_pct=5.0,
        mtu_bytes=576,
        required_security=1,
    )
    assert score_512 > score_1024
