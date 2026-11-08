from datetime import datetime

from app.database import SessionLocal
from app.services.machine_eligibility import ELIGIBILITY_RULES
from app.services.duration_estimator import calculate_operation_duration
from app.services.time_slot_finder import find_available_slot

from sqlalchemy import text


def select_machine_and_slot(
    operation_name,
    quantity,
    estimated_time_minutes,
    work_date
):
    db = SessionLocal()

    try:
        allowed_types = ELIGIBILITY_RULES.get(
            operation_name, []
        )

        if not allowed_types:
            print("No machine eligibility rule found.")
            return None

        placeholders = ", ".join(
            f":type_{i}" for i in range(len(allowed_types))
        )

        query = text(f"""
            SELECT machine_code, capacity_per_hour
            FROM machines
            WHERE is_active = 1
              AND machine_type IN ({placeholders})
            ORDER BY capacity_per_hour DESC
        """)

        parameters = {
            f"type_{i}": machine_type
            for i, machine_type in enumerate(allowed_types)
        }

        machines = db.execute(query, parameters).fetchall()

        for machine in machines:
            duration = calculate_operation_duration(
                quantity,
                estimated_time_minutes,
                machine.capacity_per_hour
            )

            slot = find_available_slot(
                machine_code=machine.machine_code,
                work_date=work_date,
                duration_minutes=duration
            )

            if slot:
                start_time, end_time = slot

                return {
                    "machine_code": machine.machine_code,
                    "duration_minutes": duration,
                    "planned_start": start_time,
                    "planned_end": end_time
                }

        return None

    finally:
        db.close()


if __name__ == "__main__":
    result = select_machine_and_slot(
        operation_name="Cutting",
        quantity=10,
        estimated_time_minutes=15,
        work_date=datetime(2026, 11, 9).date()
    )

    print("\nMACHINE AND SLOT SELECTION")
    print("=" * 45)

    if result:
        print("Selected machine:", result["machine_code"])
        print("Duration:", result["duration_minutes"], "minutes")
        print("Start:", result["planned_start"])
        print("End:", result["planned_end"])
    else:
        print("No suitable machine and time slot found.")