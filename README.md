# AQPQC Selector

Adaptive Quantum Intelligence Framework for Context-Aware Post-Quantum Cryptographic Algorithm Selection.

AQPQC Selector is a standalone Python toolkit that profiles real-time hardware telemetry and network dynamics, evaluates NIST Post-Quantum Cryptography (PQC) standards (FIPS 203, FIPS 204, FIPS 205, Falcon), and uses machine learning (XGBoost) combined with multi-objective Pareto optimization to dynamically select the optimal cryptographic primitive.

## Supported PQC Primitives

- **Key Encapsulation Mechanisms (FIPS 203)**:
  - `ML-KEM-512` (NIST Level 1)
  - `ML-KEM-768` (NIST Level 3)
  - `ML-KEM-1024` (NIST Level 5)
- **Digital Signatures (FIPS 204)**:
  - `ML-DSA-44` (NIST Level 2)
  - `ML-DSA-65` (NIST Level 3)
  - `ML-DSA-87` (NIST Level 5)
- **Compact Signatures**:
  - `Falcon-512` (NIST Level 1, 666-byte signature)
  - `Falcon-1024` (NIST Level 5, 1280-byte signature)
- **Stateless Hash-Based Signatures (FIPS 205)**:
  - `SLH-DSA-SHAKE-128s` (NIST Level 1)

## Architecture

1. **Catalog (`aqpqc.catalog`)**: Authoritative NIST size specifications, security parameters, and cycle profiles.
2. **Telemetry Prober (`aqpqc.telemetry`)**: Non-invasive live hardware monitoring (`psutil`, socket RTT, MTU probing via sysfs).
3. **Benchmark Engine (`aqpqc.benchmark`)**: Pluggable benchmarking using native `liboqs-python` when available, with calibrated reference profiles as zero-failure fallback.
4. **Dataset Labeller (`aqpqc.dataset`)**: Multi-objective Pareto utility generator spanning edge IoT, mobile WAN, and cloud datacenter profiles.
5. **Context-Aware Selector (`aqpqc.selector`)**: XGBoost ensemble with Pareto post-filtering ensuring strict physical constraints (RAM ceiling, MTU fragmentation penalty).
6. **Explainability (`aqpqc.explain`)**: Audit-compliant decision rationale tracing why a specific cipher was chosen.

## Installation

```bash
git clone https://github.com/whysooraj/aqpqc.git
cd aqpqc
pip install -e .
```

## CLI Usage

### 1. View PQC Algorithm Catalog
```bash
aqpqc catalog --op kem
aqpqc catalog --op sign
```

### 2. Sample Runtime Telemetry
```bash
aqpqc telemetry
aqpqc telemetry --json
```

### 3. Benchmark Algorithms
```bash
aqpqc benchmark --op kem --iterations 5
aqpqc benchmark --algo ML-KEM-768
```

### 4. Train Selector Model
```bash
aqpqc train --samples 1000
```

### 5. Context-Aware Cipher Selection
```bash
# Automatic recommendation based on current host metrics:
aqpqc select --op kem --security 3

# Simulated constrained edge IoT device:
aqpqc select --op kem --security 1 --mem 32 --mtu 576 --loss 5.0 --bw 1.0

# Simulated high-assurance cloud server:
aqpqc select --op sign --security 5 --mem 16384 --mtu 9000 --loss 0.0 --bw 1000.0
```

## Python API Usage

```python
from aqpqc import AQPQCSelector, TelemetryCollector

# Sample current system context
collector = TelemetryCollector()
context = collector.collect()

# Initialize and query selector
selector = AQPQCSelector()
result = selector.recommend(context, op_type="kem", min_security=3)

print("Selected:", result.algorithm)
print("Standard:", result.standard_name)
print("Confidence:", result.confidence)
print("Rationale:", result.explanation)
```

## Running Tests

```bash
pytest tests/
```
