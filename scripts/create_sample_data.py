#!/usr/bin/env python3

import frappe
import random
from frappe.utils import today, add_days, now_datetime
from datetime import datetime, timedelta

def execute():
    # Connect to site
    frappe.connect()
    
    # Create some basic call logs
    phone_numbers = [
        "+966501234567", "+966507654321", "+966512345678", 
        "+966508765432", "+966511111111", "+966522222222",
        "+966533333333"
    ]
    
    extensions = ["1001", "1002", "1003"]
    call_types = ["inbound", "outbound", "internal"]
    statuses = ["answered", "missed", "busy"]
    
    # Create 20 sample call logs
    for i in range(20):
        call_log = frappe.new_doc("CC Universal Call Log")
        call_log.call_id = f"CALL-{i+1:04d}"
        call_log.caller_number = random.choice(phone_numbers)
        call_log.called_number = random.choice(extensions)
        call_log.call_type = random.choice(call_types)
        call_log.call_status = random.choice(statuses)
        
        # Random date within last 7 days
        days_back = random.randint(0, 6)
        call_date = add_days(today(), -days_back)
        call_log.call_date = call_date
        
        # Random time
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)
        call_log.start_time = datetime.combine(call_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # Duration (0-300 seconds for answered calls)
        if call_log.call_status == "answered":
            duration = random.randint(30, 300)
        else:
            duration = 0
            
        call_log.call_duration = duration
        if duration > 0:
            call_log.end_time = call_log.start_time + timedelta(seconds=duration)
        
        call_log.insert()
        
    print(f"Created 20 sample call logs")
    
    # Create some sentiment logs
    sentiments = ["positive", "negative", "neutral"]
    for i in range(10):
        sentiment = frappe.new_doc("CC Sentiment Log")
        sentiment.call_id = f"CALL-{i+1:04d}"
        sentiment.sentiment = random.choice(sentiments)
        sentiment.confidence_score = round(random.uniform(0.7, 0.99), 2)
        sentiment.analysis_text = f"Sentiment analysis for call {i+1}"
        sentiment.insert()
    
    print(f"Created 10 sentiment records")
    
    frappe.db.commit()
    print("✅ Sample data created successfully!")
    print("Refresh your ContactCall workspace to see the data!")

if __name__ == "__main__":
    execute()