"""
YottaFlex Manufacturing - Labor Shift Scheduling Service
Manages plant labor availability checks, shift boundary compliance,
worker headcount allocation, concurrent labor capacity tracking,
and labor-related constraint violation logging.
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import (
    LaborShift,
    LaborAssignment,
    OperationSchedule,
    Operation,
    ConstraintViolation,
    EventHistory,
)


def convert_time_to_obj(val) -> time:
    """Helper to convert db time / timedelta / string into datetime.time object."""
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total_sec = int(val.total_seconds())
        h = (total_sec // 3600) % 24
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        return time(h, m, s)
    if isinstance(val, str):
        parts = [int(p) for p in val.split(":")]
        return time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0)
    return time(6, 0)


def get_active_labor_shifts(db: Session) -> List[dict]:
    """Retrieve all active labor shifts from the database."""
    shifts = db.query(LaborShift).filter(LaborShift.is_active == True).order_by(LaborShift.start_time).all()
    res = []
    for s in shifts:
        res.append({
            "id": s.id,
            "shift_code": s.shift_code,
            "shift_name": s.shift_name,
            "start_time": convert_time_to_obj(s.start_time),
            "end_time": convert_time_to_obj(s.end_time),
            "available_workers": s.available_workers,
        })
    return res


def find_shift_for_window(
    shifts: List[dict],
    target_start: datetime,
    target_end: datetime,
) -> Optional[dict]:
    """
    Find an active labor shift that completely covers the target window [target_start, target_end].
    Handles shifts wrapping across midnight (e.g. 22:00 to 06:00).
    """
    t_start = target_start.time()
    t_end = target_end.time()
    span_hours = (target_end - target_start).total_seconds() / 3600.0

    # If the window spans more than 8 hours, it crosses multiple shifts
    if span_hours > 8.0:
        return None

    for s in shifts:
        s_start = s["start_time"]
        s_end = s["end_time"]

        if s_end > s_start:
            # Regular intra-day shift (e.g. 06:00 to 14:00)
            if target_start.date() == target_end.date():
                if s_start <= t_start and t_end <= s_end:
                    return s
        else:
            # Midnight wrapping shift (e.g. 22:00 to 06:00)
            # Either both on evening side, both on morning side, or crossing midnight
            if t_start >= s_start and (t_end >= s_start or t_end <= s_end):
                return s
            if t_start <= s_end and t_end <= s_end:
                return s

    return None


def check_labor_availability(
    db: Session,
    target_start: datetime,
    target_end: datetime,
    required_workers: int = 1,
    existing_assignments: Optional[List[dict]] = None,
    shifts: Optional[List[dict]] = None,
) -> Tuple[bool, str, Optional[int]]:
    """
    Validate labor availability for an operation window [target_start, target_end].
    Returns:
        (is_available: bool, explanation: str, labor_shift_id: Optional[int])
    """
    if required_workers <= 0:
        return False, "Required workers must be at least 1.", None

    if shifts is None:
        shifts = get_active_labor_shifts(db)

    if not shifts:
        return False, "No active labor shifts are defined in the plant calendar.", None

    # 1. Respect labor shift start and end times (Shift boundary condition)
    covering_shift = find_shift_for_window(shifts, target_start, target_end)
    if not covering_shift:
        return (
            False,
            f"Unavailable labor: Scheduled window {target_start.strftime('%Y-%m-%d %H:%M')} to "
            f"{target_end.strftime('%Y-%m-%d %H:%M')} falls outside or crosses labor shift boundaries.",
            None,
        )

    # 2. Check maximum shift worker capacity
    if required_workers > covering_shift["available_workers"]:
        return (
            False,
            f"Insufficient labor capacity: Operation requires {required_workers} workers, "
            f"but {covering_shift['shift_name']} ({covering_shift['shift_code']}) only has "
            f"{covering_shift['available_workers']} available workers.",
            covering_shift["id"],
        )

    # 3. Check concurrent labor allocations to prevent labor capacity conflicts
    # Use existing_assignments list if provided (for high-speed in-memory scheduling), else query DB
    if existing_assignments is not None:
        concurrent_workers = 0
        for assign in existing_assignments:
            a_start = assign["assigned_start"]
            a_end = assign["assigned_end"]
            # Overlap check
            if target_start < a_end and target_end > a_start:
                concurrent_workers += assign.get("workers_assigned", 1)
    else:
        q = text("""
            SELECT COALESCE(SUM(workers_assigned), 0) AS total_assigned
            FROM labor_assignments
            WHERE assigned_start < :t_end AND assigned_end > :t_start
              AND status = 'ASSIGNED'
        """)
        concurrent_workers = db.execute(q, {"t_start": target_start, "t_end": target_end}).scalar() or 0

    if concurrent_workers + required_workers > covering_shift["available_workers"]:
        return (
            False,
            f"Labor capacity conflict: {concurrent_workers} of {covering_shift['available_workers']} workers "
            f"are already assigned during this period in {covering_shift['shift_name']}. "
            f"Cannot allocate {required_workers} additional workers.",
            covering_shift["id"],
        )

    return True, f"Labor available: {covering_shift['shift_name']} has sufficient capacity.", covering_shift["id"]


def assign_labor_to_schedule(
    db: Session,
    schedule_run_id: int,
    operation_schedule_id: int,
    labor_shift_id: int,
    workers_assigned: int,
    assigned_start: datetime,
    assigned_end: datetime,
    assignment_code: Optional[str] = None,
) -> LaborAssignment:
    """Persist an explicit labor assignment in the database."""
    if not assignment_code:
        max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM labor_assignments")).scalar() or 0
        uncommitted = sum(1 for obj in db.new if isinstance(obj, LaborAssignment))
        code = f"LBR-2026-{max_id + uncommitted + 1:06d}"
    else:
        code = assignment_code

    assignment = LaborAssignment(
        assignment_code=code,
        schedule_run_id=schedule_run_id,
        operation_schedule_id=operation_schedule_id,
        labor_shift_id=labor_shift_id,
        workers_assigned=workers_assigned,
        assigned_start=assigned_start,
        assigned_end=assigned_end,
        status="ASSIGNED",
    )
    db.add(assignment)
    return assignment
