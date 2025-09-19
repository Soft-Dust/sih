from functools import wraps
from flask import request, jsonify, session, current_app, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash

from app.models import User, db

# Create Blueprint
bp = Blueprint('auth', __name__)

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

@bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user, remember=True)
        return jsonify({
            'message': 'Login successful',
            'user': get_current_user_data()
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@bp.route('/current-user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user data"""
    return jsonify({'user': get_current_user_data()})

def get_current_user_data():
    """Get current user data for frontend"""
    if current_user.is_authenticated:
        data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'name': current_user.full_name
        }
        if current_user.role == 'teacher' and hasattr(current_user, 'teacher'):
            data['teacher_id'] = current_user.teacher.id
        elif current_user.role == 'student' and hasattr(current_user, 'student'):
            data['student_id'] = current_user.student.id
            data['section_id'] = current_user.student.section_id
        return data
    return None

def create_default_admin():
    """Create default admin user if none exists"""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            full_name='Administrator',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user")
    return admin