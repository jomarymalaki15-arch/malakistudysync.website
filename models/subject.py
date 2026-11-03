"""
StudySync Subject Model
Handles academic subject organization, colors, and subject-specific metrics.
"""

from services.database import execute_query

class Subject:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.subject_code = data.get('subject_code')
        self.subject_name = data.get('subject_name')
        self.instructor = data.get('instructor')
        self.color = data.get('color', '#2563EB')
        self.description = data.get('description')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        # Optional joined fields
        self.task_count = data.get('task_count', 0)
        self.pending_count = data.get('pending_count', 0)
        self.completed_count = data.get('completed_count', 0)

    @classmethod
    def find_by_id(cls, subject_id, user_id=None):
        """Finds subject by ID and enforces student isolation if user_id is provided."""
        if user_id:
            row = execute_query(
                "SELECT * FROM subjects WHERE id = %s AND user_id = %s",
                (subject_id, user_id),
                fetchone=True
            )
        else:
            row = execute_query(
                "SELECT * FROM subjects WHERE id = %s",
                (subject_id,),
                fetchone=True
            )
        return cls(row) if row else None

    @classmethod
    def get_by_user(cls, user_id):
        """Retrieves all subjects owned by the student with task statistics."""
        rows = execute_query(
            """SELECT s.*, 
                      COUNT(t.id) AS task_count,
                      SUM(CASE WHEN t.status IN ('Pending', 'In Progress', 'Overdue') THEN 1 ELSE 0 END) AS pending_count,
                      SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count
               FROM subjects s
               LEFT JOIN tasks t ON s.id = t.subject_id
               WHERE s.user_id = %s
               GROUP BY s.id
               ORDER BY s.subject_code ASC""",
            (user_id,),
            fetchall=True
        )
        return [cls(row) for row in rows]

    @classmethod
    def create(cls, user_id, subject_code, subject_name, instructor=None, color='#2563EB', description=None):
        """Creates a new academic subject for the student."""
        subject_id = execute_query(
            """INSERT INTO subjects 
               (user_id, subject_code, subject_name, instructor, color, description) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, subject_code.strip().upper(), subject_name.strip(), 
             instructor.strip() if instructor else None, color, description.strip() if description else None),
            commit=True,
            return_last_id=True
        )
        return cls.find_by_id(subject_id, user_id)

    @classmethod
    def update(cls, subject_id, user_id, subject_code, subject_name, instructor=None, color='#2563EB', description=None):
        """Updates subject details ensuring user ownership."""
        execute_query(
            """UPDATE subjects 
               SET subject_code = %s, subject_name = %s, instructor = %s, color = %s, description = %s 
               WHERE id = %s AND user_id = %s""",
            (subject_code.strip().upper(), subject_name.strip(), 
             instructor.strip() if instructor else None, color, 
             description.strip() if description else None, subject_id, user_id),
            commit=True
        )
        return cls.find_by_id(subject_id, user_id)

    @classmethod
    def delete(cls, subject_id, user_id):
        """Deletes a subject belonging to user."""
        execute_query(
            "DELETE FROM subjects WHERE id = %s AND user_id = %s",
            (subject_id, user_id),
            commit=True
        )
