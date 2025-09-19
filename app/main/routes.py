from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.main import bp
from app.models import User, Teacher, Student, Section
from app.auth import require_role

@bp.route('/')
def index():
    """Main landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@bp.route('/login')
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Role-based dashboard"""
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'teacher':
        return render_template('teacher_dashboard.html')
    elif current_user.role == 'student':
        return render_template('student_dashboard.html')
    else:
        flash('Invalid user role', 'error')
        return redirect(url_for('main.login'))

# Admin pages
@bp.route('/admin/teachers')
@require_role('admin')
def admin_teachers():
    """Teacher management page"""
    return render_template('admin/teachers.html')

@bp.route('/admin/students')
@require_role('admin')
def admin_students():
    """Student management page"""
    return render_template('admin/students.html')

@bp.route('/admin/sections')
@require_role('admin')
def admin_sections():
    """Section management page"""
    return render_template('admin/sections.html')

@bp.route('/admin/subjects')
@require_role('admin')
def admin_subjects():
    """Subject management page"""
    return render_template('admin/subjects.html')

@bp.route('/admin/classrooms')
@require_role('admin')
def admin_classrooms():
    """Classroom management page"""
    return render_template('admin/classrooms.html')

@bp.route('/admin/settings')
@require_role('admin')
def admin_settings():
    """System settings page"""
    return render_template('admin/settings.html')

@bp.route('/admin/timetable-generator')
@require_role('admin')
def admin_timetable_generator():
    """Timetable generation page"""
    return render_template('admin/timetable_generator.html')

@bp.route('/admin/manual-edit')
@require_role('admin')
def admin_manual_edit():
    """Manual timetable editing page"""
    return render_template('admin/manual_edit.html')

# Timetable viewing pages
@bp.route('/timetable/master')
@require_role('admin', 'teacher')
def view_master_timetable():
    """Master timetable view"""
    return render_template('timetable/master.html')

@bp.route('/timetable/section/<int:section_id>')
@require_role('admin', 'teacher', 'student')
def view_section_timetable(section_id):
    """Section timetable view"""
    # Check permissions for students
    if current_user.role == 'student':
        if not current_user.student or current_user.student.section_id != section_id:
            flash('Access denied', 'error')
            return redirect(url_for('main.dashboard'))

    section = Section.query.get_or_404(section_id)
    return render_template('timetable/section.html', section=section)

@bp.route('/timetable/teacher/<int:teacher_id>')
@require_role('admin', 'teacher')
def view_teacher_timetable(teacher_id):
    """Teacher timetable view"""
    # Check permissions for teachers
    if current_user.role == 'teacher':
        if not current_user.teacher or current_user.teacher.id != teacher_id:
            flash('Access denied', 'error')
            return redirect(url_for('main.dashboard'))

    teacher = Teacher.query.get_or_404(teacher_id)
    return render_template('timetable/teacher.html', teacher=teacher)

@bp.route('/my-timetable')
@login_required
def my_timetable():
    """User's personal timetable"""
    if current_user.role == 'teacher' and current_user.teacher:
        return redirect(url_for('main.view_teacher_timetable', teacher_id=current_user.teacher.id))
    elif current_user.role == 'student' and current_user.student:
        return redirect(url_for('main.view_section_timetable', section_id=current_user.student.section_id))
    else:
        flash('No timetable available', 'info')
        return redirect(url_for('main.dashboard'))

# Error handlers
@bp.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return render_template('errors/403.html'), 403

@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500