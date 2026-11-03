"""
StudySync User Model
Implements User entity, authentication, password verification,
profile management, and role-based access control.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from services.database import execute_query

class User:
    def __init__(self, data):
        self.id = data.get('id')
        self.student_id = data.get('student_id')
        self.full_name = data.get('full_name')
        self.email = data.get('email')
        self.password_hash = data.get('password_hash')
        self.role = data.get('role', 'student')
        self.course_program = data.get('course_program')
        self.year_level = data.get('year_level')
        self.bio = data.get('bio')
        self.avatar_color = data.get('avatar_color', '#2563EB')
        self.is_active = bool(data.get('is_active', 1))
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @property
    def is_admin(self):
        """Returns True if the user has administrator privileges."""
        return self.role == 'admin'

    def verify_password(self, password):
        """Verifies candidate password against stored password hash."""
        return check_password_hash(self.password_hash, password)

    @classmethod
    def find_by_id(cls, user_id):
        """Finds user by primary key ID."""
        row = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
            fetchone=True
        )
        return cls(row) if row else None

    @classmethod
    def find_by_email(cls, email):
        """Finds user by email address."""
        row = execute_query(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)",
            (email.strip(),),
            fetchone=True
        )
        return cls(row) if row else None

    @classmethod
    def find_by_student_id(cls, student_id):
        """Finds user by student / identification number."""
        row = execute_query(
            "SELECT * FROM users WHERE student_id = %s",
            (student_id.strip(),),
            fetchone=True
        )
        return cls(row) if row else None

    @classmethod
    def create(cls, student_id, full_name, email, password, role='student', course_program=None, year_level=None):
        """Creates a new registered user with hashed password."""
        hashed = generate_password_hash(password)
        user_id = execute_query(
            """INSERT INTO users 
               (student_id, full_name, email, password_hash, role, course_program, year_level) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (student_id.strip(), full_name.strip(), email.strip().lower(), hashed, role, course_program, year_level),
            commit=True,
            return_last_id=True
        )
        
        # Initialize default user settings
        execute_query(
            "INSERT INTO user_settings (user_id) VALUES (%s)",
            (user_id,),
            commit=True
        )
        
        return cls.find_by_id(user_id)

    def update_profile(self, full_name, course_program, year_level, bio, avatar_color):
        """Updates user profile information."""
        execute_query(
            """UPDATE users 
               SET full_name = %s, course_program = %s, year_level = %s, bio = %s, avatar_color = %s 
               WHERE id = %s""",
            (full_name.strip(), course_program, year_level, bio, avatar_color, self.id),
            commit=True
        )
        self.full_name = full_name
        self.course_program = course_program
        self.year_level = year_level
        self.bio = bio
        self.avatar_color = avatar_color

    def change_password(self, new_password):
        """Updates the password hash for the user."""
        new_hash = generate_password_hash(new_password)
        execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, self.id),
            commit=True
        )
        self.password_hash = new_hash

    @classmethod
    def get_all_students(cls):
        """Admin helper: returns list of all student accounts with summary task counts."""
        rows = execute_query(
            """SELECT u.id, u.student_id, u.full_name, u.email, u.role, u.course_program, 
                      u.year_level, u.is_active, u.created_at,
                      COUNT(t.id) AS total_tasks,
                      SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks
               FROM users u
               LEFT JOIN tasks t ON u.id = t.user_id
               WHERE u.role = 'student'
               GROUP BY u.id
               ORDER BY u.created_at DESC""",
            fetchall=True
        )
        return rows

    @classmethod
    def set_active_status(cls, user_id, is_active):
        """Admin helper: activates or deactivates an account."""
        execute_query(
            "UPDATE users SET is_active = %s WHERE id = %s AND role != 'admin'",
            (1 if is_active else 0, user_id),
            commit=True
        )

    @classmethod
    def get_system_stats(cls):
        """Admin helper: returns system-wide aggregate statistics."""
        stats = execute_query(
            """SELECT 
                 (SELECT COUNT(*) FROM users WHERE role = 'student') AS total_students,
                 (SELECT COUNT(*) FROM users WHERE role = 'student' AND is_active = 1) AS active_students,
                 (SELECT COUNT(*) FROM tasks) AS total_tasks,
                 (SELECT COUNT(*) FROM tasks WHERE status = 'Completed') AS completed_tasks,
                 (SELECT COUNT(*) FROM tasks WHERE status = 'Overdue') AS overdue_tasks,
                 (SELECT COUNT(*) FROM subjects) AS total_subjects""",
            fetchone=True
        )
        return stats or {}

    @classmethod
    def get_user_settings(cls, user_id):
        """Retrieves user settings preferences."""
        settings = execute_query(
            "SELECT * FROM user_settings WHERE user_id = %s",
            (user_id,),
            fetchone=True
        )
        return settings

    @classmethod
    def update_user_settings(cls, user_id, email_notifications, daily_digest, reminder_lead_days, dark_mode, theme_color):
        """Updates user preferences."""
        execute_query(
            """UPDATE user_settings 
               SET email_notifications = %s, daily_digest = %s, reminder_lead_days = %s, 
                   dark_mode = %s, theme_color = %s 
               WHERE user_id = %s""",
            (1 if email_notifications else 0, 1 if daily_digest else 0, int(reminder_lead_days),
             1 if dark_mode else 0, theme_color, user_id),
            commit=True
        )
