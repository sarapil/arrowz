// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Arrowz Box", {
  refresh: function (frm) {
    // ── Connection Test Button ──
    frm.add_custom_button(
      __("Test Connection"),
      function () {
        frappe.call({
          method: "test_connection",
          doc: frm.doc,
          freeze: true,
          freeze_message: __("Testing connection..."),
          callback: function (r) {
            if (r.message && r.message.status === "success") {
              frappe.show_alert(
                { message: __("Connection successful!"), indicator: "green" },
                5
              );
            } else {
              frappe.show_alert(
                {
                  message: __(
                    "Connection failed: " +
                      (r.message ? r.message.message : "Unknown error")
                  ),
                  indicator: "red",
                },
                7
              );
            }
            frm.reload_doc();
          },
        });
      },
      __("Actions")
    );

    // ── Push Full Config ──
    frm.add_custom_button(
      __("Push Config"),
      function () {
        frappe.confirm(
          __(
            "This will push the full compiled configuration to the device. Continue?"
          ),
          function () {
            frappe.call({
              method: "push_full_config",
              doc: frm.doc,
              freeze: true,
              freeze_message: __("Pushing configuration..."),
              callback: function (r) {
                if (r.message && r.message.status === "success") {
                  frappe.show_alert(
                    {
                      message: __("Config pushed successfully!"),
                      indicator: "green",
                    },
                    5
                  );
                } else {
                  frappe.show_alert(
                    { message: __("Push failed"), indicator: "red" },
                    7
                  );
                }
                frm.reload_doc();
              },
            });
          }
        );
      },
      __("Actions")
    );

    // ── Sync Buttons ──
    frm.add_custom_button(
      __("Pull from Device"),
      function () {
        frappe.confirm(
          __(
            "Pull device configuration into Frappe? New records may be created."
          ),
          function () {
            frappe.call({
              method: "sync_pull",
              doc: frm.doc,
              freeze: true,
              freeze_message: __("Pulling configuration from device..."),
              callback: function (r) {
                if (r.message) {
                  _show_sync_results(r.message, "Pull");
                }
                frm.reload_doc();
              },
            });
          }
        );
      },
      __("Sync")
    );

    frm.add_custom_button(
      __("Push to Device"),
      function () {
        frappe.confirm(
          __("Push Frappe configuration to the device? Device config will be overwritten."),
          function () {
            frappe.call({
              method: "sync_push",
              doc: frm.doc,
              freeze: true,
              freeze_message: __("Pushing configuration to device..."),
              callback: function (r) {
                if (r.message) {
                  _show_sync_results(r.message, "Push");
                }
                frm.reload_doc();
              },
            });
          }
        );
      },
      __("Sync")
    );

    frm.add_custom_button(
      __("Show Diff"),
      function () {
        frappe.call({
          method: "sync_diff",
          doc: frm.doc,
          freeze: true,
          freeze_message: __("Comparing configurations..."),
          callback: function (r) {
            if (r.message) {
              _show_diff_dialog(r.message);
            }
          },
        });
      },
      __("Sync")
    );

    // ── Get Device Config (preview) ──
    if (frm.doc.device_type === "MikroTik") {
      frm.add_custom_button(
        __("View Device Config"),
        function () {
          frappe.call({
            method: "get_device_config",
            doc: frm.doc,
            freeze: true,
            freeze_message: __("Reading device configuration..."),
            callback: function (r) {
              if (r.message) {
                let d = new frappe.ui.Dialog({
                  title: __("Device Configuration"),
                  size: "extra-large",
                  fields: [
                    {
                      fieldname: "config_html",
                      fieldtype: "HTML",
                    },
                  ],
                });

                let html = '<div style="max-height: 500px; overflow-y: auto;">';
                for (let section in r.message) {
                  if (section.startsWith("_")) continue;
                  let data = r.message[section];
                  let count = Array.isArray(data)
                    ? data.length
                    : typeof data === "object"
                      ? Object.keys(data).length
                      : 0;
                  html += `<h5 style="margin-top: 10px;">${section} (${count})</h5>`;
                  html += `<pre style="font-size: 11px; max-height: 200px; overflow-y: auto; background: var(--bg-color);">${JSON.stringify(data, null, 2)}</pre>`;
                }
                html += "</div>";

                d.fields_dict.config_html.$wrapper.html(html);
                d.show();
              }
            },
          });
        },
        __("Actions")
      );
    }

    // ── Telemetry ── (Linux only)
    if (frm.doc.device_type !== "MikroTik") {
      frm.add_custom_button(
        __("Sync Telemetry"),
        function () {
          frappe.call({
            method: "sync_telemetry",
            doc: frm.doc,
            freeze: true,
            freeze_message: __("Pulling telemetry..."),
            callback: function (r) {
              if (r.message && r.message.status === "success") {
                frappe.show_alert(
                  {
                    message: __("Telemetry synced successfully"),
                    indicator: "green",
                  },
                  5
                );
              }
              frm.reload_doc();
            },
          });
        },
        __("Actions")
      );
    }

    // ── Generate Token ──
    frm.add_custom_button(
      __("Generate API Token"),
      function () {
        frappe.confirm(
          __(
            "Generate a new API token? The old token will stop working."
          ),
          function () {
            frappe.call({
              method: "generate_api_token",
              doc: frm.doc,
              callback: function (r) {
                if (r.message && r.message.token) {
                  let d = new frappe.ui.Dialog({
                    title: __("New API Token"),
                    fields: [
                      {
                        fieldname: "token",
                        fieldtype: "Code",
                        label: __("Token"),
                        default: r.message.token,
                        read_only: 1,
                      },
                    ],
                    primary_action_label: __("Copy & Close"),
                    primary_action: function () {
                      navigator.clipboard.writeText(r.message.token);
                      frappe.show_alert(
                        {
                          message: __("Token copied to clipboard"),
                          indicator: "green",
                        },
                        3
                      );
                      d.hide();
                    },
                  });
                  d.show();
                }
                frm.reload_doc();
              },
            });
          }
        );
      },
      __("Actions")
    );

    // ── Status Indicator ──
    _set_status_indicator(frm);
  },

  device_type: function (frm) {
    // Auto-set default API port based on device type
    if (frm.doc.device_type === "MikroTik") {
      if (!frm.doc.mikrotik_api_port) {
        frm.set_value(
          "mikrotik_api_port",
          frm.doc.mikrotik_use_ssl ? 8729 : 8728
        );
      }
    }
  },

  mikrotik_use_ssl: function (frm) {
    if (frm.doc.device_type === "MikroTik") {
      frm.set_value(
        "mikrotik_api_port",
        frm.doc.mikrotik_use_ssl ? 8729 : 8728
      );
    }
  },
});

function _set_status_indicator(frm) {
  let indicator_map = {
    Online: "green",
    Offline: "red",
    Degraded: "orange",
    Maintenance: "blue",
  };

  let color = indicator_map[frm.doc.status] || "grey";
  frm.page.set_indicator(frm.doc.status || "Unknown", color);
}

function _show_sync_results(results, direction) {
  let messages = [];

  if (results.status) {
    let indicator = results.status === "success" ? "green" : "red";
    frappe.show_alert(
      { message: __("{0} {1}", [direction, results.status]), indicator: indicator },
      5
    );
  }

  // Show per-section results
  for (let section in results) {
    if (section === "status" || section === "errors" || section === "results")
      continue;
    let data = results[section];
    if (typeof data === "object" && data !== null) {
      let created = data.created || 0;
      let updated = data.updated || 0;
      if (created || updated) {
        messages.push(`${section}: ${created} created, ${updated} updated`);
      }
    }
  }

  if (messages.length) {
    frappe.msgprint(
      messages.join("<br>"),
      __("{0} Results", [direction])
    );
  }
}

function _show_diff_dialog(diff) {
  let d = new frappe.ui.Dialog({
    title: __("Configuration Diff"),
    size: "large",
    fields: [
      {
        fieldname: "diff_html",
        fieldtype: "HTML",
      },
    ],
  });

  let html = '<div style="max-height: 500px; overflow-y: auto;">';

  for (let section in diff) {
    let data = diff[section];
    let only_frappe = data.only_in_frappe || [];
    let only_device = data.only_in_device || [];
    let different = data.different || [];
    let identical = data.identical || 0;

    html += `<h5 style="margin-top: 15px;">${section}</h5>`;
    html += `<p>Identical: ${identical} | `;
    html += `Only in Frappe: <span style="color: var(--text-on-blue)">${only_frappe.length}</span> | `;
    html += `Only in Device: <span style="color: var(--text-on-orange)">${only_device.length}</span> | `;
    html += `Different: <span style="color: var(--text-on-red)">${different.length}</span></p>`;

    if (only_frappe.length) {
      html += `<div class="text-muted">In Frappe only: ${only_frappe.join(", ")}</div>`;
    }
    if (only_device.length) {
      html += `<div class="text-muted">In Device only: ${only_device.join(", ")}</div>`;
    }
    if (different.length) {
      html += `<pre style="font-size: 11px; max-height: 150px; overflow-y: auto;">${JSON.stringify(different, null, 2)}</pre>`;
    }
  }

  html += "</div>";
  d.fields_dict.diff_html.$wrapper.html(html);
  d.show();
}
