# tests/test_demo.py
import socket
import threading
import time
import pytest

from aqpqc.telemetry import TelemetrySnapshot
from demo.protocol import DynamicPQCHandshake
from demo.server import PQCHandshakeServer
from demo.client import PQCHandshakeClient

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def test_dynamic_handshake_end_to_end():
    port = get_free_port()
    server = PQCHandshakeServer(host="127.0.0.1", port=port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.1)

    # Client with IoT constraint (should negotiate ML-KEM-512)
    iot_context = TelemetrySnapshot(
        cpu_usage_pct=80.0,
        mem_available_mb=32.0,
        network_rtt_ms=120.0,
        network_bandwidth_mbps=0.5,
        packet_loss_pct=5.0,
        mtu_bytes=576
    )

    client = PQCHandshakeClient(host="127.0.0.1", port=port)
    result = client.run_handshake(context=iot_context, min_security=1)

    assert result["success"] is True
    assert result["algorithm"] == "ML-KEM-512"
    assert len(result["session_key_hex"]) == 64  # SHA-256 derived key (32 bytes = 64 hex chars)
    assert result["echo_response"] == "PQC_HANDSHAKE_ACK"

    server.shutdown()
