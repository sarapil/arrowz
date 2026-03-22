"""
Arrowz Engine - Telemetry Collector

Collects system telemetry data (CPU, RAM, disk, network, temperature)
using standard Linux tools and /proc / /sys filesystem reads.
"""

import logging
import os
import re
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from arrowz_engine.models import InterfaceStat, TelemetryResponse
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.collectors.telemetry")


class TelemetryCollector:
    """
    Collects system telemetry using standard Linux interfaces.

    Avoids external dependencies (like psutil) by reading directly
    from /proc, /sys, and calling standard CLI tools.
    """

    async def collect(self) -> TelemetryResponse:
        """
        Gather a full telemetry snapshot.

        Collects CPU, memory, disk, uptime, load average, network
        interface statistics, and CPU temperature.

        Returns:
            TelemetryResponse with current system metrics.
        """
        return TelemetryResponse(
            timestamp=datetime.now(timezone.utc),
            hostname=socket.gethostname(),
            uptime_seconds=self._get_uptime(),
            cpu_percent=self._get_cpu_percent(),
            cpu_count=os.cpu_count() or 1,
            memory_total_mb=self._get_memory_info("MemTotal"),
            memory_used_mb=self._get_memory_used(),
            memory_percent=self._get_memory_percent(),
            disk_total_gb=self._get_disk_total(),
            disk_used_gb=self._get_disk_used(),
            disk_percent=self._get_disk_percent(),
            load_avg=list(os.getloadavg()),
            interfaces=self._get_interface_stats(),
            temperature_celsius=self._get_cpu_temperature(),
        )

    # ------------------------------------------------------------------
    # Uptime
    # ------------------------------------------------------------------

    def _get_uptime(self) -> float:
        """Read system uptime from /proc/uptime."""
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.read().split()[0])
        except Exception as exc:
            logger.debug("Failed to read uptime: %s", exc)
            return 0.0

    # ------------------------------------------------------------------
    # CPU
    # ------------------------------------------------------------------

    def _get_cpu_percent(self) -> float:
        """
        Estimate CPU usage from /proc/stat.

        Reads two snapshots 0.1s apart and calculates the delta.
        For a lightweight approach, falls back to load average.
        """
        try:
            def read_cpu_times() -> List[int]:
                with open("/proc/stat", "r") as f:
                    line = f.readline()  # First line: cpu  user nice system idle ...
                return [int(x) for x in line.split()[1:]]

            t1 = read_cpu_times()
            time.sleep(0.1)
            t2 = read_cpu_times()

            # Delta
            delta = [t2[i] - t1[i] for i in range(len(t1))]
            total = sum(delta)
            idle = delta[3] if len(delta) > 3 else 0

            if total == 0:
                return 0.0

            return round(((total - idle) / total) * 100, 1)
        except Exception as exc:
            logger.debug("Failed to read CPU percent: %s", exc)
            # Fallback: use 1-min load average as rough estimate
            try:
                load = os.getloadavg()[0]
                cpus = os.cpu_count() or 1
                return round(min((load / cpus) * 100, 100.0), 1)
            except Exception:
                return 0.0

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def _get_memory_info(self, key: str) -> float:
        """Read a value from /proc/meminfo in MB."""
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith(key + ":"):
                        # Value is in kB
                        kb = int(line.split()[1])
                        return round(kb / 1024, 1)
        except Exception as exc:
            logger.debug("Failed to read %s from meminfo: %s", key, exc)
        return 0.0

    def _get_memory_used(self) -> float:
        """Calculate used memory (Total - Available) in MB."""
        total = self._get_memory_info("MemTotal")
        available = self._get_memory_info("MemAvailable")
        return round(total - available, 1)

    def _get_memory_percent(self) -> float:
        """Calculate memory usage percentage."""
        total = self._get_memory_info("MemTotal")
        if total <= 0:
            return 0.0
        used = self._get_memory_used()
        return round((used / total) * 100, 1)

    # ------------------------------------------------------------------
    # Disk
    # ------------------------------------------------------------------

    def _get_disk_info(self) -> Dict[str, float]:
        """Get disk usage for the root filesystem."""
        try:
            stat = os.statvfs("/")
            total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            used_gb = total_gb - free_gb
            percent = (used_gb / total_gb * 100) if total_gb > 0 else 0.0
            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": round(percent, 1),
            }
        except Exception as exc:
            logger.debug("Failed to get disk info: %s", exc)
            return {"total_gb": 0.0, "used_gb": 0.0, "free_gb": 0.0, "percent": 0.0}

    def _get_disk_total(self) -> float:
        return self._get_disk_info()["total_gb"]

    def _get_disk_used(self) -> float:
        return self._get_disk_info()["used_gb"]

    def _get_disk_percent(self) -> float:
        return self._get_disk_info()["percent"]

    # ------------------------------------------------------------------
    # Network Interfaces
    # ------------------------------------------------------------------

    def _get_interface_stats(self) -> List[InterfaceStat]:
        """
        Read network interface statistics from /sys/class/net/.

        Returns:
            List of InterfaceStat with name, status, MAC, and counters.
        """
        interfaces = []
        net_dir = "/sys/class/net"

        try:
            for iface_name in os.listdir(net_dir):
                iface_path = os.path.join(net_dir, iface_name)
                if not os.path.isdir(iface_path):
                    continue

                # Skip loopback
                if iface_name == "lo":
                    continue

                stat = InterfaceStat(name=iface_name, status="unknown")

                # Operational state
                try:
                    with open(os.path.join(iface_path, "operstate"), "r") as f:
                        stat.status = f.read().strip()
                except Exception:
                    pass

                # MAC address
                try:
                    with open(os.path.join(iface_path, "address"), "r") as f:
                        stat.mac_address = f.read().strip()
                except Exception:
                    pass

                # RX/TX bytes
                try:
                    with open(
                        os.path.join(iface_path, "statistics", "rx_bytes"), "r"
                    ) as f:
                        stat.rx_bytes = int(f.read().strip())
                except Exception:
                    pass

                try:
                    with open(
                        os.path.join(iface_path, "statistics", "tx_bytes"), "r"
                    ) as f:
                        stat.tx_bytes = int(f.read().strip())
                except Exception:
                    pass

                # IPv4 address via ip command
                try:
                    stdout, _, rc = run_command(
                        f"ip -4 addr show {iface_name} | grep -oP 'inet \\K[\\d.]+'",
                        timeout=5,
                    )
                    if rc == 0 and stdout.strip():
                        stat.ipv4 = stdout.strip().splitlines()[0]
                except Exception:
                    pass

                interfaces.append(stat)

        except Exception as exc:
            logger.error("Failed to read interface stats: %s", exc)

        return interfaces

    # ------------------------------------------------------------------
    # Temperature
    # ------------------------------------------------------------------

    def _get_cpu_temperature(self) -> Optional[float]:
        """
        Read CPU temperature from thermal zone.

        Checks /sys/class/thermal/thermal_zone0/temp (millidegrees C).
        """
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                millideg = int(f.read().strip())
                return round(millideg / 1000.0, 1)
        except FileNotFoundError:
            return None  # No thermal zone (VM / container)
        except Exception as exc:
            logger.debug("Failed to read CPU temperature: %s", exc)
            return None
