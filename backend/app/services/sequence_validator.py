def validate_operation_sequence(
    previous_end_time,
    next_start_time
):
    if previous_end_time is None:
        return True

    if next_start_time < previous_end_time:
        return False

    return True


if __name__ == "__main__":
    from datetime import datetime

    cutting_end = datetime(2026, 11, 9, 8, 30)
    machining_start = datetime(2026, 11, 9, 8, 30)

    valid = validate_operation_sequence(
        previous_end_time=cutting_end,
        next_start_time=machining_start
    )

    print("OPERATION SEQUENCE VALIDATION")
    print("=" * 45)
    print("Previous operation ends:", cutting_end)
    print("Next operation starts:", machining_start)
    print("Sequence valid:", valid)

    invalid_start = datetime(2026, 11, 9, 8, 15)

    invalid = validate_operation_sequence(
        previous_end_time=cutting_end,
        next_start_time=invalid_start
    )

    print("\nTesting an invalid sequence:")
    print("Next operation starts:", invalid_start)
    print("Sequence valid:", invalid)