// Copyright (c) 2024, Arkan Lab — https://arkan.it.com
// License: MIT

frappe.pages["arrowz-about"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("About Arrowz"),
        single_column: true,
    });

    page.main.addClass("arrowz-about-page");
    const $container = $('<div class="fv-about-container"></div>').appendTo(page.main);

    // Use frappe.visual.generator for premium rendering
    const renderWithGenerator = async () => {
        try {
            await frappe.visual.generator.aboutPage(
                $container[0],
                "arrowz",
                {
                    color: "#2563EB",
                    mainDoctype: "AZ Extension",
                    features: [
        {
                "icon": "phone-call",
                "title": "WebRTC Softphone",
                "description": "Browser-based VoIP calling with JsSIP, call transfer, hold, and recording."
        },
        {
                "icon": "brand-whatsapp",
                "title": "Omni-Channel Messaging",
                "description": "WhatsApp Cloud API and Telegram Bot integration with unified inbox."
        },
        {
                "icon": "video",
                "title": "Video Conferencing",
                "description": "OpenMeetings integration with room management and recording."
        },
        {
                "icon": "router",
                "title": "Network Management",
                "description": "MikroTik RouterOS management \u2014 interfaces, WiFi, firewall, VPN, bandwidth."
        },
        {
                "icon": "server",
                "title": "PBX Integration",
                "description": "FreePBX/Asterisk AMI integration for extension management and call routing."
        },
        {
                "icon": "wifi",
                "title": "WiFi Management",
                "description": "Hotspot, RADIUS, access point management with bandwidth control."
        },
        {
                "icon": "shield-lock",
                "title": "Firewall & VPN",
                "description": "Firewall rules, NAT, VPN tunnels, and IP accounting via device providers."
        },
        {
                "icon": "chart-bar",
                "title": "Monitoring & Billing",
                "description": "Real-time device monitoring, bandwidth usage tracking, and billing integration."
        }
],
                    roles: [
        {
                "name": "AZ Admin",
                "icon": "shield-check",
                "description": "Full system configuration and user management."
        },
        {
                "name": "AZ Call Manager",
                "icon": "phone-call",
                "description": "Call monitoring, CDR access, and extension management."
        },
        {
                "name": "AZ Network Admin",
                "icon": "router",
                "description": "Network device configuration, firewall, and VPN management."
        },
        {
                "name": "AZ Agent",
                "icon": "headset",
                "description": "Make/receive calls, handle omni-channel conversations."
        }
],
                    ctas: [
                        { label: __("Start Onboarding"), route: "arrowz-onboarding", primary: true },
                        { label: __("Open Settings"), route: "app/arrowz-settings" },
                    ],
                }
            );
        } catch(e) {
            console.warn("Generator failed, using fallback:", e);
            renderFallback($container);
        }
    };

    const renderFallback = ($el) => {
        $el.html(`
            <div style="text-align:center;padding:60px 20px">
                <h1 style="font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#2563EB,#333);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${__("Arrowz")}</h1>
                <p style="font-size:1.15rem;color:var(--text-muted);max-width:600px;margin:16px auto">${__("Browser-based VoIP calling with JsSIP, call transfer, hold, and recording.")}</p>
                <div style="margin-top:24px">
                    <a href="/app/arrowz-onboarding" class="btn btn-primary btn-lg">${__("Start Onboarding")}</a>
                </div>
            </div>
        `);
    };

    if (frappe.visual && frappe.visual.generator) {
        renderWithGenerator();
    } else {
        frappe.require("frappe_visual.bundle.js", () => {
            if (frappe.visual && frappe.visual.generator) {
                renderWithGenerator();
            } else {
                renderFallback($container);
            }
        });
    }
};
