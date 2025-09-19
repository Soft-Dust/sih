from flask import request, jsonify, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.exceptions import BadRequest
import io
import csv
from datetime import datetime, time as dt_time
from app.api import bp
from app.models import (
    User, Teacher, Student, Department, Section, Subject, SubjectInstance,
    TeacherSubject, Classroom, TimetableSlot, TimetableEntry, GenerationReport,
    SystemSettings, db
)
from app.auth import require_role, require_admin, get_current_user_data
from app.scheduler import ConstraintScheduler
from app.utils import generate_pdf_timetable

# Authentication endpoints
@bp.route('/login', methods=['POST'])
def login():
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
    logout_user()
    return jsonify({'message': 'Logout successful'})

@bp.route('/current-user', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'user': get_current_user_data()})

# Teachers CRUD
@bp.route('/teachers', methods=['GET'])
@require_role('admin', 'teacher')
def get_teachers():
    teachers = Teacher.query.all()
    return jsonify([teacher.to_dict() for teacher in teachers])

@bp.route('/teachers', methods=['POST'])
@require_admin
def create_teacher():
    data = request.get_json()

    # Create user first
    user = User(
        username=data['username'],
        role='teacher',
        full_name=data['full_name'],
        email=data.get('email')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # Get user ID

    # Create teacher
    teacher = Teacher(
        user_id=user.id,
        department=data.get('department'),
        max_periods_per_day=data.get('max_periods_per_day', 6)
    )
    db.session.add(teacher)
    db.session.commit()

    return jsonify(teacher.to_dict()), 201

@bp.route('/teachers/<int:teacher_id>', methods=['PUT'])
@require_admin
def update_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    data = request.get_json()

    # Update user
    if 'full_name' in data:
        teacher.user.full_name = data['full_name']
    if 'email' in data:
        teacher.user.email = data['email']
    if 'password' in data:
        teacher.user.set_password(data['password'])

    # Update teacher
    if 'department' in data:
        teacher.department = data['department']
    if 'max_periods_per_day' in data:
        teacher.max_periods_per_day = data['max_periods_per_day']

    db.session.commit()
    return jsonify(teacher.to_dict())

@bp.route('/teachers/<int:teacher_id>', methods=['DELETE'])
@require_admin
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = teacher.user
    db.session.delete(teacher)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Teacher deleted successfully'})

# Students CRUD
@bp.route('/students', methods=['GET'])
@require_role('admin', 'teacher')
def get_students():
    students = Student.query.all()
    return jsonify([student.to_dict() for student in students])

@bp.route('/students', methods=['POST'])
@require_admin
def create_student():
    data = request.get_json()

    # Create user first
    user = User(
        username=data['username'],
        role='student',
        full_name=data['full_name'],
        email=data.get('email')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()

    # Create student
    student = Student(
        user_id=user.id,
        section_id=data['section_id']
    )
    db.session.add(student)
    db.session.commit()

    return jsonify(student.to_dict()), 201

# Sections CRUD
@bp.route('/sections', methods=['GET'])
@require_role('admin', 'teacher')
def get_sections():
    sections = Section.query.all()
    return jsonify([section.to_dict() for section in sections])

@bp.route('/sections', methods=['POST'])
@require_admin
def create_section():
    data = request.get_json()
    section = Section(
        name=data['name'],
        department_id=data.get('department_id'),
        year_level=data.get('year_level')
    )
    db.session.add(section)
    db.session.commit()
    return jsonify(section.to_dict()), 201

@bp.route('/sections/<int:section_id>', methods=['PUT'])
@require_admin
def update_section(section_id):
    section = Section.query.get_or_404(section_id)
    data = request.get_json()

    section.name = data.get('name', section.name)
    section.department_id = data.get('department_id', section.department_id)
    section.year_level = data.get('year_level', section.year_level)

    db.session.commit()
    return jsonify(section.to_dict())

@bp.route('/sections/<int:section_id>', methods=['DELETE'])
@require_admin
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()
    return jsonify({'message': 'Section deleted successfully'})

# Subjects CRUD
@bp.route('/subjects', methods=['GET'])
@require_role('admin', 'teacher')
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([subject.to_dict() for subject in subjects])

@bp.route('/subjects', methods=['POST'])
@require_admin
def create_subject():
    data = request.get_json()
    subject = Subject(
        name=data['name'],
        code=data['code'],
        is_lab=data.get('is_lab', False),
        lab_hours_per_week=data.get('lab_hours_per_week', 0),
        periods_per_week=data['periods_per_week'],
        is_elective=data.get('is_elective', False),
        preferred_semester=data.get('preferred_semester')
    )
    db.session.add(subject)
    db.session.commit()
    return jsonify(subject.to_dict()), 201

@bp.route('/subjects/<int:subject_id>', methods=['PUT'])
@require_admin
def update_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    data = request.get_json()

    for field in ['name', 'code', 'is_lab', 'lab_hours_per_week',
                  'periods_per_week', 'is_elective', 'preferred_semester']:
        if field in data:
            setattr(subject, field, data[field])

    db.session.commit()
    return jsonify(subject.to_dict())

@bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
@require_admin
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'message': 'Subject deleted successfully'})

# Subject Instances CRUD
@bp.route('/subject-instances', methods=['GET'])
@require_role('admin', 'teacher')
def get_subject_instances():
    instances = SubjectInstance.query.all()
    return jsonify([instance.to_dict() for instance in instances])

@bp.route('/subject-instances', methods=['POST'])
@require_admin
def create_subject_instance():
    data = request.get_json()
    instance = SubjectInstance(
        subject_id=data['subject_id'],
        section_id=data['section_id'],
        required_periods_week=data['required_periods_week'],
        required_lab_hours_week=data.get('required_lab_hours_week', 0),
        is_elective=data.get('is_elective', False),
        notes=data.get('notes')
    )
    db.session.add(instance)
    db.session.commit()
    return jsonify(instance.to_dict()), 201

# Teacher-Subject assignments
@bp.route('/teacher-subjects', methods=['GET'])
@require_role('admin', 'teacher')
def get_teacher_subjects():
    assignments = TeacherSubject.query.all()
    return jsonify([assignment.to_dict() for assignment in assignments])

@bp.route('/teacher-subjects', methods=['POST'])
@require_admin
def create_teacher_subject():
    data = request.get_json()
    assignment = TeacherSubject(
        teacher_id=data['teacher_id'],
        subject_id=data['subject_id']
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify(assignment.to_dict()), 201

@bp.route('/teacher-subjects/<int:assignment_id>', methods=['DELETE'])
@require_admin
def delete_teacher_subject(assignment_id):
    assignment = TeacherSubject.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'message': 'Teacher-subject assignment deleted successfully'})

# Classrooms CRUD
@bp.route('/classrooms', methods=['GET'])
@require_role('admin', 'teacher')
def get_classrooms():
    classrooms = Classroom.query.all()
    return jsonify([classroom.to_dict() for classroom in classrooms])

@bp.route('/classrooms', methods=['POST'])
@require_admin
def create_classroom():
    data = request.get_json()
    classroom = Classroom(
        name=data['name'],
        room_type=data['room_type'],
        capacity=data.get('capacity'),
        notes=data.get('notes')
    )
    db.session.add(classroom)
    db.session.commit()
    return jsonify(classroom.to_dict()), 201

@bp.route('/classrooms/<int:classroom_id>', methods=['PUT'])
@require_admin
def update_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    data = request.get_json()

    for field in ['name', 'room_type', 'capacity', 'notes']:
        if field in data:
            setattr(classroom, field, data[field])

    db.session.commit()
    return jsonify(classroom.to_dict())

@bp.route('/classrooms/<int:classroom_id>', methods=['DELETE'])
@require_admin
def delete_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    db.session.delete(classroom)
    db.session.commit()
    return jsonify({'message': 'Classroom deleted successfully'})

# Timetable Slots management
@bp.route('/timetable-slots', methods=['GET'])
@require_role('admin', 'teacher')
def get_timetable_slots():
    slots = TimetableSlot.query.order_by(TimetableSlot.day_of_week, TimetableSlot.period_no).all()
    return jsonify([slot.to_dict() for slot in slots])

@bp.route('/timetable-slots/generate', methods=['POST'])
@require_admin
def generate_timetable_slots():
    """Generate timetable slots based on settings"""
    data = request.get_json()

    # Clear existing slots
    TimetableSlot.query.delete()

    # Get parameters
    working_days = data.get('working_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    start_time = datetime.strptime(data.get('start_time', '08:00'), '%H:%M').time()
    end_time = datetime.strptime(data.get('end_time', '15:00'), '%H:%M').time()
    period_duration = data.get('period_duration', 60)  # minutes
    break_periods = data.get('break_periods', [])  # List of period numbers that are breaks

    # Calculate periods per day
    total_minutes = (datetime.combine(datetime.today(), end_time) -
                    datetime.combine(datetime.today(), start_time)).total_seconds() / 60
    periods_per_day = int(total_minutes // period_duration)

    # Generate slots
    for day in working_days:
        for period_no in range(1, periods_per_day + 1):
            # Calculate start and end times for this period
            period_start_minutes = (period_no - 1) * period_duration
            period_start = (datetime.combine(datetime.today(), start_time) +
                          datetime.timedelta(minutes=period_start_minutes)).time()
            period_end = (datetime.combine(datetime.today(), start_time) +
                        datetime.timedelta(minutes=period_start_minutes + period_duration)).time()

            slot = TimetableSlot(
                day_of_week=day,
                period_no=period_no,
                start_time=period_start,
                end_time=period_end,
                is_break=period_no in break_periods
            )
            db.session.add(slot)

    db.session.commit()

    slots = TimetableSlot.query.order_by(TimetableSlot.day_of_week, TimetableSlot.period_no).all()
    return jsonify({
        'message': f'Generated {len(slots)} timetable slots',
        'slots': [slot.to_dict() for slot in slots]
    })

# Timetable generation
@bp.route('/generate', methods=['POST'])
@require_admin
def generate_timetable():
    """Generate timetable using constraint scheduler"""
    try:
        scheduler = ConstraintScheduler()
        result = scheduler.generate_timetable()
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Timetable generation failed: {str(e)}")
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

# Timetable viewing
@bp.route('/timetable/master', methods=['GET'])
@require_role('admin', 'teacher')
def get_master_timetable():
    """Get complete timetable for all sections"""
    entries = TimetableEntry.query.all()
    return jsonify([entry.to_dict() for entry in entries])

@bp.route('/timetable/section/<int:section_id>', methods=['GET'])
@require_role('admin', 'teacher', 'student')
def get_section_timetable(section_id):
    """Get timetable for a specific section"""
    # Check if student can only view their own section
    if current_user.role == 'student':
        if not current_user.student or current_user.student.section_id != section_id:
            return jsonify({'error': 'Access denied'}), 403

    entries = TimetableEntry.query.filter_by(section_id=section_id).all()
    return jsonify([entry.to_dict() for entry in entries])

@bp.route('/timetable/teacher/<int:teacher_id>', methods=['GET'])
@require_role('admin', 'teacher')
def get_teacher_timetable(teacher_id):
    """Get timetable for a specific teacher"""
    # Check if teacher can only view their own timetable
    if current_user.role == 'teacher':
        if not current_user.teacher or current_user.teacher.id != teacher_id:
            return jsonify({'error': 'Access denied'}), 403

    entries = TimetableEntry.query.filter_by(teacher_id=teacher_id).all()
    return jsonify([entry.to_dict() for entry in entries])

@bp.route('/timetable/student/<int:student_id>', methods=['GET'])
@require_role('admin', 'student')
def get_student_timetable(student_id):
    """Get timetable for a specific student (same as their section)"""
    if current_user.role == 'student':
        if not current_user.student or current_user.student.id != student_id:
            return jsonify({'error': 'Access denied'}), 403

    student = Student.query.get_or_404(student_id)
    entries = TimetableEntry.query.filter_by(section_id=student.section_id).all()
    return jsonify([entry.to_dict() for entry in entries])

# Manual timetable editing
@bp.route('/timetable/entry', methods=['POST'])
@require_admin
def create_timetable_entry():
    """Create or update a timetable entry"""
    data = request.get_json()

    # Check if entry already exists for this slot and section
    existing_entry = TimetableEntry.query.filter_by(
        slot_id=data['slot_id'],
        section_id=data['section_id']
    ).first()

    if existing_entry:
        # Update existing entry
        entry = existing_entry
    else:
        # Create new entry
        entry = TimetableEntry()

    entry.slot_id = data['slot_id']
    entry.section_id = data['section_id']
    entry.subject_instance_id = data.get('subject_instance_id')
    entry.teacher_id = data.get('teacher_id')
    entry.classroom_id = data.get('classroom_id')
    entry.created_by = current_user.id

    if not existing_entry:
        db.session.add(entry)

    db.session.commit()

    # Validate the change
    conflicts = validate_timetable_entry(entry)

    return jsonify({
        'entry': entry.to_dict(),
        'conflicts': conflicts
    })

@bp.route('/timetable/entry/<int:entry_id>', methods=['DELETE'])
@require_admin
def delete_timetable_entry(entry_id):
    """Delete a timetable entry"""
    entry = TimetableEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Timetable entry deleted successfully'})

def validate_timetable_entry(entry):
    """Validate a timetable entry for conflicts"""
    conflicts = []

    # Check teacher conflicts
    if entry.teacher_id:
        teacher_conflicts = TimetableEntry.query.filter(
            TimetableEntry.slot_id == entry.slot_id,
            TimetableEntry.teacher_id == entry.teacher_id,
            TimetableEntry.id != entry.id
        ).all()

        for conflict in teacher_conflicts:
            conflicts.append({
                'type': 'teacher_conflict',
                'message': f'Teacher already assigned to {conflict.section.name}',
                'conflicting_entry': conflict.to_dict()
            })

    # Check classroom conflicts
    if entry.classroom_id:
        classroom_conflicts = TimetableEntry.query.filter(
            TimetableEntry.slot_id == entry.slot_id,
            TimetableEntry.classroom_id == entry.classroom_id,
            TimetableEntry.id != entry.id
        ).all()

        for conflict in classroom_conflicts:
            conflicts.append({
                'type': 'classroom_conflict',
                'message': f'Classroom already assigned to {conflict.section.name}',
                'conflicting_entry': conflict.to_dict()
            })

    # Check section conflicts
    section_conflicts = TimetableEntry.query.filter(
        TimetableEntry.slot_id == entry.slot_id,
        TimetableEntry.section_id == entry.section_id,
        TimetableEntry.id != entry.id
    ).all()

    for conflict in section_conflicts:
        conflicts.append({
            'type': 'section_conflict',
            'message': f'Section already has a class scheduled',
            'conflicting_entry': conflict.to_dict()
        })

    return conflicts

# Export functionality
@bp.route('/timetable/export', methods=['GET'])
@require_role('admin', 'teacher', 'student')
def export_timetable():
    """Export timetable in CSV or PDF format"""
    format_type = request.args.get('format', 'csv')
    target = request.args.get('target', 'master')

    # Get entries based on target
    if target == 'master':
        entries = TimetableEntry.query.all()
        filename = 'master_timetable'
    elif target.startswith('section:'):
        section_id = int(target.split(':')[1])
        entries = TimetableEntry.query.filter_by(section_id=section_id).all()
        section = Section.query.get(section_id)
        filename = f'{section.name}_timetable' if section else 'section_timetable'
    elif target.startswith('teacher:'):
        teacher_id = int(target.split(':')[1])
        entries = TimetableEntry.query.filter_by(teacher_id=teacher_id).all()
        teacher = Teacher.query.get(teacher_id)
        filename = f'{teacher.user.username}_timetable' if teacher else 'teacher_timetable'
    else:
        return jsonify({'error': 'Invalid target'}), 400

    if format_type == 'csv':
        return export_csv(entries, filename)
    elif format_type == 'pdf':
        return export_pdf(entries, filename, target)
    else:
        return jsonify({'error': 'Invalid format'}), 400

def export_csv(entries, filename):
    """Export timetable entries as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Day', 'Period', 'Start Time', 'End Time', 'Section',
        'Subject', 'Subject Code', 'Teacher', 'Classroom', 'Is Lab'
    ])

    # Write data
    for entry in entries:
        writer.writerow([
            entry.slot.day_of_week,
            entry.slot.period_no,
            entry.slot.start_time.strftime('%H:%M'),
            entry.slot.end_time.strftime('%H:%M'),
            entry.section.name,
            entry.subject_instance.subject.name if entry.subject_instance else '',
            entry.subject_instance.subject.code if entry.subject_instance else '',
            entry.teacher.user.full_name if entry.teacher else '',
            entry.classroom.name if entry.classroom else '',
            'Yes' if entry.subject_instance and entry.subject_instance.subject.is_lab else 'No'
        ])

    output.seek(0)

    return current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )

def export_pdf(entries, filename, target):
    """Export timetable as PDF"""
    try:
        pdf_buffer = generate_pdf_timetable(entries, target)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{filename}.pdf'
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

# Generation reports
@bp.route('/generation-report/<int:report_id>', methods=['GET'])
@require_role('admin', 'teacher')
def get_generation_report(report_id):
    """Get a specific generation report"""
    report = GenerationReport.query.get_or_404(report_id)
    return jsonify(report.to_dict())

@bp.route('/generation-reports', methods=['GET'])
@require_admin
def get_generation_reports():
    """Get all generation reports"""
    reports = GenerationReport.query.order_by(GenerationReport.generation_time.desc()).limit(10).all()
    return jsonify([report.to_dict() for report in reports])

# System settings
@bp.route('/settings', methods=['GET'])
@require_admin
def get_settings():
    """Get all system settings"""
    settings = SystemSettings.query.all()
    return jsonify([setting.to_dict() for setting in settings])

@bp.route('/settings', methods=['POST'])
@require_admin
def update_settings():
    """Update system settings"""
    data = request.get_json()

    for key, value in data.items():
        SystemSettings.set_setting(key, value)

    return jsonify({'message': 'Settings updated successfully'})

# Dashboard statistics
@bp.route('/dashboard/stats', methods=['GET'])
@require_role('admin', 'teacher')
def get_dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_teachers': Teacher.query.count(),
        'total_students': Student.query.count(),
        'total_sections': Section.query.count(),
        'total_subjects': Subject.query.count(),
        'total_classrooms': Classroom.query.count(),
        'scheduled_periods': TimetableEntry.query.count(),
        'available_slots': TimetableSlot.query.filter_by(is_break=False).count(),
        'last_generation': None
    }

    # Get last generation report
    last_report = GenerationReport.query.order_by(GenerationReport.generation_time.desc()).first()
    if last_report:
        stats['last_generation'] = last_report.to_dict()

    return jsonify(stats)