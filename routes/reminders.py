"""
StudySync Reminders & Notification Routes
Feature 6: In-App Smart Reminders, Notification Center, and Status Toggles.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes.auth import login_required
from models.notification import Notification
from services.reminder_service import process_smart_reminders
from services.database import execute_query

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/reminders')
@login_required
def index():
    """Renders the comprehensive student Reminders & Notifications Center."""
    user_id = session['user_id']
    process_smart_reminders(user_id)
    
    notifications = Notification.get_all(user_id, limit=50)
    unread_count = Notification.get_unread_count(user_id)

    # Fetch active scheduled reminders
    reminders = execute_query(
        """SELECT r.*, t.title AS task_title, t.due_date, t.due_time, s.subject_code 
           FROM reminders r 
           JOIN tasks t ON r.task_id = t.id 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE r.user_id = %s 
           ORDER BY r.reminder_time DESC 
           LIMIT 20""",
        (user_id,),
        fetchall=True
    )

    return render_template(
        'reminders.html',
        notifications=notifications,
        reminders=reminders,
        unread_count=unread_count
    )

@reminders_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    """Marks a single notification as read."""
    user_id = session['user_id']
    Notification.mark_as_read(notif_id, user_id)
    return redirect(request.referrer or url_for('reminders.index'))

@reminders_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Marks all user notifications as read."""
    user_id = session['user_id']
    Notification.mark_all_read(user_id)
    flash('All notifications marked as read.', 'success')
    return redirect(request.referrer or url_for('reminders.index'))

@reminders_bp.route('/notifications/<int:notif_id>/delete', methods=['POST'])
@login_required
def delete_notification(notif_id):
    """Deletes a notification item."""
    user_id = session['user_id']
    Notification.delete(notif_id, user_id)
    flash('Notification dismissed.', 'info')
    return redirect(request.referrer or url_for('reminders.index'))

@reminders_bp.route('/api/notifications/unread')
@login_required
def unread_api():
    """Delivers JSON payload of latest unread notifications for navbar bell polling."""
    user_id = session['user_id']
    items = Notification.get_unread(user_id, limit=5)
    return jsonify({
        'count': len(items),
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'created_at': str(n.created_at)
        } for n in items]
    })
