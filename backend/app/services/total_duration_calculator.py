from app.services.changeover_calculator import calculate_changeover_time


def calculate_total_duration(
    processing_minutes,
    previous_product,
    next_product
):
    if processing_minutes <= 0:
        raise ValueError("Processing time must be greater than zero")

    changeover_minutes = calculate_changeover_time(
        previous_product,
        next_product
    )

    total_minutes = processing_minutes + changeover_minutes

    return {
        "processing_minutes": processing_minutes,
        "changeover_minutes": changeover_minutes,
        "total_minutes": total_minutes
    }


if __name__ == "__main__":
    result = calculate_total_duration(
        processing_minutes=150,
        previous_product="PROD-001",
        next_product="PROD-002"
    )

    print("TOTAL PRODUCTION DURATION")
    print("=" * 40)
    print("Processing time:", result["processing_minutes"], "minutes")
    print("Changeover time:", result["changeover_minutes"], "minutes")
    print("Total machine time:", result["total_minutes"], "minutes")