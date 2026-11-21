"""Benchmarking engine for NIST Post-Quantum Cryptography algorithms."""

from dataclasses import asdict, dataclass
import time
from typing import Any, Dict, List, Optional
import psutil

from aqpqc.catalog import ALGORITHM_CATALOG, PQCAlgorithm, get_algorithm, list_algorithms

@dataclass
class BenchmarkResult:
    algorithm: str
    op_type: str
    op_time_us: float        # Encap or Sign duration in microseconds
    keygen_time_us: float    # Keypair generation in microseconds
    verify_time_us: float    # Decap or Verify duration in microseconds
    memory_peak_kb: float    # Memory usage in KB
    cpu_cycles_est: int      # Estimated CPU cycles
    source: str              # "native_liboqs" or "calibrated_profile"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BenchmarkEngine:
    """Executes live or calibrated benchmarks for PQC algorithms."""

    def __init__(self):
        self._has_liboqs = self._check_liboqs_available()

    @staticmethod
    def _check_liboqs_available() -> bool:
        try:
            import oqs  # type: ignore
            return True
        except ImportError:
            return False

    @property
    def has_liboqs(self) -> bool:
        return self._has_liboqs

    def _get_cpu_scaling_factor(self) -> float:
        """Calculate hardware timing scale factor relative to reference 3.0 GHz x86-64."""
        # ponytail: Normalize timing against reference processor frequency
        freq = psutil.cpu_freq()
        if freq and freq.current > 0:
            scale = 3000.0 / max(freq.current, 500.0)
            return round(scale, 2)
        return 1.0

    def get_calibrated_profile(self, algo_name: str) -> BenchmarkResult:
        """Generate calibrated profile from NIST hardware reference data."""
        algo = get_algorithm(algo_name)
        scale = self._get_cpu_scaling_factor()

        # Cycles to microseconds conversion assuming reference 3 GHz: 1 us = 3000 cycles
        keygen_us = round((algo.estimated_cycles_keygen / 3000.0) * scale, 2)
        op_us = round((algo.estimated_cycles_operation / 3000.0) * scale, 2)
        verify_us = round((algo.estimated_cycles_verify / 3000.0) * scale, 2)

        return BenchmarkResult(
            algorithm=algo.name,
            op_type=algo.op_type,
            op_time_us=max(op_us, 1.0),
            keygen_time_us=max(keygen_us, 1.0),
            verify_time_us=max(verify_us, 1.0),
            memory_peak_kb=algo.memory_footprint_kb,
            cpu_cycles_est=int(algo.estimated_cycles_operation * scale),
            source="calibrated_profile",
        )

    def benchmark(self, algo_name: str, iterations: int = 10) -> BenchmarkResult:
        """Benchmark a specific algorithm, running native liboqs if present or calibrated baseline."""
        if not self._has_liboqs:
            return self.get_calibrated_profile(algo_name)

        # Native liboqs execution if installed
        try:
            import oqs  # type: ignore
            algo = get_algorithm(algo_name)
            
            # Map standardized name to liboqs identifier if needed
            liboqs_map = {
                "ML-KEM-512": "Kyber512",
                "ML-KEM-768": "Kyber768",
                "ML-KEM-1024": "Kyber1024",
                "ML-DSA-44": "Dilithium2",
                "ML-DSA-65": "Dilithium3",
                "ML-DSA-87": "Dilithium5",
                "Falcon-512": "Falcon-512",
                "Falcon-1024": "Falcon-1024",
                "SLH-DSA-SHAKE-128s": "SPHINCS+-SHAKE-128s-simple",
            }
            target = liboqs_map.get(algo_name, algo_name)

            if algo.op_type == "kem":
                with oqs.KeyEncapsulation(target) as kem:
                    # Keygen timing
                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        public_key = kem.generate_keypair()
                    keygen_us = ((time.perf_counter() - t0) / iterations) * 1e6

                    # Encap timing
                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        ciphertext, shared_secret = kem.encap_secret(public_key)
                    op_us = ((time.perf_counter() - t0) / iterations) * 1e6

                    # Decap timing
                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        _ = kem.decap_secret(ciphertext)
                    verify_us = ((time.perf_counter() - t0) / iterations) * 1e6

            else:
                with oqs.Signature(target) as sig:
                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        public_key = sig.generate_keypair()
                    keygen_us = ((time.perf_counter() - t0) / iterations) * 1e6

                    msg = b"AQPQC-selector-benchmark-payload-test-data"
                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        signature = sig.sign(msg)
                    op_us = ((time.perf_counter() - t0) / iterations) * 1e6

                    t0 = time.perf_counter()
                    for _ in range(iterations):
                        _ = sig.verify(msg, signature, public_key)
                    verify_us = ((time.perf_counter() - t0) / iterations) * 1e6

            return BenchmarkResult(
                algorithm=algo.name,
                op_type=algo.op_type,
                op_time_us=round(op_us, 2),
                keygen_time_us=round(keygen_us, 2),
                verify_time_us=round(verify_us, 2),
                memory_peak_kb=algo.memory_footprint_kb,
                cpu_cycles_est=int(op_us * 3000),
                source="native_liboqs",
            )
        except Exception:
            return self.get_calibrated_profile(algo_name)

    def benchmark_all(self, op_type: Optional[str] = None, iterations: int = 5) -> List[BenchmarkResult]:
        """Benchmark all algorithms matching op_type filter."""
        algos = list_algorithms(op_type=op_type)  # type: ignore
        return [self.benchmark(algo.name, iterations=iterations) for algo in algos]
