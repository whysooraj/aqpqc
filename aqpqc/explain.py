"""Explainable AI (XAI) rationale generator for cryptographic agility decisions."""

from typing import Dict, List, Optional
from aqpqc.catalog import get_algorithm
from aqpqc.telemetry import TelemetrySnapshot

def generate_decision_explanation(
    algo_name: str,
    context: TelemetrySnapshot,
    op_type: str,
    min_security: int,
    confidence: float,
    feature_importances: Optional[Dict[str, float]] = None,
) -> str:
    """Produce human-readable and audit-compliant rationale for cipher selection."""
    algo = get_algorithm(algo_name)

    reasons: List[str] = []

    # 1. Security rationale
    if algo.security_level == min_security:
        reasons.append(f"Directly satisfies target NIST Security Level {min_security}")
    elif algo.security_level > min_security:
        reasons.append(f"Provides elevated NIST Security Level {algo.security_level} (minimum requirement: {min_security})")

    # 2. MTU and Network Fragmentation rationale
    payload_bytes = algo.ciphertext_bytes + algo.public_key_bytes if op_type == "kem" else algo.signature_bytes + algo.public_key_bytes
    if payload_bytes <= context.mtu_bytes:
        reasons.append(f"Combined wire payload ({payload_bytes}B) fits within MTU ({context.mtu_bytes}B), avoiding IP packet fragmentation")
    else:
        fragments = (payload_bytes + context.mtu_bytes - 1) // context.mtu_bytes
        reasons.append(f"Payload ({payload_bytes}B) requires {fragments} packets on MTU {context.mtu_bytes}B under {context.packet_loss_pct:.1f}% packet loss")

    # 3. Hardware resource rationale
    if context.mem_available_mb < 128.0:
        reasons.append(f"Optimized for constrained system memory ({context.mem_available_mb:.1f}MB available, algorithm footprint {algo.memory_footprint_kb:.1f}KB)")
    elif context.mem_available_mb > 4096.0:
        reasons.append(f"Ample host memory headroom ({context.mem_available_mb:.0f}MB available)")

    # 4. Latency / RTT rationale
    if context.network_rtt_ms > 50.0:
        reasons.append(f"Mitigates high network latency ({context.network_rtt_ms:.1f}ms RTT) with efficient crypto operations ({algo.estimated_cycles_operation // 1000}k cycles)")

    bullet_points = "; ".join(reasons)
    return (
        f"Selected {algo.name} with {confidence*100.0:.1f}% confidence. "
        f"Key decision factors: {bullet_points}."
    )
