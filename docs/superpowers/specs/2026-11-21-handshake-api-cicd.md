# Design Specification: Dynamic Handshake Demo, FastAPI Service, and CI/CD Packaging

## Overview
This specification covers three final components for the AQPQC Selector framework:
1. **Live Dynamic Handshake Demo**: A real client-server socket protocol negotiating PQC KEM primitives dynamically based on network context, establishing derived symmetric encryption.
2. **FastAPI Microservice**: A REST API providing remote clients and edge IoT devices with dynamic cipher recommendation endpoints and OpenAPI documentation.
3. **CI/CD & Packaging**: Automated GitHub Actions testing workflows and production-ready Python packaging metadata.

---

## 1. Live Dynamic Handshake Demo (`demo/`)

### Protocol Design
- **Step 1 (Context Evaluation)**: Client inspects runtime telemetry (RTT, MTU, packet drop) and queries `AQPQCSelector` for optimal KEM algorithm.
- **Step 2 (Client Hello)**: Client sends JSON header: `{"algo": "<name>", "public_key_hex": "<hex>"}`.
- **Step 3 (Server Hello / Encapsulation)**: Server validates algorithm from `ALGORITHM_CATALOG`, encapsulates or generates ciphertext and shared secret, and returns: `{"status": "ok", "ciphertext_hex": "<hex>"}`.
- **Step 4 (Key Derivation & Secure Session)**: Both sides derive an encryption key using HKDF/SHA-256 over shared secret, and exchange an encrypted session payload.

### Components
- `demo/server.py`: TCP server accepting dynamic PQC handshakes.
- `demo/client.py`: TCP client querying AQPQC selector, sending handshake, and verifying session key.
- `tests/test_demo.py`: Automated integration test running ephemeral server thread and client handshake.

---

## 2. FastAPI Microservice (`aqpqc/api.py`)

### Endpoints
- `GET /health`: Health status and engine state.
- `GET /api/v1/catalog`: Supported NIST PQC primitives and security levels.
- `GET /api/v1/telemetry`: Current server hardware and network metrics.
- `POST /api/v1/recommend`: Request dynamic cipher selection.
  - Body: `{"op_type": "kem|sign", "min_security": 1|2|3|5, "telemetry_override": {...}}`
  - Returns: `SelectionResult` with confidence, top candidates, and explanation.
- `POST /api/v1/benchmark`: Trigger benchmark run on server.

### Components
- `aqpqc/api.py`: FastAPI app instance with routers and Pydantic request/response schemas.
- `tests/test_api.py`: Test suite using `fastapi.testclient.TestClient`.

---

## 3. CI/CD & Packaging

### Components
- `.github/workflows/ci.yml`: Multi-python testing (3.10, 3.11, 3.12, 3.13) and test suite automation.
- `pyproject.toml`: Add optional dependency extras (`[project.optional-dependencies] api = ["fastapi", "uvicorn", "httpx"]`), project URLs, classifiers.
