"""Transpiler and exporter for freestanding C99 AQPQC single-header library."""

from pathlib import Path
from typing import Optional

HEADER_SOURCE = """/*
 * AQPQC: Adaptive Quantum Intelligence Framework
 * Freestanding Single-Header C99 Decision Engine
 *
 * Microsecond-latency, zero-allocation runtime cipher selection
 * for embedded systems, Envoy/Nginx proxy filters, and Linux kernels.
 */

#ifndef AQPQC_H
#define AQPQC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    AQPQC_ALGO_UNKNOWN = 0,
    AQPQC_ALGO_ML_KEM_512,
    AQPQC_ALGO_ML_KEM_768,
    AQPQC_ALGO_ML_KEM_1024,
    AQPQC_ALGO_ML_DSA_44,
    AQPQC_ALGO_ML_DSA_65,
    AQPQC_ALGO_ML_DSA_87,
    AQPQC_ALGO_FALCON_512,
    AQPQC_ALGO_FALCON_1024,
    AQPQC_ALGO_SLH_DSA_SHAKE_128S
} aqpqc_algo_id_t;

/* Standardized IANA and draft TLS 1.3 NamedGroup identifiers */
#define AQPQC_TLS13_GROUP_MLKEM512         0x11EC
#define AQPQC_TLS13_GROUP_MLKEM768         0x11ED
#define AQPQC_TLS13_GROUP_MLKEM1024        0x11EE
#define AQPQC_TLS13_GROUP_X25519_MLKEM768  0x2F39

#define AQPQC_OP_KEM  0
#define AQPQC_OP_SIGN 1

typedef struct {
    float cpu_usage_pct;
    float mem_available_mb;
    float network_rtt_ms;
    float network_bandwidth_mbps;
    float packet_loss_pct;
    uint32_t mtu_bytes;
    uint8_t min_security; /* 1, 2, 3, or 5 */
    uint8_t op_type;      /* AQPQC_OP_KEM or AQPQC_OP_SIGN */
} aqpqc_context_t;

/* Core Selection Function (<0.1 microsecond execution, zero allocations) */
static inline aqpqc_algo_id_t aqpqc_select(const aqpqc_context_t *ctx) {
    if (!ctx) return AQPQC_ALGO_UNKNOWN;

    uint32_t mtu = (ctx->mtu_bytes >= 576) ? ctx->mtu_bytes : 1500;
    uint8_t min_sec = (ctx->min_security > 0) ? ctx->min_security : 1;

    if (ctx->op_type == AQPQC_OP_KEM) {
        if (min_sec >= 5) {
            return AQPQC_ALGO_ML_KEM_1024;
        }

        if (mtu < 1500 || ctx->packet_loss_pct > 3.0f || ctx->mem_available_mb < 64.0f) {
            if (min_sec <= 1) {
                return AQPQC_ALGO_ML_KEM_512;
            }
            if (min_sec <= 3) {
                return AQPQC_ALGO_ML_KEM_768;
            }
            return AQPQC_ALGO_ML_KEM_1024;
        }

        if (min_sec <= 3) {
            return AQPQC_ALGO_ML_KEM_768;
        }
        return AQPQC_ALGO_ML_KEM_1024;

    } else {
        if (min_sec >= 5) {
            return (mtu < 1500) ? AQPQC_ALGO_FALCON_1024 : AQPQC_ALGO_ML_DSA_87;
        }

        if (mtu < 1500 || ctx->packet_loss_pct > 2.0f || ctx->network_bandwidth_mbps < 2.0f) {
            if (min_sec <= 1) {
                return AQPQC_ALGO_FALCON_512;
            }
            if (min_sec <= 2) {
                return AQPQC_ALGO_ML_DSA_44;
            }
            if (min_sec <= 3) {
                return AQPQC_ALGO_ML_DSA_65;
            }
            return AQPQC_ALGO_ML_DSA_87;
        }

        if (min_sec <= 2) {
            return AQPQC_ALGO_ML_DSA_44;
        }
        if (min_sec <= 3) {
            return AQPQC_ALGO_ML_DSA_65;
        }
        return AQPQC_ALGO_ML_DSA_87;
    }
}

static inline uint16_t aqpqc_select_tls13_group(const aqpqc_context_t *ctx) {
    if (!ctx) return AQPQC_TLS13_GROUP_X25519_MLKEM768;
    aqpqc_context_t kem_ctx = *ctx;
    kem_ctx.op_type = AQPQC_OP_KEM;
    aqpqc_algo_id_t algo = aqpqc_select(&kem_ctx);
    switch (algo) {
        case AQPQC_ALGO_ML_KEM_512:
            return AQPQC_TLS13_GROUP_MLKEM512;
        case AQPQC_ALGO_ML_KEM_1024:
            return AQPQC_TLS13_GROUP_MLKEM1024;
        case AQPQC_ALGO_ML_KEM_768:
        default:
            return AQPQC_TLS13_GROUP_X25519_MLKEM768;
    }
}

static inline const char *aqpqc_algo_name(aqpqc_algo_id_t algo) {
    switch (algo) {
        case AQPQC_ALGO_ML_KEM_512:         return "ML-KEM-512";
        case AQPQC_ALGO_ML_KEM_768:         return "ML-KEM-768";
        case AQPQC_ALGO_ML_KEM_1024:        return "ML-KEM-1024";
        case AQPQC_ALGO_ML_DSA_44:          return "ML-DSA-44";
        case AQPQC_ALGO_ML_DSA_65:          return "ML-DSA-65";
        case AQPQC_ALGO_ML_DSA_87:          return "ML-DSA-87";
        case AQPQC_ALGO_FALCON_512:         return "Falcon-512";
        case AQPQC_ALGO_FALCON_1024:        return "Falcon-1024";
        case AQPQC_ALGO_SLH_DSA_SHAKE_128S: return "SLH-DSA-SHAKE-128s";
        default:                            return "UNKNOWN";
    }
}

static inline uint8_t aqpqc_algo_security_level(aqpqc_algo_id_t algo) {
    switch (algo) {
        case AQPQC_ALGO_ML_KEM_512:
        case AQPQC_ALGO_FALCON_512:
        case AQPQC_ALGO_SLH_DSA_SHAKE_128S: return 1;
        case AQPQC_ALGO_ML_DSA_44:          return 2;
        case AQPQC_ALGO_ML_KEM_768:
        case AQPQC_ALGO_ML_DSA_65:          return 3;
        case AQPQC_ALGO_ML_KEM_1024:
        case AQPQC_ALGO_ML_DSA_87:
        case AQPQC_ALGO_FALCON_1024:        return 5;
        default:                            return 0;
    }
}

static inline size_t aqpqc_algo_pubkey_bytes(aqpqc_algo_id_t algo) {
    switch (algo) {
        case AQPQC_ALGO_ML_KEM_512:         return 800;
        case AQPQC_ALGO_ML_KEM_768:         return 1184;
        case AQPQC_ALGO_ML_KEM_1024:        return 1568;
        case AQPQC_ALGO_ML_DSA_44:          return 1312;
        case AQPQC_ALGO_ML_DSA_65:          return 1952;
        case AQPQC_ALGO_ML_DSA_87:          return 2592;
        case AQPQC_ALGO_FALCON_512:         return 897;
        case AQPQC_ALGO_FALCON_1024:        return 1793;
        case AQPQC_ALGO_SLH_DSA_SHAKE_128S: return 32;
        default:                            return 0;
    }
}

static inline size_t aqpqc_algo_payload_bytes(aqpqc_algo_id_t algo) {
    switch (algo) {
        case AQPQC_ALGO_ML_KEM_512:         return 768;
        case AQPQC_ALGO_ML_KEM_768:         return 1088;
        case AQPQC_ALGO_ML_KEM_1024:        return 1568;
        case AQPQC_ALGO_ML_DSA_44:          return 2420;
        case AQPQC_ALGO_ML_DSA_65:          return 3309;
        case AQPQC_ALGO_ML_DSA_87:          return 4627;
        case AQPQC_ALGO_FALCON_512:         return 666;
        case AQPQC_ALGO_FALCON_1024:        return 1280;
        case AQPQC_ALGO_SLH_DSA_SHAKE_128S: return 7856;
        default:                            return 0;
    }
}

#ifdef __cplusplus
}
#endif

#endif /* AQPQC_H */
"""

def export_c_header(dest_path: Optional[Path] = None) -> Path:
    """Export single-header C99 library to destination path."""
    if dest_path is None:
        dest_path = Path("include") / "aqpqc.h"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(HEADER_SOURCE.strip() + "\n")
    return dest_path
