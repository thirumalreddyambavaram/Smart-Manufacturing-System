
from app.database import SessionLocal
from app.models import (
    Operation,
    Machine,
    Product,
    OperationMachineEligibility,
    ChangeoverMatrix,
)


# Maps existing operation names to compatible machine types.
ELIGIBILITY_RULES = {
    "Cutting": ["CUTTING"],
    "CNC Machining": ["CNC"],
    "Machining": ["CNC"],
    "Assembly": ["ASSEMBLY"],
    "Finishing": ["FINISHING"],
    "Inspection": ["FINISHING"],
}


# Existing prototype changeover assumptions, in minutes.
CHANGEOVER_RULES = {
    ("PROD-001", "PROD-002"): 30,
    ("PROD-001", "PROD-003"): 20,
    ("PROD-002", "PROD-001"): 40,
    ("PROD-002", "PROD-003"): 25,
    ("PROD-003", "PROD-001"): 35,
    ("PROD-003", "PROD-002"): 30,
}


def seed_planning_rules():
    db = SessionLocal()

    try:
        operations = db.query(Operation).all()
        machines = (
            db.query(Machine)
            .filter(Machine.is_active == True)
            .all()
        )
        products = db.query(Product).all()

        if not operations or not machines or not products:
            raise RuntimeError(
                "Products, operations, or active machines are missing."
            )

        eligibility_added = 0
        changeovers_added = 0
        unmapped_operations = []

        # Create operation-to-machine eligibility records.
        for operation in operations:
            allowed_types = ELIGIBILITY_RULES.get(
                operation.operation_name, []
            )

            if not allowed_types:
                unmapped_operations.append(operation.operation_name)
                continue

            eligible_machines = [
                machine for machine in machines
                if machine.machine_type in allowed_types
            ]

            if not eligible_machines:
                print(
                    f"WARNING: No eligible active machine for "
                    f"{operation.operation_name}"
                )
                continue

            for machine in eligible_machines:
                existing = (
                    db.query(OperationMachineEligibility)
                    .filter_by(
                        operation_id=operation.id,
                        machine_id=machine.id,
                    )
                    .first()
                )

                if existing is None:
                    db.add(
                        OperationMachineEligibility(
                            operation_id=operation.id,
                            machine_id=machine.id,
                            is_active=True,
                        )
                    )
                    eligibility_added += 1
                else:
                    existing.is_active = True

        # Create machine-specific product changeover records.
        for machine in machines:
            for from_product in products:
                for to_product in products:
                    key = (
                        from_product.product_code,
                        to_product.product_code,
                    )

                    if from_product.id == to_product.id:
                        duration = 0
                    else:
                        duration = CHANGEOVER_RULES.get(key, 30)

                    existing = (
                        db.query(ChangeoverMatrix)
                        .filter_by(
                            machine_id=machine.id,
                            from_product_id=from_product.id,
                            to_product_id=to_product.id,
                        )
                        .first()
                    )

                    if existing is None:
                        db.add(
                            ChangeoverMatrix(
                                machine_id=machine.id,
                                from_product_id=from_product.id,
                                to_product_id=to_product.id,
                                duration_minutes=duration,
                            )
                        )
                        changeovers_added += 1
                    else:
                        existing.duration_minutes = duration

        db.commit()

        print("Planning rules saved successfully.")
        print(f"New eligibility records: {eligibility_added}")
        print(f"New changeover records: {changeovers_added}")

        if unmapped_operations:
            print(
                "Operations needing a machine mapping:",
                sorted(set(unmapped_operations)),
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_planning_rules()
