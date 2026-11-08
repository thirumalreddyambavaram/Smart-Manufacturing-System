def validate_schedule(
    planned_start,
    planned_end,
    duration_minutes
):
    errors = []

    if planned_end <= planned_start:
        errors.append("End time must be after start time.")

    actual_duration = (
        planned_end - planned_start
    ).total_seconds() / 60

    if actual_duration != duration_minutes:
        errors.append("Planned duration does not match calculated duration.")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    from datetime import datetime

    start = datetime(2026, 11, 9, 6, 0)
    end = datetime(2026, 11, 9, 9, 0)

    result = validate_schedule(
        planned_start=start,
        planned_end=end,
        duration_minutes=180
    )

    print("SCHEDULE VALIDATION REPORT")
    print("=" * 45)
    print("Valid:", result["valid"])
    print("Errors:", result["errors"])