from datetime import datetime, timedelta, time

from sqlalchemy import text

from app.database import SessionLocal


def convert_to_time(value):
    """Convert a MySQL time value into Python time."""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return time(hours, minutes, seconds)

    return value


def get_machine_availability(machine_code, work_date):
    db = SessionLocal()

    try:
        machine_query = text("""
            SELECT id, machine_code, machine_name
            FROM machines
            WHERE machine_code = :machine_code
              AND is_active = 1
        """)

        machine = db.execute(
            machine_query,
            {"machine_code": machine_code}
        ).fetchone()

        if not machine:
            print("Machine not found or inactive.")
            return

        calendar_query = text("""
            SELECT shift_name, start_time, end_time
            FROM machine_calendars
            WHERE machine_id = :machine_id
              AND is_working_day = 1
        """)

        shifts = db.execute(
            calendar_query,
            {"machine_id": machine.id}
        ).fetchall()

        print("\nMACHINE AVAILABILITY")
        print("=" * 50)
        print("Machine:", machine.machine_code)
        print("Date:", work_date)

        if not shifts:
            print("No working shift configured.")
            return

        for shift in shifts:
            start_time = convert_to_time(shift.start_time)
            end_time = convert_to_time(shift.end_time)

            shift_start = datetime.combine(
                work_date, start_time
            )

            shift_end = datetime.combine(
                work_date, end_time
            )

            downtime_query = text("""
                SELECT reason, start_time, end_time
                FROM machine_downtimes
                WHERE machine_id = :machine_id
                  AND status = 'PLANNED'
                  AND start_time < :shift_end
                  AND end_time > :shift_start
                ORDER BY start_time
            """)

            downtimes = db.execute(
                downtime_query,
                {
                    "machine_id": machine.id,
                    "shift_start": shift_start,
                    "shift_end": shift_end
                }
            ).fetchall()

            print("\nShift:", shift.shift_name)
            print("Shift starts:", shift_start)
            print("Shift ends:", shift_end)

            available_minutes = (
                shift_end - shift_start
            ).total_seconds() / 60

            for downtime in downtimes:
                downtime_start = max(
                    downtime.start_time, shift_start
                )

                downtime_end = min(
                    downtime.end_time, shift_end
                )

                unavailable_minutes = (
                    downtime_end - downtime_start
                ).total_seconds() / 60

                available_minutes -= unavailable_minutes

                print("\nDowntime:", downtime.reason)
                print("From:", downtime_start)
                print("To:", downtime_end)

            print(
                "\nAvailable working minutes:",
                int(available_minutes)
            )

    finally:
        db.close()


if __name__ == "__main__":
    get_machine_availability(
        "MACH-001",
        datetime(2026, 11, 9).date()
    )

    get_machine_availability(
        "MACH-003",
        datetime(2026, 11, 10).date()
    )

    get_machine_availability(
        "MACH-005",
        datetime(2026, 11, 11).date()
    )