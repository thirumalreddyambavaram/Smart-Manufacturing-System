from math import ceil


def calculate_operation_duration(
    quantity,
    estimated_time_minutes,
    capacity_per_hour
):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    if estimated_time_minutes <= 0:
        raise ValueError("Estimated time must be greater than zero")

    if capacity_per_hour <= 0:
        raise ValueError("Machine capacity must be greater than zero")

    # Processing time based on the operation standard.
    standard_duration = quantity * estimated_time_minutes

    # Minimum time required based on machine throughput.
    capacity_duration = (quantity / capacity_per_hour) * 60

    # Respect whichever constraint requires more time.
    effective_duration = max(
        standard_duration,
        capacity_duration
    )

    return ceil(effective_duration)


if __name__ == "__main__":
    duration = calculate_operation_duration(
        quantity=100,
        estimated_time_minutes=15,
        capacity_per_hour=20
    )

    print("Quantity: 100 units")
    print("Standard processing time: 15 minutes/unit")
    print("Machine capacity: 20 units/hour")
    print("Estimated operation duration:", duration, "minutes")
    print("Estimated operation duration:", duration / 60, "hours")