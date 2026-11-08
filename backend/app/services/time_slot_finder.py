from datetime import datetime, timedelta, time

from sqlalchemy import text

from app.database import SessionLocal


def convert_to_time(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return time(hours, minutes, seconds)

    return value


def find_available_slot(
    machine_code,
    work_date,
    duration_minutes
):
    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero")

    db = SessionLocal()

    try:
        machine = db.execute(
            text("""
                SELECT id, machine_code
                FROM machines
                WHERE machine_code = :machine_code
                  AND is_active = 1
            """),
            {"machine_code": machine_code}
        ).fetchone()

        if not machine:
            print("Machine not found or inactive.")
            return None

        shifts = db.execute(
            text("""
                SELECT start_time, end_time
                FROM machine_calendars
                WHERE machine_id = :machine_id
                  AND is_working_day = 1
            """),
            {"machine_id": machine.id}
        ).fetchall()

        for shift in shifts:
            shift_start = datetime.combine(
                work_date,
                convert_to_time(shift.start_time)
            )

            shift_end = datetime.combine(
                work_date,
                convert_to_time(shift.end_time)
            )

            blocked_query = text("""
                SELECT start_time, end_time
                FROM machine_downtimes
                WHERE machine_id = :machine_id
                  AND status = 'PLANNED'
                  AND start_time < :shift_end
                  AND end_time > :shift_start

                UNION ALL

                SELECT planned_start, planned_end
                FROM operation_schedules
                WHERE machine_id = :machine_id
                  AND status IN ('SCHEDULED', 'IN_PROGRESS')
                  AND planned_start < :shift_end
                  AND planned_end > :shift_start
            """)

            blocked_records = db.execute(
                blocked_query,
                {
                    "machine_id": machine.id,
                    "shift_start": shift_start,
                    "shift_end": shift_end
                }
            ).fetchall()

            blocked_intervals = []

            for record in blocked_records:
                start = max(record[0], shift_start)
                end = min(record[1], shift_end)

                if start < end:
                    blocked_intervals.append((start, end))

            blocked_intervals.sort(key=lambda interval: interval[0])

            merged_intervals = []

            for start, end in blocked_intervals:
                if (
                    merged_intervals
                    and start <= merged_intervals[-1][1]
                ):
                    previous_start, previous_end = (
                        merged_intervals[-1]
                    )

                    merged_intervals[-1] = (
                        previous_start,
                        max(previous_end, end)
                    )
                else:
                    merged_intervals.append((start, end))

            current_start = shift_start

            for blocked_start, blocked_end in merged_intervals:
                possible_end = current_start + timedelta(
                    minutes=duration_minutes
                )

                if possible_end <= blocked_start:
                    return current_start, possible_end

                current_start = max(
                    current_start,
                    blocked_end
                )

            possible_end = current_start + timedelta(
                minutes=duration_minutes
            )

            if possible_end <= shift_end:
                return current_start, possible_end

        return None

    finally:
        db.close()


if __name__ == "__main__":
    result = find_available_slot(
        machine_code="MACH-001",
        work_date=datetime(2026, 11, 9).date(),
        duration_minutes=120
    )

    print("\nMACHINE TIME-SLOT RESULT")
    print("=" * 45)

    if result:
        start_time, end_time = result

        print("Machine: MACH-001")
        print("Operation duration: 120 minutes")
        print("Available start:", start_time)
        print("Available end:", end_time)
    else:
        print("No suitable time slot found.")