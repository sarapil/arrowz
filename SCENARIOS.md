# Arrowz — Scenarios & Impact Matrix

> **أروز** — إدارة الاتصالات والشبكات
> DocTypes: ~80 | APIs: ~227 | Modules: 11

## 📊 Module Map

| Module | DocTypes | APIs | Pages | Reports |
|--------|----------|------|-------|---------|
| VoIP | — | — | — | — |
| Network | — | — | — | — |
| WiFi | — | — | — | — |
| Security | — | — | — | — |
| Bandwidth | — | — | — | — |
| VPN | — | — | — | — |
| Omni Channel | — | — | — | — |
| Meetings | — | — | — | — |
| Monitoring | — | — | — | — |
| PBX | — | — | — | — |
| Setup | — | — | — | — |

## 🔄 Core Workflows

### 1. Setup & Configuration
1. Install Arrowz app
2. Configure Settings singleton
3. Assign roles to users
4. Seed reference data

### 2. Daily Operations
- Create / Read / Update / Delete core records
- Submit workflows
- Generate reports

### 3. Reporting & Analytics
- Dashboard overview
- Period reports
- Export data

## 🛡️ Impact Matrix

| Action | Affected DocTypes | Side Effects | Rollback |
|--------|-------------------|-------------|----------|
| Install | All | Creates Module Defs, Roles | Uninstall |
| Migrate | All | Schema changes | bench migrate --rollback |
| Seed | Settings, Lookups | Reference data | Manual delete |

## 📋 API Inventory

> Total `@frappe.whitelist()` endpoints: ~227
> Permission coverage: TBD

| Module | Endpoint | Method | Auth | Rate Limit |
|--------|----------|--------|------|------------|
| — | TBD | — | — | — |

## 🧪 Test Coverage

| Category | Count | Status |
|----------|-------|--------|
| Unit tests | — | ❌ |
| Integration tests | — | ❌ |
| Permission tests | — | ❌ |
| UI contract tests | — | ❌ |

---

*Auto-generated on 2026-04-02 — update as features are added.*
