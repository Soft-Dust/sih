#!/usr/bin/env python3
"""
Smart Timetable Management System
Main application entry point
"""

import os
from app import create_app, db
from app.models import User, Teacher, Student, Department, Section, Subject, SystemSettings
from app.auth import create_default_admin

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Add models to shell context for easier debugging"""
    return {
        'db': db,
        'User': User,
        'Teacher': Teacher,
        'Student': Student,
        'Department': Department,
        'Section': Section,
        'Subject': Subject,
        'SystemSettings': SystemSettings
    }

def setup_app():
    """Initialize application"""
    # Create default admin user
    create_default_admin()

    # Set default system settings
    default_settings = {
        'scheduler_max_iterations': 10000,
        'scheduler_timeout_seconds': 30,
        'max_consecutive_periods': 3,
        'working_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        'default_start_time': '08:00',
        'default_end_time': '15:00',
        'default_period_duration': 60,
        'semester_length_weeks': 16
    }

    for key, value in default_settings.items():
        existing = SystemSettings.query.filter_by(key=key).first()
        if not existing:
            SystemSettings.set_setting(key, value)

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    print("=" * 60)
    print("Smart Timetable Management System")
    print("=" * 60)
    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print()
    print("Default Login Credentials:")
    print("Username: admin")
    print("Password: admin123")
    print()
    print("Access the application at: http://localhost:5000")
    print("=" * 60)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        setup_app()

    # Run the application
    app.run(host=host, port=port, debug=debug)