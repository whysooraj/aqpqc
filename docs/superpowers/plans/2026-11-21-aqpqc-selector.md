# AQPQC Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AQPQC Selector from scratch: a standalone Python toolkit that benchmarks NIST PQC algorithms, collects runtime hardware/network telemetry, and dynamically selects optimal post-quantum ciphers using XGBoost and Pareto ranking.

**Architecture:** A modular Python package consisting of a NIST algorithm catalog, a hardware/network telemetry collector, a benchmarking engine with calibrated fallback, a synthetic dataset generator, an XGBoost + Pareto multi-objective selector, an explainability module, and an intuitive CLI/API.

**Tech Stack:** Python 3.12+, NumPy, Pandas, Scikit-learn, XGBoost, Psutil, Pytest.

## Global Constraints

- No emojis anywhere in code, comments, documentation, or commit messages.
- No AI slop or unnecessary boilerplate abstractions.
- Pure Python fallback for liboqs ensures code runs reliably on any machine without C-compilation errors.
- Every non-trivial logic component must have a runnable pytest check.
- Maintain strict type hints and clean docstrings.

---

### Task 1: Project Scaffolding & NIST PQC Catalog

**Files:**
- Create: `pyproject.toml`
- Create: `aqpqc/__init__.py`
- Create: `aqpqc/catalog.py`
- Test: `tests/test_catalog.py`

**Interfaces:**
- Produces: `PQCAlgorithm`, `ALGORITHM_CATALOG`, `get_algorithm(name: str) -> PQCAlgorithm`, `list_algorithms(op_type: str = None) -> list[PQCAlgorithm]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_catalog.py
from aqpqc.catalog import ALGORITHM_CATALOG, get_algorithm, list_algorithms

def test_catalog_contains_nist_standards():
    kem_algos = list_algorithms(op_type="kem")
    sign_algos = list_algorithms(op_type="sign")
    assert len(kem_algos) >= 3
    assert len(sign_algos) >= 4

    kyber512 = get_algorithm("ML-KEM-512")
    assert kyber512.public_key_bytes == 800
    assert kyber512.ciphertext_bytes == 768
    assert kyber512.security_level == 1
    assert kyber512.op_type == "kem"

    dsa44 = get_algorithm("ML-DSA-44")
    assert dsa44.public_key_bytes == 1312
    assert dsa44.signature_bytes == 2420
    assert dsa44.security_level == 2
```

- [ ] **Step 2: Run test to make sure it fails**
```bash
pytest tests/test_catalog.py
```

- [ ] **Step 3: Implement minimal code in `pyproject.toml`, `aqpqc/__init__.py`, and `aqpqc/catalog.py`**
Implement dataclass `PQCAlgorithm` and dictionary `ALGORITHM_CATALOG` with FIPS 203 (ML-KEM-512, 768, 1024), FIPS 204 (ML-DSA-44, 65, 87), Falcon-512/1024, and SLH-DSA.

- [ ] **Step 4: Run test and verify it passes**
```bash
pytest tests/test_catalog.py
```

- [ ] **Step 5: Git commit**
```bash
git add pyproject.toml aqpqc/ tests/test_catalog.py
git commit -m "feat(catalog): add nist pqc algorithm catalog and specifications"
```

---

### Task 2: Hardware & Network Telemetry Prober

**Files:**
- Create: `aqpqc/telemetry.py`
- Test: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: `psutil`
- Produces: `TelemetrySnapshot`, `TelemetryCollector.collect(target_host: str = "8.8.8.8") -> TelemetrySnapshot`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_telemetry.py
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot

def test_telemetry_collector_returns_valid_metrics():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    assert isinstance(snapshot, TelemetrySnapshot)
    assert 0.0 <= snapshot.cpu_usage_pct <= 100.0
    assert snapshot.mem_available_mb > 0.0
    assert snapshot.network_rtt_ms >= 0.0
    assert snapshot.mtu_bytes >= 576
```

- [ ] **Step 2: Run test to make sure it fails**
```bash
pytest tests/test_telemetry.py
```

- [ ] **Step 3: Implement `aqpqc/telemetry.py`**
Implement `TelemetrySnapshot` (dataclass with `to_dict` and `to_vector`) and `TelemetryCollector` reading `/proc` / `psutil` and socket latency check.

- [ ] **Step 4: Run test and verify it passes**
```bash
pytest tests/test_telemetry.py
```

- [ ] **Step 5: Git commit**
```bash
git add aqpqc/telemetry.py tests/test_telemetry.py
git commit -m "feat(telemetry): implement hardware and network telemetry collector"
```

---

### Task 3: Benchmarking Engine with Baseline Fallback

**Files:**
- Create: `aqpqc/benchmark.py`
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Consumes: `aqpqc.catalog.ALGORITHM_CATALOG`
- Produces: `BenchmarkResult`, `BenchmarkEngine.run_benchmark(algo_name: str, iterations: int = 10) -> BenchmarkResult`, `BenchmarkEngine.get_calibrated_profile(algo_name: str) -> BenchmarkResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_benchmark.py
from aqpqc.benchmark import BenchmarkEngine, BenchmarkResult

def test_benchmark_engine_calibrated_profile():
    engine = BenchmarkEngine()
    result = engine.benchmark("ML-KEM-768", iterations=5)
    assert isinstance(result, BenchmarkResult)
    assert result.algorithm == "ML-KEM-768"
    assert result.op_time_us > 0.0
    assert result.memory_peak_kb > 0.0
```

- [ ] **Step 2: Run test to make sure it fails**
```bash
pytest tests/test_benchmark.py
```

- [ ] **Step 3: Implement `aqpqc/benchmark.py`**
Implement dynamic check for `oqs` package. If found, run native liboqs keygen/encaps/sign operations; if not found, use calibrated hardware timing model indexed by CPU speed.

- [ ] **Step 4: Run test and verify it passes**
```bash
pytest tests/test_benchmark.py
```

- [ ] **Step 5: Git commit**
```bash
git add aqpqc/benchmark.py tests/test_benchmark.py
git commit -m "feat(benchmark): add benchmark engine with portable baseline profiles"
```

---

### Task 4: Synthetic Context Dataset Generator & Ground-Truth Labeller

**Files:**
- Create: `aqpqc/dataset.py`
- Test: `tests/test_dataset.py`

**Interfaces:**
- Consumes: `aqpqc.catalog.ALGORITHM_CATALOG`, `aqpqc.telemetry.TelemetrySnapshot`
- Produces: `generate_synthetic_dataset(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray, list[str]]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dataset.py
from aqpqc.dataset import generate_synthetic_dataset

def test_generate_synthetic_dataset():
    X, y, class_names = generate_synthetic_dataset(n_samples=200, random_state=42)
    assert X.shape[0] == 200
    assert X.shape[1] >= 7
    assert len(y) == 200
    assert len(class_names) >= 6
```

- [ ] **Step 2: Run test to make sure it fails**
```bash
pytest tests/test_dataset.py
```

- [ ] **Step 3: Implement `aqpqc/dataset.py`**
Generate stratified operational scenarios across IoT (low RAM, small MTU, packet drop), Mobile (moderate latency/bandwidth), and Datacenter (high resources). Compute optimal algorithm label using Pareto utility function balancing security level against latency and fragmentation.

- [ ] **Step 4: Run test and verify it passes**
```bash
pytest tests/test_dataset.py
```

- [ ] **Step 5: Git commit**
```bash
git add aqpqc/dataset.py tests/test_dataset.py
git commit -m "feat(dataset): implement context scenario generator with pareto utility labeling"
```

---

### Task 5: Context-Aware Selector & Explainability Module

**Files:**
- Create: `aqpqc/selector.py`
- Create: `aqpqc/explain.py`
- Test: `tests/test_selector.py`

**Interfaces:**
- Consumes: `aqpqc.dataset`, `aqpqc.catalog`, `aqpqc.telemetry`
- Produces: `SelectionResult`, `AQPQCSelector.train()`, `AQPQCSelector.recommend(context: TelemetrySnapshot, op_type: str, min_security: int) -> SelectionResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_selector.py
from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetrySnapshot

def test_selector_trains_and_recommends():
    selector = AQPQCSelector()
    train_acc = selector.train(n_samples=300)
    assert train_acc > 0.85

    # Constrained IoT edge scenario
    iot_ctx = TelemetrySnapshot(
        cpu_usage_pct=85.0,
        mem_available_mb=32.0,
        network_rtt_ms=120.0,
        network_bandwidth_mbps=0.5,
        packet_loss_pct=8.0,
        mtu_bytes=576
    )
    rec_iot = selector.recommend(iot_ctx, op_type="kem", min_security=1)
    assert rec_iot.algorithm in ["ML-KEM-512"]
    assert rec_iot.confidence > 0.0
    assert len(rec_iot.explanation) > 0

    # High assurance server scenario
    server_ctx = TelemetrySnapshot(
        cpu_usage_pct=15.0,
        mem_available_mb=16384.0,
        network_rtt_ms=1.5,
        network_bandwidth_mbps=1000.0,
        packet_loss_pct=0.0,
        mtu_bytes=9000
    )
    rec_server = selector.recommend(server_ctx, op_type="kem", min_security=5)
    assert rec_server.algorithm in ["ML-KEM-1024"]
```

- [ ] **Step 2: Run test to make sure it fails**
```bash
pytest tests/test_selector.py
```

- [ ] **Step 3: Implement `aqpqc/explain.py` and `aqpqc/selector.py`**
Implement XGBoost classifier with model caching, hard constraint filtering, Pareto re-ranking, and SHAP/feature importance explanation generator.

- [ ] **Step 4: Run test and verify it passes**
```bash
pytest tests/test_selector.py
```

- [ ] **Step 5: Git commit**
```bash
git add aqpqc/selector.py aqpqc/explain.py tests/test_selector.py
git commit -m "feat(selector): implement xgboost context-aware selector and explainability"
```

---

### Task 6: Unified CLI, Integration Suite, and Documentation

**Files:**
- Create: `aqpqc/cli.py`
- Modify: `aqpqc/__init__.py`
- Create: `tests/test_aqpqc.py`
- Create: `README.md`

**Interfaces:**
- Produces: CLI commands `aqpqc catalog`, `aqpqc telemetry`, `aqpqc benchmark`, `aqpqc train`, `aqpqc select`

- [ ] **Step 1: Write integration test `tests/test_aqpqc.py`**
Verifies end-to-end workflow: catalog lookup -> telemetry collection -> model training -> context recommendation -> CLI invocation via `subprocess` or `argparse`.

- [ ] **Step 2: Implement `aqpqc/cli.py` with `argparse` and format tabulations**
Support human-readable output and JSON output (`--json`).

- [ ] **Step 3: Write clean `README.md`**
No AI slop, no emojis, concise installation and CLI usage instructions.

- [ ] **Step 4: Run full test suite**
```bash
pytest tests/
```

- [ ] **Step 5: Git commit**
```bash
git add aqpqc/cli.py aqpqc/__init__.py tests/test_aqpqc.py README.md
git commit -m "feat(cli): add unified cli and comprehensive test suite"
```
