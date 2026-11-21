"""Evaluation engine comparing AQPQC Selector against static baselines."""

import math
from typing import Any, Dict, List
import numpy as np

from aqpqc.catalog import ALGORITHM_CATALOG, get_algorithm
from aqpqc.dataset import calculate_pareto_utility, generate_synthetic_dataset
from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetrySnapshot

def evaluate_strategies(
    n_contexts: int = 500,
    random_state: int = 42
) -> Dict[str, Dict[str, float]]:
    """Empirically evaluate Static-Max, Static-Min, and AQPQC Selector across test contexts."""
    X_test, _, _, _ = generate_synthetic_dataset(n_samples=n_contexts, random_state=random_state + 100)

    selector = AQPQCSelector()
    selector.train(n_samples=600, random_state=random_state)

    strategies = ["static_max", "static_min", "aqpqc"]
    results: Dict[str, Dict[str, List[float]]] = {
        strat: {
            "security_satisfied": [],
            "latencies_ms": [],
            "packet_counts": [],
            "severe_frag": [],
            "mem_violations": [],
            "utilities": [],
        }
        for strat in strategies
    }

    for row in X_test:
        cpu = float(row[0])
        mem = float(row[1])
        rtt = float(row[2])
        bw = float(row[3])
        loss = float(row[4])
        mtu = int(row[5])
        req_sec = int(row[6])
        is_sign = bool(row[7] > 0.5)
        op_type = "sign" if is_sign else "kem"

        ctx = TelemetrySnapshot(
            cpu_usage_pct=cpu,
            mem_available_mb=mem,
            network_rtt_ms=rtt,
            network_bandwidth_mbps=bw,
            packet_loss_pct=loss,
            mtu_bytes=mtu,
        )

        for strat in strategies:
            if strat == "static_max":
                chosen_name = "ML-DSA-87" if is_sign else "ML-KEM-1024"
            elif strat == "static_min":
                chosen_name = "ML-DSA-44" if is_sign else "ML-KEM-512"
            else:
                rec = selector.recommend(ctx, op_type=op_type, min_security=req_sec)
                chosen_name = rec.algorithm

            algo = get_algorithm(chosen_name)

            # 1. Security satisfaction
            sec_ok = 1.0 if algo.security_level >= req_sec else 0.0

            # 2. Wire payload & packet counts
            payload = algo.public_key_bytes + (algo.signature_bytes if is_sign else algo.ciphertext_bytes)
            packet_count = math.ceil(payload / mtu)
            is_severe_frag = 1.0 if packet_count > 2 else 0.0

            # 3. Latency
            safe_bw = max(bw * 1e6, 50000.0)
            tx_ms = (payload * 8.0 / safe_bw) * 1000.0
            crypto_ms = (algo.estimated_cycles_operation / 3e6) * (1.0 + cpu / 100.0)
            latency = rtt + tx_ms + crypto_ms

            # 4. Memory violation
            mem_budget_kb = max(mem * 1024.0, 1024.0)
            mem_violation = 1.0 if algo.memory_footprint_kb > (mem_budget_kb * 0.2) else 0.0

            # 5. Pareto utility
            utility = calculate_pareto_utility(
                algo_name=chosen_name,
                cpu_usage_pct=cpu,
                mem_available_mb=mem,
                network_rtt_ms=rtt,
                network_bandwidth_mbps=bw,
                packet_loss_pct=loss,
                mtu_bytes=mtu,
                required_security=req_sec,
            )

            results[strat]["security_satisfied"].append(sec_ok)
            results[strat]["latencies_ms"].append(latency)
            results[strat]["packet_counts"].append(float(packet_count))
            results[strat]["severe_frag"].append(is_severe_frag)
            results[strat]["mem_violations"].append(mem_violation)
            results[strat]["utilities"].append(utility)

    summary: Dict[str, Dict[str, float]] = {}
    for strat in strategies:
        summary[strat] = {
            "security_satisfaction_pct": round(float(np.mean(results[strat]["security_satisfied"])) * 100.0, 2),
            "mean_latency_ms": round(float(np.mean(results[strat]["latencies_ms"])), 2),
            "mean_packets": round(float(np.mean(results[strat]["packet_counts"])), 2),
            "severe_fragmentation_pct": round(float(np.mean(results[strat]["severe_frag"])) * 100.0, 2),
            "memory_violation_pct": round(float(np.mean(results[strat]["mem_violations"])) * 100.0, 2),
            "mean_utility": round(float(np.mean(results[strat]["utilities"])), 2),
        }

    return summary
