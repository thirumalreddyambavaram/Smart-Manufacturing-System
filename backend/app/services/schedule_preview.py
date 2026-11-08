from datetime import datetime, timedelta

from app.services.total_duration_calculator import calculate_total_duration


def create_schedule_preview(
    machine_code,
    processing_minutes,
    previous_product,
    next_product,
    start_time
):
    duration = calculate_total_duration(
        processing_minutes,
        previous_product,
        next_product
    )

    total_minutes = duration["total_minutes"]

    end_time = start_time + timedelta(minutes=total_minutes)

    return {
        "machine_code": machine_code,
        "previous_product": previous_product,
        "next_product": next_product,
        "processing_minutes": duration["processing_minutes"],
        "changeover_minutes": duration["changeover_minutes"],
        "total_minutes": total_minutes,
        "planned_start": start_time,
        "planned_end": end_time
    }


if __name__ == "__main__":
    preview = create_schedule_preview(
        machine_code="MACH-001",
        processing_minutes=150,
        previous_product="PROD-001",
        next_product="PROD-002",
        start_time=datetime(2026, 11, 9, 6, 0)
    )

    print("PRODUCTION SCHEDULE PREVIEW")
    print("=" * 45)

    for key, value in preview.items():
        print(f"{key}: {value}")