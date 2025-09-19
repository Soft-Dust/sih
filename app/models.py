from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import json
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student', name='user_roles'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Check password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    max_periods_per_day = db.Column(db.Integer, default=6)

    # Relationships
    teacher_subjects = db.relationship('TeacherSubject', backref='teacher', cascade='all, delete-orphan')
    timetable_entries = db.relationship('TimetableEntry', backref='teacher')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name,
            'username': self.user.username,
            'department': self.department,
            'max_periods_per_day': self.max_periods_per_day
        }

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name,
            'username': self.user.username,
            'section_id': self.section_id,
            'section_name': self.section.name if self.section else None
        }

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Relationships
    sections = db.relationship('Section', backref='department')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    year_level = db.Column(db.Integer, nullable=True)

    # Relationships
    students = db.relationship('Student', backref='section')
    subject_instances = db.relationship('SubjectInstance', backref='section', cascade='all, delete-orphan')
    timetable_entries = db.relationship('TimetableEntry', backref='section')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'year_level': self.year_level,
            'student_count': len(self.students)
        }

class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    is_lab = db.Column(db.Boolean, default=False)
    lab_hours_per_week = db.Column(db.Integer, default=0)
    periods_per_week = db.Column(db.Integer, nullable=False)
    is_elective = db.Column(db.Boolean, default=False)
    preferred_semester = db.Column(db.String(20), nullable=True)

    # Relationships
    teacher_subjects = db.relationship('TeacherSubject', backref='subject', cascade='all, delete-orphan')
    subject_instances = db.relationship('SubjectInstance', backref='subject', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'is_lab': self.is_lab,
            'lab_hours_per_week': self.lab_hours_per_week,
            'periods_per_week': self.periods_per_week,
            'is_elective': self.is_elective,
            'preferred_semester': self.preferred_semester
        }

class SubjectInstance(db.Model):
    __tablename__ = 'subject_instances'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    required_periods_week = db.Column(db.Integer, nullable=False)
    required_lab_hours_week = db.Column(db.Integer, default=0)
    is_elective = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('subject_id', 'section_id', name='uix_subject_section'),)

    # Relationships
    timetable_entries = db.relationship('TimetableEntry', backref='subject_instance')

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'subject_code': self.subject.code,
            'section_id': self.section_id,
            'section_name': self.section.name,
            'required_periods_week': self.required_periods_week,
            'required_lab_hours_week': self.required_lab_hours_week,
            'is_elective': self.is_elective,
            'notes': self.notes
        }

class TeacherSubject(db.Model):
    __tablename__ = 'teacher_subjects'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('teacher_id', 'subject_id', name='uix_teacher_subject'),)

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name,
            'subject_code': self.subject.code
        }

class Classroom(db.Model):
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    room_type = db.Column(db.Enum('lecture', 'lab', name='room_types'), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    timetable_entries = db.relationship('TimetableEntry', backref='classroom')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'room_type': self.room_type,
            'capacity': self.capacity,
            'notes': self.notes
        }

class TimetableSlot(db.Model):
    __tablename__ = 'timetable_slots'

    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', name='weekdays'), nullable=False)
    period_no = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_break = db.Column(db.Boolean, default=False)

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('day_of_week', 'period_no', name='uix_day_period'),)

    # Relationships
    timetable_entries = db.relationship('TimetableEntry', backref='slot')

    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'period_no': self.period_no,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'is_break': self.is_break
        }

class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'

    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('timetable_slots.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    subject_instance_id = db.Column(db.Integer, db.ForeignKey('subject_instances.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_by_user = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'slot_id': self.slot_id,
            'day_of_week': self.slot.day_of_week,
            'period_no': self.slot.period_no,
            'start_time': self.slot.start_time.strftime('%H:%M') if self.slot.start_time else None,
            'end_time': self.slot.end_time.strftime('%H:%M') if self.slot.end_time else None,
            'section_id': self.section_id,
            'section_name': self.section.name,
            'subject_instance_id': self.subject_instance_id,
            'subject_name': self.subject_instance.subject.name if self.subject_instance else None,
            'subject_code': self.subject_instance.subject.code if self.subject_instance else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.user.full_name if self.teacher else None,
            'classroom_id': self.classroom_id,
            'classroom_name': self.classroom.name if self.classroom else None,
            'is_lab': self.subject_instance.subject.is_lab if self.subject_instance else False,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GenerationReport(db.Model):
    __tablename__ = 'generation_reports'

    id = db.Column(db.Integer, primary_key=True)
    generation_time = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, nullable=False)
    report_json = db.Column(db.Text, nullable=True)

    def set_report_data(self, report_data):
        """Store report data as JSON"""
        self.report_json = json.dumps(report_data)

    def get_report_data(self):
        """Retrieve report data from JSON"""
        if self.report_json:
            return json.loads(self.report_json)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'generation_time': self.generation_time.isoformat() if self.generation_time else None,
            'success': self.success,
            'report_data': self.get_report_data()
        }

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_setting(key, default_value=None):
        """Get a setting value by key"""
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            try:
                return json.loads(setting.value)
            except (json.JSONDecodeError, TypeError):
                return setting.value
        return default_value

    @staticmethod
    def set_setting(key, value, description=None):
        """Set a setting value by key"""
        setting = SystemSettings.query.filter_by(key=key).first()
        if not setting:
            setting = SystemSettings(key=key)
            db.session.add(setting)

        if isinstance(value, (dict, list)):
            setting.value = json.dumps(value)
        else:
            setting.value = str(value)

        if description:
            setting.description = description

        setting.updated_at = datetime.utcnow()
        db.session.commit()
        return setting

    def to_dict(self):
        try:
            value = json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            value = self.value

        return {
            'id': self.id,
            'key': self.key,
            'value': value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }