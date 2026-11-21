# tests/test_passive_telemetry.py
import socket
import pytest
from aqpqc.passive_telemetry import extract_kernel_tcp_telemetry, PassiveTelemetrySnapshot

def test_extract_kernel_tcp_telemetry():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    conn, _ = server.accept()

    try:
        snap = extract_kernel_tcp_telemetry(conn)
        assert isinstance(snap, PassiveTelemetrySnapshot)
        assert snap.rtt_us >= 0
        assert snap.rtt_ms >= 0.0
        assert snap.mss_bytes > 0
        assert snap.effective_mtu >= 576
        assert snap.retransmits == 0
        assert 0.0 <= snap.packet_loss_est <= 1.0

        ctx = snap.to_telemetry_snapshot()
        assert ctx.mtu_bytes >= 576
        assert ctx.network_rtt_ms >= 0.0
    finally:
        server.close()
        client.close()
        conn.close()
