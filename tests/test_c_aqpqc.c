/*
 * C99 Test & Nanosecond Benchmark for AQPQC Single-Header Engine
 */

#define _POSIX_C_SOURCE 199309L
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include "aqpqc.h"

int main(void) {
    printf("Starting AQPQC C99 engine verification...\n");

    /* 1. Constrained Edge IoT context */
    aqpqc_context_t iot_ctx = {
        .cpu_usage_pct = 85.0f,
        .mem_available_mb = 32.0f,
        .network_rtt_ms = 120.0f,
        .network_bandwidth_mbps = 0.5f,
        .packet_loss_pct = 6.0f,
        .mtu_bytes = 576,
        .min_security = 1,
        .op_type = AQPQC_OP_KEM
    };

    aqpqc_algo_id_t algo_kem = aqpqc_select(&iot_ctx);
    assert(algo_kem == AQPQC_ALGO_ML_KEM_512);
    assert(strcmp(aqpqc_algo_name(algo_kem), "ML-KEM-512") == 0);
    assert(aqpqc_algo_security_level(algo_kem) == 1);
    assert(aqpqc_algo_pubkey_bytes(algo_kem) == 800);
    assert(aqpqc_algo_payload_bytes(algo_kem) == 768);

    /* 2. Signature on IoT */
    iot_ctx.op_type = AQPQC_OP_SIGN;
    aqpqc_algo_id_t algo_sign = aqpqc_select(&iot_ctx);
    assert(algo_sign == AQPQC_ALGO_FALCON_512);
    assert(aqpqc_algo_payload_bytes(algo_sign) == 666);

    /* 3. High-assurance server context */
    aqpqc_context_t srv_ctx = {
        .cpu_usage_pct = 15.0f,
        .mem_available_mb = 16384.0f,
        .network_rtt_ms = 1.0f,
        .network_bandwidth_mbps = 1000.0f,
        .packet_loss_pct = 0.0f,
        .mtu_bytes = 9000,
        .min_security = 5,
        .op_type = AQPQC_OP_KEM
    };

    algo_kem = aqpqc_select(&srv_ctx);
    assert(algo_kem == AQPQC_ALGO_ML_KEM_1024);
    assert(aqpqc_algo_security_level(algo_kem) == 5);

    /* 4. TLS 1.3 Group Selection */
    uint16_t group_iot = aqpqc_select_tls13_group(&iot_ctx);
    assert(group_iot == AQPQC_TLS13_GROUP_MLKEM512);

    uint16_t group_srv = aqpqc_select_tls13_group(&srv_ctx);
    assert(group_srv == AQPQC_TLS13_GROUP_MLKEM1024);

    /* 5. Nanosecond Benchmark: 1,000,000 selections */
    const int iterations = 1000000;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    volatile aqpqc_algo_id_t sink = AQPQC_ALGO_UNKNOWN;
    for (int i = 0; i < iterations; i++) {
        sink = aqpqc_select(&iot_ctx);
    }
    (void)sink;

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed_ns = (end.tv_sec - start.tv_sec) * 1e9 + (end.tv_nsec - start.tv_nsec);
    double avg_ns = elapsed_ns / iterations;

    printf("PASS: All C assertions succeeded.\n");
    printf("BENCHMARK: 1,000,000 selections executed in %.2f ms (Average: %.2f ns per decision).\n",
           elapsed_ns / 1e6, avg_ns);

    /* Must be well under 1000 ns (1 microsecond) */
    assert(avg_ns < 1000.0);
    return 0;
}
