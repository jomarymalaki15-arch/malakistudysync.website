"""
StudySync Smart Reminder Service
Scans tasks and generates non-duplicate notifications and reminder entries
for tasks due today, tomorrow, overdue items, and high-priority deadlines.
"""

from datetime import datetime, date, timedelta
from services.database import execute_query

def process_smart_reminders(user_id):
    """
    Evaluates current tasks for a user and generates notifications and reminders.
    Enforces duplicate prevention within a 24-hour window per task and reminder type.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # 1. Fetch active tasks for this user
    active_tasks = execute_query(
        """SELECT t.*, s.subject_code, s.subject_name 
           FROM tasks t 
           LEFT JOIN subjects s ON t.subject_id = s.id 
           WHERE t.user_id = %s AND t.status != 'Completed'""",
        (user_id,),
        fetchall=True
    )

    if not active_tasks:
        return

    now = datetime.now()

    for task in active_tasks:
        task_id = task['id']
        due_date = task['due_date']
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

        # Parse due time
        due_time = task['due_time']
        if isinstance(due_time, timedelta):
            tot = int(due_time.total_seconds())
            due_time_obj = datetime.strptime(f"{tot//3600:02d}:{(tot%3600)//60:02d}:00", '%H:%M:%S').time()
        elif isinstance(due_time, str):
            try:
                due_time_obj = datetime.strptime(due_time, '%H:%M:%S').time()
            except ValueError:
                try:
                    due_time_obj = datetime.strptime(due_time, '%H:%M').time()
                except ValueError:
                    due_time_obj = datetime.strptime('23:59:00', '%H:%M:%S').time()
        else:
            due_time_obj = datetime.strptime('23:59:00', '%H:%M:%S').time()

        deadline = datetime.combine(due_date, due_time_obj)
        hours_until = (deadline - now).total_seconds() / 3600.0

        # Category A: Overdue
        if hours_until < 0 or task['status'] == 'Overdue':
            _add_notification_and_reminder(
                user_id=user_id,
                task_id=task_id,
                reminder_type='overdue',
                title=f"⚠️ Overdue: {task['title']}",
                message=f"Task '{task['title']}' ({task['subject_code']}) passed its deadline on {due_date}. Please submit as soon as possible.",
                notification_type='overdue',
                reminder_time=now
            )

        # Category B: Due Today
        elif due_date == today:
            _add_notification_and_reminder(
                user_id=user_id,
                task_id=task_id,
                reminder_type='due_today',
                title=f"⏳ Due Today: {task['title']}",
                message=f"Task '{task['title']}' is due today by {due_time_obj.strftime('%I:%M %p')}. Complete your submission!",
                notification_type='deadline',
                reminder_time=now
            )

        # Category C: Due Tomorrow
        elif due_date == tomorrow:
            _add_notification_and_reminder(
                user_id=user_id,
                task_id=task_id,
                reminder_type='due_tomorrow',
                title=f"📅 Due Tomorrow: {task['title']}",
                message=f"Reminder: '{task['title']}' for {task['subject_code']} is due tomorrow at {due_time_obj.strftime('%I:%M %p')}.",
                notification_type='deadline',
                reminder_time=now
            )

        # Category D: High Priority or Exam within 3 days
        elif (task['priority'] in ['Critical', 'High'] or task['task_type'] == 'Exam') and 0 <= hours_until <= 72:
            _add_notification_and_reminder(
                user_id=user_id,
                task_id=task_id,
                reminder_type='high_priority',
                title=f"🔥 High Priority: {task['title']}",
                message=f"Important {task['task_type']} '{task['title']}' is due in {int(hours_until//24)} days. Ensure your preparation is on track.",
                notification_type='priority',
                reminder_time=now
            )

def _add_notification_and_reminder(user_id, task_id, reminder_type, title, message, notification_type, reminder_time):
    """Inserts a notification and reminder only if not already triggered in the last 24 hours."""
    # Check duplicate in notifications within the same day
    existing_notif = execute_query(
        """SELECT id FROM notifications 
           WHERE user_id = %s AND task_id = %s AND notification_type = %s 
             AND DATE(created_at) = CURDATE()""",
        (user_id, task_id, notification_type),
        fetchone=True
    )

    if not existing_notif:
        execute_query(
            """INSERT INTO notifications (user_id, task_id, title, message, notification_type, is_read) 
               VALUES (%s, %s, %s, %s, %s, 0)""",
            (user_id, task_id, title, message, notification_type),
            commit=True
        )

    # Check duplicate in reminders for this task and reminder_type
    existing_reminder = execute_query(
        """SELECT id FROM reminders 
           WHERE user_id = %s AND task_id = %s AND reminder_type = %s 
             AND DATE(created_at) = CURDATE()""",
        (user_id, task_id, reminder_type),
        fetchone=True
    )

    if not existing_reminder:
        execute_query(
            """INSERT INTO reminders (user_id, task_id, reminder_type, reminder_time, is_sent) 
               VALUES (%s, %s, %s, %s, 1)""",
            (user_id, task_id, reminder_type, reminder_time),
            commit=True
        )
