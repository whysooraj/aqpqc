"""Hardware and network context telemetry collection."""

from dataclasses import asdict, dataclass
import os
import socket
import time
from typing import Any, Dict, List, Optional
import psutil

@dataclass
class TelemetrySnapshot:
    cpu_usage_pct: float
    mem_available_mb: float
    network_rtt_ms: float
    network_bandwidth_mbps: float
    packet_loss_pct: float
    mtu_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_vector(self) -> List[float]:
        return [
            float(self.cpu_usage_pct),
            float(self.mem_available_mb),
            float(self.network_rtt_ms),
            float(self.network_bandwidth_mbps),
            float(self.packet_loss_pct),
            float(self.mtu_bytes),
        ]


class TelemetryCollector:
    """Collects real-time hardware telemetry and network dynamics."""

    def __init__(self, default_host: str = "1.1.1.1", default_port: int = 53):
        self.default_host = default_host
        self.default_port = default_port

    def get_cpu_usage(self) -> float:
        """Measure current CPU utilization percentage."""
        return float(psutil.cpu_percent(interval=0.1))

    def get_available_memory_mb(self) -> float:
        """Measure available system memory in megabytes."""
        mem = psutil.virtual_memory()
        return round(mem.available / (1024.0 * 1024.0), 2)

    def measure_network_rtt_ms(self, host: Optional[str] = None, port: Optional[int] = None) -> float:
        """Measure TCP connect RTT in milliseconds to target gateway."""
        target_host = host or self.default_host
        target_port = port or self.default_port
        
        # ponytail: TCP handshake latency approximation avoids raw ICMP root privilege requirements
        try:
            start_time = time.perf_counter()
            with socket.create_connection((target_host, target_port), timeout=1.0):
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return round(elapsed, 2)
        except (socket.timeout, OSError):
            return 25.0  # safe default fallback if offline or unreachable

    def detect_mtu_bytes(self) -> int:
        """Detect local network interface MTU size via sysfs or default 1500."""
        sys_net = "/sys/class/net"
        if os.path.exists(sys_net):
            for iface in os.listdir(sys_net):
                if iface == "lo":
                    continue
                mtu_path = os.path.join(sys_net, iface, "mtu")
                if os.path.isfile(mtu_path):
                    try:
                        with open(mtu_path, "r", encoding="utf-8") as f:
                            mtu_val = int(f.read().strip())
                            if 576 <= mtu_val <= 9000:
                                return mtu_val
                    except Exception:
                        continue
        return 1500

    def collect(self, probe_network: bool = True) -> TelemetrySnapshot:
        """Produce a complete context snapshot of current operational conditions."""
        cpu = self.get_cpu_usage()
        mem = self.get_available_memory_mb()
        mtu = self.detect_mtu_bytes()

        if probe_network:
            rtt = self.measure_network_rtt_ms()
            # Approximation based on RTT profile: local LAN (<5ms) -> gigabit, WAN -> ~50Mbps
            bandwidth = 1000.0 if rtt < 5.0 else (100.0 if rtt < 30.0 else 25.0)
            packet_loss = 0.0
        else:
            rtt = 15.0
            bandwidth = 100.0
            packet_loss = 0.0

        return TelemetrySnapshot(
            cpu_usage_pct=cpu,
            mem_available_mb=mem,
            network_rtt_ms=rtt,
            network_bandwidth_mbps=bandwidth,
            packet_loss_pct=packet_loss,
            mtu_bytes=mtu,
        )
