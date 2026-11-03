"""
StudySync Notification & Reminder Model
Handles in-app alerts, deadline reminders, and notification center.
"""

from services.database import execute_query

class Notification:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.task_id = data.get('task_id')
        self.title = data.get('title')
        self.message = data.get('message')
        self.notification_type = data.get('notification_type', 'info')
        self.is_read = bool(data.get('is_read', 0))
        self.created_at = data.get('created_at')
        # Joined task fields
        self.task_title = data.get('task_title')

    @classmethod
    def get_unread(cls, user_id, limit=10):
        """Retrieves recent unread notifications for navbar bell dropdown."""
        rows = execute_query(
            """SELECT n.*, t.title AS task_title 
               FROM notifications n 
               LEFT JOIN tasks t ON n.task_id = t.id 
               WHERE n.user_id = %s AND n.is_read = 0 
               ORDER BY n.created_at DESC 
               LIMIT %s""",
            (user_id, limit),
            fetchall=True
        )
        return [cls(row) for row in rows]

    @classmethod
    def get_all(cls, user_id, limit=50):
        """Retrieves all notifications for notification management page."""
        rows = execute_query(
            """SELECT n.*, t.title AS task_title 
               FROM notifications n 
               LEFT JOIN tasks t ON n.task_id = t.id 
               WHERE n.user_id = %s 
               ORDER BY n.created_at DESC 
               LIMIT %s""",
            (user_id, limit),
            fetchall=True
        )
        return [cls(row) for row in rows]

    @classmethod
    def get_unread_count(cls, user_id):
        """Returns total unread count for badge."""
        result = execute_query(
            "SELECT COUNT(*) AS count FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,),
            fetchone=True
        )
        return result['count'] if result else 0

    @classmethod
    def mark_as_read(cls, notification_id, user_id):
        """Marks a single notification as read."""
        execute_query(
            "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, user_id),
            commit=True
        )

    @classmethod
    def mark_all_read(cls, user_id):
        """Marks all notifications for a user as read."""
        execute_query(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s",
            (user_id,),
            commit=True
        )

    @classmethod
    def delete(cls, notification_id, user_id):
        """Deletes a notification item."""
        execute_query(
            "DELETE FROM notifications WHERE id = %s AND user_id = %s",
            (notification_id, user_id),
            commit=True
        )

    @classmethod
    def create(cls, user_id, title, message, notification_type='info', task_id=None):
        """Creates a new notification preventing duplicates within the same day."""
        # Duplicate check
        existing = execute_query(
            """SELECT id FROM notifications 
               WHERE user_id = %s AND title = %s AND DATE(created_at) = CURDATE()""",
            (user_id, title),
            fetchone=True
        )
        if not existing:
            execute_query(
                """INSERT INTO notifications (user_id, task_id, title, message, notification_type) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, task_id, title, message, notification_type),
                commit=True
            )
