# Arrowz v16 Migration Guide

> **Last Updated:** February 17, 2026  
> **Arrowz Version:** 16.0.0  
> **Compatible With:** Frappe v16+ / ERPNext v16+

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Breaking Changes](#3-breaking-changes)
4. [Migration Steps](#4-migration-steps)
5. [API Changes](#5-api-changes)
6. [Database Query Changes](#6-database-query-changes)
7. [JavaScript Changes](#7-javascript-changes)
8. [Permission System Changes](#8-permission-system-changes)
9. [Rollback Procedure](#9-rollback-procedure)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

Arrowz v16.0.0 is a major release designed for full compatibility with **Frappe/ERPNext v16**. This guide covers all breaking changes and migration steps for developers and server administrators.

### Version Compatibility Matrix

| Arrowz Version | Frappe Version | ERPNext Version | Python | Node.js |
|----------------|----------------|-----------------|--------|---------|
| 15.x.x | v15.x | v15.x | 3.10-3.11 | 18+ |
| **16.0.0** | **v16.x** | **v16.x** | **3.11-3.13** | **20+** |

---

## 2. Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.11 | 3.12+ |
| **Node.js** | 20 | 22 LTS |
| **MariaDB** | 10.6 | 11.x |
| **Redis** | 6.0 | 7.x |
| **Disk Space** | 2 GB | 5 GB+ |

### Pre-Migration Checklist

- [ ] Backup database: `bench --site your-site backup`
- [ ] Backup files: `bench --site your-site backup --with-files`
- [ ] Test backup restoration on a staging server
- [ ] Document all custom Arrowz configurations
- [ ] Export customized Workspaces (Copy to Clipboard in UI)
- [ ] Update Frappe to v16 first
- [ ] Update ERPNext to v16 (if installed)

---

## 3. Breaking Changes

### 3.1 Python Version

```diff
- requires-python = ">=3.10"
+ requires-python = ">=3.11"
```

**Action Required:** Upgrade Python to 3.11+ before migration.

### 3.2 frappe.db.commit() in Document Hooks

**v15 (Allowed):**
```python
def on_update(doc, method):
    # Do something
    frappe.db.commit()  # Was allowed
```

**v16 (Error):**
```python
def on_update(doc, method):
    # frappe.db.commit() raises error in document hooks
    pass
```

**Arrowz Fix:** We've moved all `frappe.db.commit()` calls out of document hooks into standalone functions or API endpoints.

### 3.3 Query Default Sorting

**v15:** Implicit `ORDER BY modified DESC`  
**v16:** Implicit `ORDER BY creation DESC`

**Action:** If your code relies on modified ordering, explicitly specify:
```python
frappe.get_all("AZ Call Log", order_by="modified desc")
```

### 3.4 Permission Hooks Must Return True

**v15 (Allowed):**
```python
def has_permission(doc, ptype, user):
    if some_condition:
        return  # None was accepted as True
```

**v16 (Required):**
```python
def has_permission(doc, ptype, user):
    if some_condition:
        return True  # Must be explicit
    return False
```

### 3.5 Single DocType db.get_value Returns Typed Values

**v15:**
```python
if frappe.db.get_value("Arrowz Settings", None, "enable_sms") == "1":
```

**v16:**
```python
if frappe.db.get_value("Arrowz Settings", None, "enable_sms") == 1:
```

### 3.6 Testing Flag

**v15 (Deprecated):**
```python
if frappe.flags.in_test:
    pass
```

**v16:**
```python
if frappe.in_test:
    pass
```

---

## 4. Migration Steps

### Step 1: Update Frappe/ERPNext

```bash
cd ~/frappe-bench

# Update Frappe to v16
bench switch-to-branch version-16 frappe --upgrade

# Update ERPNext to v16 (if installed)
bench switch-to-branch version-16 erpnext --upgrade

# Run migrations
bench --site your-site migrate
```

### Step 2: Update Arrowz

```bash
# Get latest Arrowz v16
cd ~/frappe-bench/apps/arrowz
git fetch origin
git checkout version-16

# Or install fresh
bench get-app arrowz --branch version-16
```

### Step 3: Install/Update App

```bash
# If updating
bench --site your-site migrate

# If fresh install
bench --site your-site install-app arrowz
```

### Step 4: Rebuild Assets

```bash
bench build --app arrowz
bench clear-cache
```

### Step 5: Restart Services

```bash
bench restart
# or for production
sudo supervisorctl restart all
```

---

## 5. API Changes

### 5.1 HTTP Method Requirements

These endpoints now require **POST** method in v16:

| Endpoint | v15 | v16 |
|----------|-----|-----|
| `arrowz.api.webrtc.make_call` | GET/POST | POST only |
| `arrowz.api.webrtc.hangup_call` | GET/POST | POST only |
| `arrowz.api.sms.send_sms` | GET/POST | POST only |
| `arrowz.api.agent.set_agent_status` | GET/POST | POST only |

**Client Code Update:**
```javascript
// v15 (worked with GET)
frappe.call({
    method: "arrowz.api.webrtc.make_call",
    args: { number: "1234567890" }
});

// v16 (explicit POST recommended)
frappe.call({
    method: "arrowz.api.webrtc.make_call",
    type: "POST",
    args: { number: "1234567890" }
});
```

### 5.2 Whitelisted Method Decorator

**v16 Best Practice:**
```python
@frappe.whitelist(methods=["POST"])
def state_changing_function():
    """Functions that modify state should use POST"""
    pass

@frappe.whitelist(methods=["GET"])
def read_only_function():
    """Functions that only read data can use GET"""
    pass
```

---

## 6. Database Query Changes

### 6.1 Raw SQL in get_all/get_list Fields

**v15 (Worked):**
```python
frappe.get_all("AZ Call Log",
    fields=["sum(duration) as total_duration"])
```

**v16 (Use Dict Syntax):**
```python
frappe.get_all("AZ Call Log",
    fields=[{"SUM": "duration", "as": "total_duration"}])
```

**Or Query Builder:**
```python
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum

call_log = DocType("AZ Call Log")
query = (frappe.qb.from_(call_log)
    .select(Sum(call_log.duration).as_("total_duration"))
    .run(as_dict=True))
```

### 6.2 Aggregation Examples

```python
# Count calls by disposition
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count

log = DocType("AZ Call Log")
results = (frappe.qb.from_(log)
    .select(log.disposition, Count("*").as_("count"))
    .groupby(log.disposition)
    .run(as_dict=True))

# Average call duration
from frappe.query_builder.functions import Avg

avg_duration = (frappe.qb.from_(log)
    .select(Avg(log.duration).as_("avg"))
    .where(log.disposition == "ANSWERED")
    .run()[0][0])
```

---

## 7. JavaScript Changes

### 7.1 IIFE Wrapping

Report, Dashboard, and Page JS files are now wrapped in IIFE (Immediately Invoked Function Expressions).

**v15:**
```javascript
// Variables were global
var myConfig = {};
```

**v16:**
```javascript
// Use window for global access
window.myConfig = {};

// Or use frappe.provide for namespace
frappe.provide("arrowz");
arrowz.config = {};
```

### 7.2 Apps Screen Navigation

**v15:** `/desk#apps` worked  
**v16:** Use `/app` or direct routes

### 7.3 Desktop Path Change

**v15:** `/desk`  
**v16:** `/app`

---

## 8. Permission System Changes

### 8.1 has_permission Must Return True

**v15 Pattern (Broken in v16):**
```python
def has_call_log_permission(doc, ptype, user):
    if user_can_see_all_calls(user):
        return  # None was accepted
    if doc.extension == get_user_extension(user):
        return True
```

**v16 Pattern:**
```python
def has_call_log_permission(doc, ptype, user):
    if user_can_see_all_calls(user):
        return True  # Must be explicit
    if doc.extension == get_user_extension(user):
        return True
    return False  # Explicit denial
```

### 8.2 raise_exception Parameter Removed

**v15:**
```python
frappe.permissions.has_permission("AZ Call Log", raise_exception=True)
```

**v16:**
```python
frappe.permissions.has_permission("AZ Call Log", throw=True)
```

---

## 9. Rollback Procedure

If migration fails, follow these steps:

### Step 1: Restore Database

```bash
bench --site your-site restore path/to/backup.sql.gz
```

### Step 2: Downgrade Apps

```bash
# Downgrade Arrowz
cd ~/frappe-bench/apps/arrowz
git checkout version-15

# Downgrade Frappe
bench switch-to-branch version-15 frappe

# Downgrade ERPNext
bench switch-to-branch version-15 erpnext
```

### Step 3: Migrate and Rebuild

```bash
bench --site your-site migrate
bench build
bench restart
```

---

## 10. Troubleshooting

### Issue: "frappe.db.commit() not allowed in document hooks"

**Solution:** Move the commit outside the hook or use `frappe.enqueue()`:

```python
# Instead of committing in hook
def on_update(doc, method):
    # Your logic
    frappe.enqueue(
        "arrowz.tasks.process_update",
        doc_name=doc.name
    )

# In tasks.py
def process_update(doc_name):
    # Process and commit
    frappe.db.commit()
```

### Issue: "Query returns different order"

**Solution:** Explicitly set order_by:
```python
frappe.get_all("AZ Call Log", 
    order_by="modified desc",  # Explicit ordering
    limit=100)
```

### Issue: "Permission denied" after migration

**Solution:** Check has_permission functions return True explicitly:
```python
def has_permission(doc, ptype, user):
    # ... your logic ...
    return True  # or return False
```

### Issue: JavaScript variables undefined

**Solution:** Use window or frappe.provide:
```javascript
// Global variables
window.arrowz_config = {};

// Or namespace
frappe.provide("arrowz");
arrowz.config = {};
```

### Issue: API returns 405 Method Not Allowed

**Solution:** Use POST for state-changing operations:
```javascript
frappe.call({
    method: "arrowz.api.webrtc.make_call",
    type: "POST",  // Explicit POST
    args: { number: "123" }
});
```

---

## Support

For migration assistance:

- **GitHub Issues:** https://github.com/company/arrowz/issues
- **Email:** support@arrowz.io
- **Documentation:** https://github.com/company/arrowz/wiki

---

*Last updated: February 17, 2026*
