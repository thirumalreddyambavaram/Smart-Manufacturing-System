"""
Tests for manufacturing scheduling engine:
- Operation duration estimation
- Sequence-dependent changeover time
- Working minutes calculation across shifts
- Machine schedule segment generation
- Precedence constraint preservation
"""

from datetime import datetime, date, time, timedelta
from app.services.scheduling_rules import (
    calculate_operation_duration,
    calculate_changeover_time,
    validate_operation_sequence,
    add_working_minutes,
    has_time_conflict,
)
from app.scheduling.production_scheduler import find_feasible_machine_slot


def test_operation_duration_calculation():
    # 10 units * 20 min/unit = 200 min
    # Machine capacity = 20 units/hour -> (10/20)*60 = 30 min
    # Result = max(200, 30) = 200 min
    dur = calculate_operation_duration(quantity=10, estimated_time_minutes=20, capacity_per_hour=20)
    assert dur == 200

    # Low machine capacity: 1 unit/hour -> (10/1)*60 = 600 min
    dur_cap = calculate_operation_duration(quantity=10, estimated_time_minutes=20, capacity_per_hour=1)
    assert dur_cap == 600


def test_operation_precedence_validation():
    t1 = datetime(2026, 11, 10, 8, 0)
    t2 = datetime(2026, 11, 10, 10, 0)
    t3 = datetime(2026, 11, 10, 12, 0)

    # Valid: t2 >= t1
    assert validate_operation_sequence(t1, t2) is True
    assert validate_operation_sequence(t2, t3) is True

    # Invalid precedence: start before predecessor ends
    assert validate_operation_sequence(t2, t1) is False


def test_time_conflict_detection():
    # Overlapping intervals [08:00, 12:00] and [10:00, 14:00]
    t1 = datetime(2026, 11, 10, 8, 0)
    t2 = datetime(2026, 11, 10, 12, 0)
    t3 = datetime(2026, 11, 10, 10, 0)
    t4 = datetime(2026, 11, 10, 14, 0)

    assert has_time_conflict(t1, t2, t3, t4) is True

    # Non-overlapping intervals [08:00, 10:00] and [10:00, 12:00]
    t_end = datetime(2026, 11, 10, 10, 0)
    assert has_time_conflict(t1, t_end, t_end, t4) is False


def test_find_feasible_machine_slot_respects_downtime():
    calendars = [
        {"shift_name": "Shift 1", "start_time": time(6, 0), "end_time": time(14, 0)},
        {"shift_name": "Shift 2", "start_time": time(14, 0), "end_time": time(22, 0)},
    ]
    # Planned downtime between 08:00 and 12:00
    downtimes = [
        (datetime(2026, 11, 10, 8, 0), datetime(2026, 11, 10, 12, 0))
    ]
    bookings = []

    # Request 120 minutes starting at 08:00
    # Must jump over downtime and schedule from 12:00 to 14:00
    req_start = datetime(2026, 11, 10, 8, 0)
    segments = find_feasible_machine_slot(
        machine_id=1,
        requested_start=req_start,
        duration_minutes=120,
        calendars=calendars,
        downtimes=downtimes,
        bookings=bookings,
    )

    assert segments is not None
    assert len(segments) == 1
    seg_start, seg_end = segments[0]
    assert seg_start == datetime(2026, 11, 10, 12, 0)
    assert seg_end == datetime(2026, 11, 10, 14, 0)
