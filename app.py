"""
StudySync: Intelligent Student Task and Deadline Management System
Main Flask Application Entry Point
"""

from datetime import datetime, date
from flask import Flask, render_template, session, g
from config import Config
from models.user import User
from models.notification import Notification
from routes import (
    auth_bp,
    dashboard_bp,
    tasks_bp,
    subjects_bp,
    calendar_bp,
    reminders_bp,
    reports_bp,
    admin_bp
)

def create_app(config_class=Config):
    """Application factory for StudySync."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Context Processor for Templates (Top Navigation Notification Bell & User Avatar)
    @app.context_processor
    def inject_global_data():
        user_id = session.get('user_id')
        if user_id:
            user = User.find_by_id(user_id)
            unread_count = Notification.get_unread_count(user_id)
            unread_notifications = Notification.get_unread(user_id, limit=5)
            user_settings = User.get_user_settings(user_id) or {}
            return {
                'current_user': user,
                'unread_notif_count': unread_count,
                'unread_notifs': unread_notifications,
                'user_settings': user_settings,
                'current_year': datetime.now().year,
                'today_date': date.today()
            }
        return {
            'current_user': None,
            'unread_notif_count': 0,
            'unread_notifs': [],
            'user_settings': {},
            'current_year': datetime.now().year,
            'today_date': date.today()
        }

    # Custom Jinja2 Filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%b %d, %Y'):
        if not value:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(format)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_code=404, error_message="The requested page could not be found."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', error_code=500, error_message="An internal server error occurred."), 500

    return app

app = create_app()

if __name__ == '__main__':
    print(f"Starting StudySync on http://127.0.0.1:5000 (MySQL at {Config.DB_HOST}:{Config.DB_PORT})...")
    app.run(host='127.0.0.1', port=5000, debug=True)
