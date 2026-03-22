"""
Arrowz Engine - Pydantic Models

Defines the data contracts between the Frappe Interface Layer and
the Arrowz Engine.  All configuration payloads, request bodies,
and response schemas live here.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class ClientActionType(str, Enum):
    """Supported actions for client management."""
    BLOCK = "block"
    UNBLOCK = "unblock"
    DISCONNECT = "disconnect"


class ServiceActionType(str, Enum):
    """Supported actions for service management."""
    RESTART = "restart"
    START = "start"
    STOP = "stop"
    RELOAD = "reload"


# ============================================================================
# Sub-Configuration Models
# ============================================================================

class NetworkConfig(BaseModel):
    """Network interface and routing configuration."""
    wan_interface: Optional[str] = Field(None, description="WAN interface name (e.g. eth0)")
    wan_type: Optional[str] = Field("dhcp", description="WAN type: dhcp | static | pppoe")
    wan_ip: Optional[str] = None
    wan_netmask: Optional[str] = None
    wan_gateway: Optional[str] = None
    lan_interface: Optional[str] = Field(None, description="LAN interface name (e.g. br-lan)")
    lan_ip: Optional[str] = None
    lan_netmask: Optional[str] = Field("255.255.255.0")
    dhcp_enabled: bool = True
    dhcp_start: Optional[str] = None
    dhcp_end: Optional[str] = None
    dhcp_lease_time: str = "12h"
    dns_servers: List[str] = Field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])
    static_routes: List[Dict[str, str]] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class FirewallRule(BaseModel):
    """Single firewall rule definition."""
    name: Optional[str] = None
    chain: str = "input"
    protocol: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    port: Optional[int] = None
    action: str = "accept"
    comment: Optional[str] = None


class FirewallConfig(BaseModel):
    """Firewall (nftables) configuration."""
    default_input_policy: str = Field("drop", description="Default input chain policy")
    default_forward_policy: str = Field("drop", description="Default forward chain policy")
    default_output_policy: str = Field("accept", description="Default output chain policy")
    nat_enabled: bool = True
    wan_interface: Optional[str] = None
    rules: List[FirewallRule] = Field(default_factory=list)
    port_forwards: List[Dict[str, Any]] = Field(default_factory=list)
    blocked_macs: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class WiFiConfig(BaseModel):
    """WiFi / hostapd configuration."""
    enabled: bool = True
    interface: Optional[str] = Field(None, description="WiFi interface (e.g. wlan0)")
    ssid: str = "Arrowz"
    passphrase: Optional[str] = None
    channel: int = 6
    band: str = Field("2g", description="Band: 2g | 5g | 6g")
    hw_mode: str = "g"
    ieee80211n: bool = True
    ieee80211ac: bool = False
    ieee80211ax: bool = False
    hidden: bool = False
    max_clients: int = 64
    country_code: str = "US"
    hotspot_enabled: bool = False
    hotspot_auth_server: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class BandwidthProfile(BaseModel):
    """Single bandwidth shaping profile."""
    name: str
    download_kbps: int
    upload_kbps: int
    burst_kbps: Optional[int] = None
    priority: int = Field(4, ge=1, le=7)


class BandwidthConfig(BaseModel):
    """Bandwidth / traffic shaping configuration (tc HTB + SFQ)."""
    enabled: bool = True
    wan_interface: Optional[str] = None
    lan_interface: Optional[str] = None
    total_download_kbps: int = 100000
    total_upload_kbps: int = 50000
    default_profile: str = "standard"
    profiles: List[BandwidthProfile] = Field(default_factory=list)
    per_client_rules: List[Dict[str, Any]] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ClientReservation(BaseModel):
    """DHCP static lease / client reservation."""
    mac_address: str
    ip_address: str
    hostname: Optional[str] = None
    comment: Optional[str] = None


class ClientConfig(BaseModel):
    """Client management configuration."""
    reservations: List[ClientReservation] = Field(default_factory=list)
    blocked_macs: List[str] = Field(default_factory=list)
    bandwidth_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="MAC -> bandwidth profile name mapping",
    )
    extra: Dict[str, Any] = Field(default_factory=dict)


class VPNPeer(BaseModel):
    """WireGuard peer definition."""
    public_key: str
    allowed_ips: List[str]
    endpoint: Optional[str] = None
    persistent_keepalive: int = 25
    preshared_key: Optional[str] = None
    comment: Optional[str] = None


class VPNConfig(BaseModel):
    """VPN (WireGuard) configuration."""
    enabled: bool = False
    interface: str = "wg0"
    listen_port: int = 51820
    private_key: Optional[str] = None
    address: Optional[str] = None
    dns: List[str] = Field(default_factory=list)
    peers: List[VPNPeer] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class DNSOverride(BaseModel):
    """Custom DNS record override."""
    domain: str
    address: str
    comment: Optional[str] = None


class DNSConfig(BaseModel):
    """DNS (dnsmasq) configuration."""
    upstream_servers: List[str] = Field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])
    local_domain: str = "lan"
    cache_size: int = 1000
    dnssec: bool = False
    overrides: List[DNSOverride] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Full Configuration Payload
# ============================================================================

class ConfigPayload(BaseModel):
    """Complete configuration pushed from the Frappe Interface Layer."""
    version: str = Field("1.0", description="Config schema version")
    timestamp: Optional[datetime] = None
    site: Optional[str] = Field(None, description="Frappe site name for reference")
    box_id: Optional[str] = Field(None, description="Unique identifier for this box")
    network: Optional[NetworkConfig] = None
    firewall: Optional[FirewallConfig] = None
    wifi: Optional[WiFiConfig] = None
    bandwidth: Optional[BandwidthConfig] = None
    clients: Optional[ClientConfig] = None
    vpn: Optional[VPNConfig] = None
    dns: Optional[DNSConfig] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Request Models
# ============================================================================

class ClientAction(BaseModel):
    """Request body for client management actions."""
    mac_address: str = Field(..., description="Client MAC address (e.g. AA:BB:CC:DD:EE:FF)")
    action: ClientActionType
    reason: Optional[str] = None


class ServiceAction(BaseModel):
    """Request body for service management actions."""
    service_name: str
    action: ServiceActionType


class HotspotAuthRequest(BaseModel):
    """Request to authorize / deauthorize a hotspot client."""
    mac_address: str
    duration_minutes: Optional[int] = Field(None, description="Session duration in minutes")
    bandwidth_profile: Optional[str] = None


# ============================================================================
# Response Models
# ============================================================================

class StatusResponse(BaseModel):
    """Generic status response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Engine health response."""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    hostname: Optional[str] = None
    box_id: Optional[str] = None
    services: Dict[str, str] = Field(default_factory=dict)


class InterfaceStat(BaseModel):
    """Network interface statistics."""
    name: str
    status: str
    mac_address: Optional[str] = None
    ipv4: Optional[str] = None
    rx_bytes: int = 0
    tx_bytes: int = 0


class TelemetryResponse(BaseModel):
    """System telemetry snapshot."""
    timestamp: datetime
    hostname: Optional[str] = None
    uptime_seconds: float = 0.0
    cpu_percent: float = 0.0
    cpu_count: int = 1
    memory_total_mb: float = 0.0
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    load_avg: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    interfaces: List[InterfaceStat] = Field(default_factory=list)
    temperature_celsius: Optional[float] = None
