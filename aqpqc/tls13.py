"""Standard TLS 1.3 Key Exchange NamedGroup negotiator for post-quantum hybrid and pure KEMs."""

import socket
from typing import Any, Dict, Optional

from aqpqc.passive_telemetry import extract_kernel_tcp_telemetry
from aqpqc.selector import AQPQCSelector
from aqpqc.telemetry import TelemetrySnapshot

# Standard IANA and draft NamedGroup values (RFC 8446 / draft-ietf-tls-hybrid-design)
GROUP_MLKEM512 = 0x11EC
GROUP_MLKEM768 = 0x11ED
GROUP_MLKEM1024 = 0x11EE
GROUP_X25519_MLKEM768 = 0x2F39  # Standard hybrid group widely adopted in Chrome & Cloudflare

TLS13_GROUPS = {
    GROUP_MLKEM512: {
        "name": "MLKEM512",
        "standard_algo": "ML-KEM-512",
        "security_level": 1,
        "is_hybrid": False,
    },
    GROUP_MLKEM768: {
        "name": "MLKEM768",
        "standard_algo": "ML-KEM-768",
        "security_level": 3,
        "is_hybrid": False,
    },
    GROUP_MLKEM1024: {
        "name": "MLKEM1024",
        "standard_algo": "ML-KEM-1024",
        "security_level": 5,
        "is_hybrid": False,
    },
    GROUP_X25519_MLKEM768: {
        "name": "X25519MLKEM768",
        "standard_algo": "ML-KEM-768",
        "security_level": 3,
        "is_hybrid": True,
    },
}

def select_tls13_group_from_telemetry(
    telemetry: TelemetrySnapshot,
    min_security: int = 1,
    prefer_hybrid: bool = True
) -> Dict[str, Any]:
    """Select optimal TLS 1.3 NamedGroup ID based on operational context."""
    selector = AQPQCSelector()
    rec = selector.recommend(telemetry, op_type="kem", min_security=min_security)

    if rec.algorithm == "ML-KEM-512":
        group_id = GROUP_MLKEM512
    elif rec.algorithm == "ML-KEM-1024":
        group_id = GROUP_MLKEM1024
    else:
        group_id = GROUP_X25519_MLKEM768 if prefer_hybrid else GROUP_MLKEM768

    group_info = TLS13_GROUPS[group_id]
    return {
        "group_id": group_id,
        "group_hex": f"0x{group_id:04x}",
        "group_name": group_info["name"],
        "is_hybrid": group_info["is_hybrid"],
        "security_level": group_info["security_level"],
        "algorithm": rec.algorithm,
        "confidence": rec.confidence,
        "explanation": rec.explanation,
    }


def negotiate_tls13_group(
    sock: socket.socket,
    min_security: int = 1,
    prefer_hybrid: bool = True
) -> Dict[str, Any]:
    """Passively inspect incoming client TCP socket and return preferred TLS 1.3 Key Exchange NamedGroup."""
    kernel_snap = extract_kernel_tcp_telemetry(sock)
    telem = kernel_snap.to_telemetry_snapshot()
    result = select_tls13_group_from_telemetry(telem, min_security=min_security, prefer_hybrid=prefer_hybrid)
    result["tcpi_rtt_us"] = kernel_snap.rtt_us
    result["tcpi_mss"] = kernel_snap.mss_bytes
    result["tcpi_mtu"] = kernel_snap.effective_mtu
    return result
