"""FastAPI REST Microservice for AQPQC Selector."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from aqpqc import __version__
from aqpqc.benchmark import BenchmarkEngine
from aqpqc.catalog import ALGORITHM_CATALOG, list_algorithms
from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot

app = FastAPI(
    title="AQPQC Selector API",
    description="Adaptive Quantum Intelligence Framework for Context-Aware Post-Quantum Cryptographic Algorithm Selection",
    version=__version__,
)

# Global lazy selector instance
_selector: Optional[AQPQCSelector] = None

def get_selector() -> AQPQCSelector:
    global _selector
    if _selector is None:
        _selector = AQPQCSelector()
        _selector.train(n_samples=500, random_state=42)
    return _selector


class TelemetryOverride(BaseModel):
    cpu_usage_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    mem_available_mb: Optional[float] = Field(None, ge=1.0)
    network_rtt_ms: Optional[float] = Field(None, ge=0.0)
    network_bandwidth_mbps: Optional[float] = Field(None, ge=0.01)
    packet_loss_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    mtu_bytes: Optional[int] = Field(None, ge=576, le=9000)


class RecommendRequest(BaseModel):
    op_type: str = Field("kem", pattern="^(kem|sign)$", description="Target operation: kem or sign")
    min_security: int = Field(1, description="Minimum NIST security level (1, 2, 3, or 5)")
    telemetry_override: Optional[TelemetryOverride] = None


class BenchmarkRequest(BaseModel):
    op_type: Optional[str] = Field(None, pattern="^(kem|sign)$")
    algo: Optional[str] = None
    iterations: int = Field(5, ge=1, le=50)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aqpqc-selector",
        "version": __version__,
    }


@app.get("/api/v1/catalog")
def get_catalog(op: Optional[str] = Query(None, pattern="^(kem|sign)$")):
    """List supported NIST Post-Quantum Cryptography algorithms."""
    algos = list_algorithms(op_type=op)  # type: ignore
    return [a.__dict__ for a in algos]


@app.get("/api/v1/telemetry")
def get_telemetry():
    """Retrieve live server hardware and network telemetry snapshot."""
    collector = TelemetryCollector()
    snapshot = collector.collect(probe_network=False)
    return snapshot.to_dict()


@app.post("/api/v1/recommend")
def recommend_cipher(req: RecommendRequest):
    """Recommend optimal post-quantum cryptographic cipher matching context constraints."""
    collector = TelemetryCollector()
    snapshot = collector.collect(probe_network=False)

    # Apply client-provided overrides if provided
    if req.telemetry_override:
        ov = req.telemetry_override
        if ov.cpu_usage_pct is not None:
            snapshot.cpu_usage_pct = ov.cpu_usage_pct
        if ov.mem_available_mb is not None:
            snapshot.mem_available_mb = ov.mem_available_mb
        if ov.network_rtt_ms is not None:
            snapshot.network_rtt_ms = ov.network_rtt_ms
        if ov.network_bandwidth_mbps is not None:
            snapshot.network_bandwidth_mbps = ov.network_bandwidth_mbps
        if ov.packet_loss_pct is not None:
            snapshot.packet_loss_pct = ov.packet_loss_pct
        if ov.mtu_bytes is not None:
            snapshot.mtu_bytes = ov.mtu_bytes

    selector = get_selector()
    result = selector.recommend(
        context=snapshot,
        op_type=req.op_type,
        min_security=req.min_security,
    )
    return result.to_dict()


@app.post("/api/v1/benchmark")
def run_benchmark(req: BenchmarkRequest):
    """Execute live or calibrated benchmarks for specified algorithm or type."""
    engine = BenchmarkEngine()
    if req.algo:
        if req.algo not in ALGORITHM_CATALOG:
            raise HTTPException(status_code=404, detail=f"Algorithm '{req.algo}' not found in catalog")
        res = [engine.benchmark(req.algo, iterations=req.iterations)]
    else:
        res = engine.benchmark_all(op_type=req.op_type, iterations=req.iterations)
    return [r.to_dict() for r in res]
