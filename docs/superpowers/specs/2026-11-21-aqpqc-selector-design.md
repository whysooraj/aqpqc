# Design Specification: AQPQC Selector

## Context and Goal
The rapid progress toward quantum computing threatens classic asymmetric public-key cryptosystems (RSA, ECDSA, ECDH) via Shor's algorithm. In August 2024, NIST released standardized Post-Quantum Cryptography (PQC) primitives:
- ML-KEM (FIPS 203) - Key Encapsulation
- ML-DSA (FIPS 204) - Digital Signatures
- SLH-DSA (FIPS 205) - Stateless Hash-Based Signatures
- Falcon - Fast Lattice-Based Signatures

Unlike classical algorithms, PQC algorithms have asymmetric resource footprints: huge differences in public key size, signature/ciphertext size, CPU cycles, and memory consumption. Selecting a single static cipher across heterogeneous hardware (cloud servers vs embedded IoT) and volatile network environments causes packet fragmentation, high latency, or memory exhaustion.

The goal of this project is to build **AQPQC Selector** from scratch: a standalone Python toolkit and library that dynamically profiles hardware and network context, and uses machine learning and multi-objective Pareto optimization to select the optimal post-quantum cryptographic cipher.

## Architecture and Components

The toolkit is organized into modular Python components:

```
aqpqc/
|-- pyproject.toml
|-- README.md
|-- aqpqc/
|   |-- __init__.py
|   |-- catalog.py        # NIST PQC algorithm specifications and benchmarks
|   |-- telemetry.py      # Real-time hardware and network telemetry collector
|   |-- benchmark.py      # liboqs integration with NIST-profiled baseline fallback
|   |-- dataset.py        # Synthetic context dataset generator for offline model training
|   |-- selector.py       # XGBoost classifier + multi-objective Pareto ranker
|   |-- explain.py        # Explainable AI feature importance (SHAP / heuristic weights)
|   `-- cli.py            # CLI: benchmark, train, select commands
`-- tests/
    `-- test_aqpqc.py     # Runnable verification suite
```

### 1. Catalog (`aqpqc/catalog.py`)
Maintains precise NIST specifications for PQC algorithms:
- **KEM Primitives**:
  - `ML-KEM-512` (NIST Level 1): Public key 800 B, Ciphertext 768 B, Shared Secret 32 B. Low memory/bandwidth footprint.
  - `ML-KEM-768` (NIST Level 3): Public key 1184 B, Ciphertext 1088 B, Shared Secret 32 B. Balanced enterprise default.
  - `ML-KEM-1024` (NIST Level 5): Public key 1568 B, Ciphertext 1568 B, Shared Secret 32 B. Highest security.
- **Signature Primitives**:
  - `ML-DSA-44` (NIST Level 2): Public key 1312 B, Signature 2420 B.
  - `ML-DSA-65` (NIST Level 3): Public key 1952 B, Signature 3309 B.
  - `ML-DSA-87` (NIST Level 5): Public key 2592 B, Signature 4627 B.
  - `Falcon-512` (NIST Level 1): Public key 897 B, Signature 666 B. Compact signatures, floating-point intensive.
  - `Falcon-1024` (NIST Level 5): Public key 1793 B, Signature 1280 B.
  - `SLH-DSA-SHAKE-128s` (NIST Level 1): Public key 32 B, Signature 7856 B. Minimal public key, very large signature.

### 2. Telemetry Collector (`aqpqc/telemetry.py`)
Captures runtime system and network context:
- `cpu_usage_pct`: Current CPU load percentage (`psutil.cpu_percent`).
- `mem_available_mb`: Free system memory in megabytes (`psutil.virtual_memory().available / (1024 * 1024)`).
- `network_rtt_ms`: Estimated round-trip latency to peer or gateway.
- `network_bandwidth_mbps`: Available bandwidth throughput.
- `packet_loss_pct`: Network packet loss rate.
- `mtu_bytes`: Network Maximum Transmission Unit (default 1500 bytes for standard Ethernet).

### 3. Benchmark Engine (`aqpqc/benchmark.py`)
- Detects if `oqs` (liboqs-python wrapper) is available in the environment.
- If present, executes real keypair generation, encapsulation/decapsulation, and sign/verify benchmarks, measuring cycles and elapsed microseconds.
- If absent, loads calibrated benchmark tables calibrated on standardized x86_64 / ARM64 execution cycles to ensure portable zero-failure execution on any system.

### 4. Synthetic Dataset Generator (`aqpqc/dataset.py`)
Generates balanced operational scenarios across:
- Edge IoT: Low RAM (<128MB), constrained CPU, low MTU / unstable radio link.
- Mobile / Cellular: Moderate bandwidth, fluctuating latency (40-150ms), 1-5% packet loss.
- Cloud / Datacenter: High RAM (>4GB), fast multi-core CPU, gigabit connection, low latency (<5ms).
Computes ground-truth optimal algorithm per scenario using Pareto dominance over latency, security level (1, 3, 5), and packet fragmentation penalty.

### 5. Intelligent Selector (`aqpqc/selector.py`)
- **Classifier**: Multi-class XGBoost (or LightGBM/GradientBoosting fallback) predicting optimal cipher choice based on context feature vector.
- **Pareto Ranker**: Post-evaluates candidates by scoring:
  $$\text{Score} = w_s \cdot \text{SecurityLevel} - w_l \cdot \text{NormalizedLatency} - w_m \cdot \text{FragmentationRisk}$$
- Returns primary recommendation and top-3 ranked alternatives with confidence percentages.

### 6. Explainability Module (`aqpqc/explain.py`)
Provides clear decision rationales for cryptographic agility audit logs:
- Computes feature contribution toward the chosen algorithm.
- Produces human-readable explanations (e.g., "Selected ML-KEM-512 over ML-KEM-1024 due to MTU limit 1500 bytes and packet loss rate of 4.2%").

### 7. CLI & Python API (`aqpqc/cli.py` & `aqpqc/__init__.py`)
- CLI commands:
  - `aqpqc catalog`: List supported NIST PQC primitives with sizes and security levels.
  - `aqpqc telemetry`: Display current hardware and network metrics.
  - `aqpqc train [--samples N]`: Train context-aware selector model.
  - `aqpqc select [--op kem|sign] [--security 1|3|5]`: Recommend optimal cipher for current or specified context.
- Python API:
  ```python
  from aqpqc import AQPQCSelector, TelemetryCollector
  
  collector = TelemetryCollector()
  ctx = collector.collect()
  selector = AQPQCSelector.load_or_train()
  recommendation = selector.recommend(ctx, op_type="kem", min_security=3)
  print(recommendation.algorithm, recommendation.confidence, recommendation.explanation)
  ```

## Verification & Runnable Checks
- `tests/test_aqpqc.py`: Single runnable verification script.
  - Test 1: Verify catalog size numbers match NIST FIPS 203/204 specifications.
  - Test 2: Verify telemetry collection returns valid non-negative metrics.
  - Test 3: Verify training pipeline builds model and achieves >90% validation accuracy on test scenarios.
  - Test 4: Verify context differentiation: constrained edge context picks Level 1/Falcon, whereas high-assurance cloud context picks Level 5.
