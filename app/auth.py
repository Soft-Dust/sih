from functools import wraps
from flask import request, jsonify, session, current_app
from flask_login import current_user
from app.models import User

def require_role(*allowed_roles):
    """Decorator to require specific roles for API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401

            if current_user.role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator to require admin role"""
    return require_role('admin')(f)

def require_teacher_or_admin(f):
    """Decorator to require teacher or admin role"""
    return require_role('admin', 'teacher')(f)

def get_current_user_data():
    """Get current user data for frontend"""
    if current_user.is_authenticated:
        data = current_user.to_dict()
        if current_user.role == 'teacher' and current_user.teacher:
            data['teacher_id'] = current_user.teacher.id
        elif current_user.role == 'student' and current_user.student:
            data['student_id'] = current_user.student.id
            data['section_id'] = current_user.student.section_id
        return data
    return None

def create_default_admin():
    """Create default admin user if none exists"""
    from app import db
    from app.models import User

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            role='admin',
            full_name='System Administrator',
            email='admin@timetable.local'
        )
        admin.set_password('admin123')  # Change this in production
        db.session.add(admin)
        db.session.commit()
        current_app.logger.info('Default admin user created: admin/admin123')
        return admin
    return admin