# Arrowz Docker Infrastructure
## Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VPS Host (157.173.125.136)                    │
│                                                                  │
│  ┌──────────────────── arrowz_shared_net ──────────────────────┐ │
│  │                    172.30.0.0/16                             │ │
│  │                                                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │ │
│  │  │  frappe-dev  │  │  FreePBX    │  │  OpenMeetings    │    │ │
│  │  │  172.30.x.x │  │  172.30.x.x │  │  172.30.x.x      │    │ │
│  │  │             │  │             │  │                   │    │ │
│  │  │  Frappe     │  │  Asterisk   │  │  Video Conf      │    │ │
│  │  │  ERPNext    │  │  SIP/WebRTC │  │  Kurento (KMS)   │    │ │
│  │  │  Arrowz     │  │  AMI        │  │  Recording       │    │ │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘    │ │
│  │         │                │                   │              │ │
│  │  Can reach each other directly by name/IP:                  │ │
│  │  frappe→freepbx:8088   freepbx→frappe:8000                  │ │
│  │  frappe→openmeetings:5443   etc.                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│            │                │                   │                 │
│  ┌─────────┘    ┌──────────┘        ┌──────────┘                │
│  │ also on:     │ also on:          │ also on:                  │
│  │ default net  │ initpbx_default   │ om_default                │
│  │ (mariadb,    │ (its own stack)   │ (om-db, kms)              │
│  │  redis)      │                   │                           │
│  └──────────────┴───────────────────┘                           │
│                                                                  │
│  Nginx (:443) ── SSL termination ── proxy to containers         │
│    /ws → freepbx:8089 (WSS)                                     │
│    /openmeetings → openmeetings:5443                            │
└──────────────────────────────────────────────────────────────────┘
```

## Files

| File | Run Where | Purpose |
|------|-----------|---------|
| `arrowz_infra_setup.sh` | VPS Host | **Master script** — orchestrates everything |
| `setup_shared_network.sh` | VPS Host | Creates arrowz_shared_net + connects containers |
| `fix_pjsip_local_net.sh` | VPS Host | Fixes Asterisk PJSIP local_net for Docker |
| `freepbx/docker-compose.shared-net.yml` | VPS Host | Overlay to add FreePBX to shared network |
| `openmeetings/docker-compose.yml` | VPS Host | Full OpenMeetings + Kurento + MySQL stack |
| `openmeetings/nginx-openmeetings.conf` | VPS Host | Nginx reverse proxy config for OM |

## Quick Start

```bash
# On VPS host:
cd /path/to/docker/

# Full setup (create network + connect + fix PJSIP)
sudo ./arrowz_infra_setup.sh setup

# Check status
sudo ./arrowz_infra_setup.sh status

# Start OpenMeetings
sudo ./arrowz_infra_setup.sh om-up
```

## Adding a New Container

1. Add to its docker-compose:
```yaml
networks:
  arrowz_shared:
    external: true
    name: arrowz_shared_net
services:
  myservice:
    networks:
      - default
      - arrowz_shared
```

2. Or connect manually:
```bash
docker network connect --alias myservice arrowz_shared_net <container>
```

## Why Shared Network?

Before: Each docker-compose stack creates its own isolated bridge network.
Containers can only communicate via Docker host port mapping (slow, needs published ports).

After: All Arrowz services share `arrowz_shared_net` and can communicate directly
by container name (DNS), without needing ports published on the host.

| Feature | Before (separate nets) | After (shared net) |
|---------|----------------------|-------------------|
| Container-to-container | Via host port-mapping | Direct |
| DNS resolution | ❌ | ✅ by alias |
| Speed | Extra NAT hop | Direct bridge |
| Port publishing | Required for each service | Only for external access |
| Adding services | Complex port mapping | Just connect to network |
