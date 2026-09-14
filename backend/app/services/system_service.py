"""
System monitoring service.
Provides CPU, memory, disk, network stats and service management via psutil.
"""

import platform
import time
from datetime import datetime
from typing import List

import psutil

from app.config import settings
from app.schemas.system import (
    CPUStats, MemoryStats, DiskStats, NetworkStats,
    ServiceStatus, SystemInfo, DashboardStats,
)
from app.utils.command import run_command, check_service_status


# Track network I/O for bandwidth calculation
_last_net_io = None
_last_net_time = None


def get_cpu_stats() -> CPUStats:
    """Get current CPU statistics."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    
    try:
        load_avg = psutil.getloadavg()
    except (AttributeError, OSError):
        # Windows doesn't support getloadavg
        load_avg = (0, 0, 0)

    model_name = ""
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        model_name = info.get("brand_raw", "")
    except ImportError:
        model_name = platform.processor() or "Unknown"

    return CPUStats(
        usage_percent=cpu_percent,
        cores=cpu_count,
        load_avg_1=round(load_avg[0], 2),
        load_avg_5=round(load_avg[1], 2),
        load_avg_15=round(load_avg[2], 2),
        model_name=model_name,
    )


def get_memory_stats() -> MemoryStats:
    """Get current memory statistics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return MemoryStats(
        total_mb=round(mem.total / 1024 / 1024, 1),
        used_mb=round(mem.used / 1024 / 1024, 1),
        free_mb=round(mem.available / 1024 / 1024, 1),
        usage_percent=mem.percent,
        swap_total_mb=round(swap.total / 1024 / 1024, 1),
        swap_used_mb=round(swap.used / 1024 / 1024, 1),
    )


def get_disk_stats(path: str = "/") -> DiskStats:
    """Get disk usage for a given mount point."""
    try:
        disk = psutil.disk_usage(path)
    except (FileNotFoundError, OSError, Exception):
        try:
            disk = psutil.disk_usage("C:\\")
        except Exception:
            disk = psutil.disk_usage(".")

    return DiskStats(
        total_gb=round(disk.total / 1024 / 1024 / 1024, 1),
        used_gb=round(disk.used / 1024 / 1024 / 1024, 1),
        free_gb=round(disk.free / 1024 / 1024 / 1024, 1),
        usage_percent=disk.percent,
        mount_point=path,
    )


def get_network_stats() -> NetworkStats:
    """Get network I/O statistics with bandwidth calculation."""
    global _last_net_io, _last_net_time

    net_io = psutil.net_io_counters()
    current_time = time.time()

    bandwidth_in = 0.0
    bandwidth_out = 0.0

    if _last_net_io and _last_net_time:
        elapsed = current_time - _last_net_time
        if elapsed > 0:
            bandwidth_in = ((net_io.bytes_recv - _last_net_io.bytes_recv) / elapsed) / 125000  # Mbps
            bandwidth_out = ((net_io.bytes_sent - _last_net_io.bytes_sent) / elapsed) / 125000

    _last_net_io = net_io
    _last_net_time = current_time

    return NetworkStats(
        bytes_sent=net_io.bytes_sent,
        bytes_recv=net_io.bytes_recv,
        packets_sent=net_io.packets_sent,
        packets_recv=net_io.packets_recv,
        bandwidth_in_mbps=round(bandwidth_in, 2),
        bandwidth_out_mbps=round(bandwidth_out, 2),
    )


def get_system_info() -> SystemInfo:
    """Get general system information."""
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)

    # Human-readable uptime
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime_human = f"{days}d {hours}h {minutes}m"

    return SystemInfo(
        hostname=platform.node(),
        os_name=platform.system(),
        os_version=platform.version(),
        kernel=platform.release(),
        arch=platform.machine(),
        uptime_seconds=uptime_seconds,
        uptime_human=uptime_human,
        panel_version=settings.PANEL_VERSION,
    )


async def get_services_status() -> List[ServiceStatus]:
    """Check status of key managed services."""
    services_to_check = [
        ("nginx", "Nginx Web Server"),
        ("mysql", "MySQL Database"),
        ("mariadb", "MariaDB Database"),
        ("php8.2-fpm", "PHP 8.2 FPM"),
        ("php8.1-fpm", "PHP 8.1 FPM"),
        ("ufw", "UFW Firewall"),
        ("docker", "Docker Engine"),
        ("cron", "Cron Scheduler"),
        ("ssh", "SSH Server"),
        ("postfix", "Postfix Mail"),
    ]

    statuses = []
    for service_name, display_name in services_to_check:
        try:
            status = await check_service_status(service_name)
            statuses.append(ServiceStatus(
                name=service_name,
                display_name=display_name,
                active=status["active"],
                enabled=status["enabled"],
                status=status["status"],
            ))
        except Exception:
            statuses.append(ServiceStatus(
                name=service_name,
                display_name=display_name,
                active=False,
                enabled=False,
                status="not-found",
            ))

    return statuses


def get_process_list() -> list:
    """Get list of running processes."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "user": info['username'] or "system",
                "cpu": round(info['cpu_percent'] or 0, 1),
                "memory": round(info['memory_percent'] or 0, 1),
                "status": info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU usage descending
    processes.sort(key=lambda x: x['cpu'], reverse=True)
    return processes[:50]  # Top 50
