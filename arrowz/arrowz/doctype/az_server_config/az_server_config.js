// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on('AZ Server Config', {
    refresh: function(frm) {
        // Test Connection button
        frm.add_custom_button(__('Test Connection'), function() {
            frappe.show_alert({message: __('Testing connection...'), indicator: 'blue'});
            frm.call('test_connection').then(r => {
                if (r.message.success) {
                    frappe.show_alert({message: r.message.message, indicator: 'green'});
                    frm.reload_doc();
                } else {
                    frappe.show_alert({message: r.message.message, indicator: 'red'});
                }
            });
        }, __('Actions'));
        
        // Test AMI Connection if enabled
        if (frm.doc.ami_enabled) {
            frm.add_custom_button(__('Test AMI'), function() {
                frappe.show_alert({message: __('Testing AMI connection...'), indicator: 'blue'});
                frm.call('test_ami_connection').then(r => {
                    if (r.message.success) {
                        frappe.show_alert({message: r.message.message, indicator: 'green'});
                    } else {
                        frappe.show_alert({message: r.message.message, indicator: 'red'});
                    }
                });
            }, __('Actions'));
        }
        
        // GraphQL/OAuth buttons if enabled
        if (frm.doc.graphql_enabled && frm.doc.graphql_client_id) {
            // Test GraphQL Connection
            frm.add_custom_button(__('Test GraphQL'), function() {
                frappe.show_alert({message: __('Testing GraphQL connection...'), indicator: 'blue'});
                frappe.call({
                    method: 'arrowz.freepbx_token.test_graphql_connection',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Testing GraphQL API...'),
                    callback: function(r) {
                        frm.reload_doc();
                        if (r.message.success) {
                            frappe.msgprint({
                                title: __('GraphQL Connection Successful'),
                                indicator: 'green',
                                message: __('Found {0} extensions. Token is valid.', [r.message.extensions_count])
                            });
                        } else {
                            frappe.msgprint({
                                title: __('GraphQL Connection Failed'),
                                indicator: 'red',
                                message: r.message.error
                            });
                        }
                    }
                });
            }, __('GraphQL'));
            
            // Refresh Token
            frm.add_custom_button(__('Refresh Token'), function() {
                frappe.confirm(
                    __('This will invalidate the current token and request a new one. Continue?'),
                    function() {
                        frappe.call({
                            method: 'arrowz.freepbx_token.refresh_token',
                            args: { server_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __('Refreshing OAuth Token...'),
                            callback: function(r) {
                                frm.reload_doc();
                                if (r.message.success) {
                                    frappe.show_alert({
                                        message: __('Token refreshed successfully!'),
                                        indicator: 'green'
                                    });
                                } else {
                                    frappe.msgprint({
                                        title: __('Token Refresh Failed'),
                                        indicator: 'red',
                                        message: r.message.error
                                    });
                                }
                            }
                        });
                    }
                );
            }, __('GraphQL'));
        }
        
        // Status indicator
        let status_color = 'gray';
        if (frm.doc.connection_status === 'Connected') {
            status_color = 'green';
        } else if (frm.doc.connection_status === 'Error') {
            status_color = 'red';
        }
        
        frm.page.set_indicator(__(frm.doc.connection_status || 'Unknown'), status_color);
        
        // Show token status in dashboard
        if (frm.doc.graphql_enabled && frm.doc.token_status) {
            frm.dashboard.add_indicator(__('Token: {0}', [frm.doc.token_status]), 
                frm.doc.token_status.includes('✅') ? 'green' : 'orange');
        }
        
        // ===== SSH Operations =====
        if (frm.doc.ssh_enabled) {
            // Test SSH Connection
            frm.add_custom_button(__('Test SSH'), function() {
                frappe.show_alert({message: __('Testing SSH connection...'), indicator: 'blue'});
                frappe.call({
                    method: 'arrowz.ssh_manager.test_ssh',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Connecting via SSH...'),
                    callback: function(r) {
                        frm.reload_doc();
                        if (r.message.success) {
                            frappe.msgprint({
                                title: __('SSH Connection Successful'),
                                indicator: 'green',
                                message: r.message.message
                            });
                        } else {
                            frappe.msgprint({
                                title: __('SSH Connection Failed'),
                                indicator: 'red',
                                message: r.message.message
                            });
                        }
                    }
                });
            }, __('SSH'));
            
            // Debug SSH Key (only show for RSA Key auth)
            if (frm.doc.ssh_auth_type === 'RSA Key') {
                frm.add_custom_button(__('Debug Key'), function() {
                    frappe.call({
                        method: 'arrowz.ssh_manager.ssh_debug_key',
                        args: { server_name: frm.doc.name },
                        freeze: true,
                        freeze_message: __('Analyzing SSH key...'),
                        callback: function(r) {
                            if (r.message.success) {
                                let data = r.message.data;
                                let html = `
                                    <h5>SSH Configuration</h5>
                                    <table class="table table-bordered">
                                        <tr><th>SSH Enabled</th><td>${data.ssh_enabled ? '✅' : '❌'}</td></tr>
                                        <tr><th>Auth Type</th><td>${data.ssh_auth_type}</td></tr>
                                        <tr><th>Host</th><td>${data.ssh_host}:${data.ssh_port}</td></tr>
                                        <tr><th>Username</th><td>${data.ssh_username}</td></tr>
                                        <tr><th>Has Private Key</th><td>${data.has_private_key ? '✅' : '❌'}</td></tr>
                                    </table>
                                `;
                                
                                if (data.key_info) {
                                    html += `
                                        <h5>Key Information</h5>
                                        <table class="table table-bordered">
                                            <tr><th>First Line</th><td><code>${data.key_info.first_line}</code></td></tr>
                                            <tr><th>Last Line</th><td><code>${data.key_info.last_line}</code></td></tr>
                                            <tr><th>Total Lines</th><td>${data.key_info.total_lines}</td></tr>
                                            <tr><th>Total Chars</th><td>${data.key_info.total_chars}</td></tr>
                                        </table>
                                    `;
                                }
                                
                                if (data.parse_results) {
                                    html += '<h5>Key Parsing Results</h5><table class="table table-bordered"><tr><th>Type</th><th>Status</th><th>Details</th></tr>';
                                    data.parse_results.forEach(p => {
                                        let status = p.success ? '<span class="text-success">✅ Success</span>' : '<span class="text-danger">❌ Failed</span>';
                                        let details = p.success ? `Fingerprint: ${p.fingerprint}` : p.error;
                                        html += `<tr><td>${p.type}</td><td>${status}</td><td>${details}</td></tr>`;
                                    });
                                    html += '</table>';
                                }
                                
                                if (data.key_valid) {
                                    html += `<div class="alert alert-success">✅ Key is valid (${data.key_type}). If SSH fails, ensure the public key is in <code>~/.ssh/authorized_keys</code> on the server.</div>`;
                                } else if (data.has_private_key) {
                                    html += '<div class="alert alert-danger">❌ Key could not be parsed. Check the key format.</div>';
                                }
                                
                                frappe.msgprint({
                                    title: __('SSH Key Debug Info'),
                                    indicator: data.key_valid ? 'green' : 'red',
                                    message: html
                                });
                            } else {
                                frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                            }
                        }
                    });
                }, __('SSH'));
            }
            
            // Get System Status
            frm.add_custom_button(__('System Status'), function() {
                frappe.call({
                    method: 'arrowz.ssh_manager.ssh_get_status',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Getting system status...'),
                    callback: function(r) {
                        if (r.message.success) {
                            let status = r.message.status;
                            let html = `
                                <table class="table table-bordered">
                                    <tr><th>Asterisk Version</th><td>${status.asterisk_version || 'N/A'}</td></tr>
                                    <tr><th>FreePBX Version</th><td>${status.freepbx_version || 'N/A'}</td></tr>
                                    <tr><th>Uptime</th><td>${status.uptime || 'N/A'}</td></tr>
                                    <tr><th>Channels</th><td>${status.channels_info || 'N/A'}</td></tr>
                                </table>
                            `;
                            frappe.msgprint({
                                title: __('FreePBX System Status'),
                                indicator: 'green',
                                message: html
                            });
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: r.message.message
                            });
                        }
                    }
                });
            }, __('SSH'));
            
            // List Trunks
            frm.add_custom_button(__('List Trunks'), function() {
                frappe.call({
                    method: 'arrowz.ssh_manager.ssh_get_trunks',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Loading trunks...'),
                    callback: function(r) {
                        if (r.message.success) {
                            let trunks = r.message.trunks || [];
                            if (trunks.length === 0) {
                                frappe.msgprint(__('No trunks found'));
                                return;
                            }
                            let html = '<table class="table table-bordered"><tr><th>ID</th><th>Name</th><th>Tech</th><th>Channel</th></tr>';
                            trunks.forEach(t => {
                                html += `<tr><td>${t.id}</td><td>${t.name}</td><td>${t.tech}</td><td>${t.channelid}</td></tr>`;
                            });
                            html += '</table>';
                            frappe.msgprint({
                                title: __('SIP Trunks ({0})', [trunks.length]),
                                indicator: 'blue',
                                message: html
                            });
                        } else {
                            frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                        }
                    }
                });
            }, __('SSH'));
            
            // Trunk Status
            frm.add_custom_button(__('Trunk Status'), function() {
                frappe.call({
                    method: 'arrowz.ssh_manager.ssh_get_trunk_status',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Getting trunk registration status...'),
                    callback: function(r) {
                        if (r.message.success) {
                            let regs = r.message.registrations || [];
                            if (regs.length === 0) {
                                frappe.msgprint(__('No trunk registrations found'));
                                return;
                            }
                            frappe.msgprint({
                                title: __('Trunk Registrations'),
                                indicator: 'blue',
                                message: '<pre>' + regs.join('\n') + '</pre>'
                            });
                        } else {
                            frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                        }
                    }
                });
            }, __('SSH'));
            
            // Active Calls
            frm.add_custom_button(__('Active Calls'), function() {
                frappe.call({
                    method: 'arrowz.ssh_manager.ssh_get_calls',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Getting active calls...'),
                    callback: function(r) {
                        if (r.message.success) {
                            let calls = r.message.calls || [];
                            if (calls.length === 0) {
                                frappe.msgprint({
                                    title: __('Active Calls'),
                                    indicator: 'green',
                                    message: __('No active calls at the moment')
                                });
                                return;
                            }
                            let html = '<table class="table table-bordered"><tr><th>Channel</th><th>Extension</th><th>State</th></tr>';
                            calls.forEach(c => {
                                html += `<tr><td>${c.channel}</td><td>${c.extension}</td><td>${c.state}</td></tr>`;
                            });
                            html += '</table>';
                            frappe.msgprint({
                                title: __('Active Calls ({0})', [calls.length]),
                                indicator: 'blue',
                                message: html
                            });
                        } else {
                            frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                        }
                    }
                });
            }, __('SSH'));
            
            // Reload Asterisk
            frm.add_custom_button(__('Reload (Apply Config)'), function() {
                frappe.confirm(
                    __('This will reload Asterisk configuration. Continue?'),
                    function() {
                        frappe.call({
                            method: 'arrowz.ssh_manager.ssh_reload',
                            args: { server_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __('Reloading Asterisk...'),
                            callback: function(r) {
                                if (r.message.success) {
                                    frappe.show_alert({message: __('Asterisk reloaded successfully!'), indicator: 'green'});
                                } else {
                                    frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                                }
                            }
                        });
                    }
                );
            }, __('SSH'));
            
            // Outbound Routes
            frm.add_custom_button(__('Outbound Routes'), function() {
                frappe.call({
                    method: 'arrowz.ssh_manager.ssh_get_routes',
                    args: { server_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('Loading outbound routes...'),
                    callback: function(r) {
                        if (r.message.success) {
                            let routes = r.message.routes || [];
                            if (routes.length === 0) {
                                frappe.msgprint(__('No outbound routes found'));
                                return;
                            }
                            let html = '<table class="table table-bordered"><tr><th>Seq</th><th>Name</th><th>Caller ID</th></tr>';
                            routes.forEach(rt => {
                                html += `<tr><td>${rt.sequence}</td><td>${rt.name}</td><td>${rt.caller_id || '-'}</td></tr>`;
                            });
                            html += '</table>';
                            frappe.msgprint({
                                title: __('Outbound Routes ({0})', [routes.length]),
                                indicator: 'blue',
                                message: html
                            });
                        } else {
                            frappe.msgprint({title: __('Error'), indicator: 'red', message: r.message.message});
                        }
                    }
                });
            }, __('SSH'));
        }
    },
    
    host: function(frm) {
        // Auto-build websocket URL
        if (frm.doc.host && !frm.doc.websocket_url) {
            const protocol = frm.doc.protocol === 'WSS' ? 'wss' : 'ws';
            const port = frm.doc.port || 8089;
            frm.set_value('websocket_url', `${protocol}://${frm.doc.host}:${port}/ws`);
        }
        
        // Auto-set SIP domain
        if (frm.doc.host && !frm.doc.sip_domain) {
            frm.set_value('sip_domain', frm.doc.host);
        }
        
        // Auto-set GraphQL URL
        if (frm.doc.host && !frm.doc.graphql_url) {
            frm.set_value('graphql_url', `https://${frm.doc.host}/admin/api/api/gql`);
        }
    },
    
    protocol: function(frm) {
        frm.trigger('host');
    },
    
    port: function(frm) {
        frm.trigger('host');
    },
    
    graphql_enabled: function(frm) {
        // Auto-fill GraphQL URL when enabled
        if (frm.doc.graphql_enabled && frm.doc.host && !frm.doc.graphql_url) {
            frm.set_value('graphql_url', `https://${frm.doc.host}/admin/api/api/gql`);
        }
    }
});
