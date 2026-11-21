# tests/test_telemetry.py
import pytest
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot

def test_telemetry_snapshot_properties():
    snapshot = TelemetrySnapshot(
        cpu_usage_pct=25.5,
        mem_available_mb=2048.0,
        network_rtt_ms=12.4,
        network_bandwidth_mbps=50.0,
        packet_loss_pct=0.0,
        mtu_bytes=1500
    )
    vector = snapshot.to_vector()
    assert len(vector) == 6
    assert vector[0] == 25.5
    assert vector[1] == 2048.0
    data_dict = snapshot.to_dict()
    assert data_dict["mtu_bytes"] == 1500

def test_telemetry_collector_returns_valid_metrics():
    collector = TelemetryCollector()
    snapshot = collector.collect(probe_network=False)
    assert isinstance(snapshot, TelemetrySnapshot)
    assert 0.0 <= snapshot.cpu_usage_pct <= 100.0
    assert snapshot.mem_available_mb > 0.0
    assert snapshot.network_rtt_ms >= 0.0
    assert snapshot.mtu_bytes >= 576
