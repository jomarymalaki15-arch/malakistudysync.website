"""
StudySync Administrator Dashboard & Management Routes
Feature 14: Student Directory, Account Activation/Deactivation,
System-wide Metrics, Audit Logs, and Administrative Reporting.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import admin_required
from models.user import User
from services.database import execute_query, log_activity

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
@admin_required
def index():
    """Renders the Administrator Dashboard with system stats, student directory, and audit logs."""
    stats = User.get_system_stats()
    students = User.get_all_students()
    
    # Fetch recent system audit logs
    audit_logs = execute_query(
        """SELECT a.*, u.full_name, u.email, u.role 
           FROM activity_logs a 
           LEFT JOIN users u ON a.user_id = u.id 
           ORDER BY a.created_at DESC 
           LIMIT 25""",
        fetchall=True
    )

    return render_template(
        'admin.html',
        stats=stats,
        students=students,
        audit_logs=audit_logs
    )

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Activates or deactivates a student account."""
    admin_id = session.get('user_id')
    user = User.find_by_id(user_id)
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('admin.index'))

    if user.is_admin:
        flash('Cannot modify administrator accounts from this action.', 'danger')
        return redirect(url_for('admin.index'))

    new_status = not user.is_active
    User.set_active_status(user_id, new_status)
    status_str = "activated" if new_status else "deactivated"
    
    log_activity(admin_id, "User Status Changed", f"Admin {status_str} account for {user.email}", request.remote_addr)
    flash(f"User account for {user.full_name} has been {status_str}.", 'success')
    return redirect(url_for('admin.index'))

@admin_bp.route('/admin/logs/clear', methods=['POST'])
@admin_required
def clear_logs():
    """Clears old activity logs keeping the most recent 50."""
    admin_id = session.get('user_id')
    execute_query(
        """DELETE FROM activity_logs 
           WHERE id NOT IN (
               SELECT id FROM (
                   SELECT id FROM activity_logs ORDER BY created_at DESC LIMIT 50
               ) AS keep_table
           )""",
        commit=True
    )
    log_activity(admin_id, "Logs Maintained", "Pruned system activity logs to last 50", request.remote_addr)
    flash('Old activity logs purged successfully.', 'info')
    return redirect(url_for('admin.index'))
