# 🔧 توصيات الإصلاح - Arrowz Softphone

## المشاكل المتبقية والحلول المقترحة

---

## 1. 🔴 إضافة معالجات أحداث ناقصة (CRITICAL)

### المشكلة:
عند وصول `CANCEL` من FreePBX، لا توجد معالج محددة لهذا الحدث → الاتصال قد يبقى في حالة معلقة.

### الحل:

**File:** `arrowz/public/js/softphone_v2.js` → Function `setupSessionEvents()`

إضافة المعالجات التالية:

```javascript
// Handle call rejection
this.session.on('rejected', (e) => {
    console.warn('Arrowz: Call rejected:', e.cause);
    this._isAnswering = false;
    this._callConfirmed = false;
    this.stopRingtone();
    this.endCall(`Rejected: ${e.cause}`);
});

// Handle call cancellation (FreePBX sends CANCEL)
this.session.on('cancel', (e) => {
    console.warn('Arrowz: Call cancelled by remote:', e.cause);
    this._isAnswering = false;
    this._callConfirmed = false;
    this.stopRingtone();
    this.endCall('Call Cancelled');
});

// Handle redirects
this.session.on('redirected', (e) => {
    console.warn('Arrowz: Call redirected to:', e.target);
    this._isAnswering = false;
    this._callConfirmed = false;
    this.endCall('Call Redirected');
});

// Handle no answer timeout
this.session.on('requesttimeout', () => {
    console.warn('Arrowz: Request timeout - no response from peer');
    this._isAnswering = false;
    this._callConfirmed = false;
    this.endCall('No Response');
});
```

### الموقع بالضبط:
بعد سطر 1007 (بعد معالج `failed`)

---

## 2. 🟡 تحسين معالجة أخطاء ICE (HIGH PRIORITY)

### المشكلة:
عندما يفشل ICE connection، لا يتم إنهاء الاتصال تلقائياً → المستخدم ينتظر بدون جدوى.

### الحل:

**File:** `arrowz/public/js/softphone_v2.js` → Function `setupSessionEvents()` → Inside `peerconnection` handler

تحسين معالجة ICE states:

```javascript
this.session.on('peerconnection', (e) => {
    console.log('Arrowz: Peerconnection event received');
    const pc = e.peerconnection;
    
    // Track ICE candidates
    let hostCandidateReceived = false;
    
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log('Arrowz: ICE candidate:', event.candidate.type);
            if (event.candidate.type === 'host') {
                hostCandidateReceived = true;
            }
        } else {
            console.log('Arrowz: ICE gathering complete');
            if (!hostCandidateReceived) {
                console.warn('Arrowz: No host ICE candidates received - may have connectivity issues');
            }
        }
    };
    
    // Monitor ICE connection state
    let iceFailureTimeout;
    pc.oniceconnectionstatechange = () => {
        const state = pc.iceConnectionState;
        console.log('Arrowz: ICE connection state:', state);
        
        switch (state) {
            case 'connected':
            case 'completed':
                clearTimeout(iceFailureTimeout);
                console.log('Arrowz: ICE connection established');
                break;
                
            case 'failed':
                console.error('Arrowz: ICE connection failed - terminating call');
                this.endCall('ICE Connection Failed');
                break;
                
            case 'disconnected':
                console.warn('Arrowz: ICE disconnected - setting timeout');
                // Give 5 seconds to recover
                iceFailureTimeout = setTimeout(() => {
                    if (pc.iceConnectionState === 'disconnected') {
                        console.error('Arrowz: ICE still disconnected after 5s - terminating');
                        this.endCall('ICE Disconnected');
                    }
                }, 5000);
                break;
        };
    };
    
    // Monitor gathering state
    pc.onicegatheringstatechange = () => {
        console.log('Arrowz: ICE gathering state:', pc.iceGatheringState);
    };
    
    // Monitor overall connection state
    pc.onconnectionstatechange = () => {
        const state = pc.connectionState;
        console.log('Arrowz: Connection state:', state);
        
        if (state === 'failed' || state === 'closed') {
            console.error('Arrowz: Connection failed/closed');
            if (!this._callConfirmed) {
                this.endCall('Connection Failed');
            }
        }
    };
    
    // Handle remote track
    pc.ontrack = (event) => {
        console.log('Arrowz: Track received:', event.track.kind);
        if (event.streams && event.streams[0]) {
            this.remoteStream = event.streams[0];
            this.audioPlayer.srcObject = event.streams[0];
            this.audioPlayer.play().catch(() => {});
        }
    };
    
    // Handle connection errors
    pc.addEventListener('error', (event) => {
        console.error('Arrowz: PeerConnection error:', event);
    });
});
```

### الموقع بالضبط:
من سطر 904 إلى 950

---

## 3. 🟡 تحسين تسجيل Call Log (HIGH PRIORITY)

### المشكلة:
حالة المكالمة في قاعدة البيانات لا تُحدّث في الوقت الفعلي → بيانات غير دقيقة.

### الحل أ: تحديث الفوري عند التأكيد

**File:** `arrowz/public/js/softphone_v2.js` → Function `setupSessionEvents()`

```javascript
this.session.on('confirmed', () => {
    console.log('Arrowz: Session confirmed');
    this._callConfirmed = true;
    this._isAnswering = false;
    this.stopRingtone();
    this.callStartTime = new Date();
    this.startCallTimer();
    this.updateCallStatus(__('Connected'));
    this.updateNavbarStatus('in-call', this._currentCallee);
    
    // ✅ NEW: Update database immediately
    frappe.call({
        method: 'arrowz.api.call_log.update_call_status',
        args: {
            status: 'In Progress',
            answer_time: new Date().toISOString(),
            call_id: this.session.id
        },
        async: true,
        error: () => console.warn('Failed to update call status')
    });
});

this.session.on('failed', (e) => {
    // ... existing error handling ...
    
    // ✅ NEW: Mark call as failed in database
    frappe.call({
        method: 'arrowz.api.call_log.update_call_status',
        args: {
            status: 'Failed',
            disposition: 'FAILED',
            reason: e.cause,
            call_id: this.session?.id
        },
        async: true,
        error: () => console.warn('Failed to update failed call status')
    });
});
```

### الحل ب: إنشاء API جديد في Python

**File:** `arrowz/api/call_log.py` (جديد - إنشاء الملف)

```python
import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def update_call_status(status, call_id=None, answer_time=None, disposition=None, reason=None):
    """
    Update call status in real-time from WebRTC client.
    
    Args:
        status: 'In Progress', 'Failed', 'Completed'
        call_id: JsSIP session ID (for linking)
        answer_time: When call was answered
        disposition: ANSWERED, NO ANSWER, FAILED, etc
        reason: Error reason if failed
    """
    try:
        # Find call log by session or recent call
        if call_id:
            call_log = frappe.db.get_value(
                "AZ Call Log",
                {"call_id": call_id},
                "name"
            )
        else:
            # Get most recent call from current user
            call_log = frappe.db.get_value(
                "AZ Call Log",
                {"status": "Ringing"},
                "name",
                order_by="start_time desc"
            )
        
        if not call_log:
            frappe.log_error(f"Cannot find call log to update: {call_id}")
            return {"success": False, "error": "Call not found"}
        
        # Update the call
        doc = frappe.get_doc("AZ Call Log", call_log)
        doc.status = status
        
        if answer_time:
            doc.answer_time = answer_time
        
        if disposition:
            doc.disposition = disposition
        
        if reason and status == 'Failed':
            doc.notes = f"WebRTC Error: {reason}"
        
        if status == 'Completed' or status == 'Failed':
            doc.end_time = now_datetime()
        
        doc.save(ignore_permissions=True)
        
        # Publish real-time update
        frappe.publish_realtime(
            "call_status_update",
            {"call_log": doc.name, "status": status},
            user=frappe.session.user
        )
        
        return {"success": True, "call_log": doc.name}
        
    except Exception as e:
        frappe.log_error(f"Error updating call status: {str(e)}")
        return {"success": False, "error": str(e)}
```

---

## 4. 🟠 تحسين STUN/TURN Configuration (MEDIUM PRIORITY)

### المشكلة:
استخدام سيرفرات متعددة يزيد وقت ICE Gathering.

### الحل:

**File:** `arrowz/api/webrtc.py` → Function `get_webrtc_config()`

```python
# Current (lines 68-85)
ice_servers = [{"urls": "stun:stun.l.google.com:19302"}]

if server.stun_server:
    ice_servers.append({"urls": server.stun_server})

if server.turn_server:
    turn_config = {"urls": server.turn_server}
    if server.turn_username:
        turn_config["username"] = server.turn_username
    if server.turn_password:
        turn_config["credential"] = server.get_password("turn_password")
    ice_servers.append(turn_config)

# ✅ IMPROVED:
ice_servers = []

# Add Google STUN (most reliable)
ice_servers.append({"urls": "stun:stun.l.google.com:19302"})

# Add server-specific STUN only if it's different and working
if server.stun_server and server.stun_server != "stun:stun.l.google.com:19302":
    # Test if server is reachable (optional)
    ice_servers.append({"urls": server.stun_server})

# Add TURN only if relay is needed (for very restrictive networks)
# Most LAN/office networks don't need TURN
if server.turn_server and getattr(server, 'enable_turn', False):
    turn_config = {"urls": server.turn_server}
    if server.turn_username:
        turn_config["username"] = server.turn_username
    if server.turn_password:
        turn_config["credential"] = server.get_password("turn_password")
    # Limit TURN to last position (use only if STUN fails)
    ice_servers.append(turn_config)

# Limit ICE candidates for faster negotiation
# Return top 2-3 STUN servers max
return {
    # ...
    "ice_servers": ice_servers[:3],  # Limit to first 3
    # ...
}
```

---

## 5. 🟠 إضافة معالجة فشل WebRTC (MEDIUM PRIORITY)

### المشكلة:
عندما ينقطع الاتصال بسبب مشاكل WebRTC، لا يوجد إخطار واضح.

### الحل:

**File:** `arrowz/public/js/softphone_v2.js` → Function `setupSessionEvents()`

```javascript
// Add SDP negotiation failure handlers
this.session.on('peerconnection:setlocaldescriptionfailed', (e) => {
    console.error('Arrowz: Failed to set local description:', e.error);
    
    // Check for RTCP-MUX issues
    if (e.error?.message?.includes('RTCP')) {
        frappe.show_alert({
            message: __('Media Error: FreePBX RTCP-MUX Configuration Issue'),
            indicator: 'red'
        }, 10);
    }
    
    this.endCall('Media Negotiation Failed');
});

this.session.on('peerconnection:setremotedescriptionfailed', (e) => {
    console.error('Arrowz: Failed to set remote description:', e.error);
    
    if (e.error?.message?.includes('RTCP-MUX')) {
        frappe.show_alert({
            message: __('Media Error: FreePBX needs RTCP-MUX enabled in PJSIP settings'),
            indicator: 'red'
        }, 10);
    } else if (e.error?.message?.includes('BUNDLE')) {
        frappe.show_alert({
            message: __('Media Error: BUNDLE negotiation failed'),
            indicator: 'red'
        }, 10);
    }
    
    this.endCall('Media Setup Failed');
});

// Handle missing remote streams
this.session.on('peerconnection:addstreamfailed', (e) => {
    console.error('Arrowz: Failed to add stream:', e.error);
    frappe.show_alert({
        message: __('Audio Stream Error - call may be one-way'),
        indicator: 'orange'
    }, 7);
});
```

---

## 6. 🟢 تحسين معالجة إيقاف الاتصال (NICE-TO-HAVE)

### الحل:

**File:** `arrowz/public/js/softphone_v2.js` → Function `endCall()`

```javascript
endCall(reason) {
    this.stopCallTimer();
    this.stopRingtone();
    
    // Reset flags
    this._isAnswering = false;
    this._callConfirmed = false;
    
    // Clean up pre-granted stream
    if (this._preGrantedStream) {
        console.log('Arrowz: Cleaning up unused pre-granted stream');
        this._preGrantedStream.getTracks().forEach(track => track.stop());
        this._preGrantedStream = null;
    }
    
    // Clean up local stream
    if (this.localStream) {
        console.log('Arrowz: Stopping local stream');
        this.localStream.getTracks().forEach(t => t.stop());
        this.localStream = null;
    }
    
    // Clean up remote stream
    if (this.remoteStream) {
        console.log('Arrowz: Stopping remote stream');
        this.remoteStream.getTracks().forEach(t => t.stop());
        this.remoteStream = null;
    }
    
    // Clean up audio player
    if (this.audioPlayer) {
        this.audioPlayer.pause();
        this.audioPlayer.srcObject = null;
    }
    
    // Clean up session
    this.session = null;
    this.callStartTime = null;
    this._currentCallee = null;
    
    // Update UI
    this.updateNavbarStatus('registered', this.config?.extension || '---');
    
    if (this.isDropdownOpen) {
        this.showDialerUI();
    }
    
    // Show reason if provided
    if (reason) {
        frappe.show_alert({
            message: __('Call ended: {0}', [reason]),
            indicator: 'orange'
        }, 3);
    }
    
    // ✅ NEW: Notify database
    frappe.call({
        method: 'arrowz.api.call_log.log_call_ended',
        args: {reason: reason, call_id: this.session?.id},
        async: true
    });
}
```

---

## 📋 قائمة التحقق للتنفيذ

### Phase 1: Critical (هذا الأسبوع)
- [ ] إضافة معالجات الأحداث الناقصة (rejected, cancel, redirected)
- [ ] تحسين معالجة ICE failures
- [ ] إنشاء API لتحديث حالة المكالمة

### Phase 2: Important (الأسبوع القادم)
- [ ] تحسين STUN/TURN configuration
- [ ] إضافة معالجة SDP failures
- [ ] تحسين معالجة stream cleanup

### Phase 3: Enhancement (اختياري)
- [ ] إضافة قياس جودة الاتصال
- [ ] إضافة تقارير أداء WebRTC
- [ ] تحسين معالجة الشبكات البطيئة

---

## 🧪 Testing Checklist

### Test Case 1: Incoming Call with Fast Answer
- [ ] Call arrives
- [ ] Microphone pre-request visible in console
- [ ] User clicks Answer after 2 seconds
- [ ] "Using pre-granted stream" visible in console
- [ ] Call connects in < 2 seconds

### Test Case 2: Incoming Call - User Rejects
- [ ] Call arrives
- [ ] User clicks Reject button
- [ ] "Cleaning up pre-granted stream" visible in console
- [ ] No background microphone access active

### Test Case 3: Outgoing Call
- [ ] User dials number
- [ ] getUserMedia requested
- [ ] INVITE sent within 5 seconds
- [ ] Ringing status shown
- [ ] Call connects successfully

### Test Case 4: Call Failure Handling
- [ ] Simulate network disconnect
- [ ] Verify "ICE Failed" message shown
- [ ] Verify database updated with Failed status
- [ ] Verify cleanup executed

### Test Case 5: Database State
- [ ] Make 5 calls, disconnect some mid-ringing
- [ ] Wait 10 minutes for cleanup task
- [ ] Verify no "stale" calls remain in Active Calls counter
- [ ] Verify all calls have proper end_time and status

---

**آخر تحديث:** 31 يناير 2026
