from sqlalchemy import text

from app.database import SessionLocal
from app.services.machine_eligibility import ELIGIBILITY_RULES
from app.services.duration_estimator import calculate_operation_duration


def prepare_operation_assignments():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                po.order_number,
                p.product_name,
                po.quantity,
                o.operation_code,
                o.operation_name,
                o.sequence_number,
                o.estimated_time_minutes
            FROM production_orders po
            JOIN products p
                ON po.product_id = p.id
            JOIN routings r
                ON r.product_id = p.id
                AND r.is_active = 1
            JOIN operations o
                ON o.routing_id = r.id
            WHERE po.status = 'PENDING'
            ORDER BY po.id, o.sequence_number
        """)

        operations = db.execute(query).fetchall()

        print("\nOPERATION-TO-MACHINE ASSIGNMENT REPORT")
        print("=" * 75)

        total_assignments = 0

        for operation in operations:
            allowed_types = ELIGIBILITY_RULES.get(
                operation.operation_name, []
            )

            if not allowed_types:
                print(
                    f"\nWARNING: No eligibility rule for "
                    f"{operation.operation_name}"
                )
                continue

            placeholders = ", ".join(
                f":type_{i}" for i in range(len(allowed_types))
            )

            machine_query = text(f"""
                SELECT
                    machine_code,
                    machine_name,
                    machine_type,
                    capacity_per_hour
                FROM machines
                WHERE is_active = 1
                  AND machine_type IN ({placeholders})
                ORDER BY capacity_per_hour DESC, machine_code
            """)

            parameters = {
                f"type_{i}": machine_type
                for i, machine_type in enumerate(allowed_types)
            }

            machines = db.execute(
                machine_query, parameters
            ).fetchall()

            print(f"\nOrder: {operation.order_number}")
            print(f"Product: {operation.product_name}")
            print(f"Operation: {operation.operation_name}")
            print(f"Sequence: {operation.sequence_number}")

            if not machines:
                print("No eligible machines available.")
                continue

            for machine in machines:
                duration = calculate_operation_duration(
                    quantity=operation.quantity,
                    estimated_time_minutes=operation.estimated_time_minutes,
                    capacity_per_hour=machine.capacity_per_hour
                )

                print(f"\n  Machine: {machine.machine_code}")
                print(f"  Machine type: {machine.machine_type}")
                print(f"  Capacity: {machine.capacity_per_hour} units/hour")
                print(f"  Estimated duration: {duration} minutes")

                total_assignments += 1

            print("-" * 55)

        print("\nASSIGNMENT PREPARATION SUMMARY")
        print("Operations processed:", len(operations))
        print("Eligible machine options:", total_assignments)

    except Exception as error:
        print("Assignment preparation failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    prepare_operation_assignments()