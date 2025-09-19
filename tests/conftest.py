import pytest
from app import create_app, db
from app.models import User, Teacher, Student, Section, Subject, Classroom, TimetableSlot
from datetime import time

@pytest.fixture
def app():
    """Create and configure a test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    """Create an admin user"""
    user = User(
        username='admin',
        role='admin',
        full_name='Test Admin',
        email='admin@test.com'
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def teacher_user(app):
    """Create a teacher user"""
    user = User(
        username='teacher1',
        role='teacher',
        full_name='Test Teacher',
        email='teacher@test.com'
    )
    user.set_password('password')
    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        department='Computer Science',
        max_periods_per_day=6
    )
    db.session.add(teacher)
    db.session.commit()
    return user

@pytest.fixture
def student_user(app):
    """Create a student user"""
    # Create section first
    section = Section(name='CSE-1', year_level=1)
    db.session.add(section)
    db.session.flush()

    user = User(
        username='student1',
        role='student',
        full_name='Test Student',
        email='student@test.com'
    )
    user.set_password('password')
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        section_id=section.id
    )
    db.session.add(student)
    db.session.commit()
    return user

@pytest.fixture
def sample_data(app):
    """Create sample data for testing"""
    # Create section
    section = Section(name='CSE-1', year_level=1)
    db.session.add(section)
    db.session.flush()

    # Create subject
    subject = Subject(
        name='Programming',
        code='CS101',
        is_lab=False,
        periods_per_week=4,
        is_elective=False
    )
    db.session.add(subject)
    db.session.flush()

    # Create classroom
    classroom = Classroom(
        name='Room-101',
        room_type='lecture',
        capacity=60
    )
    db.session.add(classroom)
    db.session.flush()

    # Create time slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    slots = []
    for day in days:
        for period in range(1, 5):
            slot = TimetableSlot(
                day_of_week=day,
                period_no=period,
                start_time=time(8 + period - 1, 0),
                end_time=time(9 + period - 1, 0),
                is_break=False
            )
            db.session.add(slot)
            slots.append(slot)

    db.session.commit()

    return {
        'section': section,
        'subject': subject,
        'classroom': classroom,
        'slots': slots
    }

def login_user(client, username, password):
    """Helper function to log in a user"""
    return client.post('/api/login', json={
        'username': username,
        'password': password
    })