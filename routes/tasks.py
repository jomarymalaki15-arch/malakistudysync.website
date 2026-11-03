"""
StudySync Task & Analytics Routes
Implements Task CRUD, Deadline Tracking, Smart Priority View, Status Board,
Workload Monitor, Progress Dashboard, Search/Filter, Recommendations, and Statistics.
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes.auth import login_required
from models.task import Task
from models.subject import Subject
from services.priority_service import calculate_smart_priority
from services.reminder_service import process_smart_reminders
from services.database import execute_query, log_activity

tasks_bp = Blueprint('tasks', __name__)

# ============================================================================
# FEATURE 2: TASK MANAGEMENT (CRUD & OVERVIEW)
# ============================================================================

@tasks_bp.route('/tasks')
@login_required
def index():
    """Renders the main task list with status pills, priority badges, and quick filters."""
    user_id = session['user_id']
    Task.sync_overdue_tasks(user_id)

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    subject_filter = request.args.get('subject_id', type=int)
    type_filter = request.args.get('task_type')
    sort_by = request.args.get('sort_by', 'newest')

    tasks = Task.get_by_user(
        user_id=user_id,
        status=status_filter,
        priority=priority_filter,
        subject_id=subject_filter,
        task_type=type_filter,
        sort_by=sort_by
    )
    subjects = Subject.get_by_user(user_id)

    return render_template(
        'tasks.html',
        tasks=tasks,
        subjects=subjects,
        selected_status=status_filter,
        selected_priority=priority_filter,
        selected_subject=subject_filter,
        selected_type=type_filter,
        selected_sort=sort_by
    )

@tasks_bp.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add():
    """Adds a new academic task with automatic smart priority calculation."""
    user_id = session['user_id']
    subjects = Subject.get_by_user(user_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        subject_id = request.form.get('subject_id', type=int)
        task_type = request.form.get('task_type', 'Assignment')
        due_date = request.form.get('due_date')
        due_time = request.form.get('due_time') or '23:59'
        student_priority = request.form.get('priority', 'Medium')

        if not title or not due_date:
            flash('Task title and due date are required.', 'danger')
            return render_template('task_form.html', action='Add', subjects=subjects, today=date.today())

        # Ensure due_time has seconds
        if len(due_time.split(':')) == 2:
            due_time += ':00'

        # Calculate explainable smart priority
        calc_priority, reason = calculate_smart_priority(
            due_date=due_date,
            due_time=due_time,
            task_type=task_type,
            student_priority=student_priority,
            status='Pending'
        )

        try:
            new_task = Task.create(
                user_id=user_id,
                subject_id=subject_id,
                title=title,
                description=description,
                task_type=task_type,
                due_date=due_date,
                due_time=due_time,
                priority=student_priority,
                calculated_priority=calc_priority,
                priority_reason=reason
            )

            # Re-evaluate smart reminders
            process_smart_reminders(user_id)
            log_activity(user_id, "Task Created", f"Created task: {title}", request.remote_addr)

            flash(f'Task "{title}" created successfully with priority: {calc_priority}!', 'success')
            return redirect(url_for('tasks.index'))

        except Exception as e:
            flash(f'Error creating task: {e}', 'danger')

    prefill_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    return render_template('task_form.html', action='Add', subjects=subjects, prefill_date=prefill_date)

@tasks_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    """Edits an existing task and recalculates smart priority."""
    user_id = session['user_id']
    task = Task.find_by_id(task_id, user_id)
    if not task:
        flash('Task not found or access denied.', 'danger')
        return redirect(url_for('tasks.index'))

    subjects = Subject.get_by_user(user_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        subject_id = request.form.get('subject_id', type=int)
        task_type = request.form.get('task_type', 'Assignment')
        due_date = request.form.get('due_date')
        due_time = request.form.get('due_time') or '23:59'
        student_priority = request.form.get('priority', 'Medium')
        status = request.form.get('status', task.status)

        if not title or not due_date:
            flash('Task title and due date are required.', 'danger')
            return render_template('task_form.html', action='Edit', task=task, subjects=subjects)

        if len(due_time.split(':')) == 2:
            due_time += ':00'

        calc_priority, reason = calculate_smart_priority(
            due_date=due_date,
            due_time=due_time,
            task_type=task_type,
            student_priority=student_priority,
            status=status
        )

        Task.update(
            task_id=task_id,
            user_id=user_id,
            subject_id=subject_id,
            title=title,
            description=description,
            task_type=task_type,
            due_date=due_date,
            due_time=due_time,
            priority=student_priority,
            calculated_priority=calc_priority,
            priority_reason=reason,
            status=status
        )

        process_smart_reminders(user_id)
        log_activity(user_id, "Task Updated", f"Updated task #{task_id}: {title}", request.remote_addr)

        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.index'))

    return render_template('task_form.html', action='Edit', task=task, subjects=subjects)

@tasks_bp.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_status(task_id):
    """Toggles task completion between Completed and Pending."""
    user_id = session['user_id']
    task = Task.find_by_id(task_id, user_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('tasks.index'))

    new_status = 'Pending' if task.status == 'Completed' else 'Completed'
    Task.update_status(task_id, user_id, new_status, f"Quick toggle to {new_status}")
    log_activity(user_id, "Status Changed", f"Task #{task_id} toggled to {new_status}", request.remote_addr)

    flash(f'Task marked as {new_status}.', 'success')
    return redirect(request.referrer or url_for('tasks.index'))

@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    """Deletes a task owned by current student."""
    user_id = session['user_id']
    task = Task.find_by_id(task_id, user_id)
    if task:
        Task.delete(task_id, user_id)
        log_activity(user_id, "Task Deleted", f"Deleted task #{task_id}: {task.title}", request.remote_addr)
        flash('Task deleted successfully.', 'info')
    else:
        flash('Task not found.', 'danger')
    return redirect(url_for('tasks.index'))

# ============================================================================
# FEATURE 3: DEADLINE TRACKING
# ============================================================================

@tasks_bp.route('/deadlines')
@login_required
def deadlines():
    """Feature 3: Categorized upcoming, today, tomorrow, overdue, and completed deadlines."""
    user_id = session['user_id']
    categorized = Task.get_deadlines_categorized(user_id)
    return render_template('deadlines.html', deadlines=categorized)

# ============================================================================
# FEATURE 4: SMART TASK PRIORITIZATION VIEW
# ============================================================================

@tasks_bp.route('/tasks/priority')
@login_required
def priority_view():
    """Feature 4: Prioritized task view grouped into Critical, High, Medium, and Low."""
    user_id = session['user_id']
    Task.sync_overdue_tasks(user_id)
    all_tasks = Task.get_by_user(user_id, sort_by='priority')

    grouped = {'Critical': [], 'High': [], 'Medium': [], 'Low': []}
    for t in all_tasks:
        prio = t.calculated_priority or t.priority
        if prio in grouped:
            grouped[prio].append(t)
        else:
            grouped['Medium'].append(t)

    return render_template('priority_tasks.html', priority_groups=grouped)

# ============================================================================
# FEATURE 8: TASK STATUS TRACKING (KANBAN BOARD)
# ============================================================================

@tasks_bp.route('/tasks/status')
@login_required
def status_board():
    """Feature 8: Dedicated status tracking view & Kanban board."""
    user_id = session['user_id']
    Task.sync_overdue_tasks(user_id)
    all_tasks = Task.get_by_user(user_id)

    columns = {
        'Pending': [t for t in all_tasks if t.status == 'Pending'],
        'In Progress': [t for t in all_tasks if t.status == 'In Progress'],
        'Overdue': [t for t in all_tasks if t.status == 'Overdue'],
        'Completed': [t for t in all_tasks if t.status == 'Completed']
    }

    return render_template('task_status.html', columns=columns)

@tasks_bp.route('/tasks/<int:task_id>/move_status', methods=['POST'])
@login_required
def move_status(task_id):
    """Handles status changes directly from the Kanban status board."""
    user_id = session['user_id']
    new_status = request.form.get('new_status')
    if new_status in ['Pending', 'In Progress', 'Completed', 'Overdue']:
        Task.update_status(task_id, user_id, new_status, f"Moved on Kanban board to {new_status}")
        flash(f'Task status updated to {new_status}.', 'success')
    return redirect(url_for('tasks.status_board'))

# ============================================================================
# FEATURE 9: ACADEMIC WORKLOAD MONITORING
# ============================================================================

@tasks_bp.route('/workload')
@login_required
def workload_monitor():
    """Feature 9: Academic Workload Analysis & stress indicators."""
    user_id = session['user_id']
    Task.sync_overdue_tasks(user_id)

    # 1. Total pending requirements
    pending_tasks = Task.get_by_user(user_id, status='Pending')
    in_progress = Task.get_by_user(user_id, status='In Progress')
    overdue = Task.get_by_user(user_id, status='Overdue')
    total_pending_count = len(pending_tasks) + len(in_progress) + len(overdue)

    # 2. Tasks due this week
    today = date.today()
    week_end = today + timedelta(days=7)
    tasks_this_week = execute_query(
        """SELECT t.*, s.subject_code, s.subject_name 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s AND t.status != 'Completed' 
             AND t.due_date BETWEEN %s AND %s 
           ORDER BY t.due_date ASC""",
        (user_id, today, week_end),
        fetchall=True
    )
    tasks_this_week = [Task(r) for r in tasks_this_week]

    # 3. Upcoming examinations
    upcoming_exams = execute_query(
        """SELECT t.*, s.subject_code, s.subject_name 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s AND t.task_type = 'Exam' AND t.status != 'Completed' 
             AND t.due_date >= CURDATE() 
           ORDER BY t.due_date ASC""",
        (user_id,),
        fetchall=True
    )
    upcoming_exams = [Task(r) for r in upcoming_exams]

    # 4. Tasks per subject
    subjects_workload = execute_query(
        """SELECT s.subject_code, s.subject_name, s.color, 
                  COUNT(t.id) AS total_tasks,
                  SUM(CASE WHEN t.status IN ('Pending', 'In Progress', 'Overdue') THEN 1 ELSE 0 END) AS pending_tasks,
                  SUM(CASE WHEN t.priority IN ('Critical', 'High') AND t.status != 'Completed' THEN 1 ELSE 0 END) AS `high_priority`
           FROM subjects s
           LEFT JOIN tasks t ON s.id = t.subject_id
           WHERE s.user_id = %s
           GROUP BY s.id
           ORDER BY pending_tasks DESC""",
        (user_id,),
        fetchall=True
    )

    # 5. Workload index computation
    # Base calculation: pending + 2 * high_priority + 3 * exams_this_week
    high_priority_count = sum(float(s['high_priority'] or 0) for s in subjects_workload)
    score = float(total_pending_count) + (high_priority_count * 1.5) + (float(len(upcoming_exams)) * 2.0)
    
    if score >= 14:
        workload_level = 'Overloaded'
        workload_badge = 'danger'
        advice = 'Your academic workload is critical. Consider delegating group responsibilities and prioritizing overdue items.'
    elif score >= 8:
        workload_level = 'Heavy'
        workload_badge = 'warning'
        advice = 'Heavy workload this week. Dedicate time blocks for your major assignments and examinations.'
    elif score >= 4:
        workload_level = 'Moderate'
        workload_badge = 'info'
        advice = 'Healthy workload. Keep steady progress to prevent deadline pile-up.'
    else:
        workload_level = 'Light'
        workload_badge = 'success'
        advice = 'Manageable workload. A great time to study ahead or rest!'

    return render_template(
        'workload.html',
        total_pending=total_pending_count,
        tasks_this_week=tasks_this_week,
        upcoming_exams=upcoming_exams,
        subjects_workload=subjects_workload,
        workload_level=workload_level,
        workload_badge=workload_badge,
        workload_advice=advice,
        workload_score=round(score, 1)
    )

# ============================================================================
# FEATURE 10: PROGRESS DASHBOARD
# ============================================================================

@tasks_bp.route('/progress')
@login_required
def progress():
    """Feature 10: Academic Progress and completion metrics."""
    user_id = session['user_id']
    stats = Task.get_dashboard_stats(user_id)
    total = stats['total_tasks']
    completed = stats['completed_tasks']
    rate = round((completed / total * 100), 1) if total > 0 else 0

    # Subject performance
    subjects = execute_query(
        """SELECT s.subject_code, s.subject_name, s.color,
                  COUNT(t.id) as total,
                  SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed
           FROM subjects s
           LEFT JOIN tasks t ON s.id = t.subject_id
           WHERE s.user_id = %s
           GROUP BY s.id""",
        (user_id,),
        fetchall=True
    )
    for s in subjects:
        s_total = s['total']
        s_comp = s['completed']
        s['rate'] = round((s_comp / s_total * 100), 1) if s_total > 0 else 0

    return render_template('progress.html', stats=stats, completion_rate=rate, subjects=subjects)

# ============================================================================
# FEATURE 11: ADVANCED SEARCH AND FILTERING
# ============================================================================

@tasks_bp.route('/tasks/search')
@login_required
def search_filter():
    """Feature 11: Multi-criteria dynamic task search and filter page."""
    user_id = session['user_id']
    keyword = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    subject_filter = request.args.get('subject_id', type=int)
    type_filter = request.args.get('task_type', '')
    sort_by = request.args.get('sort_by', 'deadline_asc')

    tasks = Task.get_by_user(
        user_id=user_id,
        status=status_filter or None,
        priority=priority_filter or None,
        subject_id=subject_filter or None,
        task_type=type_filter or None,
        search=keyword or None,
        sort_by=sort_by
    )
    subjects = Subject.get_by_user(user_id)

    return render_template(
        'search.html',
        tasks=tasks,
        subjects=subjects,
        keyword=keyword,
        status_filter=status_filter,
        priority_filter=priority_filter,
        subject_filter=subject_filter,
        type_filter=type_filter,
        sort_by=sort_by
    )

# ============================================================================
# FEATURE 12: STUDY RECOMMENDATIONS ENGINE
# ============================================================================

@tasks_bp.route('/recommendations')
@login_required
def recommendations():
    """Feature 12: Rule-based intelligent study recommendations without paid APIs."""
    user_id = session['user_id']
    Task.sync_overdue_tasks(user_id)

    recommendations_list = []

    # 1. Check Overdue Tasks
    overdue_tasks = Task.get_by_user(user_id, status='Overdue')
    if overdue_tasks:
        titles = ", ".join([f'"{t.title}"' for t in overdue_tasks[:2]])
        recommendations_list.append({
            'type': 'danger',
            'icon': 'bi-exclamation-octagon-fill',
            'title': 'Prioritize Overdue Requirements',
            'description': f'You have {len(overdue_tasks)} overdue task(s) including {titles}. Finishing these immediately avoids late penalties and reduces academic anxiety.',
            'action_label': 'Resolve Overdue Tasks',
            'action_url': url_for('tasks.deadlines')
        })

    # 2. Check Same-day Deadline Clusters
    clusters = execute_query(
        """SELECT due_date, COUNT(*) as count 
           FROM tasks 
           WHERE user_id = %s AND status != 'Completed' AND due_date >= CURDATE()
           GROUP BY due_date 
           HAVING count >= 2 
           ORDER BY due_date ASC 
           LIMIT 2""",
        (user_id,),
        fetchall=True
    )
    for c in clusters:
        d_str = c['due_date'].strftime('%A, %b %d') if hasattr(c['due_date'], 'strftime') else str(c['due_date'])
        recommendations_list.append({
            'type': 'warning',
            'icon': 'bi-calendar-event',
            'title': f'Deadline Cluster Alert: {d_str}',
            'description': f'You have {c["count"]} tasks scheduled for the exact same date ({d_str}). Start working on the heavier assignment earlier to prevent last-minute stress.',
            'action_label': 'View Calendar',
            'action_url': url_for('calendar.index')
        })

    # 3. Check Upcoming Examinations
    exams = execute_query(
        """SELECT t.*, s.subject_code 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s AND t.task_type = 'Exam' AND t.status != 'Completed' 
             AND t.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)""",
        (user_id,),
        fetchall=True
    )
    for ex in exams:
        recommendations_list.append({
            'type': 'primary',
            'icon': 'bi-mortarboard-fill',
            'title': f'Prepare for {ex["subject_code"]} Exam',
            'description': f'Your exam "{ex["title"]}" is scheduled for {ex["due_date"]}. Schedule 25-minute Pomodoro study sessions today to review core syllabus materials.',
            'action_label': 'Review Subject',
            'action_url': url_for('subjects.index')
        })

    # 4. Check Subject Backlog
    backlogs = execute_query(
        """SELECT s.subject_code, s.subject_name, COUNT(t.id) as pending_count 
           FROM subjects s 
           JOIN tasks t ON s.id = t.subject_id 
           WHERE s.user_id = %s AND t.status != 'Completed' 
           GROUP BY s.id 
           HAVING pending_count >= 3 
           ORDER BY pending_count DESC 
           LIMIT 1""",
        (user_id,),
        fetchall=True
    )
    if backlogs:
        b = backlogs[0]
        recommendations_list.append({
            'type': 'info',
            'icon': 'bi-stack',
            'title': f'Address Backlog in {b["subject_code"]}',
            'description': f'{b["subject_name"]} currently has {b["pending_count"]} unfinished tasks. Dedicate your next study block specifically to clear these requirements.',
            'action_label': 'Open Subject Tasks',
            'action_url': url_for('tasks.index', subject_id=backlogs[0].get('id'))
        })

    # Default encouraging recommendation if all is smooth
    if not recommendations_list:
        recommendations_list.append({
            'type': 'success',
            'icon': 'bi-check-circle-fill',
            'title': 'Great Job Staying Ahead!',
            'description': 'Your deadlines are well-spaced and you have no overdue requirements. Keep up your current productivity habits and pace your studies evenly.',
            'action_label': 'View Dashboard',
            'action_url': url_for('dashboard.index')
        })

    return render_template('recommendations.html', recommendations=recommendations_list)

# ============================================================================
# FEATURE 13: COMPLETION STATISTICS
# ============================================================================

@tasks_bp.route('/statistics')
@login_required
def statistics():
    """Feature 13: Detailed completion statistics and analytics."""
    user_id = session['user_id']
    stats = Task.get_dashboard_stats(user_id)

    # 1. Tasks completed today
    today_completed = execute_query(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'Completed' AND DATE(completed_at) = CURDATE()",
        (user_id,),
        fetchone=True
    )['count'] or 0

    # 2. Tasks completed this week (last 7 days)
    week_completed = execute_query(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'Completed' AND completed_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
        (user_id,),
        fetchone=True
    )['count'] or 0

    # 3. Tasks completed this month
    month_completed = execute_query(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND status = 'Completed' AND MONTH(completed_at) = MONTH(CURDATE()) AND YEAR(completed_at) = YEAR(CURDATE())",
        (user_id,),
        fetchone=True
    )['count'] or 0

    # 4. On-time delivery rate
    on_time = execute_query(
        """SELECT COUNT(*) as count FROM tasks 
           WHERE user_id = %s AND status = 'Completed' AND completed_at <= CONCAT(due_date, ' ', due_time)""",
        (user_id,),
        fetchone=True
    )['count'] or 0
    total_completed = stats['completed_tasks']
    on_time_rate = round((on_time / total_completed * 100), 1) if total_completed > 0 else 100

    # 5. Subject completion table
    subject_stats = execute_query(
        """SELECT s.subject_code, s.subject_name, s.color,
                  COUNT(t.id) as total,
                  SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed,
                  SUM(CASE WHEN t.status = 'Overdue' THEN 1 ELSE 0 END) as overdue
           FROM subjects s
           LEFT JOIN tasks t ON s.id = t.subject_id
           WHERE s.user_id = %s
           GROUP BY s.id""",
        (user_id,),
        fetchall=True
    )

    return render_template(
        'statistics.html',
        stats=stats,
        today_completed=today_completed,
        week_completed=week_completed,
        month_completed=month_completed,
        on_time_rate=on_time_rate,
        subject_stats=subject_stats
    )
