# Design Specification: AQPQC Production Hardening (C99 Single-Header, Passive Kernel Telemetry, and TLS 1.3 Group Negotiation)

## Problem Statement
The initial Python prototype demonstrated algorithmic viability, but has three fatal production limitations:
1. **Decision Latency**: Python + XGBoost takes 5-15ms, whereas crypto takes ~60µs.
2. **Telemetry Overhead**: Probing DNS (1.1.1.1) creates outbound traffic, leaks metadata, and fails in air-gapped environments.
3. **Wire Protocol Interop**: Custom JSON framing cannot integrate with real TLS 1.3 proxies (Envoy, Nginx, OpenSSL).

## Goals & Architectural Solutions

### 1. Passive Kernel Telemetry (`aqpqc/passive_telemetry.py` & C equivalent)
- Reads `TCP_INFO` directly from Linux kernel via `getsockopt(fd, IPPROTO_TCP, TCP_INFO)`.
- Extracts:
  - `tcpi_rtt` (RTT in microseconds)
  - `tcpi_rttvar` (jitter)
  - `tcpi_snd_mss` (active MSS -> MTU)
  - `tcpi_retrans` / `tcpi_total_retrans` (packet loss / retransmission rate)
- Generates context vector with 0 additional network packets and 0ms latency overhead.

### 2. Zero-Dependency C99 Single-Header Transpiler (`include/aqpqc.h`)
- Compiles the decision logic and Pareto boundaries into a freestanding C99 single-header file: `include/aqpqc.h`.
- Requires only `stdint.h` and `stddef.h`. Zero external libraries, zero dynamic allocation (`malloc`).
- RAM consumption: <4 KB.
- Execution speed: <0.1 microseconds (compiled branch jumps).
- Compatible with embedded targets (`-nostdlib`, ARM Cortex-M, ESP32) and high-throughput proxies (Envoy, OpenSSL providers).

### 3. TLS 1.3 Named Group Negotiator
- Maps NIST PQC KEM algorithms to standardized IANA / draft TLS 1.3 NamedGroup identifiers:
  - `0x11ec`: `MLKEM512`
  - `0x11ed`: `MLKEM768`
  - `0x11ee`: `MLKEM1024`
  - `0x2f39`: `X25519MLKEM768` (hybrid)
- Given a connected client socket file descriptor, reads kernel socket state, determines optimal PQC group in <1µs, and returns preferred TLS 1.3 group identifier.

## Verification
- C unit test: `tests/test_c_aqpqc.c` compiled with `gcc -Wall -Wextra -Werror` verifying C decision engine matches Python output with <1µs latency.
- Python pytest: `tests/test_passive_telemetry.py` and `tests/test_tls13.py`.
