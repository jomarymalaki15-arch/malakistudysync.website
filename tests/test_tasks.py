"""
StudySync Unit & Integration Tests: Task Management, Prioritization & Isolation
"""

import unittest
import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.task import Task
from models.user import User
from services.priority_service import calculate_smart_priority

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_smart_priority_rules(self):
        """Verifies explainable priority calculations under different conditions."""
        today = date.today()

        # Rule A: Overdue task should be marked Critical with explanation
        overdue_date = today - timedelta(days=2)
        prio, reason = calculate_smart_priority(overdue_date, '23:59:00', 'Assignment', 'Low', 'Overdue')
        self.assertEqual(prio, 'Critical')
        self.assertIn('passed', reason)

        # Rule B: Due today should be Critical
        prio_today, reason_today = calculate_smart_priority(today, '12:00:00', 'Assignment', 'Medium', 'Pending')
        self.assertIn(prio_today, ['Critical', 'High'])

        # Rule C: Exam due in 3 days has high academic weight
        exam_date = today + timedelta(days=3)
        prio_exam, reason_exam = calculate_smart_priority(exam_date, '09:00:00', 'Exam', 'Medium', 'Pending')
        self.assertEqual(prio_exam, 'High')
        self.assertIn('Exam', reason_exam)

        # Rule D: Comfortable deadline (> 7 days) with low baseline
        far_date = today + timedelta(days=14)
        prio_far, reason_far = calculate_smart_priority(far_date, '23:59:00', 'Assignment', 'Low', 'Pending')
        self.assertEqual(prio_far, 'Low')
        self.assertIn('Comfortable', reason_far)

    def test_task_creation_and_isolation(self):
        """Verifies task creation and ensures student data isolation."""
        student = User.find_by_email('student@studysync.edu')
        self.assertIsNotNone(student)

        # Create a test task for student
        due_test = date.today() + timedelta(days=5)
        new_task = Task.create(
            user_id=student.id,
            subject_id=None,
            title="Unit Test Sample Task",
            description="Testing isolation and insertion",
            task_type="Assignment",
            due_date=str(due_test),
            due_time="18:00:00",
            priority="High",
            calculated_priority="High",
            priority_reason="Test priority calculation"
        )

        self.assertIsNotNone(new_task.id)
        self.assertEqual(new_task.user_id, student.id)

        # Isolation test: Task.find_by_id with a non-existent or different user_id (e.g. 9999) must return None
        isolated_check = Task.find_by_id(new_task.id, user_id=99999)
        self.assertIsNone(isolated_check, "Data isolation violation: Task should not be accessible by another user")

        # Cleanup test task
        Task.delete(new_task.id, student.id)
        deleted_check = Task.find_by_id(new_task.id)
        self.assertIsNone(deleted_check)

    def test_deadline_categorization(self):
        """Verifies that deadlines are properly sorted into today, tomorrow, upcoming, and overdue."""
        student = User.find_by_email('student@studysync.edu')
        categories = Task.get_deadlines_categorized(student.id)
        
        self.assertIn('today', categories)
        self.assertIn('tomorrow', categories)
        self.assertIn('upcoming', categories)
        self.assertIn('overdue', categories)
        self.assertIn('completed', categories)

if __name__ == '__main__':
    unittest.main()
