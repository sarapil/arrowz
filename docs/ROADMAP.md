# Arrowz Roadmap & Proposals

> **Last Updated:** February 17, 2026  
> **Status:** Active Development  
> **Review Cycle:** Weekly

---

## 🎯 Vision

Make Arrowz the most comprehensive open-source unified communications platform for Frappe/ERPNext, enabling businesses to manage all their communication channels from a single interface.

---

## 📋 Current Sprint (February 2026)

### In Progress 🔄

| ID | Feature | Priority | Status | Notes |
|----|---------|----------|--------|-------|
| R-001 | Fix WebRTC ICE negotiation issues | HIGH | 🔄 In Progress | Docker NAT causing 30s delay |
| R-002 | Add TURN server support | HIGH | 🔄 In Progress | Required for NAT traversal |
| R-003 | Improve GraphQL error handling | MEDIUM | ✅ Done | 400 errors now return proper messages |
| R-004 | SSH fallback for PBX sync | MEDIUM | ✅ Done | When GraphQL auth fails |

### Completed ✅

| ID | Feature | Completed Date |
|----|---------|----------------|
| R-003 | GraphQL 400 error handling | Feb 17, 2026 |
| R-004 | SSH fallback sync method | Feb 17, 2026 |
| R-005 | Workspace sidebar ordering | Feb 17, 2026 |
| R-006 | Port configuration (8001/9001) | Feb 17, 2026 |

---

## 🚀 Short-term Roadmap (Q1 2026)

### February 2026
- [x] WebRTC softphone v2 release
- [x] OpenMeetings integration
- [x] Omni-channel messaging (WhatsApp, Telegram)
- [ ] TURN server integration for WebRTC
- [ ] ICE candidate optimization
- [ ] Call quality monitoring

### March 2026
- [ ] Facebook Messenger integration
- [ ] Viber integration
- [ ] Advanced IVR builder UI
- [ ] Call queue management
- [ ] Agent break/pause management

---

## 📅 Mid-term Roadmap (Q2-Q3 2026)

### Q2 2026
| Feature | Description | Priority |
|---------|-------------|----------|
| AI Call Transcription | Real-time speech-to-text | HIGH |
| AI Sentiment Analysis | Analyze call sentiment | HIGH |
| Voice Bot Integration | Basic IVR with AI | MEDIUM |
| Call Center Supervisor | Advanced monitoring | MEDIUM |
| WebRTC Recording | Client-side recording | LOW |

### Q3 2026
| Feature | Description | Priority |
|---------|-------------|----------|
| Predictive Dialer | Auto-dial campaigns | HIGH |
| Screen Recording | Record agent screens | MEDIUM |
| Quality Assurance | Call scoring system | MEDIUM |
| Custom Integrations | Webhook builder | MEDIUM |
| Mobile App | React Native softphone | LOW |

---

## 🔮 Long-term Vision (2027+)

### AI-Powered Features
- [ ] AI-powered call routing based on sentiment
- [ ] Automatic call summarization
- [ ] Real-time translation during calls
- [ ] Voice biometrics authentication
- [ ] Conversational AI bot

### Platform Expansion
- [ ] Multi-tenant SaaS deployment
- [ ] Kubernetes helm charts
- [ ] White-label customization
- [ ] Partner/reseller portal
- [ ] API marketplace

### Enterprise Features
- [ ] High availability clustering
- [ ] Geographic redundancy
- [ ] Compliance recording (PCI-DSS, HIPAA)
- [ ] Advanced analytics with ML
- [ ] Custom report builder

---

## 💡 Proposals & Ideas

### Community Suggestions

| ID | Proposal | Submitted By | Status | Discussion |
|----|----------|--------------|--------|------------|
| P-001 | Add RingCentral integration | - | 📝 Review | Evaluate API |
| P-002 | Microsoft Teams connector | - | 📝 Review | Direct Routing |
| P-003 | Zoom integration | - | 📝 Review | Zoom Phone API |
| P-004 | HubSpot CRM sync | - | 📝 Review | Webhook-based |
| P-005 | Salesforce integration | - | 📝 Review | REST API |

### Technical Debt

| ID | Issue | Priority | Effort |
|----|-------|----------|--------|
| TD-001 | Upgrade JsSIP to latest | LOW | 2 days |
| TD-002 | Refactor call state machine | MEDIUM | 1 week |
| TD-003 | Add TypeScript to frontend | LOW | 2 weeks |
| TD-004 | Improve test coverage (>80%) | HIGH | 2 weeks |
| TD-005 | Performance optimization | MEDIUM | 1 week |

### Architecture Improvements

| ID | Improvement | Impact | Status |
|----|-------------|--------|--------|
| A-001 | Separate WebSocket service | HIGH | 📝 Planned |
| A-002 | Event-driven architecture | HIGH | 📝 Planned |
| A-003 | Microservices for recording | MEDIUM | 📝 Planned |
| A-004 | CDN for static assets | LOW | 📝 Planned |

---

## 🐛 Known Issues

### Critical
| Issue | Description | Workaround |
|-------|-------------|------------|
| ICE-001 | WebRTC 30s delay in Docker | Pre-grant mic, use TURN |
| AUTH-001 | FreePBX GraphQL 401 | SSH fallback implemented |

### High Priority
| Issue | Description | Status |
|-------|-------------|--------|
| CALL-001 | Incoming calls disconnect early | Investigating |
| REC-001 | Recording playback CORS | Configure CDN headers |

### Medium Priority
| Issue | Description | Status |
|-------|-------------|--------|
| UI-001 | Softphone modal z-index | CSS fix needed |
| WS-001 | WebSocket reconnection | Auto-reconnect added |

---

## 📊 Metrics & Goals

### Q1 2026 Targets
| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | ~40% | 80% |
| API Response Time | 500ms | <200ms |
| Call Setup Time | ~30s | <3s |
| Documentation | 60% | 100% |
| User Satisfaction | - | 4.5/5 |

---

## 📝 How to Submit Proposals

1. **Open an Issue** on GitHub with `[PROPOSAL]` prefix
2. **Use Template:**
   ```
   ## Summary
   Brief description
   
   ## Problem
   What problem does this solve?
   
   ## Solution
   Proposed solution
   
   ## Impact
   Who benefits?
   
   ## Effort Estimate
   Time/resources needed
   ```
3. **Discussion** - Community feedback period
4. **Review** - Maintainers review
5. **Decision** - Accept/Reject/Modify

---

## 🔄 Update Log

| Date | Changes |
|------|---------|
| Feb 17, 2026 | Initial roadmap created |
| Feb 17, 2026 | Added SSH fallback, workspace updates |
| Feb 17, 2026 | Added known issues section |

---

*This document is maintained actively. Submit proposals via GitHub Issues.*
