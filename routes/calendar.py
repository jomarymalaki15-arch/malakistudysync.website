"""
StudySync Calendar Routes
Feature 7: FullCalendar.js Integration, Monthly/Weekly/Daily Views,
Color-coded events, and Direct Task Addition from Calendar.
"""

from flask import Blueprint, render_template, session, jsonify, request
from routes.auth import login_required
from models.task import Task
from models.subject import Subject
from services.database import execute_query

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar')
@login_required
def index():
    """Renders the interactive FullCalendar interface."""
    user_id = session['user_id']
    subjects = Subject.get_by_user(user_id)
    return render_template('calendar.html', subjects=subjects)

@calendar_bp.route('/api/calendar/events')
@login_required
def calendar_events():
    """Delivers JSON formatted task event feed for FullCalendar.js."""
    user_id = session['user_id']
    
    tasks = execute_query(
        """SELECT t.*, s.subject_code, s.subject_name, s.color AS subject_color 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s""",
        (user_id,),
        fetchall=True
    )

    events = []
    for t in tasks:
        # Determine background color based on status or subject
        event_color = t['subject_color'] or '#2563EB'
        if t['status'] == 'Completed':
            event_color = '#10B981'  # Green for completed
        elif t['status'] == 'Overdue':
            event_color = '#EF4444'  # Red for overdue

        # Form start datetime string
        d_str = str(t['due_date'])
        t_str = str(t['due_time'])
        start_datetime = f"{d_str}T{t_str}"

        events.append({
            'id': t['id'],
            'title': f"[{t['subject_code'] or 'Task'}] {t['title']}",
            'start': start_datetime,
            'allDay': False,
            'backgroundColor': event_color,
            'borderColor': event_color,
            'textColor': '#ffffff',
            'extendedProps': {
                'taskId': t['id'],
                'subject': t['subject_code'] or 'General',
                'description': t['description'] or 'No description provided.',
                'taskType': t['task_type'],
                'priority': t['calculated_priority'] or t['priority'],
                'priorityReason': t['priority_reason'] or '',
                'status': t['status'],
                'dueDate': d_str,
                'dueTime': t_str
            }
        })

    return jsonify(events)
