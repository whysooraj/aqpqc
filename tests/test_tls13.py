# tests/test_tls13.py
import socket
import pytest
from aqpqc.tls13 import (
    TLS13_GROUPS,
    negotiate_tls13_group,
    select_tls13_group_from_telemetry,
    GROUP_MLKEM512,
    GROUP_MLKEM768,
    GROUP_MLKEM1024,
    GROUP_X25519_MLKEM768,
)
from aqpqc.telemetry import TelemetrySnapshot

def test_tls13_groups_constants():
    assert GROUP_MLKEM512 == 0x11ec
    assert GROUP_MLKEM768 == 0x11ed
    assert GROUP_MLKEM1024 == 0x11ee
    assert GROUP_X25519_MLKEM768 == 0x2f39
    assert 0x11ec in TLS13_GROUPS

def test_select_tls13_group_iot():
    iot = TelemetrySnapshot(
        cpu_usage_pct=80.0,
        mem_available_mb=32.0,
        network_rtt_ms=100.0,
        network_bandwidth_mbps=1.0,
        packet_loss_pct=5.0,
        mtu_bytes=576
    )
    res = select_tls13_group_from_telemetry(iot, min_security=1)
    assert res["group_id"] == GROUP_MLKEM512
    assert res["group_name"] == "MLKEM512"

def test_select_tls13_group_cloud():
    cloud = TelemetrySnapshot(
        cpu_usage_pct=10.0,
        mem_available_mb=16384.0,
        network_rtt_ms=1.0,
        network_bandwidth_mbps=1000.0,
        packet_loss_pct=0.0,
        mtu_bytes=9000
    )
    res = select_tls13_group_from_telemetry(cloud, min_security=5)
    assert res["group_id"] == GROUP_MLKEM1024
    assert res["group_name"] == "MLKEM1024"

def test_negotiate_tls13_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    conn, _ = server.accept()

    try:
        res = negotiate_tls13_group(conn, min_security=1)
        assert res["group_id"] in TLS13_GROUPS
        assert "tcpi_rtt_us" in res
    finally:
        server.close()
        client.close()
        conn.close()
