from sqlalchemy import text

from app.database import SessionLocal


# Prototype rules: operation name -> eligible machine type
ELIGIBILITY_RULES = {
    "Cutting": ["CUTTING"],
    "CNC Machining": ["CNC"],
    "Machining": ["CNC"],
    "Assembly": ["ASSEMBLY"],
    "Finishing": ["FINISHING"],
    "Inspection": ["FINISHING"],
}


def get_eligible_machines(operation_name):
    allowed_types = ELIGIBILITY_RULES.get(operation_name, [])

    if not allowed_types:
        return []

    db = SessionLocal()

    try:
        query = text("""
            SELECT machine_code, machine_name, machine_type,
                   capacity_per_hour
            FROM machines
            WHERE is_active = 1
              AND machine_type IN :machine_types
            ORDER BY machine_code
        """).bindparams()

        # Build safe SQL placeholders for the allowed machine types.
        placeholders = ", ".join(
            f":type_{index}" for index in range(len(allowed_types))
        )

        sql = text(f"""
            SELECT machine_code, machine_name, machine_type,
                   capacity_per_hour
            FROM machines
            WHERE is_active = 1
              AND machine_type IN ({placeholders})
            ORDER BY machine_code
        """)

        parameters = {
            f"type_{index}": machine_type
            for index, machine_type in enumerate(allowed_types)
        }

        return db.execute(sql, parameters).fetchall()

    finally:
        db.close()


def show_machine_eligibility():
    print("\nMACHINE ELIGIBILITY")
    print("=" * 65)

    for operation_name in ELIGIBILITY_RULES:
        machines = get_eligible_machines(operation_name)

        print(f"\nOperation: {operation_name}")

        if machines:
            for machine in machines:
                print(
                    f"  {machine.machine_code} - "
                    f"{machine.machine_name} "
                    f"({machine.capacity_per_hour} units/hour)"
                )
        else:
            print("  No eligible active machines found")


if __name__ == "__main__":
    show_machine_eligibility()