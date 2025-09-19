import time
import copy
from datetime import datetime, time as dt_time
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from app.models import (
    TimetableSlot, TimetableEntry, SubjectInstance, Teacher,
    Classroom, Section, Subject, TeacherSubject, SystemSettings
)
from app import db

class SchedulerDemand:
    """Represents a scheduling demand for a subject instance"""
    def __init__(self, subject_instance, is_lab_block=False, lab_block_id=None):
        self.subject_instance = subject_instance
        self.is_lab_block = is_lab_block  # True if this is a 2-period lab block
        self.lab_block_id = lab_block_id  # Identifier for lab blocks (same for both periods)
        self.assigned_slot = None
        self.assigned_teacher = None
        self.assigned_classroom = None

    @property
    def periods_needed(self):
        return 2 if self.is_lab_block else 1

    @property
    def subject(self):
        return self.subject_instance.subject

    @property
    def section(self):
        return self.subject_instance.section

    def __repr__(self):
        lab_str = " (LAB)" if self.is_lab_block else ""
        return f"Demand({self.subject.code}-{self.section.name}{lab_str})"

class ConstraintScheduler:
    """Main scheduler implementing constraint satisfaction with backtracking"""

    def __init__(self):
        self.max_iterations = SystemSettings.get_setting('scheduler_max_iterations', 10000)
        self.timeout_seconds = SystemSettings.get_setting('scheduler_timeout_seconds', 30)
        self.max_consecutive_periods = SystemSettings.get_setting('max_consecutive_periods', 3)

        # Scheduling state
        self.demands = []
        self.available_slots = []
        self.assignments = {}  # slot_id -> TimetableEntry
        self.teacher_schedule = defaultdict(set)  # teacher_id -> set of slot_ids
        self.classroom_schedule = defaultdict(set)  # classroom_id -> set of slot_ids
        self.section_schedule = defaultdict(set)  # section_id -> set of slot_ids

        # Constraints tracking
        self.teacher_subjects = {}  # teacher_id -> set of subject_ids
        self.eligible_teachers = {}  # subject_id -> list of teacher_ids
        self.eligible_classrooms = {}  # subject_type -> list of classroom_ids

        # Statistics
        self.iterations = 0
        self.start_time = None

    def generate_timetable(self) -> Dict:
        """Main entry point for timetable generation"""
        self.start_time = time.time()
        self.iterations = 0

        try:
            # Clear existing timetable
            self._clear_existing_timetable()

            # Prepare scheduling environment
            self._prepare_environment()

            # Generate demands
            self._generate_demands()

            if not self.demands:
                return self._create_report(True, "No demands to schedule")

            # Sort demands by difficulty
            self._sort_demands_by_difficulty()

            # Attempt scheduling with backtracking
            success = self._backtrack_schedule(0)

            if success:
                # Save successful assignments
                self._save_assignments()
                # Validate final solution
                validation_result = self._validate_solution()
                return self._create_report(validation_result['valid'],
                                         validation_result['message'],
                                         validation_result.get('conflicts', []))
            else:
                # Analyze failure and provide recommendations
                analysis = self._analyze_failure()
                return self._create_report(False, "Scheduling failed", analysis)

        except Exception as e:
            return self._create_report(False, f"Scheduler error: {str(e)}")

    def _clear_existing_timetable(self):
        """Remove all existing timetable entries"""
        TimetableEntry.query.delete()
        db.session.commit()

    def _prepare_environment(self):
        """Set up available slots and constraint mappings"""
        # Get available time slots (non-break slots)
        self.available_slots = TimetableSlot.query.filter_by(is_break=False).order_by(
            TimetableSlot.day_of_week, TimetableSlot.period_no
        ).all()

        # Build teacher-subject eligibility mapping
        teacher_subjects = TeacherSubject.query.all()
        for ts in teacher_subjects:
            if ts.teacher_id not in self.teacher_subjects:
                self.teacher_subjects[ts.teacher_id] = set()
            self.teacher_subjects[ts.teacher_id].add(ts.subject_id)

            if ts.subject_id not in self.eligible_teachers:
                self.eligible_teachers[ts.subject_id] = []
            self.eligible_teachers[ts.subject_id].append(ts.teacher_id)

        # Build classroom eligibility mapping
        classrooms = Classroom.query.all()
        for room in classrooms:
            if room.room_type not in self.eligible_classrooms:
                self.eligible_classrooms[room.room_type] = []
            self.eligible_classrooms[room.room_type].append(room.id)

    def _generate_demands(self):
        """Generate scheduling demands from subject instances"""
        subject_instances = SubjectInstance.query.all()
        lab_block_counter = 0

        for si in subject_instances:
            # Regular lecture periods
            lecture_periods = si.required_periods_week
            if si.subject.is_lab:
                # Subtract lab hours from lecture periods
                lecture_periods -= si.required_lab_hours_week

            # Add regular lecture demands
            for _ in range(lecture_periods):
                self.demands.append(SchedulerDemand(si, is_lab_block=False))

            # Add lab block demands (2 consecutive periods each)
            if si.subject.is_lab and si.required_lab_hours_week > 0:
                lab_blocks_needed = si.required_lab_hours_week // 2
                for _ in range(lab_blocks_needed):
                    lab_block_counter += 1
                    # Create 2 demands for the lab block (consecutive periods)
                    self.demands.append(SchedulerDemand(si, is_lab_block=True, lab_block_id=lab_block_counter))

    def _sort_demands_by_difficulty(self):
        """Sort demands by scheduling difficulty (hardest first)"""
        def difficulty_score(demand):
            score = 0

            # Lab blocks are harder to schedule
            if demand.is_lab_block:
                score += 1000

            # Electives are harder due to pooling constraints
            if demand.subject.is_elective:
                score += 500

            # Fewer eligible teachers = harder
            eligible_teachers = self.eligible_teachers.get(demand.subject.id, [])
            score += max(0, 10 - len(eligible_teachers)) * 50

            # Fewer eligible classrooms = harder
            room_type = 'lab' if demand.subject.is_lab else 'lecture'
            eligible_rooms = self.eligible_classrooms.get(room_type, [])
            score += max(0, 10 - len(eligible_rooms)) * 30

            return score

        self.demands.sort(key=difficulty_score, reverse=True)

    def _backtrack_schedule(self, demand_index: int) -> bool:
        """Recursive backtracking algorithm"""
        self.iterations += 1

        # Check timeout
        if time.time() - self.start_time > self.timeout_seconds:
            return False

        # Check iteration limit
        if self.iterations > self.max_iterations:
            return False

        # Base case: all demands scheduled
        if demand_index >= len(self.demands):
            return True

        demand = self.demands[demand_index]

        # Get candidates for this demand
        candidates = self._get_candidates_for_demand(demand)

        for slot, teacher, classroom in candidates:
            # Try assignment
            if self._try_assignment(demand, slot, teacher, classroom):
                # Recursively try next demand
                if self._backtrack_schedule(demand_index + 1):
                    return True
                # Backtrack: undo assignment
                self._undo_assignment(demand, slot, teacher, classroom)

        return False

    def _get_candidates_for_demand(self, demand) -> List[Tuple]:
        """Get valid (slot, teacher, classroom) candidates for a demand"""
        candidates = []

        # Get eligible teachers
        eligible_teachers = self.eligible_teachers.get(demand.subject.id, [])
        if not eligible_teachers:
            return candidates

        # Get eligible classrooms
        room_type = 'lab' if demand.subject.is_lab else 'lecture'
        eligible_classrooms = self.eligible_classrooms.get(room_type, [])
        if not eligible_classrooms:
            return candidates

        # Check each slot
        for slot in self.available_slots:
            # For lab blocks, check if we can get consecutive slots
            slots_needed = [slot]
            if demand.is_lab_block:
                next_slot = self._get_next_consecutive_slot(slot)
                if not next_slot:
                    continue
                slots_needed = [slot, next_slot]

            # Check each teacher
            for teacher_id in eligible_teachers:
                # Check if teacher is available for all needed slots
                if not all(self._is_teacher_available(teacher_id, s) for s in slots_needed):
                    continue

                # Check each classroom
                for classroom_id in eligible_classrooms:
                    # Check if classroom is available for all needed slots
                    if not all(self._is_classroom_available(classroom_id, s) for s in slots_needed):
                        continue

                    # Check if section is available for all needed slots
                    if not all(self._is_section_available(demand.section.id, s) for s in slots_needed):
                        continue

                    # Additional constraints for electives
                    if demand.subject.is_elective:
                        if not self._check_elective_constraints(demand, slots_needed, teacher_id):
                            continue

                    # Valid candidate found
                    candidates.append((slots_needed[0] if len(slots_needed) == 1 else slots_needed,
                                    teacher_id, classroom_id))

        # Sort candidates by soft constraint preferences
        return self._sort_candidates_by_preference(demand, candidates)

    def _get_next_consecutive_slot(self, slot) -> Optional[TimetableSlot]:
        """Get the next consecutive slot on the same day"""
        next_slot = TimetableSlot.query.filter(
            TimetableSlot.day_of_week == slot.day_of_week,
            TimetableSlot.period_no == slot.period_no + 1,
            TimetableSlot.is_break == False
        ).first()
        return next_slot

    def _is_teacher_available(self, teacher_id: int, slot: TimetableSlot) -> bool:
        """Check if teacher is available for a slot"""
        return slot.id not in self.teacher_schedule[teacher_id]

    def _is_classroom_available(self, classroom_id: int, slot: TimetableSlot) -> bool:
        """Check if classroom is available for a slot"""
        return slot.id not in self.classroom_schedule[classroom_id]

    def _is_section_available(self, section_id: int, slot: TimetableSlot) -> bool:
        """Check if section is available for a slot"""
        return slot.id not in self.section_schedule[section_id]

    def _check_elective_constraints(self, demand, slots, teacher_id) -> bool:
        """Check constraints specific to elective subjects"""
        # For electives, ensure the same teacher doesn't teach different sections at the same time
        for slot in (slots if isinstance(slots, list) else [slots]):
            for section_id, assigned_slots in self.section_schedule.items():
                if slot.id in assigned_slots and section_id != demand.section.id:
                    # Check if the same teacher is assigned to another section in this slot
                    for existing_slot_id in assigned_slots:
                        if existing_slot_id == slot.id:
                            existing_entry = self.assignments.get(existing_slot_id)
                            if existing_entry and existing_entry.teacher_id == teacher_id:
                                # Check if it's the same elective subject
                                if (existing_entry.subject_instance and
                                    existing_entry.subject_instance.subject.is_elective and
                                    existing_entry.subject_instance.subject.id == demand.subject.id):
                                    return False
        return True

    def _sort_candidates_by_preference(self, demand, candidates) -> List[Tuple]:
        """Sort candidates by soft constraint preferences"""
        def preference_score(candidate):
            slot_or_slots, teacher_id, classroom_id = candidate
            slots = slot_or_slots if isinstance(slot_or_slots, list) else [slot_or_slots]
            score = 0

            # Prefer avoiding too many consecutive periods for teacher
            consecutive_periods = self._count_consecutive_periods(teacher_id, slots[0])
            if consecutive_periods >= self.max_consecutive_periods:
                score += 1000

            # Prefer balanced teacher loads
            teacher_load = len(self.teacher_schedule[teacher_id])
            score += teacher_load * 10

            # Prefer not scheduling labs at start/end of day
            if demand.is_lab_block:
                for slot in slots:
                    if slot.period_no <= 1 or slot.period_no >= 7:  # Assuming 8 periods max
                        score += 50

            # Prefer spreading subjects across the week
            day_distribution_penalty = self._calculate_day_distribution_penalty(demand, slots[0])
            score += day_distribution_penalty

            return score

        candidates.sort(key=preference_score)
        return candidates

    def _count_consecutive_periods(self, teacher_id: int, slot: TimetableSlot) -> int:
        """Count consecutive periods for a teacher around a given slot"""
        consecutive = 0
        current_period = slot.period_no

        # Count backwards
        for period in range(current_period - 1, 0, -1):
            prev_slot = TimetableSlot.query.filter(
                TimetableSlot.day_of_week == slot.day_of_week,
                TimetableSlot.period_no == period,
                TimetableSlot.is_break == False
            ).first()
            if prev_slot and prev_slot.id in self.teacher_schedule[teacher_id]:
                consecutive += 1
            else:
                break

        # Count forwards
        for period in range(current_period + 1, 10):  # Assuming max 10 periods
            next_slot = TimetableSlot.query.filter(
                TimetableSlot.day_of_week == slot.day_of_week,
                TimetableSlot.period_no == period,
                TimetableSlot.is_break == False
            ).first()
            if next_slot and next_slot.id in self.teacher_schedule[teacher_id]:
                consecutive += 1
            else:
                break

        return consecutive

    def _calculate_day_distribution_penalty(self, demand, slot: TimetableSlot) -> int:
        """Calculate penalty for poor day distribution of subject"""
        penalty = 0
        subject_id = demand.subject.id
        section_id = demand.section.id

        # Count how many times this subject is already scheduled for this section
        same_subject_count = 0
        for assigned_slot_id in self.section_schedule[section_id]:
            entry = self.assignments.get(assigned_slot_id)
            if (entry and entry.subject_instance and
                entry.subject_instance.subject.id == subject_id):
                assigned_slot = TimetableSlot.query.get(assigned_slot_id)
                if assigned_slot.day_of_week == slot.day_of_week:
                    same_subject_count += 1

        # Penalty for having too many of the same subject on the same day
        penalty += same_subject_count * 20

        return penalty

    def _try_assignment(self, demand, slot_or_slots, teacher_id: int, classroom_id: int) -> bool:
        """Try to assign a demand to specific resources"""
        slots = slot_or_slots if isinstance(slot_or_slots, list) else [slot_or_slots]

        # Create temporary assignments
        temp_entries = []
        for slot in slots:
            entry = TimetableEntry(
                slot_id=slot.id,
                section_id=demand.section.id,
                subject_instance_id=demand.subject_instance.id,
                teacher_id=teacher_id,
                classroom_id=classroom_id
            )
            temp_entries.append(entry)

        # Update scheduling state
        for i, slot in enumerate(slots):
            self.assignments[slot.id] = temp_entries[i]
            self.teacher_schedule[teacher_id].add(slot.id)
            self.classroom_schedule[classroom_id].add(slot.id)
            self.section_schedule[demand.section.id].add(slot.id)

        return True

    def _undo_assignment(self, demand, slot_or_slots, teacher_id: int, classroom_id: int):
        """Undo an assignment (backtrack)"""
        slots = slot_or_slots if isinstance(slot_or_slots, list) else [slot_or_slots]

        for slot in slots:
            if slot.id in self.assignments:
                del self.assignments[slot.id]
            self.teacher_schedule[teacher_id].discard(slot.id)
            self.classroom_schedule[classroom_id].discard(slot.id)
            self.section_schedule[demand.section.id].discard(slot.id)

    def _save_assignments(self):
        """Save successful assignments to database"""
        for entry in self.assignments.values():
            db.session.add(entry)
        db.session.commit()

    def _validate_solution(self) -> Dict:
        """Validate the final solution against all constraints"""
        conflicts = []

        # Check hard constraints
        # 1. No double booking of teachers
        teacher_slots = defaultdict(list)
        for entry in self.assignments.values():
            if entry.teacher_id:
                teacher_slots[entry.teacher_id].append(entry.slot_id)

        for teacher_id, slots in teacher_slots.items():
            if len(slots) != len(set(slots)):
                conflicts.append(f"Teacher {teacher_id} has conflicting assignments")

        # 2. No double booking of classrooms
        classroom_slots = defaultdict(list)
        for entry in self.assignments.values():
            if entry.classroom_id:
                classroom_slots[entry.classroom_id].append(entry.slot_id)

        for classroom_id, slots in classroom_slots.items():
            if len(slots) != len(set(slots)):
                conflicts.append(f"Classroom {classroom_id} has conflicting assignments")

        # 3. No double booking of sections
        section_slots = defaultdict(list)
        for entry in self.assignments.values():
            section_slots[entry.section_id].append(entry.slot_id)

        for section_id, slots in section_slots.items():
            if len(slots) != len(set(slots)):
                conflicts.append(f"Section {section_id} has conflicting assignments")

        # 4. Check period requirements are met
        for si in SubjectInstance.query.all():
            assigned_periods = sum(1 for entry in self.assignments.values()
                                 if entry.subject_instance_id == si.id)
            required_periods = si.required_periods_week
            if si.subject.is_lab:
                required_periods += si.required_lab_hours_week

            if assigned_periods < required_periods:
                conflicts.append(f"Subject {si.subject.code} in section {si.section.name} "
                               f"needs {required_periods} periods but only {assigned_periods} assigned")

        is_valid = len(conflicts) == 0
        message = "Solution is valid" if is_valid else f"Found {len(conflicts)} constraint violations"

        return {
            'valid': is_valid,
            'message': message,
            'conflicts': conflicts
        }

    def _analyze_failure(self) -> Dict:
        """Analyze why scheduling failed and provide recommendations"""
        analysis = {
            'unmet_demands': [],
            'bottlenecks': [],
            'recommendations': []
        }

        # Count unmet demands by subject and section
        demand_count = defaultdict(int)
        for demand in self.demands:
            key = f"{demand.subject.code}-{demand.section.name}"
            demand_count[key] += 1

        assigned_count = defaultdict(int)
        for entry in self.assignments.values():
            if entry.subject_instance:
                key = f"{entry.subject_instance.subject.code}-{entry.subject_instance.section.name}"
                assigned_count[key] += 1

        for key, needed in demand_count.items():
            assigned = assigned_count.get(key, 0)
            if assigned < needed:
                analysis['unmet_demands'].append({
                    'subject_section': key,
                    'needed': needed,
                    'assigned': assigned,
                    'missing': needed - assigned
                })

        # Identify bottlenecks
        total_slots = len(self.available_slots)
        total_demands = len(self.demands)

        if total_demands > total_slots:
            analysis['bottlenecks'].append('Insufficient time slots')
            analysis['recommendations'].append('Increase periods per day or add working days')

        # Check teacher availability
        for subject_id, teachers in self.eligible_teachers.items():
            if len(teachers) < 2:
                subject = Subject.query.get(subject_id)
                analysis['bottlenecks'].append(f'Limited teachers for {subject.name}')
                analysis['recommendations'].append(f'Assign more teachers to {subject.name}')

        # Check classroom availability
        lab_subjects = Subject.query.filter_by(is_lab=True).count()
        lab_rooms = len(self.eligible_classrooms.get('lab', []))
        if lab_subjects > 0 and lab_rooms < 2:
            analysis['bottlenecks'].append('Insufficient lab rooms')
            analysis['recommendations'].append('Add more lab rooms')

        return analysis

    def _create_report(self, success: bool, message: str, details=None) -> Dict:
        """Create a generation report"""
        report_data = {
            'success': success,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'iterations': self.iterations,
            'duration_seconds': time.time() - self.start_time if self.start_time else 0,
            'total_demands': len(self.demands),
            'assigned_demands': len(self.assignments),
            'details': details or {}
        }

        # Save report to database
        from app.models import GenerationReport
        report = GenerationReport(success=success)
        report.set_report_data(report_data)
        db.session.add(report)
        db.session.commit()

        report_data['report_id'] = report.id
        return report_data