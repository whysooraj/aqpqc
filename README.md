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

1. **Freestanding C99 Engine (`include/aqpqc.h`)**: Single-header zero-dependency C99 decision engine executing in <0.1 microseconds with zero dynamic allocations (`malloc`). Embeddable in microcontrollers (ARM Cortex-M), Linux kernel modules, and Envoy/Nginx proxy filters.
2. **Passive Kernel Telemetry (`aqpqc.passive_telemetry`)**: Zero-overhead passive extraction from Linux `getsockopt(fd, IPPROTO_TCP, TCP_INFO)`. Directly reads TCP RTT, MSS, and retransmission packet loss with 0 outbound network requests.
3. **TLS 1.3 NamedGroup Negotiator (`aqpqc.tls13`)**: Maps decisions directly to standard TLS 1.3 Key Exchange NamedGroups (`0x11EC` MLKEM512, `0x11ED` MLKEM768, `0x11EE` MLKEM1024, `0x2F39` X25519MLKEM768).
4. **Catalog (`aqpqc.catalog`)**: Authoritative NIST size specifications, security parameters, and cycle profiles.
5. **Benchmark Engine (`aqpqc.benchmark`)**: Pluggable benchmarking using native `liboqs-python` when available, with calibrated reference profiles as zero-failure fallback.
6. **Context-Aware Selector (`aqpqc.selector`)**: XGBoost ensemble with Pareto post-filtering ensuring strict physical constraints (RAM ceiling, MTU fragmentation penalty).
7. **Explainability (`aqpqc.explain`)**: Audit-compliant decision rationale tracing why a specific cipher was chosen.

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

### 6. Start REST Microservice
```bash
aqpqc serve --host 127.0.0.1 --port 8000
# OpenAPI documentation interactive UI: http://127.0.0.1:8000/docs
```

### 7. Export C99 Single-Header Engine
```bash
aqpqc export-c --out include/aqpqc.h
```

## Embedding C99 Engine (<0.1 µs Latency, Zero Malloc)

For embedded microcontrollers or high-throughput TLS reverse proxies:

```c
#include "aqpqc.h"

aqpqc_context_t ctx = {
    .cpu_usage_pct = 75.0f,
    .mem_available_mb = 32.0f,
    .network_rtt_ms = 85.0f,
    .mtu_bytes = 576,
    .min_security = 1,
    .op_type = AQPQC_OP_KEM
};

// Sub-nanosecond decision, zero dynamic allocations
aqpqc_algo_id_t algo = aqpqc_select(&ctx);
printf("Selected PQC Algorithm: %s\n", aqpqc_algo_name(algo));

// Standard TLS 1.3 NamedGroup ID (e.g. 0x11EC for ML-KEM-512)
uint16_t tls13_group = aqpqc_select_tls13_group(&ctx);
```

Compile cleanly with any C99 compiler:
```bash
gcc -O3 -Wall -Wextra -Werror -std=c99 -pedantic -Iinclude tests/test_c_aqpqc.c -o test_c && ./test_c
```

## Live Dynamic Handshake Demo

Run the client-server socket demo negotiating PQC primitives in real time:

```bash
# Terminal 1: Start Server
python demo/server.py 9999

# Terminal 2: Run Client
python demo/client.py 9999
```

The client measures real-time network latency and MTU, queries the AQPQC Selector for the optimal KEM (e.g., ML-KEM-512 for constrained links), exchanges public keys and ciphertexts, and derives a symmetric 256-bit session key.

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

## Running Empirical Benchmarks

Run the 1,000-scenario comparison across Static-Max, Static-Min, and AQPQC Selector:

```bash
python experiments/benchmark_evaluation.py 1000
python experiments/plot_results.py
```

Generated outputs:
- CSV: `experiments/results/benchmark_summary.csv`
- Figures: `figures/static_vs_aqpqc_comparison.png`, `figures/feature_importance.png`

## Running Tests

```bash
pytest tests/
```
