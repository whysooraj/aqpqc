"""AQPQC Selector - Adaptive Quantum Intelligence Framework for Context-Aware Post-Quantum Cryptographic Algorithm Selection."""

from aqpqc.benchmark import BenchmarkEngine, BenchmarkResult
from aqpqc.catalog import ALGORITHM_CATALOG, PQCAlgorithm, get_algorithm, list_algorithms
from aqpqc.evaluator import evaluate_strategies
from aqpqc.passive_telemetry import PassiveTelemetrySnapshot, extract_kernel_tcp_telemetry
from aqpqc.selector import AQPQCSelector, SelectionResult
from aqpqc.telemetry import TelemetryCollector, TelemetrySnapshot
from aqpqc.tls13 import (
    GROUP_MLKEM512,
    GROUP_MLKEM768,
    GROUP_MLKEM1024,
    GROUP_X25519_MLKEM768,
    TLS13_GROUPS,
    negotiate_tls13_group,
    select_tls13_group_from_telemetry,
)
from aqpqc.transpile import export_c_header

__version__ = "0.2.0"

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
    "export_c_header",
    "GROUP_MLKEM512",
    "GROUP_MLKEM768",
    "GROUP_MLKEM1024",
    "GROUP_X25519_MLKEM768",
    "TLS13_GROUPS",
    "negotiate_tls13_group",
    "select_tls13_group_from_telemetry",
]
