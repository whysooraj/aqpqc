"""AQPQC Selector - Adaptive Quantum Intelligence Framework for Context-Aware Post-Quantum Cryptographic Algorithm Selection."""

from aqpqc.benchmark import BenchmarkEngine, BenchmarkResult
from aqpqc.catalog import ALGORITHM_CATALOG, PQCAlgorithm, get_algorithm, list_algorithms
from aqpqc.evaluator import evaluate_strategies
from aqpqc.passive_telemetry import PassiveTelemetrySnapshot, extract_kernel_tcp_telemetry
from aqpqc.selector import AQPQCSelector, SelectionResult
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot

__version__ = "0.1.0"

__all__ = [
    "ALGORITHM_CATALOG",
    "PQCAlgorithm",
    "get_algorithm",
    "list_algorithms",
    "TelemetryCollector",
    "TelemetrySnapshot",
    "PassiveTelemetrySnapshot",
    "extract_kernel_tcp_telemetry",
    "BenchmarkEngine",
    "BenchmarkResult",
    "AQPQCSelector",
    "SelectionResult",
    "evaluate_strategies",
]
