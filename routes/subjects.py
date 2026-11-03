"""
StudySync Subject Organization Routes
Feature 5: Subject Management, Custom Colors, and Course-Specific Task Views.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from models.subject import Subject
from models.task import Task
from services.database import log_activity

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/subjects')
@login_required
def index():
    """Renders the list of student subjects with task counts and color codes."""
    user_id = session['user_id']
    subjects = Subject.get_by_user(user_id)
    return render_template('subjects.html', subjects=subjects)

@subjects_bp.route('/subjects/add', methods=['POST'])
@login_required
def add():
    """Creates a new academic subject."""
    user_id = session['user_id']
    code = request.form.get('subject_code', '').strip()
    name = request.form.get('subject_name', '').strip()
    instructor = request.form.get('instructor', '').strip()
    color = request.form.get('color', '#2563EB')
    description = request.form.get('description', '').strip()

    if not code or not name:
        flash('Subject Code and Subject Name are required.', 'danger')
        return redirect(url_for('subjects.index'))

    Subject.create(
        user_id=user_id,
        subject_code=code,
        subject_name=name,
        instructor=instructor or None,
        color=color,
        description=description or None
    )

    log_activity(user_id, "Subject Created", f"Added subject: {code} - {name}", request.remote_addr)
    flash(f'Subject "{code} - {name}" added successfully!', 'success')
    return redirect(url_for('subjects.index'))

@subjects_bp.route('/subjects/<int:subject_id>/edit', methods=['POST'])
@login_required
def edit(subject_id):
    """Edits an existing subject."""
    user_id = session['user_id']
    code = request.form.get('subject_code', '').strip()
    name = request.form.get('subject_name', '').strip()
    instructor = request.form.get('instructor', '').strip()
    color = request.form.get('color', '#2563EB')
    description = request.form.get('description', '').strip()

    if not code or not name:
        flash('Subject Code and Subject Name are required.', 'danger')
        return redirect(url_for('subjects.index'))

    Subject.update(
        subject_id=subject_id,
        user_id=user_id,
        subject_code=code,
        subject_name=name,
        instructor=instructor or None,
        color=color,
        description=description or None
    )

    log_activity(user_id, "Subject Updated", f"Updated subject #{subject_id}", request.remote_addr)
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('subjects.index'))

@subjects_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete(subject_id):
    """Deletes an academic subject."""
    user_id = session['user_id']
    subject = Subject.find_by_id(subject_id, user_id)
    if subject:
        Subject.delete(subject_id, user_id)
        log_activity(user_id, "Subject Deleted", f"Deleted subject: {subject.subject_code}", request.remote_addr)
        flash(f'Subject "{subject.subject_code}" deleted.', 'info')
    else:
        flash('Subject not found.', 'danger')
    return redirect(url_for('subjects.index'))
