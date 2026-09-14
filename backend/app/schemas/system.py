"""System and dashboard schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CPUStats(BaseModel):
    model_config = {"protected_namespaces": ()}
    usage_percent: float
    cores: int
    load_avg_1: float
    load_avg_5: float
    load_avg_15: float
    model_name: str = ""


class MemoryStats(BaseModel):
    total_mb: float
    used_mb: float
    free_mb: float
    usage_percent: float
    swap_total_mb: float
    swap_used_mb: float


class DiskStats(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    mount_point: str = "/"


class NetworkStats(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    bandwidth_in_mbps: float = 0
    bandwidth_out_mbps: float = 0


class ServiceStatus(BaseModel):
    name: str
    display_name: str
    active: bool
    enabled: bool
    status: str


class SystemInfo(BaseModel):
    hostname: str
    os_name: str
    os_version: str
    kernel: str
    arch: str
    uptime_seconds: int
    uptime_human: str
    panel_version: str


class DashboardStats(BaseModel):
    cpu: CPUStats
    memory: MemoryStats
    disk: DiskStats
    network: NetworkStats
    system_info: SystemInfo
    services: List[ServiceStatus]
    websites_count: int = 0
    databases_count: int = 0
    domains_count: int = 0
    users_count: int = 0


class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    category: str
    description: str
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
