from app.services.time_slot_finder import find_available_slot


def check_schedule_feasibility(
    machine_code,
    work_date,
    planned_start,
    duration_minutes
):
    available_slot = find_available_slot(
        machine_code=machine_code,
        work_date=work_date,
        duration_minutes=duration_minutes
    )

    if available_slot is None:
        return {
            "feasible": False,
            "message": "No continuous available slot found."
        }

    available_start, available_end = available_slot

    if available_start <= planned_start < available_end:
        return {
            "feasible": True,
            "message": "A suitable machine slot is available.",
            "available_start": available_start,
            "available_end": available_end
        }

    return {
        "feasible": False,
        "message": "The proposed start time does not match the available slot.",
        "available_start": available_start,
        "available_end": available_end
    }


if __name__ == "__main__":
    from datetime import date, datetime

    result = check_schedule_feasibility(
        machine_code="MACH-001",
        work_date=date(2026, 11, 9),
        planned_start=datetime(2026, 11, 9, 6, 0),
        duration_minutes=180
    )

    print("SCHEDULE FEASIBILITY CHECK")
    print("=" * 45)

    for key, value in result.items():
        print(f"{key}: {value}")