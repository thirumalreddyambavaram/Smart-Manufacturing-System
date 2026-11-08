"""Fast acceptance checks for the scheduler's core resource constraints."""
from datetime import datetime, time

from app.services.labor_service import check_labor_availability, get_tool_busy_intervals
from app.scheduling.production_scheduler import find_feasible_machine_slot


def test_labor_capacity_rejects_overlapping_assignments():
    shift = [{"id": 7, "shift_code": "D", "shift_name": "Day",
              "start_time": time(6), "end_time": time(14), "available_workers": 3}]
    existing = [{"assigned_start": datetime(2026, 11, 10, 8),
                 "assigned_end": datetime(2026, 11, 10, 12), "workers_assigned": 3}]
    ok, message, shift_id = check_labor_availability(
        db=None, target_start=datetime(2026, 11, 10, 9),
        target_end=datetime(2026, 11, 10, 10), required_workers=1,
        existing_assignments=existing, shifts=shift)
    assert not ok and shift_id == 7 and "capacity conflict" in message


def test_tool_capacity_blocks_only_when_all_units_are_busy():
    bookings = [(datetime(2026, 11, 10, 8), datetime(2026, 11, 10, 10)),
                (datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 11))]
    assert get_tool_busy_intervals(bookings, 1) == [(datetime(2026, 11, 10, 8), datetime(2026, 11, 10, 11))]
    assert get_tool_busy_intervals(bookings, 2) == [(datetime(2026, 11, 10, 9), datetime(2026, 11, 10, 10))]


def test_machine_slot_respects_existing_bookings_and_changeover_duration():
    calendars = [{"shift_name": "Day", "start_time": time(6), "end_time": time(14)}]
    booked = [(datetime(2026, 11, 10, 8), datetime(2026, 11, 10, 10))]
    result = find_feasible_machine_slot(
        machine_id=1, requested_start=datetime(2026, 11, 10, 8),
        duration_minutes=90, calendars=calendars, downtimes=[], bookings=booked)
    assert result == [(datetime(2026, 11, 10, 10), datetime(2026, 11, 10, 11, 30))]
