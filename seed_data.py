#!/usr/bin/env python3
"""
Seed data script for Smart Timetable Management System
Creates sample data for testing and demonstration
"""

from app import create_app, db
from app.models import (
    User, Teacher, Student, Department, Section, Subject, SubjectInstance,
    TeacherSubject, Classroom, TimetableSlot, SystemSettings
)
from datetime import time

def clear_data():
    """Clear all existing data"""
    print("Clearing existing data...")
    db.drop_all()
    db.create_all()

def create_users_and_departments():
    """Create users, teachers, students, and departments"""
    print("Creating users and departments...")

    # Create admin user
    admin = User(
        username='admin',
        role='admin',
        full_name='System Administrator',
        email='admin@timetable.local'
    )
    admin.set_password('admin123')
    db.session.add(admin)

    # Create department
    cse_dept = Department(code='CSE', name='Computer Science Engineering')
    db.session.add(cse_dept)
    db.session.flush()

    # Create sections
    sections_data = [
        {'name': 'CSE-1', 'department_id': cse_dept.id, 'year_level': 1},
        {'name': 'CSE-2', 'department_id': cse_dept.id, 'year_level': 1},
        {'name': 'CSE-3', 'department_id': cse_dept.id, 'year_level': 2},
    ]

    sections = []
    for section_data in sections_data:
        section = Section(**section_data)
        db.session.add(section)
        sections.append(section)

    db.session.flush()

    # Create teachers
    teachers_data = [
        {'username': 'teacher1', 'full_name': 'Dr. Alice Johnson', 'email': 'alice@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher2', 'full_name': 'Prof. Bob Smith', 'email': 'bob@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher3', 'full_name': 'Dr. Carol Brown', 'email': 'carol@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher4', 'full_name': 'Prof. David Wilson', 'email': 'david@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher5', 'full_name': 'Dr. Eve Davis', 'email': 'eve@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher6', 'full_name': 'Prof. Frank Miller', 'email': 'frank@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher7', 'full_name': 'Dr. Grace Taylor', 'email': 'grace@timetable.local', 'department': 'Computer Science'},
        {'username': 'teacher8', 'full_name': 'Prof. Henry Anderson', 'email': 'henry@timetable.local', 'department': 'Computer Science'},
    ]

    teachers = []
    for teacher_data in teachers_data:
        # Create user
        user = User(
            username=teacher_data['username'],
            role='teacher',
            full_name=teacher_data['full_name'],
            email=teacher_data['email']
        )
        user.set_password('teacher123')
        db.session.add(user)
        db.session.flush()

        # Create teacher
        teacher = Teacher(
            user_id=user.id,
            department=teacher_data['department'],
            max_periods_per_day=6
        )
        db.session.add(teacher)
        teachers.append(teacher)

    db.session.flush()

    # Create students
    students_per_section = 10
    for section in sections:
        for i in range(1, students_per_section + 1):
            # Create user
            user = User(
                username=f'student_{section.name.lower()}_{i:02d}',
                role='student',
                full_name=f'Student {section.name}-{i:02d}',
                email=f'student{i}@{section.name.lower()}.timetable.local'
            )
            user.set_password('student123')
            db.session.add(user)
            db.session.flush()

            # Create student
            student = Student(
                user_id=user.id,
                section_id=section.id
            )
            db.session.add(student)

    db.session.commit()
    print(f"Created {len(teachers)} teachers and {len(sections) * students_per_section} students")
    return sections, teachers

def create_subjects_and_instances(sections, teachers):
    """Create subjects and subject instances"""
    print("Creating subjects and subject instances...")

    subjects_data = [
        {'name': 'Programming Fundamentals', 'code': 'CS101', 'is_lab': False, 'periods_per_week': 4, 'is_elective': False},
        {'name': 'Data Structures', 'code': 'CS201', 'is_lab': False, 'periods_per_week': 3, 'is_elective': False},
        {'name': 'Data Structures Lab', 'code': 'CS201L', 'is_lab': True, 'lab_hours_per_week': 2, 'periods_per_week': 2, 'is_elective': False},
        {'name': 'Database Systems', 'code': 'CS301', 'is_lab': False, 'periods_per_week': 3, 'is_elective': False},
        {'name': 'Operating Systems', 'code': 'CS302', 'is_lab': False, 'periods_per_week': 4, 'is_elective': False},
        {'name': 'Computer Networks', 'code': 'CS401', 'is_lab': False, 'periods_per_week': 3, 'is_elective': False},
        {'name': 'Software Engineering', 'code': 'CS402', 'is_lab': False, 'periods_per_week': 3, 'is_elective': False},
        {'name': 'Web Development', 'code': 'CS403', 'is_lab': False, 'periods_per_week': 2, 'is_elective': False},
        {'name': 'Web Development Lab', 'code': 'CS403L', 'is_lab': True, 'lab_hours_per_week': 2, 'periods_per_week': 2, 'is_elective': False},
        {'name': 'Artificial Intelligence', 'code': 'CS501', 'is_lab': False, 'periods_per_week': 3, 'is_elective': True},
        {'name': 'Machine Learning', 'code': 'CS502', 'is_lab': False, 'periods_per_week': 3, 'is_elective': True},
        {'name': 'Mobile App Development', 'code': 'CS503', 'is_lab': False, 'periods_per_week': 3, 'is_elective': True},
    ]

    subjects = []
    for subject_data in subjects_data:
        subject = Subject(**subject_data)
        db.session.add(subject)
        subjects.append(subject)

    db.session.flush()

    # Create subject instances for each section
    for section in sections:
        for subject in subjects:
            # Skip some electives for different sections to create variety
            if subject.is_elective and section.name == 'CSE-3':
                continue

            # Create subject instance
            instance = SubjectInstance(
                subject_id=subject.id,
                section_id=section.id,
                required_periods_week=subject.periods_per_week,
                required_lab_hours_week=subject.lab_hours_per_week if subject.is_lab else 0,
                is_elective=subject.is_elective
            )
            db.session.add(instance)

    db.session.flush()

    # Create teacher-subject assignments
    teacher_subject_assignments = [
        # Teacher 1: Programming, Data Structures
        (0, [0, 1, 2]),  # CS101, CS201, CS201L
        # Teacher 2: Database, Operating Systems
        (1, [3, 4]),     # CS301, CS302
        # Teacher 3: Networks, Software Engineering
        (2, [5, 6]),     # CS401, CS402
        # Teacher 4: Web Development
        (3, [7, 8]),     # CS403, CS403L
        # Teacher 5: AI, Machine Learning
        (4, [9, 10]),    # CS501, CS502
        # Teacher 6: Mobile Development, can also teach Programming
        (5, [11, 0]),    # CS503, CS101
        # Teacher 7: Can teach multiple subjects
        (6, [1, 2, 3]),  # CS201, CS201L, CS301
        # Teacher 8: Can teach multiple subjects
        (7, [4, 5, 6]),  # CS302, CS401, CS402
    ]

    for teacher_idx, subject_indices in teacher_subject_assignments:
        teacher = teachers[teacher_idx]
        for subject_idx in subject_indices:
            if subject_idx < len(subjects):
                assignment = TeacherSubject(
                    teacher_id=teacher.id,
                    subject_id=subjects[subject_idx].id
                )
                db.session.add(assignment)

    db.session.commit()
    print(f"Created {len(subjects)} subjects and assigned to teachers")
    return subjects

def create_classrooms():
    """Create classrooms"""
    print("Creating classrooms...")

    classrooms_data = [
        {'name': 'Room-101', 'room_type': 'lecture', 'capacity': 60},
        {'name': 'Room-102', 'room_type': 'lecture', 'capacity': 60},
        {'name': 'Room-103', 'room_type': 'lecture', 'capacity': 40},
        {'name': 'Room-104', 'room_type': 'lecture', 'capacity': 40},
        {'name': 'Room-105', 'room_type': 'lecture', 'capacity': 80},
        {'name': 'Lab-201', 'room_type': 'lab', 'capacity': 30},
        {'name': 'Lab-202', 'room_type': 'lab', 'capacity': 30},
    ]

    classrooms = []
    for classroom_data in classrooms_data:
        classroom = Classroom(**classroom_data)
        db.session.add(classroom)
        classrooms.append(classroom)

    db.session.commit()
    print(f"Created {len(classrooms)} classrooms")
    return classrooms

def create_time_slots():
    """Create time slots"""
    print("Creating time slots...")

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = [
        (1, time(8, 0), time(9, 0), False),
        (2, time(9, 0), time(10, 0), False),
        (3, time(10, 0), time(10, 15), True),   # Break
        (4, time(10, 15), time(11, 15), False),
        (5, time(11, 15), time(12, 15), False),
        (6, time(12, 15), time(13, 15), True),  # Lunch
        (7, time(13, 15), time(14, 15), False),
        (8, time(14, 15), time(15, 15), False),
    ]

    slots = []
    for day in days:
        for period_no, start_time, end_time, is_break in periods:
            slot = TimetableSlot(
                day_of_week=day,
                period_no=period_no,
                start_time=start_time,
                end_time=end_time,
                is_break=is_break
            )
            db.session.add(slot)
            slots.append(slot)

    db.session.commit()
    print(f"Created {len(slots)} time slots")
    return slots

def create_system_settings():
    """Create system settings"""
    print("Creating system settings...")

    settings = [
        ('scheduler_max_iterations', 10000, 'Maximum iterations for scheduler'),
        ('scheduler_timeout_seconds', 30, 'Timeout for scheduler in seconds'),
        ('max_consecutive_periods', 3, 'Maximum consecutive periods for teachers'),
        ('semester_length_weeks', 16, 'Length of semester in weeks'),
        ('working_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'Working days of the week'),
        ('default_start_time', '08:00', 'Default start time for classes'),
        ('default_end_time', '15:15', 'Default end time for classes'),
        ('default_period_duration', 60, 'Default period duration in minutes'),
    ]

    for key, value, description in settings:
        SystemSettings.set_setting(key, value, description)

    print(f"Created {len(settings)} system settings")

def main():
    """Main function to create all seed data"""
    app = create_app()

    with app.app_context():
        print("Starting seed data creation...")
        print("=" * 50)

        # Clear existing data
        clear_data()

        # Create all data
        sections, teachers = create_users_and_departments()
        subjects = create_subjects_and_instances(sections, teachers)
        classrooms = create_classrooms()
        slots = create_time_slots()
        create_system_settings()

        print("=" * 50)
        print("Seed data creation completed!")
        print()
        print("Summary:")
        print(f"- {len(sections)} sections created")
        print(f"- {len(teachers)} teachers created")
        print(f"- {len(sections) * 10} students created")
        print(f"- {len(subjects)} subjects created")
        print(f"- {len(classrooms)} classrooms created")
        print(f"- {len(slots)} time slots created")
        print()
        print("Login credentials:")
        print("Admin: admin / admin123")
        print("Teachers: teacher1-8 / teacher123")
        print("Students: student_[section]_[number] / student123")
        print()
        print("You can now start the application and test the timetable generation!")

if __name__ == '__main__':
    main()