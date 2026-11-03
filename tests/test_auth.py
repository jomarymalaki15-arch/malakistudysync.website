"""
StudySync Unit & Integration Tests: Authentication & Authorization
"""

import unittest
import os
import sys

# Ensure root directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user import User
from services.database import execute_query

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_admin_account_exists(self):
        """Verifies that the default seeded admin account exists and has admin privileges."""
        admin = User.find_by_email('admin@studysync.edu')
        self.assertIsNotNone(admin, "Admin account should exist in studysync_db")
        self.assertTrue(admin.is_admin, "Admin account must have role == 'admin'")
        self.assertTrue(admin.verify_password('AdminPassword123!'), "Admin password verification failed")

    def test_student_account_exists(self):
        """Verifies that the demo student account exists."""
        student = User.find_by_email('student@studysync.edu')
        self.assertIsNotNone(student, "Demo student account should exist")
        self.assertFalse(student.is_admin, "Student account must not have admin privileges")
        self.assertTrue(student.verify_password('StudentPassword123!'), "Student password verification failed")

    def test_password_hashing_security(self):
        """Verifies password hashes are secure and not stored as plain text."""
        student = User.find_by_email('student@studysync.edu')
        self.assertNotEqual(student.password_hash, 'StudentPassword123!')
        self.assertTrue(student.password_hash.startswith('scrypt:') or student.password_hash.startswith('pbkdf2:'))

    def test_unauthenticated_redirect(self):
        """Verifies that accessing protected pages without login redirects to /login."""
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_student_login_flow(self):
        """Verifies successful login flow for student."""
        response = self.client.post('/login', data={
            'identifier': 'student@studysync.edu',
            'password': 'StudentPassword123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alex Rivera', response.data)

    def test_invalid_login(self):
        """Verifies failed login with bad credentials."""
        response = self.client.post('/login', data={
            'identifier': 'student@studysync.edu',
            'password': 'WrongPassword999!'
        }, follow_redirects=True)
        self.assertIn(b'Invalid login credentials', response.data)

if __name__ == '__main__':
    unittest.main()
