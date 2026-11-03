"""
StudySync Academic Reports Routes
Feature 15: Filtered Report Generation, On-screen Summary, CSV and PDF Downloads.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, make_response, session, flash, redirect, url_for
from routes.auth import login_required
from models.subject import Subject
from models.user import User
from services.report_service import fetch_report_data, generate_csv_report, generate_pdf_report
from services.database import log_activity

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    """Renders the reports control panel and on-screen report preview."""
    user_id = session['user_id']
    subjects = Subject.get_by_user(user_id)

    report_type = request.args.get('type', 'summary')
    subject_id = request.args.get('subject_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    tasks_data = fetch_report_data(
        user_id=user_id,
        report_type=report_type,
        subject_id=subject_id,
        date_from=date_from or None,
        date_to=date_to or None
    )

    # Compute breakdown metrics
    total = len(tasks_data)
    completed = sum(1 for t in tasks_data if t['status'] == 'Completed')
    pending = sum(1 for t in tasks_data if t['status'] in ('Pending', 'In Progress'))
    overdue = sum(1 for t in tasks_data if t['status'] == 'Overdue')

    return render_template(
        'reports.html',
        subjects=subjects,
        tasks_data=tasks_data,
        report_type=report_type,
        selected_subject=subject_id,
        date_from=date_from,
        date_to=date_to,
        total_count=total,
        completed_count=completed,
        pending_count=pending,
        overdue_count=overdue
    )

@reports_bp.route('/reports/export/<string:format_type>')
@login_required
def export(format_type):
    """Exports generated reports to either PDF or CSV."""
    user_id = session['user_id']
    user = User.find_by_id(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    user_info = {
        'full_name': user.full_name,
        'student_id': user.student_id,
        'course_program': user.course_program
    }

    report_type = request.args.get('type', 'summary')
    subject_id = request.args.get('subject_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    tasks_data = fetch_report_data(
        user_id=user_id,
        report_type=report_type,
        subject_id=subject_id,
        date_from=date_from or None,
        date_to=date_to or None
    )

    title_map = {
        'summary': 'Task Summary Academic Report',
        'completed': 'Completed Requirements Report',
        'pending': 'Pending Requirements Workload Report',
        'overdue': 'Overdue Critical Tasks Report'
    }
    report_title = title_map.get(report_type, 'Academic Report')
    filename_base = f"studysync_{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    log_activity(user_id, "Report Exported", f"Exported {report_type} report as {format_type.upper()}", request.remote_addr)

    if format_type == 'csv':
        csv_content = generate_csv_report(user_info, tasks_data, report_title)
        response = make_response(csv_content)
        response.headers['Content-Disposition'] = f'attachment; filename={filename_base}.csv'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response

    elif format_type == 'pdf':
        pdf_bytes = generate_pdf_report(user_info, tasks_data, report_title)
        response = make_response(pdf_bytes)
        response.headers['Content-Disposition'] = f'attachment; filename={filename_base}.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response

    flash('Invalid export format requested.', 'danger')
    return redirect(url_for('reports.index'))
