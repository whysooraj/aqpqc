# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from aqpqc.api import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_catalog_endpoint():
    res = client.get("/api/v1/catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 7
    names = [a["name"] for a in data]
    assert "ML-KEM-512" in names
    assert "ML-DSA-44" in names

def test_telemetry_endpoint():
    res = client.get("/api/v1/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert "cpu_usage_pct" in data
    assert "mem_available_mb" in data

def test_recommend_endpoint_iot():
    payload = {
        "op_type": "kem",
        "min_security": 1,
        "telemetry_override": {
            "cpu_usage_pct": 80.0,
            "mem_available_mb": 32.0,
            "network_rtt_ms": 120.0,
            "network_bandwidth_mbps": 0.5,
            "packet_loss_pct": 5.0,
            "mtu_bytes": 576
        }
    }
    res = client.post("/api/v1/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["algorithm"] == "ML-KEM-512"
    assert data["confidence"] > 0
    assert len(data["explanation"]) > 0

def test_benchmark_endpoint():
    res = client.post("/api/v1/benchmark", json={"op_type": "kem", "iterations": 2})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
