
from datetime import datetime, timedelta


def calculate_production_time(quantity, capacity_per_hour):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    if capacity_per_hour <= 0:
        raise ValueError("Machine capacity must be greater than zero")

    total_hours = quantity / capacity_per_hour

    return total_hours * 60


def calculate_operation_end_time(start_time, duration_minutes):
    return start_time + timedelta(minutes=duration_minutes)
