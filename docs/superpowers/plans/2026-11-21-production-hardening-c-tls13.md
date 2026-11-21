# Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform AQPQC into a real-world, production-ready system with kernel-level passive socket telemetry, a freestanding <1µs C99 single-header engine (`include/aqpqc.h`), and standard TLS 1.3 NamedGroup negotiation.

**Architecture:**
- Linux `TCP_INFO` socket parser extracting live RTT, MSS, and retransmission stats.
- C99 standalone header `include/aqpqc.h` with zero dynamic allocation, compiled and tested with GCC.
- Python transpiler and TLS 1.3 group negotiator.

**Tech Stack:** C99, GCC, Python 3.12+, Linux Sockets, Pytest.

## Global Constraints
- No emojis anywhere in code, comments, documentation, or commit messages.
- Single-header C engine must compile cleanly with `gcc -Wall -Wextra -Werror -std=c99 -pedantic`.
- Zero dynamic allocations (`malloc`/`free`) in the C decision engine.

---

### Task 1: Zero-Overhead Passive Kernel Telemetry via `TCP_INFO`

**Files:**
- Create: `aqpqc/passive_telemetry.py`
- Test: `tests/test_passive_telemetry.py`

- [ ] **Step 1: Write failing test in `tests/test_passive_telemetry.py`**
- [ ] **Step 2: Implement socket `getsockopt(TCP_INFO)` parser in Python**
- [ ] **Step 3: Run test and verify it passes**
- [ ] **Step 4: Git commit**

---

### Task 2: C99 Freestanding Single-Header Engine (`include/aqpqc.h`)

**Files:**
- Create: `include/aqpqc.h`
- Create: `aqpqc/transpile.py`
- Test: `tests/test_c_aqpqc.c`

- [ ] **Step 1: Implement freestanding C99 single-header library with Pareto logic and zero allocations**
- [ ] **Step 2: Write C unit test verifying execution time <1µs and accurate decisions**
- [ ] **Step 3: Compile and run C test with `gcc`**
- [ ] **Step 4: Git commit**

---

### Task 3: Standard TLS 1.3 Named Group Negotiator & CLI Export

**Files:**
- Create: `aqpqc/tls13.py`
- Modify: `aqpqc/cli.py`
- Modify: `README.md`
- Test: `tests/test_tls13.py`

- [ ] **Step 1: Implement TLS 1.3 NamedGroup mapping and negotiation helper**
- [ ] **Step 2: Add `aqpqc export-c` and `aqpqc tls13-negotiate` commands to CLI**
- [ ] **Step 3: Run all tests (pytest + C binary)**
- [ ] **Step 4: Update README with C embedding and TLS 1.3 examples**
- [ ] **Step 5: Git commit**
