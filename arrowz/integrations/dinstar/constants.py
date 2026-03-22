# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
Dinstar Constants — Page URLs, Form Actions, Field Mappings

Complete catalog of the Dinstar UC2000-VE web interface covering:
- All .htm page URLs
- All goform POST/GET endpoints
- Enum/lookup tables for coded values
"""

# ═══════════════════════════════════════════════════════════════════
# Page URLs (GET) — embedded HTML with JS data
# ═══════════════════════════════════════════════════════════════════

DINSTAR_PAGES = {
    # ─── System ───
    "system_info":          "/enSysInfo.htm",
    "summary":              "/enSummary.htm",
    "local_network":        "/enLocalNetwork.htm",
    "manage_cfg":           "/enManageCfg.htm",
    "password":             "/enPassword.htm",
    "restart":              "/enRestart.htm",
    "restart_timer":        "/enRestartTimer.htm",
    "firmware_upload":      "/enFirmwareUpload.htm",
    "data_restore":         "/enDataRestore.htm",
    "default_set":          "/enDefaultSet.htm",
    "sys_log":              "/enSysLog.htm",
    "file_log":             "/enFileLog.htm",
    "web_operation_log":    "/enWebOperationLog.htm",
    "provision":            "/enProvision.htm",
    "permission_control":   "/enPermissionControl.htm",

    # ─── SIP / VoIP ───
    "sip_cfg":              "/enSIPCfg.htm",
    "port_list":            "/enPortList.htm",
    "port_info":            "/enPortInfo.htm",
    "service_cfg":          "/enServiceCfg.htm",
    "media_param_cfg":      "/enMediaParamCfg.htm",
    "digit_map":            "/enDigitMap.htm",
    "call_conference":      "/enCallConference.htm",
    "call_forward_time":    "/enCallForwardTimeCfg.htm",

    # ─── Statistics ───
    "call_stat":            "/enCallStat.htm",
    "current_call_stat":    "/enCurrentCallStat.htm",
    "call_cdr":             "/enCallCDR.htm",
    "rtp_stat":             "/enRTPStat.htm",
    "protocol_stat":        "/enProtocolStat.htm",
    "ecc_stat":             "/enEccStat.htm",
    "relay_mux_stat":       "/enRelayMuxStat.htm",

    # ─── GSM / Mobile ───
    "gsm_operate":          "/enGsmOperate.htm",
    "gsm_event":            "/enGSMEvent.htm",
    "gsm_network_test":     "/enGsmNetworkTest.htm",
    "wia_port_stat":        "/enWIAPortStatNew.htm",
    "wia_basic_cfg":        "/enWIABasicCfg.htm",
    "wia_sim_cfg":          "/enWIASimCfg.htm",
    "wia_carrier_cfg":      "/enWIACarrierCfg.htm",
    "wia_carrier_rule":     "/enWIACarrierRule.htm",
    "wia_call_forward":     "/enWIACallForwardCfg.htm",
    "wia_call_waiting":     "/enWIACallWaitingCfg.htm",
    "wia_set_number":       "/enWIASetNumber.htm",
    "wia_ussd":             "/enWIAUSSD.htm",
    "wia_bcch_total_cfg":   "/enWIABCCHTotalCfg.htm",
    "bcch_stat":            "/enBCCHStat.htm",
    "module_log":           "/enModuleLog.htm",
    "module_recovery":      "/enModuleRecovery.htm",
    "module_upgrade":       "/enModuleUpgrade.htm",
    "imei_term":            "/enIMEITerm.htm",

    # ─── SMS ───
    "sms_cfg":              "/enSMSCfg.htm",
    "sms_overview":         "/enSMSOverview.htm",
    "sms_send":             "/enWIASendMsg.htm",
    "sms_recv":             "/enSmsRecvNew.htm",
    "sms_send_record":      "/enSmsSendRecord.htm",
    "sms_routing":          "/enSMSRouting.htm",
    "sms_balance":          "/enSMSBalance.htm",
    "smsc_switch":          "/enSMSCSwitchSetting.htm",

    # ─── Routing Groups ───
    "port_group":           "/enPortGroup.htm",
    "ip_group":             "/enIpGroup.htm",
    "ip_cfg":               "/enIpCfg.htm",

    # ─── Heartbeat / Balance ───
    "hb_basic_cfg":         "/enHBBasicCfg.htm",
    "hb_sim":               "/enHBSim.htm",
    "hb_balance":           "/enHBBalance.htm",
    "hb_balance_rate":      "/enHBBalanceRate.htm",
    "hb_balance_calc":      "/enHBBalanceCalculate.htm",
    "hb_phone_number":      "/enHBPhoneNumber.htm",
    "hb_auto_cfg":          "/enHBAutoCfg.htm",
    "hb_abnormal_call":     "/enHBAbnormalCall.htm",
    "schedule_task":        "/enScheduleTaskCfg.htm",

    # ─── Network ───
    "vlan_cfg":             "/enVLANCfg.htm",
    "vpn_cfg":              "/enVPNCfg.htm",
    "firewall_acc_rule":    "/enFirewallACCRule.htm",
    "arp_add":              "/enARPAdd.htm",
    "dma_cfg":              "/enDMACfg.htm",
    "ping_test":            "/enPingTest.htm",
    "tracert_test":         "/enTracertTest.htm",
    "network_capture":      "/enNetworkCaptureNew.htm",
    "email_param":          "/enEmailParam.htm",

    # ─── Cloud / Remote ───
    "cloud_server_cfg":     "/enCloudServerCfg.htm",
    "relay_server_cfg":     "/enRelayServerCfg.htm",
    "remote_server_cfg":    "/enRemoteServerCfg.htm",
    "remote_sim_log":       "/enRemoteSimLog.htm",
    "mbn_config":           "/enMBNConfig.htm",
    "user_board_upgrade":   "/enUserBoardUpgrade.htm",
}


# ═══════════════════════════════════════════════════════════════════
# GoForm Actions (POST) — form submit endpoints
# ═══════════════════════════════════════════════════════════════════

DINSTAR_GOFORMS = {
    # Auth
    "login":                "/goform/IADIdentityAuth",

    # System
    "local_network":        "/goform/LocalNetwork",
    "manage_cfg":           "/goform/ManageCfg",
    "restart":              "/goform/Restart",
    "default_set":          "/goform/DefaultSet",

    # SIP
    "sip_cfg":              "/goform/SipCfg",
    "port_cfg":             "/goform/PortCfg",
    "service_cfg":          "/goform/ServiceCfg",
    "media_param_cfg":      "/goform/EiaMediaParamCfg",

    # Statistics
    "call_stat_refresh":    "/goform/CallStatRefresh",
    "cdr_record":           "/goform/EiaisCdrRecord",
    "cdr_clear":            "/goform/EiaCDRClear",
    "cdr_filter":           "/goform/EiaSetCDRreportFilter",

    # GSM Operations
    "gsm_rule":             "/goform/WIAGSMRule",
    "gsm_event_filter":     "/goform/EiaSetGSMEventFilter",
    "module_reset":         "/goform/ModuleGotoResetCfg",
    "module_reset_new":     "/goform/ModuleGotoResetNew",
    "module_block":         "/goform/ModuleGotoBlockCfg",
    "module_block_new":     "/goform/ModuleGotoBlockNew",
    "call_block":           "/goform/CallGotoSetCfg",
    "call_block_new":       "/goform/CallGotoBlockNew",
    "module_power_on":      "/goform/ModuleGotoPowerOn",
    "module_power_off":     "/goform/ModuleGotoPowerOff",
    "sms_block_cfg":        "/goform/SmsGotoSetCfg",
    "wia_basic_cfg":        "/goform/WIABasicCfg",
    "wia_sim_cfg":          "/goform/WIASIMCardCfg",
    "wia_sim_lock":         "/goform/LockGoto",

    # SMS
    "sms_cfg":              "/goform/WIASMSCfg",
    "sms_overview_reset":   "/goform/EiaSMSCfgReset",
    "sms_send":             "/goform/WIAMsgSend",
    "sms_send_stop":        "/goform/SmsSendGoStop",
    "sms_recv_filter":      "/goform/EiaSmsRecvFilter",
    "sms_recv_clear":       "/goform/EiaSmsRecvClear",
    "sms_recv_record":      "/goform/EiaisSmsRecord",
    "sms_routing":          "/goform/WIASMSRouteCfg",

    # Routing
    "port_group":           "/goform/PortGroup",
    "port_group_change":    "/goform/PortGroupChange",
    "port_group_del":       "/goform/PortGroupGoDel",
    "port_group_mod":       "/goform/PortGroupGoMod",
    "ip_group":             "/goform/IpGroup",
    "ip_group_change":      "/goform/IpGroupChange",
    "ip_group_del":         "/goform/IpGroupGoDel",
    "ip_group_mod":         "/goform/IpGroupGoMod",
    "ip_cfg":               "/goform/IpCfg",

    # VPN
    "vpn_cfg":              "/goform/VPNCfg",
    "vpn_info":             "/goform/WebGetOvpnInfo",

    # Summary (AJAX)
    "summary_query":        "/goform/EiaSummaryQuery",
}


# ═══════════════════════════════════════════════════════════════════
# Enum / Lookup Tables
# ═══════════════════════════════════════════════════════════════════

PORT_STATUS_MAP = {
    "Idle":         {"label": "Idle",          "color": "#10b981", "icon": "✅"},
    "Talking":      {"label": "In Call",       "color": "#f59e0b", "icon": "📞"},
    "Ringing":      {"label": "Ringing",       "color": "#3b82f6", "icon": "🔔"},
    "Blocked":      {"label": "Blocked",       "color": "#ef4444", "icon": "🚫"},
    "NoSIM":        {"label": "No SIM",        "color": "#6b7280", "icon": "⚠️"},
    "NoSignal":     {"label": "No Signal",     "color": "#ef4444", "icon": "📵"},
    "Registering":  {"label": "Registering",   "color": "#8b5cf6", "icon": "⏳"},
    "Disabled":     {"label": "Disabled",      "color": "#9ca3af", "icon": "⭕"},
    "PowerOff":     {"label": "Power Off",     "color": "#374151", "icon": "⬛"},
}

BAND_TYPE_MAP = {
    "0":    "GSM900/1800 (Europe/MEA)",
    "1":    "GSM900/1900",
    "2":    "GSM850/1800",
    "3":    "GSM850/1900 (Americas)",
    "64":   "GSM900",
    "128":  "GSM1800",
    "256":  "GSM850",
    "512":  "Default (Auto)",
    "1024": "GSM1900",
}

NETWORK_MODE_MAP = {
    "0": "Auto",
    "1": "GSM Only",
    "2": "WCDMA Only",
    "3": "LTE Only",
    "4": "CDMA Only",
}

CODEC_MAP = {
    "0": {"name": "PCMU",  "label": "G.711 µ-law", "bandwidth": "64 kbps"},
    "8": {"name": "PCMA",  "label": "G.711 A-law",  "bandwidth": "64 kbps"},
    "4": {"name": "G723",  "label": "G.723.1",      "bandwidth": "6.3 kbps"},
    "18":{"name": "G729",  "label": "G.729A",       "bandwidth": "8 kbps"},
    "2": {"name": "G726",  "label": "G.726-32",     "bandwidth": "32 kbps"},
    "3": {"name": "GSM",   "label": "GSM FR",       "bandwidth": "13 kbps"},
    "98":{"name": "iLBC",  "label": "iLBC",         "bandwidth": "15 kbps"},
}

DTMF_METHOD_MAP = {
    "0": "RFC2833",
    "1": "SIP INFO",
    "2": "Inband",
    "3": "RFC2833 + SIP INFO",
}

CALL_PROGRESS_TONE_MAP = {
    "0":  "China",
    "1":  "USA",
    "2":  "UK",
    "3":  "Australia",
    "4":  "Germany",
    "5":  "France",
    "6":  "Brazil",
    "7":  "South Africa",
    "8":  "India",
    "9":  "Italy",
    "10": "Spain",
    "11": "Japan",
    "12": "Turkey",
    "13": "Mexico",
    "14": "Russia",
    "15": "Custom",
}

SIP_TRANSPORT_MAP = {
    "0": "UDP",
    "1": "TCP",
    "2": "TLS",
}

SRTP_MODE_MAP = {
    "0": "Disabled",
    "1": "Optional",
    "2": "Mandatory",
}

SILENCE_SUPPRESSION_MAP = {
    "0": "Disabled",
    "1": "Enabled",
}

WAN_MODE_MAP = {
    "DHCP": "DHCP",
    "Static": "Static IP",
    "PPPoE": "PPPoE",
}

# GSM signal strength ranges (dBm)
SIGNAL_STRENGTH = {
    "excellent": {"min": -70, "max": 0,     "bars": 5, "label": "Excellent"},
    "good":      {"min": -85, "max": -70,   "bars": 4, "label": "Good"},
    "fair":      {"min": -100, "max": -85,  "bars": 3, "label": "Fair"},
    "poor":      {"min": -110, "max": -100, "bars": 2, "label": "Poor"},
    "very_poor": {"min": -120, "max": -110, "bars": 1, "label": "Very Poor"},
    "none":      {"min": -999, "max": -120, "bars": 0, "label": "No Signal"},
}

# Call stat table column definitions
CALL_STAT_COLUMNS = [
    "port", "total_calls", "answered", "failed", "busy",
    "no_answer", "rejected", "duration_total", "asr_percent",
]

ECC_STAT_COLUMNS = [
    "port", "total_calls", "duration_hm", "answered", "busy",
    "no_answer", "no_carrier", "no_dialtone", "congestion",
    "unallocated_number", "normal_clearing", "call_rejected", "other",
]

# Per-port field names in PortCfg form (indexed 0..N)
PORT_CFG_FIELDS = [
    "SipLocalPort", "SipAcc", "AuthenticateID", "SipAccPsw",
    "Register", "TxGain", "RxGain", "OffhookAutodial", "PSTNHotline",
]

# Summary AJAX polling URL (returns JSON)
SUMMARY_POLL_URL = "/goform/EiaSummaryQuery"
