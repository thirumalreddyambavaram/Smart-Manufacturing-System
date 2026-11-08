def calculate_changeover_time(
    previous_product,
    next_product
):
    # No changeover is needed if the product stays the same.
    if previous_product == next_product:
        return 0

    # Temporary prototype changeover rules (minutes).
    changeover_rules = {
        ("PROD-001", "PROD-002"): 30,
        ("PROD-001", "PROD-003"): 20,
        ("PROD-002", "PROD-001"): 40,
        ("PROD-002", "PROD-003"): 25,
        ("PROD-003", "PROD-001"): 35,
        ("PROD-003", "PROD-002"): 30,
    }

    return changeover_rules.get(
        (previous_product, next_product),
        30
    )


if __name__ == "__main__":
    changeover = calculate_changeover_time(
        "PROD-001",
        "PROD-002"
    )

    print("CHANGEOVER CALCULATOR")
    print("=" * 40)
    print("Previous product: PROD-001")
    print("Next product: PROD-002")
    print("Changeover time:", changeover, "minutes")

    same_product = calculate_changeover_time(
        "PROD-001",
        "PROD-001"
    )

    print("\nTesting same product:")
    print("Changeover time:", same_product, "minutes")