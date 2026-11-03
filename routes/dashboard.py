"""
StudySync Dashboard Routes
Renders the primary student overview, stat cards, Chart.js integrations,
recent activities, and completion progress bars.
"""

from flask import Blueprint, render_template, session, jsonify
from routes.auth import login_required
from models.task import Task
from models.subject import Subject
from services.reminder_service import process_smart_reminders
from services.database import execute_query

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard view with statistics, charts, and upcoming deadlines."""
    user_id = session['user_id']
    
    # 1. Trigger automated reminder & overdue checks
    process_smart_reminders(user_id)
    Task.sync_overdue_tasks(user_id)

    # 2. Get 6 Overview Statistic Cards
    stats = Task.get_dashboard_stats(user_id)

    # 3. Calculate Completion Percentage
    total = stats['total_tasks']
    completed = stats['completed_tasks']
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    # 4. Fetch Upcoming Deadlines (Limit to next 5)
    upcoming_tasks = execute_query(
        """SELECT t.*, s.subject_code, s.subject_name, s.color AS subject_color 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s AND t.status != 'Completed' 
           ORDER BY t.due_date ASC, t.due_time ASC 
           LIMIT 5""",
        (user_id,),
        fetchall=True
    )
    upcoming_objects = [Task(r) for r in upcoming_tasks]

    # 5. Fetch Recent Activities from task_history & activity_logs
    recent_activities = execute_query(
        """SELECT action, remarks AS details, created_at, 'task' AS source 
           FROM task_history 
           WHERE user_id = %s 
           ORDER BY created_at DESC 
           LIMIT 6""",
        (user_id,),
        fetchall=True
    )

    # 6. Fetch Subject Workload Breakdown for Doughnut Chart
    subject_distribution = execute_query(
        """SELECT s.subject_name, s.color, COUNT(t.id) AS count 
           FROM subjects s 
           LEFT JOIN tasks t ON s.id = t.subject_id 
           WHERE s.user_id = %s 
           GROUP BY s.id 
           ORDER BY count DESC""",
        (user_id,),
        fetchall=True
    )

    return render_template(
        'dashboard.html',
        stats=stats,
        completion_rate=completion_rate,
        upcoming_tasks=upcoming_objects,
        recent_activities=recent_activities,
        subject_distribution=subject_distribution
    )

@dashboard_bp.route('/api/dashboard/charts')
@login_required
def charts_api():
    """API endpoint delivering JSON data for interactive Chart.js charts."""
    user_id = session['user_id']

    # Chart 1: Status distribution
    status_counts = execute_query(
        """SELECT status, COUNT(*) AS count 
           FROM tasks 
           WHERE user_id = %s 
           GROUP BY status""",
        (user_id,),
        fetchall=True
    )
    status_dict = {'Pending': 0, 'In Progress': 0, 'Completed': 0, 'Overdue': 0}
    for row in status_counts:
        if row['status'] in status_dict:
            status_dict[row['status']] = row['count']

    # Chart 2: Subject tasks distribution
    subjects = execute_query(
        """SELECT s.subject_code, s.color, COUNT(t.id) AS count 
           FROM subjects s 
           LEFT JOIN tasks t ON s.id = t.subject_id 
           WHERE s.user_id = %s 
           GROUP BY s.id""",
        (user_id,),
        fetchall=True
    )

    # Chart 3: Weekly completion trends (Last 7 days)
    weekly = execute_query(
        """SELECT DATE(completed_at) AS date_completed, COUNT(*) AS count 
           FROM tasks 
           WHERE user_id = %s AND status = 'Completed' 
             AND completed_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
           GROUP BY DATE(completed_at) 
           ORDER BY date_completed ASC""",
        (user_id,),
        fetchall=True
    )

    return jsonify({
        'status_labels': list(status_dict.keys()),
        'status_values': list(status_dict.values()),
        'subject_labels': [s['subject_code'] for s in subjects],
        'subject_values': [s['count'] for s in subjects],
        'subject_colors': [s['color'] for s in subjects],
        'weekly_trends': weekly
    })
