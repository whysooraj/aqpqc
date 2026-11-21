# tests/test_selector.py
import pytest
from aqpqc.selector import AQPQCSelector, SelectionResult
from aqpqc.telemetry import TelemetrySnapshot

def test_selector_trains_and_recommends():
    selector = AQPQCSelector()
    acc = selector.train(n_samples=400, random_state=42)
    assert acc > 0.85
    assert selector.is_trained

    # Constrained IoT edge scenario: low RAM (32MB), low MTU (576B), packet loss 6%
    iot_ctx = TelemetrySnapshot(
        cpu_usage_pct=85.0,
        mem_available_mb=32.0,
        network_rtt_ms=120.0,
        network_bandwidth_mbps=0.5,
        packet_loss_pct=6.0,
        mtu_bytes=576
    )
    rec_iot = selector.recommend(iot_ctx, op_type="kem", min_security=1)
    assert isinstance(rec_iot, SelectionResult)
    assert rec_iot.algorithm == "ML-KEM-512"
    assert rec_iot.confidence > 0.0
    assert len(rec_iot.explanation) > 0
    assert len(rec_iot.top_candidates) >= 1

    # High assurance server scenario: ample RAM (16GB), gigabit network, min_security 5
    server_ctx = TelemetrySnapshot(
        cpu_usage_pct=15.0,
        mem_available_mb=16384.0,
        network_rtt_ms=1.5,
        network_bandwidth_mbps=1000.0,
        packet_loss_pct=0.0,
        mtu_bytes=9000
    )
    rec_server = selector.recommend(server_ctx, op_type="kem", min_security=5)
    assert rec_server.algorithm == "ML-KEM-1024"
    assert rec_server.security_level == 5

def test_selector_sign_recommendation():
    selector = AQPQCSelector()
    selector.train(n_samples=300, random_state=42)
    
    # IoT environment for signature: Falcon-512 has small signature (666B) vs ML-DSA-44 (2420B)
    iot_sign_ctx = TelemetrySnapshot(
        cpu_usage_pct=40.0,
        mem_available_mb=64.0,
        network_rtt_ms=150.0,
        network_bandwidth_mbps=0.2,
        packet_loss_pct=8.0,
        mtu_bytes=576
    )
    rec_sign = selector.recommend(iot_sign_ctx, op_type="sign", min_security=1)
    assert rec_sign.algorithm in ["Falcon-512", "ML-DSA-44"]
    assert rec_sign.op_type == "sign"
