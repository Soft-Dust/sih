import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from collections import defaultdict
from app.models import TimetableSlot, Section, Teacher

def generate_pdf_timetable(entries, target_type):
    """Generate PDF timetable from entries"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )

    if target_type == 'master':
        title = "Master Timetable"
    elif target_type.startswith('section:'):
        section_id = int(target_type.split(':')[1])
        section = Section.query.get(section_id)
        title = f"Timetable - {section.name}" if section else "Section Timetable"
    elif target_type.startswith('teacher:'):
        teacher_id = int(target_type.split(':')[1])
        teacher = Teacher.query.get(teacher_id)
        title = f"Timetable - {teacher.user.full_name}" if teacher else "Teacher Timetable"
    else:
        title = "Timetable"

    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))

    # Get all available slots and organize data
    slots = TimetableSlot.query.filter_by(is_break=False).order_by(
        TimetableSlot.day_of_week, TimetableSlot.period_no
    ).all()

    # Create timetable grid
    if target_type == 'master':
        table_data = create_master_timetable_grid(entries, slots)
    else:
        table_data = create_simple_timetable_grid(entries, slots)

    if table_data:
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(table)
    else:
        story.append(Paragraph("No timetable data available.", styles['Normal']))

    # Add generation timestamp
    story.append(Spacer(1, 20))
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generated on: {timestamp}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_simple_timetable_grid(entries, slots):
    """Create a simple timetable grid for single section/teacher"""
    # Get unique days and periods
    days = []
    periods = set()

    for slot in slots:
        if slot.day_of_week not in days:
            days.append(slot.day_of_week)
        periods.add(slot.period_no)

    periods = sorted(list(periods))

    # Create entry lookup
    entry_lookup = {}
    for entry in entries:
        key = (entry.slot.day_of_week, entry.slot.period_no)
        entry_lookup[key] = entry

    # Build table data
    table_data = []

    # Header row
    header = ['Period']
    for day in days:
        header.append(day)
    table_data.append(header)

    # Data rows
    for period in periods:
        row = [f"Period {period}"]
        for day in days:
            entry = entry_lookup.get((day, period))
            if entry:
                cell_text = ""
                if entry.subject_instance:
                    cell_text += f"{entry.subject_instance.subject.code}\n"
                if entry.teacher:
                    cell_text += f"{entry.teacher.user.full_name}\n"
                if entry.classroom:
                    cell_text += f"{entry.classroom.name}"
                row.append(cell_text.strip())
            else:
                row.append("")
        table_data.append(row)

    return table_data

def create_master_timetable_grid(entries, slots):
    """Create a comprehensive master timetable grid"""
    # Group entries by day and period
    timetable_grid = defaultdict(lambda: defaultdict(list))

    for entry in entries:
        day = entry.slot.day_of_week
        period = entry.slot.period_no
        timetable_grid[day][period].append(entry)

    # Get unique days and periods
    days = []
    periods = set()

    for slot in slots:
        if slot.day_of_week not in days:
            days.append(slot.day_of_week)
        periods.add(slot.period_no)

    periods = sorted(list(periods))

    # Build table data
    table_data = []

    # Header row
    header = ['Time/Day']
    for day in days:
        header.append(day)
    table_data.append(header)

    # Data rows
    for period in periods:
        # Get time for this period
        time_slot = TimetableSlot.query.filter_by(
            period_no=period, is_break=False
        ).first()
        time_str = f"Period {period}"
        if time_slot:
            time_str += f"\n{time_slot.start_time.strftime('%H:%M')}-{time_slot.end_time.strftime('%H:%M')}"

        row = [time_str]

        for day in days:
            entries_for_slot = timetable_grid[day][period]
            if entries_for_slot:
                cell_text = ""
                for entry in entries_for_slot:
                    if cell_text:
                        cell_text += "\n---\n"
                    cell_text += f"{entry.section.name}: "
                    if entry.subject_instance:
                        cell_text += f"{entry.subject_instance.subject.code}"
                    if entry.teacher:
                        cell_text += f"\n{entry.teacher.user.full_name}"
                    if entry.classroom:
                        cell_text += f"\n{entry.classroom.name}"

                row.append(cell_text)
            else:
                row.append("")

        table_data.append(row)

    return table_data

def validate_time_format(time_str):
    """Validate time format HH:MM"""
    try:
        from datetime import datetime
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def get_time_slots_for_day(day, period_duration=60, start_time="08:00", end_time="15:00"):
    """Generate time slots for a given day"""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')

    slots = []
    current = start
    period_no = 1

    while current + timedelta(minutes=period_duration) <= end:
        slot_end = current + timedelta(minutes=period_duration)
        slots.append({
            'period_no': period_no,
            'start_time': current.time(),
            'end_time': slot_end.time(),
            'day_of_week': day
        })
        current = slot_end
        period_no += 1

    return slots

def check_timetable_conflicts(entries):
    """Check for conflicts in timetable entries"""
    conflicts = []

    # Group entries by slot
    slot_entries = defaultdict(list)
    for entry in entries:
        slot_entries[entry.slot_id].append(entry)

    for slot_id, slot_entry_list in slot_entries.items():
        if len(slot_entry_list) > 1:
            # Check for teacher conflicts
            teachers = [e.teacher_id for e in slot_entry_list if e.teacher_id]
            if len(teachers) != len(set(teachers)):
                conflicts.append({
                    'type': 'teacher_conflict',
                    'slot_id': slot_id,
                    'entries': [e.id for e in slot_entry_list]
                })

            # Check for classroom conflicts
            classrooms = [e.classroom_id for e in slot_entry_list if e.classroom_id]
            if len(classrooms) != len(set(classrooms)):
                conflicts.append({
                    'type': 'classroom_conflict',
                    'slot_id': slot_id,
                    'entries': [e.id for e in slot_entry_list]
                })

    return conflicts

def calculate_teacher_workload(teacher_id):
    """Calculate workload statistics for a teacher"""
    from app.models import TimetableEntry

    entries = TimetableEntry.query.filter_by(teacher_id=teacher_id).all()

    stats = {
        'total_periods': len(entries),
        'periods_per_day': defaultdict(int),
        'subjects_taught': set(),
        'sections_taught': set()
    }

    for entry in entries:
        day = entry.slot.day_of_week
        stats['periods_per_day'][day] += 1

        if entry.subject_instance:
            stats['subjects_taught'].add(entry.subject_instance.subject.name)
            stats['sections_taught'].add(entry.section.name)

    stats['subjects_taught'] = list(stats['subjects_taught'])
    stats['sections_taught'] = list(stats['sections_taught'])
    stats['periods_per_day'] = dict(stats['periods_per_day'])

    return stats

def calculate_section_schedule_stats(section_id):
    """Calculate schedule statistics for a section"""
    from app.models import TimetableEntry, TimetableSlot

    entries = TimetableEntry.query.filter_by(section_id=section_id).all()
    total_slots = TimetableSlot.query.filter_by(is_break=False).count()

    stats = {
        'scheduled_periods': len(entries),
        'total_available_slots': total_slots,
        'utilization_percentage': (len(entries) / total_slots * 100) if total_slots > 0 else 0,
        'subjects_scheduled': defaultdict(int),
        'daily_schedule': defaultdict(int)
    }

    for entry in entries:
        if entry.subject_instance:
            subject_name = entry.subject_instance.subject.name
            stats['subjects_scheduled'][subject_name] += 1

        day = entry.slot.day_of_week
        stats['daily_schedule'][day] += 1

    stats['subjects_scheduled'] = dict(stats['subjects_scheduled'])
    stats['daily_schedule'] = dict(stats['daily_schedule'])

    return stats