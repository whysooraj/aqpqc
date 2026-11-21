# Handshake Demo, FastAPI Microservice, and CI/CD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver live dynamic TCP handshake demo, FastAPI REST microservice with OpenAPI docs, and GitHub Actions CI/CD workflow with enhanced packaging metadata.

**Architecture:**
- TCP socket handshake simulating PQC negotiation with simulated/native KEM crypto.
- FastAPI service exporting endpoints for remote cipher recommendations.
- GitHub Actions CI workflow executing pytest on push/pull-request.

**Tech Stack:** Python 3.12+, FastAPI, Uvicorn, Sockets, Pytest, GitHub Actions.

## Global Constraints
- No emojis anywhere in code, comments, documentation, or commit messages.
- Clean standard library usage for sockets and crypto derivation (hashlib / hmac).
- All new functionality must have runnable pytest checks.

---

### Task 1: Live Dynamic PQC Handshake Protocol & Demo

**Files:**
- Create: `demo/protocol.py`
- Create: `demo/server.py`
- Create: `demo/client.py`
- Test: `tests/test_demo.py`

- [ ] **Step 1: Write test in `tests/test_demo.py` verifying handshake exchange**
- [ ] **Step 2: Implement protocol, server, and client**
- [ ] **Step 3: Run test and verify it passes**
- [ ] **Step 4: Git commit**

---

### Task 2: FastAPI Microservice & OpenAPI Schema

**Files:**
- Create: `aqpqc/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write tests for `/health`, `/api/v1/catalog`, `/api/v1/telemetry`, and `/api/v1/recommend`**
- [ ] **Step 2: Implement `aqpqc/api.py` with FastAPI endpoints**
- [ ] **Step 3: Run test and verify it passes**
- [ ] **Step 4: Git commit**

---

### Task 3: CI/CD Pipeline & Packaging Polish

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Create GitHub Actions workflow for test matrix**
- [ ] **Step 2: Update `pyproject.toml` with extras and packaging metadata**
- [ ] **Step 3: Update `README.md` with demo and API instructions**
- [ ] **Step 4: Run full test suite**
- [ ] **Step 5: Git commit**
