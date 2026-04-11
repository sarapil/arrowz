# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Arrowz Scheduled Tasks

Background tasks that run periodically.
"""

import frappe
from frappe.utils import now_datetime, add_to_date, get_datetime


def cleanup_stale_calls():
    """
    Clean up stale call records that are stuck in Ringing/In Progress state.
    These are typically orphaned records from crashes or disconnections.
    Runs every 10 minutes.
    """
    # Calls that are "Ringing" for more than 5 minutes are stale
    threshold_ringing = add_to_date(now_datetime(), minutes=-5)

    # Calls that are "In Progress" for more than 4 hours are stale
    threshold_in_progress = add_to_date(now_datetime(), hours=-4)

    # Count before cleanup
    ringing_count = frappe.db.count('AZ Call Log', filters={
        'status': 'Ringing',
        'start_time': ['<', threshold_ringing]
    })

    progress_count = frappe.db.count('AZ Call Log', filters={
        'status': ['in', ['In Progress', 'On Hold']],
        'start_time': ['<', threshold_in_progress]
    })

    if ringing_count == 0 and progress_count == 0:
        return {"success": True, "cleaned": 0}

    # Update stale "Ringing" calls to "Missed"
    frappe.db.sql("""
        UPDATE `tabAZ Call Log`
        SET status = 'Missed',
            end_time = %(now)s,
            duration = 0,
            modified = %(now)s
        WHERE status = 'Ringing'
        AND start_time < %(threshold)s
    """, {
        "now": now_datetime(),
        "threshold": threshold_ringing
    })

    # Update stale "In Progress" calls to "Completed"
    frappe.db.sql("""
        UPDATE `tabAZ Call Log`
        SET status = 'Completed',
            end_time = %(now)s,
            duration = TIMESTAMPDIFF(SECOND, start_time, %(now)s),
            modified = %(now)s
        WHERE status IN ('In Progress', 'On Hold')
        AND start_time < %(threshold)s
    """, {
        "now": now_datetime(),
        "threshold": threshold_in_progress
    })

    frappe.db.commit()

    total_cleaned = ringing_count + progress_count
    if total_cleaned > 0:
        frappe.logger().info(
            f"Arrowz: Cleaned up {total_cleaned} stale calls "
            f"({ringing_count} Ringing→Missed, {progress_count} InProgress→Completed)"
        )

    return {"success": True, "cleaned": total_cleaned}


def cleanup_stale_presence():
    """
    Clean up stale agent presence records.
    Runs every 5 minutes.
    """
    # Mark agents as offline if no heartbeat for 10 minutes
    threshold = add_to_date(now_datetime(), minutes=-10)

    stale_agents = frappe.db.get_all(
        "AZ Extension",
        filters={
            "last_registered": ["<", threshold],
            "status": ["!=", "offline"]
        },
        pluck="name"
    )

    for ext in stale_agents:
        frappe.db.set_value("AZ Extension", ext, "status", "offline")

        # Publish real-time update
        frappe.publish_realtime(
            event="arrowz_agent_status_changed",
            message={"extension": ext, "status": "offline"},
            after_commit=True
        )

    frappe.db.commit()


def sync_pbx_status():
    """
    Sync extension status with PBX.
    Runs every hour.
    """
    # Get all active server configs
    servers = frappe.get_all(
        "AZ Server Config",
        filters={"is_active": 1},
        pluck="name"
    )

    for server_name in servers:
        try:
            server = frappe.get_doc("AZ Server Config", server_name)

            # Get extensions for this server
            extensions = frappe.get_all(
                "AZ Extension",
                filters={"server": server_name, "is_active": 1},
                fields=["name", "extension"]
            )

            # Sync logic would go here
            # This is a placeholder for actual PBX integration

        except Exception as e:
            frappe.log_error(f"Error syncing with PBX {server_name}: {str(e)}")


def cleanup_old_presence_logs():
    """
    Clean up old presence logs.
    Runs daily.
    """
    # Keep logs for 30 days
    threshold = add_to_date(now_datetime(), days=-30)

    # Delete old presence logs if they exist
    # This is a placeholder - implement if you add a presence log table
    pass


def generate_daily_report():
    """
    Generate and email daily call statistics.
    Runs daily.
    """
    from datetime import date, timedelta

    yesterday = date.today() - timedelta(days=1)

    # Get call statistics
    stats = frappe.db.sql("""
        SELECT
            COUNT(*) as total_calls,
            SUM(CASE WHEN direction = 'inbound' THEN 1 ELSE 0 END) as inbound_calls,
            SUM(CASE WHEN direction = 'outbound' THEN 1 ELSE 0 END) as outbound_calls,
            SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed_calls,
            AVG(duration) as avg_duration,
            SUM(duration) as total_duration
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = %s
    """, yesterday, as_dict=True)[0]

    # Get manager emails
    managers = frappe.get_all(
        "Has Role",
        filters={"role": "Call Center Manager"},
        pluck="parent"
    )

    if not managers or stats.total_calls == 0:
        return

    # Prepare email content
    subject = f"Arrowz Daily Report - {yesterday.strftime('%Y-%m-%d')}"

    message = f"""
    <h2>Daily Call Statistics</h2>
    <p>Report for: {yesterday.strftime('%A, %B %d, %Y')}</p>

    <table border="1" cellpadding="8" cellspacing="0">
        <tr><td><strong>Total Calls</strong></td><td>{stats.total_calls or 0}</td></tr>
        <tr><td><strong>Inbound Calls</strong></td><td>{stats.inbound_calls or 0}</td></tr>
        <tr><td><strong>Outbound Calls</strong></td><td>{stats.outbound_calls or 0}</td></tr>
        <tr><td><strong>Missed Calls</strong></td><td>{stats.missed_calls or 0}</td></tr>
        <tr><td><strong>Avg Duration</strong></td><td>{format_duration(stats.avg_duration or 0)}</td></tr>
        <tr><td><strong>Total Talk Time</strong></td><td>{format_duration(stats.total_duration or 0)}</td></tr>
    </table>

    <p><a href="/desk/arrowz-analytics">View Full Analytics</a></p>
    """

    # Send email
    for user in managers:
        email = frappe.db.get_value("User", user, "email")
        if email:
            try:
                frappe.sendmail(
                    recipients=[email],
                    subject=subject,
                    message=message
                )
            except Exception as e:
                frappe.log_error(f"Error sending daily report to {email}: {str(e)}")


def generate_weekly_analytics():
    """
    Generate weekly analytics summary.
    Runs weekly.
    """
    from datetime import date, timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # Weekly statistics
    stats = frappe.db.sql("""
        SELECT
            COUNT(*) as total_calls,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_calls,
            SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed_calls,
            AVG(duration) as avg_duration
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
    """, (start_date, end_date), as_dict=True)[0]

    # Top agents
    top_agents = frappe.db.sql("""
        SELECT
            extension,
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) BETWEEN %s AND %s
            AND extension IS NOT NULL
        GROUP BY extension
        ORDER BY total_calls DESC
        LIMIT 5
    """, (start_date, end_date), as_dict=True)

    # Log the analytics
    frappe.logger().info(f"Weekly Analytics: {stats}")


def format_duration(seconds):
    """Format seconds into HH:MM:SS"""
    if not seconds:
        return "0:00"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# =============================================================================
# Omni-Channel Scheduled Tasks
# =============================================================================

def check_window_expiry():
    """
    Check for expired WhatsApp 24h windows.
    Runs every 15 minutes.
    """
    from arrowz.events.conversation import check_window_expiry as do_check
    do_check()

    # Also check for windows expiring soon (within 30 minutes)
    from frappe.utils import add_to_date

    expiring_soon = add_to_date(now_datetime(), minutes=30)

    sessions = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "channel": "WhatsApp",
            "status": "Active",
            "window_expires": ["between", [now_datetime(), expiring_soon]],
        },
        fields=["name"]
    )

    for session in sessions:
        from arrowz.notifications import notify_window_expiring
        notify_window_expiring(session.name)

    frappe.db.commit()


def sync_openmeetings_status():
    """
    Sync meeting room status with OpenMeetings.
    Runs hourly.
    """
    from arrowz.events.meeting import sync_openmeetings_status as do_sync
    do_sync()

    # Also check for meeting reminders
    from arrowz.notifications import check_meeting_reminders
    check_meeting_reminders()


def cleanup_ended_conversations():
    """
    Cleanup old ended conversations.
    Runs daily.
    """
    # Archive conversations closed more than 90 days ago
    threshold = add_to_date(now_datetime(), days=-90)

    old_sessions = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "status": "Closed",
            "session_end": ["<", threshold]
        },
        pluck="name"
    )

    for session in old_sessions:
        try:
            # Archive the session (you can customize this behavior)
            frappe.db.set_value("AZ Conversation Session", session, "status", "Archived")
        except Exception as e:
            frappe.log_error(
                title=f"Error archiving session {session}",
                message=str(e)
            )

    frappe.db.commit()


def cleanup_temporary_rooms():
    """
    Cleanup temporary meeting rooms that ended.
    Runs daily.
    """
    # Delete temporary rooms that ended more than 7 days ago
    threshold = add_to_date(now_datetime(), days=-7)

    old_rooms = frappe.get_all(
        "AZ Meeting Room",
        filters={
            "room_type": "Temporary",
            "status": "Ended",
            "scheduled_end": ["<", threshold]
        },
        pluck="name"
    )

    for room in old_rooms:
        try:
            frappe.delete_doc("AZ Meeting Room", room, ignore_permissions=True)
        except Exception as e:
            frappe.log_error(
                title=f"Error deleting room {room}",
                message=str(e)
            )

    frappe.db.commit()


def generate_omni_channel_report():
    """
    Generate weekly Omni-Channel analytics report.
    Runs weekly.
    """
    from datetime import date, timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # Message statistics by channel
    channel_stats = frappe.db.sql("""
        SELECT
            channel,
            COUNT(*) as total_sessions,
            SUM(message_count) as total_messages
        FROM `tabAZ Conversation Session`
        WHERE DATE(creation) BETWEEN %s AND %s
        GROUP BY channel
    """, (start_date, end_date), as_dict=True)

    # Meeting statistics
    meeting_stats = frappe.db.sql("""
        SELECT
            COUNT(*) as total_meetings,
            SUM(CASE WHEN status = 'Ended' THEN 1 ELSE 0 END) as completed_meetings,
            SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_meetings,
            AVG(TIMESTAMPDIFF(MINUTE, scheduled_start, scheduled_end)) as avg_duration_minutes
        FROM `tabAZ Meeting Room`
        WHERE DATE(creation) BETWEEN %s AND %s
    """, (start_date, end_date), as_dict=True)[0]

    # Response time statistics
    response_stats = frappe.db.sql("""
        SELECT
            AVG(TIMESTAMPDIFF(MINUTE, creation, first_response_time)) as avg_first_response_minutes
        FROM `tabAZ Conversation Session`
        WHERE DATE(creation) BETWEEN %s AND %s
            AND first_response_at IS NOT NULL
    """, (start_date, end_date), as_dict=True)[0]

    # Get manager emails
    managers = frappe.get_all(
        "Has Role",
        filters={"role": ["in", ["Omni Channel Manager", "System Manager"]]},
        pluck="parent"
    )

    if not managers:
        return

    # Prepare email content
    subject = f"Arrowz Omni-Channel Weekly Report - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

    channel_rows = ""
    for cs in channel_stats:
        channel_rows += f"""
            <tr>
                <td>{cs.channel}</td>
                <td>{cs.total_sessions or 0}</td>
                <td>{cs.total_messages or 0}</td>
            </tr>
        """

    message = f"""
    <h2>Weekly Omni-Channel Report</h2>
    <p>Report for: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}</p>

    <h3>Channel Statistics</h3>
    <table border="1" cellpadding="8" cellspacing="0">
        <tr>
            <th>Channel</th>
            <th>Sessions</th>
            <th>Messages</th>
        </tr>
        {channel_rows}
    </table>

    <h3>Meeting Statistics</h3>
    <table border="1" cellpadding="8" cellspacing="0">
        <tr><td><strong>Total Meetings</strong></td><td>{meeting_stats.total_meetings or 0}</td></tr>
        <tr><td><strong>Completed</strong></td><td>{meeting_stats.completed_meetings or 0}</td></tr>
        <tr><td><strong>Cancelled</strong></td><td>{meeting_stats.cancelled_meetings or 0}</td></tr>
        <tr><td><strong>Avg Duration</strong></td><td>{int(meeting_stats.avg_duration_minutes or 0)} minutes</td></tr>
    </table>

    <h3>Response Metrics</h3>
    <table border="1" cellpadding="8" cellspacing="0">
        <tr><td><strong>Avg First Response Time</strong></td><td>{int(response_stats.avg_first_response_minutes or 0)} minutes</td></tr>
    </table>

    <p><a href="/desk/query-report/AZ%20Omni%20Channel%20Analytics">View Full Analytics</a></p>
    """

    # Send email
    for user in set(managers):
        email = frappe.db.get_value("User", user, "email")
        if email:
            try:
                frappe.sendmail(
                    recipients=[email],
                    subject=subject,
                    message=message
                )
            except Exception as e:
                frappe.log_error(f"Error sending omni report to {email}: {str(e)}")
