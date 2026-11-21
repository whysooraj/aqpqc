"""Zero-overhead passive telemetry extraction from Linux kernel socket TCP_INFO."""

from dataclasses import dataclass
import socket
import struct
from typing import Optional
import psutil

from aqpqc.telemetry import TelemetrySnapshot

TCP_INFO_OPT = getattr(socket, "TCP_INFO", 11)

@dataclass
class PassiveTelemetrySnapshot:
    rtt_us: int
    rttvar_us: int
    mss_bytes: int
    effective_mtu: int
    retransmits: int
    packet_loss_est: float
    cpu_usage_pct: float
    mem_available_mb: float

    @property
    def rtt_ms(self) -> float:
        return round(self.rtt_us / 1000.0, 3)

    def to_telemetry_snapshot(self) -> TelemetrySnapshot:
        """Convert passive kernel telemetry into standard TelemetrySnapshot."""
        # Estimate bandwidth from TCP MSS and RTT
        rtt_s = max(self.rtt_us / 1e6, 0.0001)
        est_bw_mbps = (self.mss_bytes * 8.0 / rtt_s) / 1e6

        return TelemetrySnapshot(
            cpu_usage_pct=self.cpu_usage_pct,
            mem_available_mb=self.mem_available_mb,
            network_rtt_ms=max(self.rtt_ms, 0.1),
            network_bandwidth_mbps=round(max(est_bw_mbps, 1.0), 2),
            packet_loss_pct=round(self.packet_loss_est * 100.0, 2),
            mtu_bytes=self.effective_mtu,
        )


def extract_kernel_tcp_telemetry(sock: socket.socket) -> PassiveTelemetrySnapshot:
    """Extract live socket metrics directly from Linux kernel via TCP_INFO."""
    try:
        raw_info = sock.getsockopt(socket.IPPROTO_TCP, TCP_INFO_OPT, 256)
        if len(raw_info) >= 104:
            # Unpack standard struct tcp_info (first 104 bytes)
            # tcpi_state, tcpi_ca_state, tcpi_retransmits, tcpi_probes, tcpi_backoff, tcpi_options,
            # tcpi_snd_wscale:4, tcpi_rcv_wscale:4, tcpi_delivery_rate_app_limited:1
            # tcpi_rto, tcpi_ato, tcpi_snd_mss, tcpi_rcv_mss, tcpi_unacked, tcpi_sacked, tcpi_lost,
            # tcpi_retrans, tcpi_fackets, tcpi_last_data_sent, tcpi_last_ack_sent, tcpi_last_data_recv,
            # tcpi_last_ack_recv, tcpi_pmtu, tcpi_rcv_ssthresh, tcpi_rtt, tcpi_rttvar...
            fmt = "BBBBBBBBIIIIIIIIIIIIIIIII"
            unpacked = struct.unpack_from(fmt, raw_info)
            retrans = unpacked[2]
            snd_mss = unpacked[10]
            pmtu = unpacked[21]
            rtt_us = unpacked[23]
            rttvar_us = unpacked[24]

            effective_mtu = pmtu if (576 <= pmtu <= 9000) else (snd_mss + 40 if snd_mss > 0 else 1500)
            loss_est = min(float(retrans) / 10.0, 1.0)
        else:
            rtt_us = 1000
            rttvar_us = 100
            snd_mss = 1460
            effective_mtu = 1500
            retrans = 0
            loss_est = 0.0
    except OSError:
        rtt_us = 1000
        rttvar_us = 100
        snd_mss = 1460
        effective_mtu = 1500
        retrans = 0
        loss_est = 0.0

    # Read lightweight host resources
    cpu = float(psutil.cpu_percent(interval=None))
    mem_mb = round(psutil.virtual_memory().available / (1024.0 * 1024.0), 2)

    return PassiveTelemetrySnapshot(
        rtt_us=rtt_us,
        rttvar_us=rttvar_us,
        mss_bytes=snd_mss,
        effective_mtu=effective_mtu,
        retransmits=retrans,
        packet_loss_est=loss_est,
        cpu_usage_pct=cpu,
        mem_available_mb=mem_mb,
    )
