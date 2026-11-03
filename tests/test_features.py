"""
StudySync Unit & Integration Tests: Subjects, Calendar, Reminders, Reports & Admin
"""

import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User
from models.subject import Subject
from models.task import Task
from models.notification import Notification

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_student(self):
        return self.client.post('/login', data={
            'identifier': 'student@studysync.edu',
            'password': 'StudentPassword123!'
        }, follow_redirects=True)

    def login_admin(self):
        return self.client.post('/login', data={
            'identifier': 'admin@studysync.edu',
            'password': 'AdminPassword123!'
        }, follow_redirects=True)

    def test_dashboard_access(self):
        """Verifies dashboard renders with stats for logged in student."""
        self.login_student()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Academic Dashboard', response.data)
        self.assertIn(b'Overall Academic Progress', response.data)

    def test_dashboard_charts_api(self):
        """Verifies Chart.js API returns structured JSON data."""
        self.login_student()
        response = self.client.get('/api/dashboard/charts')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn('status_labels', data)
        self.assertIn('subject_labels', data)

    def test_calendar_events_api(self):
        """Verifies FullCalendar event feed JSON."""
        self.login_student()
        response = self.client.get('/api/calendar/events')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        events = response.get_json()
        self.assertIsInstance(events, list)

    def test_subject_crud(self):
        """Verifies adding and deleting a subject."""
        self.login_student()
        student = User.find_by_email('student@studysync.edu')

        # Create test subject
        sub = Subject.create(
            user_id=student.id,
            subject_code="TEST101",
            subject_name="Test Engineering",
            color="#3B82F6",
            description="Automated test subject"
        )
        self.assertIsNotNone(sub.id)

        # Retrieve
        fetched = Subject.find_by_id(sub.id, student.id)
        self.assertEqual(fetched.subject_code, "TEST101")

        # Delete
        Subject.delete(sub.id, student.id)
        self.assertIsNone(Subject.find_by_id(sub.id, student.id))

    def test_report_csv_export(self):
        """Verifies CSV report generation and download header."""
        self.login_student()
        response = self.client.get('/reports/export/csv?type=summary')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn(b'Task ID', response.data)

    def test_report_pdf_export(self):
        """Verifies PDF report generation and download header."""
        self.login_student()
        response = self.client.get('/reports/export/pdf?type=summary')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF'))

    def test_admin_panel_access_control(self):
        """Verifies that non-admin student cannot access /admin, but admin can."""
        # 1. Student access blocked
        self.login_student()
        res_student = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied', res_student.data)

        # 2. Logout student first so admin can log in
        self.client.get('/logout')

        # 3. Admin access allowed
        self.login_admin()
        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'System Administration Panel', res_admin.data)
        self.assertIn(b'Registered Student Accounts', res_admin.data)

if __name__ == '__main__':
    unittest.main()
