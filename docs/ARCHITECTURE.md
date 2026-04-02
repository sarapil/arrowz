# Arrowz — Architecture Guide

## System Overview
Arrowz is built on the Frappe Framework as a modular voip & network management solution.

## Architecture Layers
```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  (Frappe UI + frappe_visual components) │
├─────────────────────────────────────────┤
│            Business Logic               │
│     (Controllers + Services Layer)      │
├─────────────────────────────────────────┤
│            Data Access Layer            │
│      (Frappe ORM + DocType models)      │
├─────────────────────────────────────────┤
│          Integration Layer              │
│    (APIs + External System Connectors)  │
├─────────────────────────────────────────┤
│           Infrastructure                │
│  (MariaDB + Redis + Background Workers) │
└─────────────────────────────────────────┘
```

## Module Structure
- **Core Module**: Primary business logic and DocTypes
- **API Layer**: `api/v1/` versioned endpoints with `api/response.py` helpers
- **Services**: `services/` layer for business logic separation
- **CAPS Integration**: `caps_integration/gate.py` for permission enforcement
- **Utils**: `utils/validators.py`, `formatters.py`, `constants.py`

## Key Design Decisions
1. **Service Layer Pattern** — Business logic in services, not controllers
2. **CAPS-first Security** — All access goes through capability gates
3. **API Response Standardization** — `success()`, `error()`, `paginated()` helpers
4. **Arabic-first i18n** — All strings wrapped in `_()` / `__()`

## Data Flow
1. Client → Frappe Router → Controller
2. Controller → Service Layer → Data Access
3. Data Access → MariaDB (via Frappe ORM)
4. Background tasks → Redis Queue → Worker

## هيكل النظام (عربي)
Arrowz مبني على إطار عمل فريب كحل VoIP & Network Management متكامل.
