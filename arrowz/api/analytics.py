# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Analytics API
Provides data for analytics dashboards and reports.
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, getdate, flt


@frappe.whitelist()
def get_analytics(date_range="today"):
    """
    Get analytics data for dashboard.
    
    Args:
        date_range: 'today', 'week', 'month', 'year'
    
    Returns:
        dict with total_calls, avg_duration, avg_wait_time, chart_data
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    # Calculate date range
    if date_range == "today":
        from_date = today()
        to_date = today()
    elif date_range == "week":
        from_date = add_days(today(), -7)
        to_date = today()
    elif date_range == "month":
        from_date = add_days(today(), -30)
        to_date = today()
    elif date_range == "year":
        from_date = add_days(today(), -365)
        to_date = today()
    else:
        from_date = today()
        to_date = today()
    
    # Get total calls
    total_calls = frappe.db.count("AZ Call Log", {
        "start_time": ["between", [from_date, add_days(to_date, 1)]]
    }) or 0
    
    # Get average duration
    avg_duration_result = frappe.db.sql("""
        SELECT AVG(duration) as avg_duration
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
    """, (from_date, to_date), as_dict=True)
    
    avg_duration = flt(avg_duration_result[0].avg_duration if avg_duration_result else 0)
    
    # Get average wait time (ring duration)
    avg_wait_result = frappe.db.sql("""
        SELECT AVG(ring_duration) as avg_wait
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        AND ring_duration IS NOT NULL
    """, (from_date, to_date), as_dict=True)
    
    avg_wait_time = flt(avg_wait_result[0].avg_wait if avg_wait_result else 0)
    
    # Get chart data (daily breakdown)
    chart_data = frappe.db.sql("""
        SELECT 
            DATE(start_time) as date,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        GROUP BY DATE(start_time)
        ORDER BY date
    """, (from_date, to_date), as_dict=True)
    
    return {
        "total_calls": total_calls,
        "avg_duration": avg_duration,
        "avg_wait_time": avg_wait_time,
        "chart_data": chart_data
    }


@frappe.whitelist()
def get_daily_trend(from_date=None, to_date=None):
    """
    Get daily call trend data.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not from_date:
        from_date = add_days(today(), -30)
    if not to_date:
        to_date = today()
    
    data = frappe.db.sql("""
        SELECT 
            DATE(start_time) as date,
            direction,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        GROUP BY DATE(start_time), direction
        ORDER BY date
    """, (from_date, to_date), as_dict=True)
    
    # Process into series
    dates = []
    inbound = []
    outbound = []
    
    current_date = getdate(from_date)
    end_date = getdate(to_date)
    
    date_data = {}
    for row in data:
        date_str = str(row.date)
        if date_str not in date_data:
            date_data[date_str] = {"inbound": 0, "outbound": 0}
        
        if row.direction == "Inbound":
            date_data[date_str]["inbound"] = row.count
        elif row.direction == "Outbound":
            date_data[date_str]["outbound"] = row.count
    
    while current_date <= end_date:
        date_str = str(current_date)
        dates.append(date_str)
        
        day_data = date_data.get(date_str, {"inbound": 0, "outbound": 0})
        inbound.append(day_data["inbound"])
        outbound.append(day_data["outbound"])
        
        current_date = add_days(current_date, 1)
    
    return {
        "dates": dates,
        "inbound": inbound,
        "outbound": outbound
    }


@frappe.whitelist()
def get_disposition_breakdown(from_date=None, to_date=None):
    """
    Get call disposition breakdown.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not from_date:
        from_date = today()
    if not to_date:
        to_date = today()
    
    data = frappe.db.sql("""
        SELECT 
            COALESCE(disposition, 'Unknown') as disposition,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        GROUP BY disposition
        ORDER BY count DESC
    """, (from_date, to_date), as_dict=True)
    
    return data


@frappe.whitelist()
def get_agent_performance(from_date=None, to_date=None):
    """
    Get performance metrics by agent.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not from_date:
        from_date = today()
    if not to_date:
        to_date = today()
    
    data = frappe.db.sql("""
        SELECT 
            extension,
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered,
            SUM(CASE WHEN status = 'Missed' THEN 1 ELSE 0 END) as missed,
            AVG(CASE WHEN duration > 0 THEN duration ELSE NULL END) as avg_duration,
            AVG(sentiment_score) as avg_sentiment
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        AND extension IS NOT NULL
        GROUP BY extension
        ORDER BY total_calls DESC
    """, (from_date, to_date), as_dict=True)
    
    # Enrich with agent info
    for row in data:
        ext_info = frappe.db.get_value(
            "AZ Extension",
            {"extension": row.extension},
            ["display_name", "user"],
            as_dict=True
        )
        
        if ext_info:
            row.display_name = ext_info.display_name
            if ext_info.user:
                row.full_name = frappe.db.get_value("User", ext_info.user, "full_name")
    
    return data


@frappe.whitelist()
def get_hourly_heatmap(from_date=None, to_date=None):
    """
    Get hourly activity data for heatmap.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not from_date:
        from_date = add_days(today(), -7)
    if not to_date:
        to_date = today()
    
    data = frappe.db.sql("""
        SELECT 
            DAYOFWEEK(start_time) as day_of_week,
            HOUR(start_time) as hour,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        GROUP BY DAYOFWEEK(start_time), HOUR(start_time)
    """, (from_date, to_date), as_dict=True)
    
    # Build matrix (7 days x 24 hours)
    matrix = [[0] * 24 for _ in range(7)]
    
    for row in data:
        # MySQL DAYOFWEEK returns 1=Sunday, 7=Saturday
        # Convert to 0=Monday, 6=Sunday
        day_index = (row.day_of_week - 2) % 7
        matrix[day_index][row.hour] = row.count
    
    return {
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "hours": list(range(24)),
        "data": matrix
    }


@frappe.whitelist()
def get_sentiment_distribution(from_date=None, to_date=None):
    """
    Get sentiment score distribution.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not from_date:
        from_date = today()
    if not to_date:
        to_date = today()
    
    data = frappe.db.sql("""
        SELECT 
            sentiment_label,
            COUNT(*) as count,
            AVG(sentiment_score) as avg_score
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
        AND sentiment_label IS NOT NULL
        GROUP BY sentiment_label
    """, (from_date, to_date), as_dict=True)
    
    return data


@frappe.whitelist()
def export_report(from_date=None, to_date=None, format="xlsx"):
    """
    Generate and export a report.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    if not from_date:
        from_date = add_days(today(), -30)
    if not to_date:
        to_date = today()
    
    # Queue background job for large exports
    frappe.enqueue(
        "arrowz.api.analytics._generate_report",
        from_date=from_date,
        to_date=to_date,
        format=format,
        user=frappe.session.user,
        queue="long"
    )
    
    return {"status": "queued", "message": _("Report generation queued")}


def _generate_report(from_date, to_date, format, user):
    """
    Background job to generate report.
    """
    # Get data
    calls = frappe.get_all(
        "AZ Call Log",
        filters={
            "start_time": ["between", [from_date, to_date]]
        },
        fields=[
            "name", "direction", "status", "disposition",
            "caller_id", "callee_id", "contact_name",
            "extension", "start_time", "end_time", "duration",
            "has_recording", "sentiment_label"
        ],
        order_by="start_time desc"
    )
    
    # Generate file (simplified)
    if format == "xlsx":
        # Would use frappe.utils.xlsxutils
        pass
    
    # Notify user
    frappe.publish_realtime(
        "report_ready",
        {"message": _("Your report is ready")},
        user=user
    )
