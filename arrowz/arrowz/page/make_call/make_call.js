// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Make Call Page
 * Beautiful dialer interface with gradient design
 */

frappe.pages['make-call'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Make Call'),
        single_column: true
    });
    
    wrapper.classList.add('arrowz-make-call-page');
    wrapper.make_call = new ArrowzMakeCall(page);
};

class ArrowzMakeCall {
    constructor(page) {
        this.page = page;
        this.phone_number = '';
        this.init();
    }
    
    init() {
        this.add_styles();
        this.render_layout();
        this.setup_events();
        this.load_recent_contacts();
    }
    
    add_styles() {
        if (document.getElementById('arrowz-make-call-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'arrowz-make-call-styles';
        styles.textContent = `
            .arrowz-make-call-page .page-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: calc(100vh - 60px);
            }
            
            .az-dialer {
                display: flex;
                justify-content: center;
                padding: 40px 20px;
            }
            
            .az-dialer-container {
                background: white;
                border-radius: 32px;
                padding: 40px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            
            .az-dialer-header {
                text-align: center;
                margin-bottom: 32px;
            }
            
            .az-dialer-header img {
                width: 64px;
                height: 64px;
                margin-bottom: 16px;
            }
            
            .az-dialer-header h2 {
                margin: 0;
                font-size: 24px;
                color: #1a1a2e;
            }
            
            .az-phone-display {
                background: linear-gradient(135deg, #f5f7fa 0%, #e8ebed 100%);
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                margin-bottom: 24px;
                min-height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .az-phone-number {
                font-size: 32px;
                font-weight: 300;
                color: #1a1a2e;
                letter-spacing: 2px;
                word-break: break-all;
            }
            
            .az-phone-number.empty {
                font-size: 18px;
                color: #999;
            }
            
            .az-keypad {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 24px;
            }
            
            .az-key {
                aspect-ratio: 1.2;
                border: none;
                border-radius: 16px;
                background: linear-gradient(135deg, #f5f7fa 0%, #e8ebed 100%);
                font-size: 28px;
                font-weight: 500;
                color: #1a1a2e;
                cursor: pointer;
                transition: all 0.15s ease;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            
            .az-key:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                transform: scale(1.05);
            }
            
            .az-key:active {
                transform: scale(0.95);
            }
            
            .az-key-letters {
                font-size: 10px;
                opacity: 0.5;
                margin-top: 2px;
                letter-spacing: 1px;
            }
            
            .az-call-actions {
                display: flex;
                justify-content: center;
                gap: 16px;
            }
            
            .az-action-btn {
                width: 72px;
                height: 72px;
                border: none;
                border-radius: 50%;
                font-size: 28px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .az-action-btn:hover {
                transform: scale(1.1);
            }
            
            .az-action-btn.call {
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                color: white;
                box-shadow: 0 8px 20px rgba(67, 233, 123, 0.4);
            }
            
            .az-action-btn.delete {
                background: linear-gradient(135deg, #f5f7fa 0%, #e8ebed 100%);
                color: #666;
            }
            
            .az-action-btn.clear {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);
                color: white;
            }
            
            /* Recent Contacts */
            .az-recent-section {
                margin-top: 32px;
                padding-top: 24px;
                border-top: 1px solid #f0f0f0;
            }
            
            .az-recent-title {
                font-size: 14px;
                color: #666;
                margin-bottom: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .az-recent-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .az-recent-item {
                display: flex;
                align-items: center;
                padding: 12px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .az-recent-item:hover {
                background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
            }
            
            .az-recent-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                margin-right: 12px;
            }
            
            .az-recent-info {
                flex: 1;
            }
            
            .az-recent-name {
                font-weight: 500;
                color: #1a1a2e;
            }
            
            .az-recent-phone {
                font-size: 12px;
                color: #999;
            }
            
            .az-recent-call-btn {
                width: 36px;
                height: 36px;
                border: none;
                border-radius: 50%;
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }
        `;
        document.head.appendChild(styles);
    }
    
    render_layout() {
        this.$container = $(`
            <div class="az-dialer">
                <div class="az-dialer-container">
                    <div class="az-dialer-header">
                        <img src="/assets/arrowz/images/arrowz-icon-animated.svg" alt="Arrowz">
                        <h2>${__('Make a Call')}</h2>
                    </div>
                    
                    <div class="az-phone-display">
                        <span class="az-phone-number empty">${__('Enter phone number')}</span>
                    </div>
                    
                    <div class="az-keypad">
                        <button class="az-key" data-digit="1">1<span class="az-key-letters">&nbsp;</span></button>
                        <button class="az-key" data-digit="2">2<span class="az-key-letters">ABC</span></button>
                        <button class="az-key" data-digit="3">3<span class="az-key-letters">DEF</span></button>
                        <button class="az-key" data-digit="4">4<span class="az-key-letters">GHI</span></button>
                        <button class="az-key" data-digit="5">5<span class="az-key-letters">JKL</span></button>
                        <button class="az-key" data-digit="6">6<span class="az-key-letters">MNO</span></button>
                        <button class="az-key" data-digit="7">7<span class="az-key-letters">PQRS</span></button>
                        <button class="az-key" data-digit="8">8<span class="az-key-letters">TUV</span></button>
                        <button class="az-key" data-digit="9">9<span class="az-key-letters">WXYZ</span></button>
                        <button class="az-key" data-digit="*">*</button>
                        <button class="az-key" data-digit="0">0<span class="az-key-letters">+</span></button>
                        <button class="az-key" data-digit="#">#</button>
                    </div>
                    
                    <div class="az-call-actions">
                        <button class="az-action-btn clear" title="${__('Clear')}">✕</button>
                        <button class="az-action-btn call" title="${__('Call')}">📞</button>
                        <button class="az-action-btn delete" title="${__('Delete')}">⌫</button>
                    </div>
                    
                    <div class="az-recent-section">
                        <div class="az-recent-title">${__('Recent Contacts')}</div>
                        <div class="az-recent-list">
                            <p class="text-center text-muted">${__('Loading...')}</p>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
    }
    
    setup_events() {
        // Keypad clicks
        this.$container.find('.az-key').on('click', (e) => {
            const digit = $(e.currentTarget).data('digit');
            this.add_digit(digit);
            this.play_tone(digit);
        });
        
        // Long press on 0 for +
        let pressTimer;
        this.$container.find('.az-key[data-digit="0"]').on('mousedown touchstart', () => {
            pressTimer = setTimeout(() => {
                this.add_digit('+');
            }, 500);
        }).on('mouseup touchend mouseleave', () => {
            clearTimeout(pressTimer);
        });
        
        // Call button
        this.$container.find('.az-action-btn.call').on('click', () => {
            this.make_call();
        });
        
        // Delete button
        this.$container.find('.az-action-btn.delete').on('click', () => {
            this.delete_digit();
        });
        
        // Clear button
        this.$container.find('.az-action-btn.clear').on('click', () => {
            this.clear_number();
        });
        
        // Keyboard support
        $(document).on('keydown.make-call', (e) => {
            if (e.key >= '0' && e.key <= '9') {
                this.add_digit(e.key);
            } else if (e.key === '*' || e.key === '#') {
                this.add_digit(e.key);
            } else if (e.key === '+') {
                this.add_digit('+');
            } else if (e.key === 'Backspace') {
                this.delete_digit();
            } else if (e.key === 'Enter') {
                this.make_call();
            } else if (e.key === 'Escape') {
                this.clear_number();
            }
        });
    }
    
    add_digit(digit) {
        this.phone_number += digit;
        this.update_display();
    }
    
    delete_digit() {
        this.phone_number = this.phone_number.slice(0, -1);
        this.update_display();
    }
    
    clear_number() {
        this.phone_number = '';
        this.update_display();
    }
    
    update_display() {
        const $display = this.$container.find('.az-phone-number');
        if (this.phone_number) {
            $display.removeClass('empty').text(this.phone_number);
        } else {
            $display.addClass('empty').text(__('Enter phone number'));
        }
    }
    
    play_tone(digit) {
        // Optional: Play DTMF tone
        try {
            if (typeof arrowz !== 'undefined' && arrowz.softphone && arrowz.softphone.playDTMF) {
                arrowz.softphone.playDTMF(digit);
            }
        } catch (e) {}
    }
    
    make_call() {
        if (!this.phone_number) {
            frappe.show_alert({ message: __('Please enter a phone number'), indicator: 'orange' });
            return;
        }
        
        // Try to use softphone if available
        if (typeof arrowz !== 'undefined' && arrowz.softphone) {
            arrowz.softphone.call(this.phone_number);
        } else {
            // Fallback: Use click-to-call API
            frappe.call({
                method: 'arrowz.api.call_log.initiate_call',
                args: { phone_number: this.phone_number },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: __('Call initiated'), indicator: 'green' });
                        this.clear_number();
                    } else {
                        frappe.show_alert({ 
                            message: r.message?.error || __('Failed to initiate call'), 
                            indicator: 'red' 
                        });
                    }
                }
            });
        }
    }
    
    async load_recent_contacts() {
        try {
            const r = await frappe.call({
                method: 'arrowz.api.agent.get_recent_contacts',
                args: { limit: 5 }
            });
            
            this.render_recent_contacts(r.message || []);
        } catch (e) {
            console.error('Error loading contacts:', e);
            this.render_recent_contacts([]);
        }
    }
    
    render_recent_contacts(contacts) {
        const $list = this.$container.find('.az-recent-list').empty();
        
        if (!contacts.length) {
            $list.html(`<p class="text-center text-muted">${__('No recent contacts')}</p>`);
            return;
        }
        
        contacts.forEach(contact => {
            const initials = (contact.name || contact.phone || 'U').charAt(0).toUpperCase();
            
            $list.append(`
                <div class="az-recent-item" data-phone="${contact.phone}">
                    <div class="az-recent-avatar">${initials}</div>
                    <div class="az-recent-info">
                        <div class="az-recent-name">${contact.name || __('Unknown')}</div>
                        <div class="az-recent-phone">${contact.phone}</div>
                    </div>
                    <button class="az-recent-call-btn">📞</button>
                </div>
            `);
        });
        
        // Click on recent contact
        $list.find('.az-recent-item').on('click', (e) => {
            const phone = $(e.currentTarget).data('phone');
            this.phone_number = phone;
            this.update_display();
        });
        
        // Quick call button
        $list.find('.az-recent-call-btn').on('click', (e) => {
            e.stopPropagation();
            const phone = $(e.currentTarget).closest('.az-recent-item').data('phone');
            this.phone_number = phone;
            this.make_call();
        });
    }
    
    destroy() {
        $(document).off('keydown.make-call');
    }
}
