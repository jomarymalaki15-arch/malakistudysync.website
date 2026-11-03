"""
StudySync Smart Task Prioritization Service
Explainable, rule-based algorithmic prioritization engine.
Calculates priority levels (Critical, High, Medium, Low) and gives human-readable reasons.
"""

from datetime import datetime, date, timedelta

TASK_TYPE_WEIGHTS = {
    'Exam': 1.6,
    'Project': 1.4,
    'Presentation': 1.2,
    'Quiz': 1.1,
    'Assignment': 1.0,
    'Other': 0.8
}

PRIORITY_BASE_SCORES = {
    'Critical': 80,
    'High': 60,
    'Medium': 40,
    'Low': 20
}

def calculate_smart_priority(due_date, due_time, task_type='Assignment', student_priority='Medium', status='Pending'):
    """
    Computes rule-based explainable priority.
    
    Returns:
        tuple: (calculated_priority, priority_reason)
    """
    if status == 'Completed':
        return ('Low', 'Task is already completed.')

    # Convert due_date to date object if string
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            due_date = date.today()

    # Convert due_time to time object
    if isinstance(due_time, str):
        try:
            due_time = datetime.strptime(due_time, '%H:%M:%S').time()
        except ValueError:
            try:
                due_time = datetime.strptime(due_time, '%H:%M').time()
            except ValueError:
                due_time = datetime.strptime('23:59:00', '%H:%M:%S').time()
    elif isinstance(due_time, timedelta):
        tot = int(due_time.total_seconds())
        due_time = datetime.strptime(f"{tot//3600:02d}:{(tot%3600)//60:02d}:00", '%H:%M:%S').time()
    elif not due_time:
        due_time = datetime.strptime('23:59:00', '%H:%M:%S').time()

    now = datetime.now()
    deadline = datetime.combine(due_date, due_time)
    hours_remaining = (deadline - now).total_seconds() / 3600.0

    # Rule 1: Overdue tasks
    if hours_remaining < 0 or status == 'Overdue':
        past_hours = abs(int(hours_remaining))
        return ('Critical', f"Urgent: Deadline passed {past_hours}h ago. Immediate submission required.")

    # Rule 2: Due in under 12 hours
    if hours_remaining <= 12:
        return ('Critical', f"Due in {int(hours_remaining)}h today! Immediate focus required.")

    # Rule 3: Major Exam or Project due within 48 hours
    type_weight = TASK_TYPE_WEIGHTS.get(task_type, 1.0)
    if task_type in ['Exam', 'Project'] and hours_remaining <= 48:
        return ('Critical', f"Upcoming {task_type} in {int(hours_remaining//24)}d ({int(hours_remaining)}h). High academic impact.")

    # Rule 4: Due within 24 hours
    if hours_remaining <= 24:
        return ('High', f"Due tomorrow in {int(hours_remaining)} hours.")

    # Rule 5: User set Critical and deadline is within 5 days
    if student_priority == 'Critical' and hours_remaining <= 120:
        return ('Critical', f"Marked Critical by student with deadline in {int(hours_remaining//24)} days.")

    # Rule 6: Due within 3 days with High priority or heavy type
    if hours_remaining <= 72:
        if student_priority in ['High', 'Critical'] or type_weight >= 1.2:
            return ('High', f"{task_type} due in {int(hours_remaining//24)} days. Preparation required.")
        return ('Medium', f"Due in {int(hours_remaining//24)} days. On-track schedule.")

    # Rule 7: Due within 7 days
    if hours_remaining <= 168:
        if student_priority == 'High':
            return ('High', f"Due in {int(hours_remaining//24)} days with student-flagged importance.")
        if task_type == 'Exam':
            return ('High', f"Exam in {int(hours_remaining//24)} days. Recommend starting revision.")
        return ('Medium', f"Due in {int(hours_remaining//24)} days. Moderate lead time.")

    # Rule 8: Ample lead time (> 7 days)
    days_left = int(hours_remaining // 24)
    if student_priority == 'Critical':
        return ('High', f"Critical task scheduled in {days_left} days. Advance planning advised.")
    elif student_priority == 'High':
        return ('Medium', f"High importance task with ample time ({days_left} days remaining).")
    else:
        return ('Low', f"Comfortable deadline ({days_left} days remaining).")
