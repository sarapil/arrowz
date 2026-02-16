# Arrowz - Troubleshooting Guide

> Common issues and solutions for Arrowz development and production.

---

## Table of Contents
1. [Softphone Issues](#softphone-issues)
2. [Omni-Channel Issues](#omni-channel-issues)
3. [Video Conferencing Issues](#video-conferencing-issues)
4. [Database Issues](#database-issues)
5. [Build & Asset Issues](#build--asset-issues)
6. [Real-time Issues](#real-time-issues)
7. [Performance Issues](#performance-issues)
8. [API Issues](#api-issues)

---

## Softphone Issues

### Issue: Softphone Not Appearing in Navbar

**Symptoms:**
- No phone icon in navbar
- Console shows "Navbar not found" error

**Diagnosis:**
```javascript
// Open browser console (F12) and run:
console.log(document.querySelector('.navbar'));
console.log(document.querySelector('.navbar-nav'));
console.log(typeof arrowz);
```

**Solutions:**

1. **Clear cache and rebuild:**
```bash
cd /workspace/development/frappe-bench
bench --site dev.localhost clear-cache
bench build --app arrowz
```

2. **Check hooks.py includes:**
```python
# Verify in arrowz/hooks.py
app_include_js = [
    "/assets/arrowz/js/softphone_v2.js"
]
```

3. **Check navbar selectors in softphone_v2.js:**
```javascript
// Should use Frappe v15 compatible selectors
const navbar = document.querySelector('.navbar .navbar-collapse .navbar-nav');
```

4. **Verify JsSIP loaded:**
```javascript
console.log(typeof JsSIP);  // Should be "function"
```

---

### Issue: WebRTC Registration Failed

**Symptoms:**
- Softphone shows "Disconnected" or "Registration Failed"
- Console shows JsSIP errors

**Diagnosis:**
```javascript
// Check registration status
console.log(arrowz.softphone?.ua?.isRegistered());
console.log(arrowz.softphone?.ua?.registrator?.state);
```

**Solutions:**

1. **Check WebSocket URL:**
```python
# In AZ Server Config
websocket_url = "wss://pbx.example.com:8089/ws"  # Must be wss:// for production
```

2. **Verify SIP credentials:**
```bash
# In Frappe console
bench --site dev.localhost console
>>> ext = frappe.get_doc("AZ Extension", "1001")
>>> print(ext.sip_password)  # Should have value
```

3. **Check PBX WebSocket port is open:**
```bash
# Test connectivity
curl -v https://pbx.example.com:8089/ws
```

4. **Check browser permissions:**
- Microphone permission must be granted
- Site must be served over HTTPS

---

### Issue: No Audio During Calls

**Symptoms:**
- Call connects but no audio
- One-way audio

**Diagnosis:**
```javascript
// Check media streams
const localStream = arrowz.softphone?.currentSession?.connection?.getLocalStreams();
const remoteStream = arrowz.softphone?.currentSession?.connection?.getRemoteStreams();
console.log('Local:', localStream, 'Remote:', remoteStream);
```

**Solutions:**

1. **Check ICE servers configuration:**
```javascript
// In JsSIP config
pcConfig: {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { 
            urls: "turn:turn.example.com:3478", 
            username: "user", 
            credential: "pass" 
        }
    ]
}
```

2. **Check NAT/Firewall:**
- Ensure UDP ports 10000-20000 are open
- Ensure STUN/TURN servers are reachable

3. **Check audio output device:**
```javascript
// List available devices
navigator.mediaDevices.enumerateDevices()
    .then(devices => console.log(devices.filter(d => d.kind === 'audiooutput')));
```

---

### Issue: Click-to-Call Not Working

**Symptoms:**
- Phone icon buttons don't trigger calls
- Console errors on click

**Diagnosis:**
```javascript
// Check if phone_actions.js loaded
console.log(typeof arrowz.phone_actions);
```

**Solutions:**

1. **Verify event listeners:**
```javascript
// In phone_actions.js
$(document).on('click', '.phone-link, [data-phone]', function(e) {
    e.preventDefault();
    const phone = $(this).data('phone') || $(this).text();
    arrowz.softphone.dial(phone);
});
```

2. **Check extension is registered:**
```javascript
if (!arrowz.softphone.ua?.isRegistered()) {
    frappe.throw(__('Softphone not registered'));
}
```

---

## Omni-Channel Issues

### Issue: WhatsApp Messages Not Receiving

**Symptoms:**
- Webhook not receiving messages
- No new messages in Omni Panel

**Diagnosis:**
```bash
# Check webhook logs
tail -f /workspace/development/frappe-bench/logs/worker.log | grep whatsapp
```

**Solutions:**

1. **Verify webhook URL in Meta Dashboard:**
```
https://your-domain.com/api/method/arrowz.api.webhooks.whatsapp_webhook
```

2. **Check webhook verification:**
```python
# In arrowz/api/webhooks.py
@frappe.whitelist(allow_guest=True)
def whatsapp_webhook():
    if frappe.request.method == "GET":
        # Handle verification challenge
        mode = frappe.request.args.get("hub.mode")
        token = frappe.request.args.get("hub.verify_token")
        challenge = frappe.request.args.get("hub.challenge")
        # ...
```

3. **Check API credentials:**
```bash
bench --site dev.localhost console
>>> settings = frappe.get_single("AZ Omni Provider")
>>> print(settings.access_token[:10] + "...")  # Should have value
```

4. **Test manually:**
```bash
curl -X POST https://your-domain.com/api/method/arrowz.api.webhooks.whatsapp_webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

### Issue: WhatsApp Template Not Sending

**Symptoms:**
- Template messages fail with error
- 24-hour window messages work

**Solutions:**

1. **Check template is approved:**
```python
# Template must be approved in Meta Business Manager
template_name = "order_confirmation"
template_language = "en"
```

2. **Verify template parameters:**
```python
# Parameters must match template definition exactly
frappe.call("arrowz.integrations.whatsapp.send_template", 
    template_name="order_confirmation",
    to="+1234567890",
    components=[
        {"type": "body", "parameters": [{"type": "text", "text": "John"}]}
    ]
)
```

---

### Issue: Telegram Bot Not Responding

**Symptoms:**
- Bot doesn't receive messages
- No updates in polling

**Diagnosis:**
```bash
# Check Telegram polling task
bench --site dev.localhost execute arrowz.tasks.process_telegram_updates
```

**Solutions:**

1. **Check bot token:**
```bash
# Test token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

2. **Check webhook vs polling mode:**
```python
# If using webhooks, set URL:
frappe.call("arrowz.integrations.telegram.set_webhook",
    url="https://your-domain.com/api/method/arrowz.api.webhooks.telegram_webhook"
)
```

3. **Check scheduled task in hooks.py:**
```python
scheduler_events = {
    "cron": {
        "* * * * *": ["arrowz.tasks.process_telegram_updates"]
    }
}
```

---

## Video Conferencing Issues

### Issue: Cannot Create Meeting Room

**Symptoms:**
- "Failed to create room" error
- OpenMeetings API errors

**Diagnosis:**
```bash
# Test OpenMeetings connection
bench --site dev.localhost console
>>> from arrowz.integrations.openmeetings import OpenMeetingsClient
>>> client = OpenMeetingsClient()
>>> client.get_session_id()  # Should return valid session
```

**Solutions:**

1. **Check OpenMeetings credentials:**
```python
# In AZ Server Config
om_url = "https://meetings.example.com/openmeetings"
om_user = "admin"
om_password = "****"
```

2. **Check OpenMeetings server status:**
```bash
curl https://meetings.example.com/openmeetings/services/info/version
```

3. **Check room type:**
```python
# Valid room types: 1 (Conference), 2 (Interview), 3 (Presentation)
room_type = 1
```

---

### Issue: Users Cannot Join Meeting

**Symptoms:**
- Join link not working
- "Invalid hash" error

**Solutions:**

1. **Generate new secure hash:**
```python
from arrowz.integrations.openmeetings import OpenMeetingsClient
client = OpenMeetingsClient()
hash = client.get_user_hash(
    room_id=room.om_room_id,
    user_email=user.email,
    user_name=user.full_name
)
join_url = f"{client.om_url}?secureHash={hash}"
```

2. **Check hash expiration:**
- Hashes may expire after a period
- Generate fresh hash for each join attempt

---

## Database Issues

### Issue: Migration Errors

**Symptoms:**
- `bench migrate` fails
- "Column doesn't exist" errors

**Solutions:**

1. **Check DocType JSON syntax:**
```bash
# Validate JSON
python -m json.tool arrowz/arrowz/doctype/az_call_log/az_call_log.json
```

2. **Run sync manually:**
```bash
bench --site dev.localhost run-sync
```

3. **Rebuild table:**
```bash
bench --site dev.localhost console
>>> frappe.reload_doc("arrowz", "doctype", "az_call_log")
```

---

### Issue: Permission Denied Errors

**Symptoms:**
- "No permission for DocType" errors
- Users can't access documents

**Solutions:**

1. **Check role permissions:**
```bash
bench --site dev.localhost console
>>> from frappe.permissions import get_doc_permissions
>>> get_doc_permissions(frappe.get_doc("AZ Call Log", "xxx"), user="user@example.com")
```

2. **Update permissions in DocType:**
```json
{
    "permissions": [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "Arrowz User", "read": 1, "write": 1, "create": 1}
    ]
}
```

3. **Clear permission cache:**
```bash
bench --site dev.localhost clear-cache
```

---

## Build & Asset Issues

### Issue: JavaScript Not Loading

**Symptoms:**
- Browser shows old code
- New features not visible

**Solutions:**

1. **Clear all caches:**
```bash
bench --site dev.localhost clear-cache
bench --site dev.localhost clear-website-cache
rm -rf sites/dev.localhost/public/files/cache/*
```

2. **Force rebuild:**
```bash
bench build --app arrowz --force
```

3. **Check hooks.py:**
```python
# Ensure files are included
app_include_js = [
    "/assets/arrowz/js/softphone_v2.js",
    "/assets/arrowz/js/omni_panel.js",
    # ...
]
```

4. **Hard refresh in browser:**
- Ctrl+Shift+R (Windows/Linux)
- Cmd+Shift+R (Mac)

---

### Issue: CSS Not Applying

**Symptoms:**
- Styles not visible
- Layout broken

**Solutions:**

1. **Check CSS syntax:**
```bash
# Look for syntax errors
npx stylelint arrowz/public/css/*.css
```

2. **Check hooks.py:**
```python
app_include_css = [
    "/assets/arrowz/css/softphone.css"
]
```

3. **Check specificity:**
```css
/* Use more specific selectors */
.arrowz-softphone .btn {
    /* styles */
}
```

---

## Real-time Issues

### Issue: Socket.IO Not Connecting

**Symptoms:**
- Real-time events not received
- Console shows WebSocket errors

**Diagnosis:**
```javascript
console.log(frappe.socketio?.socket?.connected);
```

**Solutions:**

1. **Check socketio process:**
```bash
ps aux | grep socketio
# Should show running process
```

2. **Restart bench:**
```bash
# In bench directory
bench start  # Or restart if running
```

3. **Check common_site_config.json:**
```json
{
    "socketio_port": 9000
}
```

4. **Check nginx configuration:**
```nginx
location /socket.io {
    proxy_pass http://localhost:9000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

### Issue: Events Not Reaching Specific Users

**Symptoms:**
- Some users don't receive events
- Events work for current user only

**Solutions:**

1. **Check user parameter in publish_realtime:**
```python
# Send to specific user
frappe.publish_realtime("event", data, user="user@example.com")

# Send to all users in a room
frappe.publish_realtime("event", data, room="room_name")

# Broadcast to all
frappe.publish_realtime("event", data)
```

2. **Check user is subscribed:**
```javascript
// Verify subscription
console.log(frappe.realtime.socket.rooms);
```

---

## Performance Issues

### Issue: Slow API Responses

**Symptoms:**
- API calls take > 1 second
- UI feels sluggish

**Solutions:**

1. **Add indexes to frequently queried fields:**
```sql
ALTER TABLE `tabAZ Call Log` ADD INDEX idx_caller (caller);
ALTER TABLE `tabAZ Call Log` ADD INDEX idx_start_time (start_time);
```

2. **Optimize queries:**
```python
# Bad - fetches all fields
calls = frappe.get_all("AZ Call Log", filters={"caller": "1001"})

# Good - fetch only needed fields
calls = frappe.get_all("AZ Call Log", 
    filters={"caller": "1001"},
    fields=["name", "caller", "duration"],
    limit=100
)
```

3. **Use caching:**
```python
@frappe.whitelist()
def get_extension_config():
    cache_key = f"ext_config_{frappe.session.user}"
    config = frappe.cache().get_value(cache_key)
    if not config:
        config = fetch_config_from_db()
        frappe.cache().set_value(cache_key, config, expires_in_sec=300)
    return config
```

---

### Issue: Memory Leaks in Frontend

**Symptoms:**
- Browser becomes slow over time
- Memory usage grows

**Solutions:**

1. **Clean up event listeners:**
```javascript
arrowz.myComponent = {
    init() {
        this.handler = this.handleEvent.bind(this);
        frappe.realtime.on('event', this.handler);
    },
    cleanup() {
        frappe.realtime.off('event', this.handler);
    }
};
```

2. **Avoid global variable accumulation:**
```javascript
// Bad
window.allCalls = [];
window.allCalls.push(newCall);  // Grows forever

// Good - limit array size
arrowz.recentCalls = [];
arrowz.addCall = function(call) {
    this.recentCalls.push(call);
    if (this.recentCalls.length > 100) {
        this.recentCalls.shift();
    }
};
```

---

## API Issues

### Issue: "Method Not Whitelisted" Error

**Symptoms:**
- API call returns 403
- "Method not whitelisted" message

**Solutions:**

1. **Add @frappe.whitelist() decorator:**
```python
@frappe.whitelist()
def my_function():
    pass
```

2. **For guest access:**
```python
@frappe.whitelist(allow_guest=True)
def public_webhook():
    pass
```

3. **Restart bench after adding decorator:**
```bash
# Gunicorn needs restart to pick up changes
bench restart  # or kill -HUP <gunicorn_pid>
```

---

### Issue: "Permission Denied" in API

**Symptoms:**
- API returns 403 for non-admin users
- "No permission for DocType" error

**Solutions:**

1. **Check role requirements:**
```python
@frappe.whitelist()
def my_function():
    frappe.only_for(["System Manager", "Arrowz User"])
    # ...
```

2. **Check document permissions:**
```python
@frappe.whitelist()
def get_my_calls():
    if not frappe.has_permission("AZ Call Log", "read"):
        frappe.throw(_("No permission"), frappe.PermissionError)
    # ...
```

---

## Quick Diagnostic Commands

```bash
# Check all running processes
ps aux | grep -E "gunicorn|redis|socketio|worker"

# Check error logs
tail -f /workspace/development/frappe-bench/logs/web.error.log
tail -f /workspace/development/frappe-bench/logs/worker.error.log

# Check bench status
bench doctor

# Test database connection
bench --site dev.localhost mariadb -e "SELECT 1"

# Clear everything and rebuild
bench --site dev.localhost clear-cache && bench build --app arrowz

# Check installed apps
bench --site dev.localhost list-apps
```
