"""Synthetic context scenario generator and multi-objective Pareto ground-truth labeller."""

import math
from typing import List, Tuple
import numpy as np

from aqpqc.catalog import ALGORITHM_CATALOG, get_algorithm, list_algorithms

FEATURE_NAMES: List[str] = [
    "cpu_usage_pct",
    "mem_available_mb",
    "network_rtt_ms",
    "network_bandwidth_mbps",
    "packet_loss_pct",
    "mtu_bytes",
    "required_security",
    "op_type_is_sign",
]

def calculate_pareto_utility(
    algo_name: str,
    cpu_usage_pct: float,
    mem_available_mb: float,
    network_rtt_ms: float,
    network_bandwidth_mbps: float,
    packet_loss_pct: float,
    mtu_bytes: int,
    required_security: int,
) -> float:
    """Compute multi-objective Pareto utility score for an algorithm in a given context."""
    algo = get_algorithm(algo_name)

    # Hard security constraint: heavily penalize algorithms failing minimum requirement
    if algo.security_level < required_security:
        return -1000.0 - (required_security - algo.security_level) * 100.0

    # Calculate payload size across wire
    if algo.op_type == "kem":
        payload_bytes = algo.public_key_bytes + algo.ciphertext_bytes
    else:
        payload_bytes = algo.public_key_bytes + algo.signature_bytes

    # Packet fragmentation calculation
    safe_mtu = max(mtu_bytes, 576)
    packet_count = math.ceil(payload_bytes / safe_mtu)
    fragmentation_penalty = max(0, packet_count - 1) * (20.0 + packet_loss_pct * 5.0)

    # Transmission and computation latency (ms)
    safe_bandwidth_bps = max(network_bandwidth_mbps * 1e6, 50000.0)
    tx_time_ms = (payload_bytes * 8.0 / safe_bandwidth_bps) * 1000.0
    crypto_time_ms = (algo.estimated_cycles_operation / 3e6) * (1.0 + (cpu_usage_pct / 100.0))
    total_latency_ms = network_rtt_ms + tx_time_ms + crypto_time_ms

    # Memory pressure penalty
    mem_budget_kb = max(mem_available_mb * 1024.0, 1024.0)
    if algo.memory_footprint_kb > (mem_budget_kb * 0.2):
        memory_penalty = 50.0 + (algo.memory_footprint_kb / mem_budget_kb) * 100.0
    else:
        memory_penalty = 0.0

    # Multi-objective utility balance:
    # Security reward + efficiency bonus - latency cost - fragmentation risk - memory penalty
    security_reward = algo.security_level * 30.0
    latency_cost = total_latency_ms * 0.35

    return security_reward - latency_cost - fragmentation_penalty - memory_penalty


def generate_synthetic_dataset(
    n_samples: int = 1000,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """Synthesize stratified context vectors and compute optimal Pareto ground-truth labels."""
    rng = np.random.default_rng(random_state)
    
    class_names = sorted(list(ALGORITHM_CATALOG.keys()))
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    X_list: List[List[float]] = []
    y_list: List[int] = []

    # Partition: 35% Edge/IoT, 35% Mobile/WAN, 30% Datacenter/Cloud
    n_iot = int(n_samples * 0.35)
    n_mobile = int(n_samples * 0.35)
    n_cloud = n_samples - n_iot - n_mobile

    configs = [
        # (count, cpu_range, mem_range, rtt_range, bw_range, loss_range, mtu_choices)
        (n_iot, (30.0, 95.0), (16.0, 256.0), (40.0, 250.0), (0.1, 5.0), (0.5, 8.0), [576, 1280, 1500]),
        (n_mobile, (10.0, 75.0), (512.0, 4096.0), (15.0, 80.0), (5.0, 80.0), (0.0, 3.0), [1400, 1500]),
        (n_cloud, (5.0, 50.0), (4096.0, 32768.0), (0.5, 10.0), (100.0, 10000.0), (0.0, 0.2), [1500, 9000]),
    ]

    for count, (cpu_min, cpu_max), (mem_min, mem_max), (rtt_min, rtt_max), (bw_min, bw_max), (loss_min, loss_max), mtus in configs:
        for _ in range(count):
            cpu = float(rng.uniform(cpu_min, cpu_max))
            mem = float(rng.uniform(mem_min, mem_max))
            rtt = float(rng.uniform(rtt_min, rtt_max))
            bw = float(rng.uniform(bw_min, bw_max))
            loss = float(rng.uniform(loss_min, loss_max))
            mtu = int(rng.choice(mtus))
            
            # Op type: 50% kem, 50% sign
            is_sign = bool(rng.choice([True, False]))
            target_op = "sign" if is_sign else "kem"
            
            # Security requirement: 1, 2, 3, or 5
            possible_sec = [1, 3, 5] if target_op == "kem" else [1, 2, 3, 5]
            req_sec = int(rng.choice(possible_sec))

            # Select candidate algorithms matching op_type
            candidates = list_algorithms(op_type=target_op)  # type: ignore
            
            best_algo = None
            best_score = -float("inf")
            for cand in candidates:
                score = calculate_pareto_utility(
                    algo_name=cand.name,
                    cpu_usage_pct=cpu,
                    mem_available_mb=mem,
                    network_rtt_ms=rtt,
                    network_bandwidth_mbps=bw,
                    packet_loss_pct=loss,
                    mtu_bytes=mtu,
                    required_security=req_sec,
                )
                if score > best_score:
                    best_score = score
                    best_algo = cand.name

            # Fallback in rare case all negative
            if best_algo is None:
                best_algo = candidates[0].name

            feat_vector = [
                cpu,
                mem,
                rtt,
                bw,
                loss,
                float(mtu),
                float(req_sec),
                1.0 if is_sign else 0.0,
            ]
            X_list.append(feat_vector)
            y_list.append(class_to_idx[best_algo])

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int64), class_names, FEATURE_NAMES
