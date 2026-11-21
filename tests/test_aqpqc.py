# tests/test_aqpqc.py
"""Comprehensive end-to-end integration tests for AQPQC Selector."""

import json
import pytest
from aqpqc.catalog import ALGORITHM_CATALOG, list_algorithms
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot
from aqpqc.benchmark import BenchmarkEngine
from aqpqc.selector import AQPQCSelector
from aqpqc.cli import build_parser, run_cli

def test_end_to_end_pipeline():
    # 1. Probing telemetry
    collector = TelemetryCollector()
    snapshot = collector.collect(probe_network=False)
    assert snapshot.mem_available_mb > 0

    # 2. Benchmark engine
    bench = BenchmarkEngine()
    kem_bench = bench.benchmark("ML-KEM-512", iterations=2)
    assert kem_bench.op_time_us > 0

    # 3. Model training & selector recommendation
    selector = AQPQCSelector()
    acc = selector.train(n_samples=250, random_state=42)
    assert acc > 0.80

    # 4. Context recommendation
    rec = selector.recommend(snapshot, op_type="kem", min_security=1)
    assert rec.algorithm.startswith("ML-KEM-")
    assert rec.confidence > 0.0
    assert len(rec.explanation) > 0

def test_cli_catalog_command(capsys):
    parser = build_parser()
    args = parser.parse_args(["catalog", "--op", "kem"])
    exit_code = run_cli(args)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "ML-KEM-512" in captured
    assert "ML-KEM-768" in captured

def test_cli_telemetry_command_json(capsys):
    parser = build_parser()
    args = parser.parse_args(["telemetry", "--no-network-probe", "--json"])
    exit_code = run_cli(args)
    assert exit_code == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "cpu_usage_pct" in data
    assert "mem_available_mb" in data

def test_cli_select_command_json(capsys):
    parser = build_parser()
    args = parser.parse_args([
        "select",
        "--op", "kem",
        "--security", "3",
        "--cpu", "10",
        "--mem", "8192",
        "--rtt", "5",
        "--bw", "500",
        "--loss", "0",
        "--mtu", "1500",
        "--json"
    ])
    exit_code = run_cli(args)
    assert exit_code == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert "algorithm" in data
    assert data["security_level"] >= 3
    assert "confidence" in data
    assert "explanation" in data
