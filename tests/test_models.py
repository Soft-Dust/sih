import pytest
from app.models import User, Teacher, Student, Section, Subject, SubjectInstance, Classroom, TimetableSlot

def test_user_password_hashing(app):
    """Test user password hashing and verification"""
    user = User(
        username='testuser',
        role='admin',
        full_name='Test User',
        email='test@example.com'
    )
    user.set_password('secret')

    assert user.password_hash != 'secret'
    assert user.check_password('secret')
    assert not user.check_password('wrong')

def test_user_roles(app):
    """Test user role validation"""
    user = User(
        username='testuser',
        role='admin',
        full_name='Test User'
    )
    assert user.role == 'admin'

def test_section_creation(app):
    """Test section creation and relationships"""
    section = Section(name='CSE-1', year_level=1)
    db.session.add(section)
    db.session.commit()

    assert section.id is not None
    assert section.name == 'CSE-1'
    assert section.year_level == 1

def test_subject_validation(app):
    """Test subject model validation"""
    # Regular subject
    subject = Subject(
        name='Programming',
        code='CS101',
        is_lab=False,
        periods_per_week=4,
        is_elective=False
    )
    assert subject.periods_per_week > 0

    # Lab subject
    lab_subject = Subject(
        name='Programming Lab',
        code='CS101L',
        is_lab=True,
        lab_hours_per_week=2,
        periods_per_week=2,
        is_elective=False
    )
    assert lab_subject.is_lab
    assert lab_subject.lab_hours_per_week > 0

def test_subject_instance_creation(app, sample_data):
    """Test subject instance creation"""
    from app.models import SubjectInstance, db

    instance = SubjectInstance(
        subject_id=sample_data['subject'].id,
        section_id=sample_data['section'].id,
        required_periods_week=4,
        required_lab_hours_week=0,
        is_elective=False
    )
    db.session.add(instance)
    db.session.commit()

    assert instance.id is not None
    assert instance.required_periods_week == 4
    assert instance.subject.name == 'Programming'
    assert instance.section.name == 'CSE-1'

def test_classroom_types(app):
    """Test classroom type validation"""
    lecture_room = Classroom(
        name='Room-101',
        room_type='lecture',
        capacity=60
    )
    assert lecture_room.room_type == 'lecture'

    lab_room = Classroom(
        name='Lab-201',
        room_type='lab',
        capacity=30
    )
    assert lab_room.room_type == 'lab'

def test_timetable_slot_creation(app):
    """Test timetable slot creation"""
    from datetime import time
    from app.models import db

    slot = TimetableSlot(
        day_of_week='Monday',
        period_no=1,
        start_time=time(8, 0),
        end_time=time(9, 0),
        is_break=False
    )
    db.session.add(slot)
    db.session.commit()

    assert slot.id is not None
    assert slot.day_of_week == 'Monday'
    assert slot.period_no == 1
    assert not slot.is_break

def test_teacher_student_relationships(app):
    """Test teacher and student relationships"""
    from app.models import db

    # Create section
    section = Section(name='CSE-1', year_level=1)
    db.session.add(section)
    db.session.flush()

    # Create teacher user
    teacher_user = User(
        username='teacher1',
        role='teacher',
        full_name='Test Teacher'
    )
    teacher_user.set_password('password')
    db.session.add(teacher_user)
    db.session.flush()

    teacher = Teacher(
        user_id=teacher_user.id,
        department='CS'
    )
    db.session.add(teacher)

    # Create student user
    student_user = User(
        username='student1',
        role='student',
        full_name='Test Student'
    )
    student_user.set_password('password')
    db.session.add(student_user)
    db.session.flush()

    student = Student(
        user_id=student_user.id,
        section_id=section.id
    )
    db.session.add(student)
    db.session.commit()

    # Test relationships
    assert teacher.user.role == 'teacher'
    assert student.user.role == 'student'
    assert student.section.name == 'CSE-1'

def test_model_to_dict_methods(app, sample_data):
    """Test model to_dict methods"""
    section = sample_data['section']
    subject = sample_data['subject']
    classroom = sample_data['classroom']

    section_dict = section.to_dict()
    assert 'id' in section_dict
    assert 'name' in section_dict
    assert section_dict['name'] == 'CSE-1'

    subject_dict = subject.to_dict()
    assert 'id' in subject_dict
    assert 'code' in subject_dict
    assert subject_dict['code'] == 'CS101'

    classroom_dict = classroom.to_dict()
    assert 'id' in classroom_dict
    assert 'room_type' in classroom_dict
    assert classroom_dict['room_type'] == 'lecture'