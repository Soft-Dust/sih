import pytest
from app.scheduler import ConstraintScheduler, SchedulerDemand
from app.models import (
    Subject, Section, SubjectInstance, Teacher, Classroom,
    TimetableSlot, TeacherSubject, User, db
)
from datetime import time

def test_scheduler_initialization(app):
    """Test scheduler initialization"""
    scheduler = ConstraintScheduler()
    assert scheduler.max_iterations > 0
    assert scheduler.timeout_seconds > 0
    assert len(scheduler.demands) == 0

def test_scheduler_demand_creation(app, sample_data):
    """Test scheduler demand creation"""
    # Create subject instance
    instance = SubjectInstance(
        subject_id=sample_data['subject'].id,
        section_id=sample_data['section'].id,
        required_periods_week=4,
        required_lab_hours_week=0,
        is_elective=False
    )
    db.session.add(instance)
    db.session.commit()

    # Create regular demand
    demand = SchedulerDemand(instance, is_lab_block=False)
    assert demand.periods_needed == 1
    assert not demand.is_lab_block
    assert demand.subject_instance == instance

    # Create lab demand
    lab_demand = SchedulerDemand(instance, is_lab_block=True, lab_block_id=1)
    assert lab_demand.periods_needed == 2
    assert lab_demand.is_lab_block
    assert lab_demand.lab_block_id == 1

def test_scheduler_environment_preparation(app, sample_data):
    """Test scheduler environment preparation"""
    # Create teacher and assign subject
    teacher_user = User(
        username='teacher1',
        role='teacher',
        full_name='Test Teacher'
    )
    teacher_user.set_password('password')
    db.session.add(teacher_user)
    db.session.flush()

    teacher = Teacher(user_id=teacher_user.id, department='CS')
    db.session.add(teacher)
    db.session.flush()

    # Create teacher-subject assignment
    assignment = TeacherSubject(
        teacher_id=teacher.id,
        subject_id=sample_data['subject'].id
    )
    db.session.add(assignment)
    db.session.commit()

    scheduler = ConstraintScheduler()
    scheduler._prepare_environment()

    # Check if environment is properly prepared
    assert len(scheduler.available_slots) > 0
    assert sample_data['subject'].id in scheduler.eligible_teachers
    assert teacher.id in scheduler.eligible_teachers[sample_data['subject'].id]

def test_scheduler_demand_generation(app, sample_data):
    """Test scheduler demand generation"""
    # Create subject instance
    instance = SubjectInstance(
        subject_id=sample_data['subject'].id,
        section_id=sample_data['section'].id,
        required_periods_week=4,
        required_lab_hours_week=0,
        is_elective=False
    )
    db.session.add(instance)

    # Create lab subject and instance
    lab_subject = Subject(
        name='Programming Lab',
        code='CS101L',
        is_lab=True,
        lab_hours_per_week=2,
        periods_per_week=2,
        is_elective=False
    )
    db.session.add(lab_subject)
    db.session.flush()

    lab_instance = SubjectInstance(
        subject_id=lab_subject.id,
        section_id=sample_data['section'].id,
        required_periods_week=2,
        required_lab_hours_week=2,
        is_elective=False
    )
    db.session.add(lab_instance)
    db.session.commit()

    scheduler = ConstraintScheduler()
    scheduler._generate_demands()

    # Should have 4 regular demands + 1 lab block demand
    regular_demands = [d for d in scheduler.demands if not d.is_lab_block]
    lab_demands = [d for d in scheduler.demands if d.is_lab_block]

    assert len(regular_demands) == 4  # 4 periods for CS101
    assert len(lab_demands) == 1      # 1 lab block for CS101L

def test_scheduler_constraint_checking(app, sample_data):
    """Test scheduler constraint checking methods"""
    scheduler = ConstraintScheduler()
    scheduler._prepare_environment()

    # Test slot availability
    slot = sample_data['slots'][0]
    teacher_id = 1
    classroom_id = sample_data['classroom'].id
    section_id = sample_data['section'].id

    # Initially all should be available
    assert scheduler._is_teacher_available(teacher_id, slot)
    assert scheduler._is_classroom_available(classroom_id, slot)
    assert scheduler._is_section_available(section_id, slot)

    # Assign and check availability
    scheduler.teacher_schedule[teacher_id].add(slot.id)
    assert not scheduler._is_teacher_available(teacher_id, slot)

def test_scheduler_difficulty_sorting(app, sample_data):
    """Test demand sorting by difficulty"""
    # Create multiple subjects with different characteristics
    easy_subject = Subject(
        name='Easy Subject',
        code='EASY101',
        is_lab=False,
        periods_per_week=2,
        is_elective=False
    )

    hard_subject = Subject(
        name='Hard Subject',
        code='HARD101',
        is_lab=True,
        lab_hours_per_week=2,
        periods_per_week=4,
        is_elective=True
    )

    db.session.add_all([easy_subject, hard_subject])
    db.session.flush()

    easy_instance = SubjectInstance(
        subject_id=easy_subject.id,
        section_id=sample_data['section'].id,
        required_periods_week=2,
        is_elective=False
    )

    hard_instance = SubjectInstance(
        subject_id=hard_subject.id,
        section_id=sample_data['section'].id,
        required_periods_week=4,
        required_lab_hours_week=2,
        is_elective=True
    )

    db.session.add_all([easy_instance, hard_instance])
    db.session.commit()

    scheduler = ConstraintScheduler()
    scheduler._generate_demands()
    scheduler._sort_demands_by_difficulty()

    # Lab and elective demands should come first (harder)
    assert scheduler.demands[0].is_lab_block or scheduler.demands[0].subject.is_elective

def test_scheduler_consecutive_slot_detection(app, sample_data):
    """Test consecutive slot detection for lab blocks"""
    scheduler = ConstraintScheduler()
    scheduler._prepare_environment()

    # Get first slot of Monday
    monday_slot1 = next((s for s in sample_data['slots']
                        if s.day_of_week == 'Monday' and s.period_no == 1), None)
    assert monday_slot1 is not None

    # Should find consecutive slot
    next_slot = scheduler._get_next_consecutive_slot(monday_slot1)
    assert next_slot is not None
    assert next_slot.day_of_week == 'Monday'
    assert next_slot.period_no == 2

def test_scheduler_validation_basic(app, sample_data):
    """Test basic scheduler validation"""
    scheduler = ConstraintScheduler()

    # Test with empty assignments (should be valid)
    result = scheduler._validate_solution()
    assert result['valid']
    assert len(result['conflicts']) == 0

def test_full_scheduler_integration(app):
    """Integration test with complete scheduler setup"""
    # Create complete test environment
    section = Section(name='TEST-1', year_level=1)
    db.session.add(section)
    db.session.flush()

    subject = Subject(
        name='Test Subject',
        code='TEST101',
        is_lab=False,
        periods_per_week=2,
        is_elective=False
    )
    db.session.add(subject)
    db.session.flush()

    instance = SubjectInstance(
        subject_id=subject.id,
        section_id=section.id,
        required_periods_week=2,
        is_elective=False
    )
    db.session.add(instance)

    teacher_user = User(
        username='teacher_test',
        role='teacher',
        full_name='Test Teacher'
    )
    teacher_user.set_password('password')
    db.session.add(teacher_user)
    db.session.flush()

    teacher = Teacher(user_id=teacher_user.id, department='CS')
    db.session.add(teacher)
    db.session.flush()

    assignment = TeacherSubject(
        teacher_id=teacher.id,
        subject_id=subject.id
    )
    db.session.add(assignment)

    classroom = Classroom(
        name='TEST-ROOM',
        room_type='lecture',
        capacity=30
    )
    db.session.add(classroom)

    # Create time slots
    for day in ['Monday', 'Tuesday']:
        for period in range(1, 3):
            slot = TimetableSlot(
                day_of_week=day,
                period_no=period,
                start_time=time(8 + period - 1, 0),
                end_time=time(9 + period - 1, 0),
                is_break=False
            )
            db.session.add(slot)

    db.session.commit()

    # Run scheduler
    scheduler = ConstraintScheduler()
    result = scheduler.generate_timetable()

    # Should succeed with this simple setup
    assert 'success' in result
    assert 'message' in result
    assert 'total_demands' in result