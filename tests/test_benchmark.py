# tests/test_benchmark.py
import pytest
from aqpqc.benchmark import BenchmarkEngine, BenchmarkResult

def test_benchmark_result_properties():
    res = BenchmarkResult(
        algorithm="ML-KEM-512",
        op_type="kem",
        op_time_us=65.2,
        keygen_time_us=48.0,
        verify_time_us=55.0,
        memory_peak_kb=16.0,
        cpu_cycles_est=62000,
        source="calibrated_profile"
    )
    assert res.algorithm == "ML-KEM-512"
    assert res.op_time_us > 0.0
    data = res.to_dict()
    assert data["source"] == "calibrated_profile"

def test_benchmark_engine_run():
    engine = BenchmarkEngine()
    result = engine.benchmark("ML-KEM-768", iterations=5)
    assert isinstance(result, BenchmarkResult)
    assert result.algorithm == "ML-KEM-768"
    assert result.op_time_us > 0.0
    assert result.memory_peak_kb > 0.0

def test_benchmark_engine_benchmark_all():
    engine = BenchmarkEngine()
    results = engine.benchmark_all(op_type="kem", iterations=3)
    assert len(results) >= 3
    names = [r.algorithm for r in results]
    assert "ML-KEM-512" in names
    assert "ML-KEM-768" in names
    assert "ML-KEM-1024" in names
