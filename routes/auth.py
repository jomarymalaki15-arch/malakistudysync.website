"""
StudySync Authentication & User Profile Routes
Handles student registration, user login, admin access, sessions,
profile editing, and password updates.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models.user import User
from services.database import log_activity

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator ensuring that the user is authenticated in current session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator ensuring that current user has administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Access denied: Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles both student and administrator authentication."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash('Please enter both your Student ID / Email and password.', 'danger')
            return render_template('login.html')

        # Check by email or student ID
        user = User.find_by_email(identifier)
        if not user:
            user = User.find_by_student_id(identifier)

        if not user or not user.verify_password(password):
            flash('Invalid login credentials. Please check your identifier and password.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Your account has been deactivated by the administrator.', 'danger')
            return render_template('login.html')

        # Create session
        session.clear()
        session['user_id'] = user.id
        session['student_id'] = user.student_id
        session['full_name'] = user.full_name
        session['role'] = user.role
        session['avatar_color'] = user.avatar_color

        log_activity(user.id, f"{'Admin' if user.is_admin else 'Student'} Login", f"Successful login by {user.email}", request.remote_addr)

        flash(f'Welcome back, {user.full_name}!', 'success')
        
        if user.is_admin:
            return redirect(url_for('admin.index'))
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles student account self-registration."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        course_program = request.form.get('course_program', '').strip()
        year_level = request.form.get('year_level', '').strip()

        # Validation
        if not all([student_id, full_name, email, password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        # Check existing student ID or email
        if User.find_by_email(email):
            flash('An account with this email address already exists.', 'danger')
            return render_template('register.html')

        if User.find_by_student_id(student_id):
            flash('An account with this Student ID already exists.', 'danger')
            return render_template('register.html')

        try:
            new_user = User.create(
                student_id=student_id,
                full_name=full_name,
                email=email,
                password=password,
                role='student',
                course_program=course_program or 'Computer Science',
                year_level=year_level or '1st Year'
            )

            log_activity(new_user.id, "Student Registration", f"New registration for {email}", request.remote_addr)
            flash('Registration successful! You may now log in to StudySync.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f'Registration error: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    """Clears user session and logs user out."""
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, "User Logout", "Logged out from system", request.remote_addr)
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handles student profile viewing and updates."""
    user = User.find_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            course_program = request.form.get('course_program', '').strip()
            year_level = request.form.get('year_level', '').strip()
            bio = request.form.get('bio', '').strip()
            avatar_color = request.form.get('avatar_color', '#2563EB')

            if not full_name:
                flash('Full Name cannot be empty.', 'danger')
            else:
                user.update_profile(full_name, course_program, year_level, bio, avatar_color)
                session['full_name'] = full_name
                session['avatar_color'] = avatar_color
                log_activity(user.id, "Profile Updated", "Updated profile information", request.remote_addr)
                flash('Your profile has been successfully updated!', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            if not user.verify_password(current_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            else:
                user.change_password(new_password)
                log_activity(user.id, "Password Changed", "Successfully changed account password", request.remote_addr)
                flash('Your password has been updated securely!', 'success')

    return render_template('profile.html', user=user)

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handles student preference settings."""
    user_id = session['user_id']
    user = User.find_by_id(user_id)
    user_settings = User.get_user_settings(user_id) or {}

    if request.method == 'POST':
        email_notif = bool(request.form.get('email_notifications'))
        daily_digest = bool(request.form.get('daily_digest'))
        reminder_lead = int(request.form.get('reminder_lead_days', 2))
        dark_mode = bool(request.form.get('dark_mode'))
        theme_color = request.form.get('theme_color', '#2563EB')

        User.update_user_settings(user_id, email_notif, daily_digest, reminder_lead, dark_mode, theme_color)
        flash('Preferences saved successfully!', 'success')
        return redirect(url_for('auth.settings'))

    return render_template('settings.html', user=user, settings=user_settings)
