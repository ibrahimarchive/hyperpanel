"""
Process manager service.
Lists and manages running processes via psutil.
"""

import logging
import os
import signal
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


class ProcessService:
    """Manages system processes."""

    def get_process_list(
        self,
        sort_by: str = "cpu",
        limit: int = 50,
        search: Optional[str] = None,
    ) -> list[dict]:
        """Get a list of running processes sorted by CPU or memory."""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'cmdline']):
            try:
                info = proc.info
                name = info.get('name', '')
                cmdline = info.get('cmdline', [])
                cmd_str = ' '.join(cmdline) if cmdline else name

                if search and search.lower() not in name.lower() and search.lower() not in cmd_str.lower():
                    continue

                processes.append({
                    "pid": info['pid'],
                    "name": name,
                    "username": info.get('username', ''),
                    "cpu_percent": round(info.get('cpu_percent', 0.0), 1),
                    "memory_percent": round(info.get('memory_percent', 0.0), 1),
                    "memory_rss": info.get('memory_info', None).rss if info.get('memory_info') else 0,
                    "status": info.get('status', 'unknown'),
                    "command": cmd_str[:200],
                    "create_time": info.get('create_time', 0),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort
        if sort_by == "memory":
            processes.sort(key=lambda p: p['memory_percent'], reverse=True)
        else:
            processes.sort(key=lambda p: p['cpu_percent'], reverse=True)

        return processes[:limit]

    def get_summary(self) -> dict:
        """Get a summary of system processes."""
        total = 0
        running = 0
        sleeping = 0
        zombie = 0

        for proc in psutil.process_iter(['status']):
            try:
                total += 1
                status = proc.info.get('status', '')
                if status == psutil.STATUS_RUNNING:
                    running += 1
                elif status == psutil.STATUS_SLEEPING:
                    sleeping += 1
                elif status == psutil.STATUS_ZOMBIE:
                    zombie += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

        return {
            "total": total,
            "running": running,
            "sleeping": sleeping,
            "zombie": zombie,
            "load_avg_1": round(load_avg[0], 2),
            "load_avg_5": round(load_avg[1], 2),
            "load_avg_15": round(load_avg[2], 2),
        }

    def kill_process(self, pid: int, sig: int = signal.SIGTERM) -> dict:
        """Kill a process by PID."""
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()

            # Safety: don't kill PID 1 or the panel itself
            if pid == 1:
                return {"success": False, "error": "Cannot kill init process"}
            if pid == os.getpid():
                return {"success": False, "error": "Cannot kill the panel process"}

            proc.send_signal(sig)
            logger.info(f"Sent signal {sig} to process {pid} ({proc_name})")

            return {"success": True, "process": proc_name}

        except psutil.NoSuchProcess:
            return {"success": False, "error": f"Process {pid} not found"}
        except psutil.AccessDenied:
            return {"success": False, "error": f"Permission denied to kill process {pid}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
process_service = ProcessService()
