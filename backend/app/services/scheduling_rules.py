from datetime import datetime, timedelta, time

from sqlalchemy import text


def calculate_operation_duration(
    quantity,
    estimated_time_minutes,
    capacity_per_hour
):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if estimated_time_minutes <= 0:
        raise ValueError("Operation time must be greater than zero.")

    if capacity_per_hour <= 0:
        raise ValueError("Machine capacity must be greater than zero.")

    standard_duration = quantity * estimated_time_minutes
    capacity_duration = (quantity / capacity_per_hour) * 60

    return max(
        int(standard_duration),
        int(capacity_duration + 0.999999)
    )


def calculate_changeover_time(
    db,
    machine_id,
    previous_product_id,
    next_product_id
):
    """
    Get machine-specific changeover time from the database.
    Returns setup duration in minutes.
    """

    if previous_product_id is None or next_product_id is None:
        return 0

    if previous_product_id == next_product_id:
        return 0

    query = text("""
        SELECT duration_minutes
        FROM changeover_matrix
        WHERE machine_id = :machine_id
          AND from_product_id = :from_product_id
          AND to_product_id = :to_product_id
    """)

    result = db.execute(
        query,
        {
            "machine_id": machine_id,
            "from_product_id": previous_product_id,
            "to_product_id": next_product_id
        }
    ).scalar()

    if result is None:
        # Default sequence-dependent changeover time between different products
        return 30

    return int(result)


def calculate_total_duration(
    processing_minutes,
    previous_product,
    next_product
):
    if processing_minutes <= 0:
        raise ValueError("Processing duration must be positive.")

    changeover_minutes = calculate_changeover_time(
        previous_product,
        next_product
    )

    return processing_minutes + changeover_minutes


def calculate_end_time(start_time, duration_minutes):
    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")

    return start_time + timedelta(minutes=duration_minutes)


def validate_operation_sequence(previous_end_time, next_start_time):
    if previous_end_time is None:
        return True

    return next_start_time >= previous_end_time


def validate_schedule(planned_start, planned_end, duration_minutes):
    if planned_end <= planned_start:
        return False

    actual_minutes = (
        planned_end - planned_start
    ).total_seconds() / 60

    return actual_minutes == duration_minutes


def has_time_conflict(
    start_time,
    end_time,
    blocked_start,
    blocked_end
):
    return (
        start_time < blocked_end
        and end_time > blocked_start
    )


def add_working_minutes(
    start_time,
    duration_minutes,
    shift_start=time(6, 0),
    shift_end=time(14, 0),
    working_days=None
):
    """
    Calculate the completion time across recurring working shifts.
    Machine downtime and existing bookings must be checked separately.
    """

    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")

    if shift_start >= shift_end:
        raise ValueError("Shift end must be after shift start.")

    if working_days is None:
        working_days = {0, 1, 2, 3, 4, 5, 6}

    remaining_minutes = duration_minutes
    current = start_time

    while remaining_minutes > 0:
        if current.weekday() not in working_days:
            current = datetime.combine(
                current.date() + timedelta(days=1),
                shift_start
            )
            continue

        day_start = datetime.combine(current.date(), shift_start)
        day_end = datetime.combine(current.date(), shift_end)

        if current < day_start:
            current = day_start

        if current >= day_end:
            current = datetime.combine(
                current.date() + timedelta(days=1),
                shift_start
            )
            continue

        available_minutes = int(
            (day_end - current).total_seconds() / 60
        )

        worked_minutes = min(
            remaining_minutes,
            available_minutes
        )

        current += timedelta(minutes=worked_minutes)
        remaining_minutes -= worked_minutes

        if remaining_minutes > 0:
            current = datetime.combine(
                current.date() + timedelta(days=1),
                shift_start
            )

    return current


def _convert_db_time(value):
    """Convert MySQL TIME values into Python time objects."""

    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hours, minutes, seconds)

    if isinstance(value, time):
        return value

    raise ValueError(f"Unsupported shift time: {value}")


def find_machine_work_segments(
    db,
    machine_id,
    requested_start,
    duration_minutes,
    max_search_days=365
):
    """
    Find working-time segments for one machine.

    Respects:
    - Machine working calendars
    - Planned machine downtime
    - All active scheduled and in-progress operations,
      including operations from completed scheduling runs
    - Legacy schedules without schedule segments
    """

    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")

    calendar_query = text("""
        SELECT start_time, end_time, is_working_day
        FROM machine_calendars
        WHERE machine_id = :machine_id
          AND is_working_day = 1
    """)

    calendars = db.execute(
        calendar_query,
        {"machine_id": machine_id}
    ).fetchall()

    if not calendars:
        return None

    remaining = duration_minutes
    segments = []
    current_date = requested_start.date()

    downtime_query = text("""
        SELECT start_time, end_time
        FROM machine_downtimes
        WHERE machine_id = :machine_id
          AND status = 'PLANNED'
          AND start_time < :shift_end
          AND end_time > :shift_start
    """)

    schedule_query = text("""
        SELECT
            ss.segment_start AS start_time,
            ss.segment_end AS end_time
        FROM schedule_segments ss
        JOIN operation_schedules os
            ON os.id = ss.operation_schedule_id
        WHERE os.machine_id = :machine_id
          AND os.status IN ('SCHEDULED', 'IN_PROGRESS')
          AND ss.segment_start < :shift_end
          AND ss.segment_end > :shift_start

        UNION ALL

        SELECT
            os.planned_start AS start_time,
            os.planned_end AS end_time
        FROM operation_schedules os
        WHERE os.machine_id = :machine_id
          AND os.status IN ('SCHEDULED', 'IN_PROGRESS')
          AND os.planned_start < :shift_end
          AND os.planned_end > :shift_start
          AND NOT EXISTS (
              SELECT 1
              FROM schedule_segments ss
              WHERE ss.operation_schedule_id = os.id
          )
    """)

    for _ in range(max_search_days):

        for calendar in calendars:

            shift_start_time = _convert_db_time(
                calendar.start_time
            )

            shift_end_time = _convert_db_time(
                calendar.end_time
            )

            shift_start = datetime.combine(
                current_date,
                shift_start_time
            )

            shift_end = datetime.combine(
                current_date,
                shift_end_time
            )

            if shift_end <= shift_start:
                continue

            if shift_start < requested_start:
                shift_start = requested_start

            if shift_start >= shift_end:
                continue

            parameters = {
                "machine_id": machine_id,
                "shift_start": shift_start,
                "shift_end": shift_end
            }

            downtimes = db.execute(
                downtime_query,
                parameters
            ).fetchall()

            bookings = db.execute(
                schedule_query,
                parameters
            ).fetchall()

            blocked = sorted(
                [
                    (
                        max(row.start_time, shift_start),
                        min(row.end_time, shift_end)
                    )
                    for row in list(downtimes) + list(bookings)
                ],
                key=lambda interval: interval[0]
            )

            merged = []

            for block_start, block_end in blocked:

                if not merged or block_start > merged[-1][1]:
                    merged.append([block_start, block_end])

                else:
                    merged[-1][1] = max(
                        merged[-1][1],
                        block_end
                    )

            cursor = shift_start

            for block_start, block_end in merged:

                if cursor < block_start and remaining > 0:

                    available = int(
                        (block_start - cursor).total_seconds() / 60
                    )

                    worked = min(remaining, available)

                    if worked > 0:
                        segment_end = cursor + timedelta(
                            minutes=worked
                        )

                        segments.append((cursor, segment_end))
                        remaining -= worked

                    if remaining == 0:
                        return segments

                cursor = max(cursor, block_end)

            if cursor < shift_end and remaining > 0:

                available = int(
                    (shift_end - cursor).total_seconds() / 60
                )

                worked = min(remaining, available)

                if worked > 0:
                    segment_end = cursor + timedelta(
                        minutes=worked
                    )

                    segments.append((cursor, segment_end))
                    remaining -= worked

                if remaining == 0:
                    return segments

        current_date += timedelta(days=1)

    return None
