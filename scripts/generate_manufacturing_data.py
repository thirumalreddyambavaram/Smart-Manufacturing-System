import random
from datetime import date, timedelta

from sqlalchemy import text

from app.database import SessionLocal
from app.models import (
    Product,
    Machine,
    Material,
    ProductionOrder,
    Routing,
    Operation,
)


TARGETS = {
    "products": 132,
    "machines": 50,
    "materials": 2100,
    "orders": 520,
    "order_operations": 2100,
}

# These are the generated product codes that may receive
# one additional Packaging operation if needed to reach 2,100.
GENERATED_PRODUCT_START = 5
GENERATED_PRODUCT_END = 132


def add_missing_products(db):
    print("Checking products...")

    for number in range(
        GENERATED_PRODUCT_START,
        GENERATED_PRODUCT_END + 1,
    ):
        if db.query(Product).count() >= TARGETS["products"]:
            break

        code = f"PROD-{number:03d}"

        exists = (
            db.query(Product)
            .filter(Product.product_code == code)
            .first()
        )

        if exists:
            continue

        db.add(
            Product(
                product_code=code,
                product_name=f"Manufactured Product {number:03d}",
                description=f"Generated manufacturing product {number:03d}",
                unit_of_measure="PCS",
                is_active=True,
            )
        )

    db.flush()

    actual = db.query(Product).count()
    if actual != TARGETS["products"]:
        raise ValueError(
            f"Products target not reached. Expected "
            f"{TARGETS['products']}, found {actual}."
        )


def add_missing_machines(db):
    print("Checking machines...")

    number = 1

    while db.query(Machine).count() < TARGETS["machines"]:
        code = f"MACH-{number:03d}"

        exists = (
            db.query(Machine)
            .filter(Machine.machine_code == code)
            .first()
        )

        if not exists:
            templates = (
                db.query(Machine)
                .order_by(Machine.id)
                .all()
            )

            if not templates:
                raise ValueError(
                    "No existing machine is available to copy "
                    "machine type and capacity from."
                )

            template = templates[(number - 1) % len(templates)]

            db.add(
                Machine(
                    machine_code=code,
                    machine_name=f"Production Machine {number:03d}",
                    machine_type=template.machine_type,
                    capacity_per_hour=template.capacity_per_hour,
                    is_active=True,
                )
            )
            db.flush()

        number += 1

    db.flush()


def add_missing_materials(db):
    print("Checking materials...")

    number = 1

    while db.query(Material).count() < TARGETS["materials"]:
        code = f"MAT-{number:04d}"

        exists = (
            db.query(Material)
            .filter(Material.material_code == code)
            .first()
        )

        if not exists:
            db.add(
                Material(
                    material_code=code,
                    material_name=f"Raw Material {number:04d}",
                    unit_of_measure="KG",
                    current_stock=1000.0,
                    minimum_stock=100.0,
                    is_active=True,
                )
            )
            db.flush()

        number += 1

    db.flush()


def add_missing_routings(db):
    print("Checking routings and operations...")

    products = (
        db.query(Product)
        .order_by(Product.id)
        .all()
    )

    standard_steps = [
        ("Cutting", 15),
        ("CNC Machining", 30),
        ("Finishing", 20),
        ("Inspection", 10),
    ]

    for product in products:
        existing_routing = (
            db.query(Routing)
            .filter(
                Routing.product_id == product.id,
                Routing.is_active == 1,
            )
            .first()
        )

        if existing_routing:
            continue

        routing = Routing(
            routing_code=f"ROUTE-{product.product_code}",
            product_id=product.id,
            routing_name=f"Standard Routing - {product.product_name}",
            description=f"Standard manufacturing routing for {product.product_code}",
            is_active=1,
        )

        db.add(routing)
        db.flush()

        for sequence, (operation_name, duration) in enumerate(
            standard_steps,
            start=1,
        ):
            db.add(
                Operation(
                    operation_code=(
                        f"OP-{product.product_code}-{sequence:02d}"
                    ),
                    routing_id=routing.id,
                    operation_name=operation_name,
                    sequence_number=sequence,
                    estimated_time_minutes=duration,
                )
            )

        db.flush()


def add_missing_orders(db):
    print("Checking production orders...")

    products = (
        db.query(Product)
        .order_by(Product.id)
        .all()
    )

    if not products:
        raise ValueError("No products are available.")

    if db.query(ProductionOrder).count() > TARGETS["orders"]:
        raise ValueError(
            "Existing production order count is already above the target."
        )

    number = 1
    today = date.today()

    while db.query(ProductionOrder).count() < TARGETS["orders"]:
        order_code = f"ORD-GEN-{number:04d}"

        exists = (
            db.query(ProductionOrder)
            .filter(ProductionOrder.order_number == order_code)
            .first()
        )

        if not exists:
            product = products[(number - 1) % len(products)]

            order_date = today + timedelta(days=number % 15)
            due_date = order_date + timedelta(days=30 + number % 30)

            db.add(
                ProductionOrder(
                    order_number=order_code,
                    product_id=product.id,
                    quantity=random.randint(10, 100),
                    priority=random.choice(
                        ["LOW", "MEDIUM", "HIGH"]
                    ),
                    order_date=order_date,
                    due_date=due_date,
                    status="PENDING",
                )
            )
            db.flush()

        number += 1


def get_order_operation_count(db):
    result = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM production_orders po
            JOIN routings r
                ON r.product_id = po.product_id
                AND r.is_active = 1
            JOIN operations o
                ON o.routing_id = r.id
            """
        )
    )

    return result.scalar() or 0


def add_packaging_operations_if_needed(db):
    """
    Add one Packaging operation to selected generated product routings.

    Each added operation increases the derived Order Operations count
    by the number of production orders belonging to that product.

    A dynamic subset calculation is used to avoid guessing which
    products will produce the exact required increase.
    """

    print("Checking Order Operations target...")

    current_count = get_order_operation_count(db)
    required_increase = TARGETS["order_operations"] - current_count

    if required_increase == 0:
        print("Order Operations target already reached.")
        return

    if required_increase < 0:
        raise ValueError(
            f"Order Operations count is already {current_count}, "
            f"which exceeds the target of {TARGETS['order_operations']}. "
            "Existing operations will not be deleted."
        )

    generated_products = (
        db.query(Product)
        .filter(
            Product.product_code >= f"PROD-{GENERATED_PRODUCT_START:03d}",
            Product.product_code <= f"PROD-{GENERATED_PRODUCT_END:03d}",
        )
        .order_by(Product.id)
        .all()
    )

    # Each product's weight is the number of orders using that product.
    candidates = []

    for product in generated_products:
        routing = (
            db.query(Routing)
            .filter(
                Routing.product_id == product.id,
                Routing.is_active == 1,
            )
            .first()
        )

        if not routing:
            continue

        order_count = (
            db.query(ProductionOrder)
            .filter(ProductionOrder.product_id == product.id)
            .count()
        )

        if order_count > 0:
            candidates.append((product, routing, order_count))

    # Dynamic programming: find a group of products whose order counts
    # add up to exactly the required increase.
    possible = {0: []}

    for index, (_, _, weight) in enumerate(candidates):
        new_possible = dict(possible)

        for total, selected in possible.items():
            new_total = total + weight

            if (
                new_total <= required_increase
                and new_total not in new_possible
            ):
                new_possible[new_total] = selected + [index]

        possible = new_possible

    if required_increase not in possible:
        raise ValueError(
            f"Cannot reach exactly {TARGETS['order_operations']} "
            f"Order Operations from the available generated products. "
            f"Current count: {current_count}; "
            f"required increase: {required_increase}. "
            "No changes will be committed."
        )

    selected_indexes = possible[required_increase]

    for index in selected_indexes:
        product, routing, _ = candidates[index]

        existing_operations = (
            db.query(Operation)
            .filter(Operation.routing_id == routing.id)
            .all()
        )

        next_sequence = max(
            (operation.sequence_number for operation in existing_operations),
            default=0,
        ) + 1

        operation_code = (
            f"OP-{product.product_code}-{next_sequence:02d}"
        )

        code_exists = (
            db.query(Operation)
            .filter(Operation.operation_code == operation_code)
            .first()
        )

        if code_exists:
            raise ValueError(
                f"Operation code {operation_code} already exists. "
                "Cannot safely add the Packaging operation."
            )

        db.add(
            Operation(
                operation_code=operation_code,
                routing_id=routing.id,
                operation_name="Packaging",
                sequence_number=next_sequence,
                estimated_time_minutes=10,
            )
        )

    db.flush()

    final_count = get_order_operation_count(db)

    if final_count != TARGETS["order_operations"]:
        raise ValueError(
            f"Order Operations target mismatch. "
            f"Expected {TARGETS['order_operations']}, "
            f"found {final_count}."
        )


def show_counts(db):
    print("\nFINAL DATABASE COUNTS")
    print("----------------------")
    print("Products:", db.query(Product).count())
    print("Machines:", db.query(Machine).count())
    print("Materials:", db.query(Material).count())
    print("Production Orders:", db.query(ProductionOrder).count())
    print("Order Operations:", get_order_operation_count(db))


def main():
    db = SessionLocal()

    try:
        print("Starting manufacturing data generation...")

        # Preserve existing data. Only add missing records.
        add_missing_products(db)
        add_missing_machines(db)
        add_missing_materials(db)
        add_missing_routings(db)
        add_missing_orders(db)
        add_packaging_operations_if_needed(db)

        db.flush()

        actual_counts = {
            "products": db.query(Product).count(),
            "machines": db.query(Machine).count(),
            "materials": db.query(Material).count(),
            "orders": db.query(ProductionOrder).count(),
            "order_operations": get_order_operation_count(db),
        }

        print("\nCHECKING TARGET COUNTS")
        print("----------------------")

        for name, actual in actual_counts.items():
            expected = TARGETS[name]
            print(f"{name}: {actual} / {expected}")

            if actual != expected:
                raise ValueError(
                    f"{name} count mismatch: expected {expected}, "
                    f"found {actual}. Changes will be rolled back."
                )

        db.commit()

        print("\nData generation completed successfully.")
        show_counts(db)

    except Exception as error:
        db.rollback()
        print("\nData generation stopped.")
        print("All changes from this run have been rolled back.")
        print("Reason:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()