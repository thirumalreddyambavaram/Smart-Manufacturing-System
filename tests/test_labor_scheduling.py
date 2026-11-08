"""
Unit and integration tests for actual labor shift scheduling:
- Available labor
- Unavailable labor
- Insufficient labor capacity
- Shift boundary conditions
- Overlapping labor assignments / capacity conflicts
"""

import pytest
from datetime import datetime, date, time, timedelta
from sqlalchemy import text

from app.database import SessionLocal
from app.models import LaborShift, LaborAssignment, OperationSchedule, ProductionOrder
from app.services.labor_service import (
    check_labor_availability,
    assign_labor_to_schedule,
    get_active_labor_shifts,
)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_available_labor_successful(db_session):
    """Test checking labor availability within a valid shift with adequate capacity returns True."""
    # Morning shift: 06:00 to 14:00
    valid_start = datetime(2026, 11, 10, 8, 0, 0)
    valid_end = datetime(2026, 11, 10, 11, 0, 0)

    is_avail, explanation, shift_id = check_labor_availability(
        db=db_session,
        target_start=valid_start,
        target_end=valid_end,
        required_workers=2,
    )
    assert is_avail is True
    assert shift_id is not None
    assert "has sufficient capacity" in explanation


def test_unavailable_labor_outside_shifts(db_session):
    """Test scheduling outside defined labor shifts returns unavailable labor error."""
    # Temporarily check with dummy shift list where non-working window is tested
    custom_shifts = [
        {
            "id": 1,
            "shift_code": "SHIFT-DAY-ONLY",
            "shift_name": "Day Only",
            "start_time": time(8, 0, 0),
            "end_time": time(16, 0, 0),
            "available_workers": 10,
        }
    ]
    # Night time 01:00 to 03:00 has no active shift
    night_start = datetime(2026, 11, 10, 1, 0, 0)
    night_end = datetime(2026, 11, 10, 3, 0, 0)

    is_avail, explanation, shift_id = check_labor_availability(
        db=db_session,
        target_start=night_start,
        target_end=night_end,
        required_workers=1,
        shifts=custom_shifts,
    )
    assert is_avail is False
    assert shift_id is None
    assert "Unavailable labor" in explanation


def test_insufficient_labor_capacity_exceeds_headcount(db_session):
    """Test operation requiring more workers than the shift's total workforce is rejected."""
    # Day shift has 25 workers. Request 50 workers.
    target_start = datetime(2026, 11, 10, 8, 0, 0)
    target_end = datetime(2026, 11, 10, 10, 0, 0)

    is_avail, explanation, shift_id = check_labor_availability(
        db=db_session,
        target_start=target_start,
        target_end=target_end,
        required_workers=50,
    )
    assert is_avail is False
    assert "Insufficient labor capacity" in explanation
    assert "50 workers" in explanation


def test_shift_boundary_conditions(db_session):
    """Test operation crossing across two separate shift boundaries is rejected for single-shift assignment."""
    # 13:00 to 15:00 crosses from Shift 1 (06:00-14:00) into Shift 2 (14:00-22:00)
    crossing_start = datetime(2026, 11, 10, 13, 0, 0)
    crossing_end = datetime(2026, 11, 10, 15, 0, 0)

    is_avail, explanation, shift_id = check_labor_availability(
        db=db_session,
        target_start=crossing_start,
        target_end=crossing_end,
        required_workers=1,
    )
    assert is_avail is False
    assert "boundaries" in explanation


def test_overlapping_labor_assignments_capacity_conflict(db_session):
    """Test concurrent overlapping assignments that exhaust shift headcount trigger labor capacity conflict."""
    target_start = datetime(2026, 11, 10, 8, 0, 0)
    target_end = datetime(2026, 11, 10, 12, 0, 0)

    # Simulate existing active assignments utilizing 24 out of 25 workers
    mock_assignments = [
        {
            "assigned_start": datetime(2026, 11, 10, 7, 0, 0),
            "assigned_end": datetime(2026, 11, 10, 13, 0, 0),
            "workers_assigned": 24,
        }
    ]

    # Attempt to assign 2 more workers (24 + 2 = 26 > 25)
    is_avail, explanation, shift_id = check_labor_availability(
        db=db_session,
        target_start=target_start,
        target_end=target_end,
        required_workers=2,
        existing_assignments=mock_assignments,
    )
    assert is_avail is False
    assert "Labor capacity conflict" in explanation
    assert "24 of 25 workers are already assigned" in explanation


def test_persisting_labor_assignment(db_session):
    """Test creating an explicit labor assignment record."""
    sched = db_session.query(OperationSchedule).first()
    assert sched is not None

    shift = db_session.query(LaborShift).first()
    assert shift is not None

    assignment = assign_labor_to_schedule(
        db=db_session,
        schedule_run_id=sched.schedule_run_id or 1,
        operation_schedule_id=sched.id,
        labor_shift_id=shift.id,
        workers_assigned=1,
        assigned_start=sched.planned_start,
        assigned_end=sched.planned_end,
    )
    db_session.flush()

    assert assignment.assignment_code.startswith("LBR-2026-")
    assert assignment.operation_schedule_id == sched.id
    assert assignment.labor_shift_id == shift.id

    # Clean up test assignment
    db_session.delete(assignment)
    db_session.commit()
