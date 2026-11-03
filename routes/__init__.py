from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.tasks import tasks_bp
from routes.subjects import subjects_bp
from routes.calendar import calendar_bp
from routes.reminders import reminders_bp
from routes.reports import reports_bp
from routes.admin import admin_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'tasks_bp',
    'subjects_bp',
    'calendar_bp',
    'reminders_bp',
    'reports_bp',
    'admin_bp'
]
