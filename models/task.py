"""
StudySync Task Model
Handles task entity, status transitions, deadline calculations,
and data access for student tasks.
"""

from datetime import datetime, date, timedelta
from services.database import execute_query

class Task:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.subject_id = data.get('subject_id')
        self.title = data.get('title')
        self.description = data.get('description')
        self.task_type = data.get('task_type', 'Assignment')
        self.due_date = data.get('due_date')
        self.due_time = data.get('due_time')
        self.priority = data.get('priority', 'Medium')
        self.calculated_priority = data.get('calculated_priority', 'Medium')
        self.priority_reason = data.get('priority_reason')
        self.status = data.get('status', 'Pending')
        self.completed_at = data.get('completed_at')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

        # Joined Subject fields
        self.subject_code = data.get('subject_code') or 'General'
        self.subject_name = data.get('subject_name') or 'General Academic'
        self.subject_color = data.get('subject_color') or '#64748B'

    @property
    def due_datetime(self):
        """Combines due_date and due_time into a full datetime object."""
        if not self.due_date:
            return None
            
        d = self.due_date
        if isinstance(d, str):
            try:
                d = datetime.strptime(d, '%Y-%m-%d').date()
            except ValueError:
                return None
                
        t = self.due_time
        if isinstance(t, timedelta):
            # MySQL connector sometimes returns TIME as timedelta
            total_seconds = int(t.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            t = datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", '%H:%M:%S').time()
        elif isinstance(t, str):
            try:
                t = datetime.strptime(t, '%H:%M:%S').time()
            except ValueError:
                try:
                    t = datetime.strptime(t, '%H:%M').time()
                except ValueError:
                    t = datetime.strptime('23:59:00', '%H:%M:%S').time()
        elif not t:
            t = datetime.strptime('23:59:00', '%H:%M:%S').time()
            
        return datetime.combine(d, t)

    @property
    def remaining_time_display(self):
        """Calculates and formats human-readable remaining time or overdue duration."""
        if self.status == 'Completed':
            return "Completed"
            
        dt = self.due_datetime
        if not dt:
            return "No deadline"
            
        now = datetime.now()
        diff = dt - now
        
        if diff.total_seconds() < 0:
            past = abs(diff)
            days = past.days
            hours = past.seconds // 3600
            if days > 0:
                return f"Overdue by {days}d {hours}h"
            return f"Overdue by {hours}h"
            
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        if days == 0:
            if hours == 0:
                return f"Due in {minutes}m"
            return f"Due in {hours}h {minutes}m"
        elif days == 1:
            return f"Due tomorrow at {dt.strftime('%I:%M %p')}"
        elif days < 7:
            return f"Due in {days} days ({dt.strftime('%a, %I:%M %p')})"
        else:
            return f"Due in {days} days ({dt.strftime('%b %d')})"

    @classmethod
    def sync_overdue_tasks(cls, user_id=None):
        """
        Scans tasks where due_date + due_time < NOW() and status IN ('Pending', 'In Progress')
        and updates them to 'Overdue', recording in task_history and notifications.
        """
        user_filter = "AND t.user_id = %s" if user_id else ""
        params = (user_id,) if user_id else ()
        
        overdue_tasks = execute_query(
            f"""SELECT t.id, t.user_id, t.title, t.status 
                FROM tasks t 
                WHERE CONCAT(t.due_date, ' ', t.due_time) < NOW() 
                  AND t.status IN ('Pending', 'In Progress')
                  {user_filter}""",
            params,
            fetchall=True
        )
        
        for task in overdue_tasks:
            execute_query(
                "UPDATE tasks SET status = 'Overdue' WHERE id = %s",
                (task['id'],),
                commit=True
            )
            # Log to history
            execute_query(
                """INSERT INTO task_history (task_id, user_id, action, previous_status, new_status, remarks) 
                   VALUES (%s, %s, 'status_changed', %s, 'Overdue', 'Deadline elapsed without completion')""",
                (task['id'], task['user_id'], task['status']),
                commit=True
            )
            # Add notification if not already notified
            exists = execute_query(
                "SELECT id FROM notifications WHERE user_id = %s AND task_id = %s AND notification_type = 'overdue'",
                (task['user_id'], task['id']),
                fetchone=True
            )
            if not exists:
                execute_query(
                    """INSERT INTO notifications (user_id, task_id, title, message, notification_type) 
                       VALUES (%s, %s, %s, %s, 'overdue')""",
                    (task['user_id'], task['id'], 'Task Overdue Alert',
                     f"Your task '{task['title']}' is now overdue. Please review and complete it!"),
                    commit=True
                )

    @classmethod
    def find_by_id(cls, task_id, user_id=None):
        """Finds task with subject details."""
        if user_id:
            row = execute_query(
                """SELECT t.*, s.subject_code, s.subject_name, s.color AS subject_color 
                   FROM tasks t 
                   LEFT JOIN subjects s ON t.subject_id = s.id 
                   WHERE t.id = %s AND t.user_id = %s""",
                (task_id, user_id),
                fetchone=True
            )
        else:
            row = execute_query(
                """SELECT t.*, s.subject_code, s.subject_name, s.color AS subject_color 
                   FROM tasks t 
                   LEFT JOIN subjects s ON t.subject_id = s.id 
                   WHERE t.id = %s""",
                (task_id,),
                fetchone=True
            )
        return cls(row) if row else None

    @classmethod
    def get_by_user(cls, user_id, status=None, priority=None, subject_id=None, task_type=None, search=None, sort_by=None):
        """Queries tasks for a student with flexible multi-criteria filtering."""
        query = """
            SELECT t.*, s.subject_code, s.subject_name, s.color AS subject_color 
            FROM tasks t 
            LEFT JOIN subjects s ON t.subject_id = s.id 
            WHERE t.user_id = %s
        """
        params = [user_id]

        if status:
            query += " AND t.status = %s"
            params.append(status)
        if priority:
            query += " AND (t.priority = %s OR t.calculated_priority = %s)"
            params.extend([priority, priority])
        if subject_id:
            query += " AND t.subject_id = %s"
            params.append(subject_id)
        if task_type:
            query += " AND t.task_type = %s"
            params.append(task_type)
        if search:
            query += " AND (t.title LIKE %s OR t.description LIKE %s OR s.subject_code LIKE %s OR s.subject_name LIKE %s)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term])

        # Sorting logic
        if sort_by == 'deadline_asc':
            query += " ORDER BY t.due_date ASC, t.due_time ASC"
        elif sort_by == 'deadline_desc':
            query += " ORDER BY t.due_date DESC, t.due_time DESC"
        elif sort_by == 'priority':
            query += """ ORDER BY FIELD(t.calculated_priority, 'Critical', 'High', 'Medium', 'Low'), 
                                   t.due_date ASC"""
        elif sort_by == 'oldest':
            query += " ORDER BY t.created_at ASC"
        else:  # newest by default
            query += " ORDER BY t.created_at DESC"

        rows = execute_query(query, tuple(params), fetchall=True)
        return [cls(row) for row in rows]

    @classmethod
    def create(cls, user_id, subject_id, title, description, task_type, due_date, due_time, priority, calculated_priority, priority_reason):
        """Creates a new task and logs creation in history."""
        task_id = execute_query(
            """INSERT INTO tasks 
               (user_id, subject_id, title, description, task_type, due_date, due_time, 
                priority, calculated_priority, priority_reason, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')""",
            (user_id, subject_id if subject_id else None, title.strip(), 
             description.strip() if description else None, task_type, due_date, 
             due_time or '23:59:00', priority, calculated_priority, priority_reason),
            commit=True,
            return_last_id=True
        )
        
        # Log to task_history
        execute_query(
            """INSERT INTO task_history (task_id, user_id, action, previous_status, new_status, remarks) 
               VALUES (%s, %s, 'created', NULL, 'Pending', 'Task created by student')""",
            (task_id, user_id),
            commit=True
        )
        
        return cls.find_by_id(task_id, user_id)

    @classmethod
    def update(cls, task_id, user_id, subject_id, title, description, task_type, due_date, due_time, priority, calculated_priority, priority_reason, status=None):
        """Updates task information."""
        status_clause = ", status = %s" if status else ""
        params = [subject_id if subject_id else None, title.strip(), description.strip() if description else None,
                  task_type, due_date, due_time or '23:59:00', priority, calculated_priority, priority_reason]
        if status:
            params.append(status)
        params.extend([task_id, user_id])

        execute_query(
            f"""UPDATE tasks 
               SET subject_id = %s, title = %s, description = %s, task_type = %s, 
                   due_date = %s, due_time = %s, priority = %s, calculated_priority = %s, 
                   priority_reason = %s {status_clause} 
               WHERE id = %s AND user_id = %s""",
            tuple(params),
            commit=True
        )

        execute_query(
            """INSERT INTO task_history (task_id, user_id, action, remarks) 
               VALUES (%s, %s, 'updated', 'Task details updated')""",
            (task_id, user_id),
            commit=True
        )

        return cls.find_by_id(task_id, user_id)

    @classmethod
    def update_status(cls, task_id, user_id, new_status, remarks=None):
        """Updates task status and timestamp."""
        current = cls.find_by_id(task_id, user_id)
        if not current:
            return None

        completed_clause = "NOW()" if new_status == 'Completed' else "NULL"
        execute_query(
            f"""UPDATE tasks 
                SET status = %s, completed_at = {completed_clause} 
                WHERE id = %s AND user_id = %s""",
            (new_status, task_id, user_id),
            commit=True
        )

        execute_query(
            """INSERT INTO task_history (task_id, user_id, action, previous_status, new_status, remarks) 
               VALUES (%s, %s, 'status_changed', %s, %s, %s)""",
            (task_id, user_id, current.status, new_status, remarks or f"Status transitioned to {new_status}"),
            commit=True
        )

        return cls.find_by_id(task_id, user_id)

    @classmethod
    def delete(cls, task_id, user_id):
        """Deletes a task ensuring user ownership."""
        execute_query(
            "DELETE FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, user_id),
            commit=True
        )

    @classmethod
    def get_dashboard_stats(cls, user_id):
        """Calculates 6 overview cards for the student dashboard."""
        cls.sync_overdue_tasks(user_id)
        stats = execute_query(
            """SELECT 
                 COUNT(*) AS total_tasks,
                 SUM(CASE WHEN status IN ('Pending', 'In Progress') THEN 1 ELSE 0 END) AS pending_tasks,
                 SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
                 SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END) AS overdue_tasks,
                 SUM(CASE WHEN status != 'Completed' AND due_date >= CURDATE() AND due_date <= DATE_ADD(CURDATE(), INTERVAL 3 DAY) THEN 1 ELSE 0 END) AS upcoming_deadlines,
                 SUM(CASE WHEN status != 'Completed' AND (priority IN ('Critical', 'High') OR calculated_priority IN ('Critical', 'High')) THEN 1 ELSE 0 END) AS high_priority_tasks
               FROM tasks 
               WHERE user_id = %s""",
            (user_id,),
            fetchone=True
        )
        return {
            'total_tasks': stats['total_tasks'] or 0,
            'pending_tasks': stats['pending_tasks'] or 0,
            'completed_tasks': stats['completed_tasks'] or 0,
            'overdue_tasks': stats['overdue_tasks'] or 0,
            'upcoming_deadlines': stats['upcoming_deadlines'] or 0,
            'high_priority_tasks': stats['high_priority_tasks'] or 0
        }

    @classmethod
    def get_deadlines_categorized(cls, user_id):
        """Categorizes all tasks for deadline tracking."""
        cls.sync_overdue_tasks(user_id)
        tasks = cls.get_by_user(user_id, sort_by='deadline_asc')
        today = date.today()
        tomorrow = today + timedelta(days=1)

        result = {
            'today': [],
            'tomorrow': [],
            'upcoming': [],
            'overdue': [],
            'completed': []
        }

        for t in tasks:
            if t.status == 'Completed':
                result['completed'].append(t)
            elif t.status == 'Overdue' or (t.due_date and t.due_date < today):
                result['overdue'].append(t)
            elif t.due_date == today:
                result['today'].append(t)
            elif t.due_date == tomorrow:
                result['tomorrow'].append(t)
            else:
                result['upcoming'].append(t)

        return result
