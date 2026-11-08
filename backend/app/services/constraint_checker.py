from sqlalchemy import text

from app.database import SessionLocal


def check_production_constraints():
    db = SessionLocal()

    try:
        print("\nPRODUCTION CONSTRAINT SUMMARY")
        print("=" * 65)

        # 1. Check pending production orders
        orders = db.execute(text("""
            SELECT COUNT(*)
            FROM production_orders
            WHERE status = 'PENDING'
        """)).scalar()

        print("\n1. PENDING PRODUCTION ORDERS")
        print("Total:", orders)

        # 2. Check material shortages
        shortages = db.execute(text("""
            SELECT
                m.material_name,
                SUM(po.quantity * pm.quantity_required)
                    - m.current_stock AS shortage
            FROM production_orders po
            JOIN product_materials pm
                ON po.product_id = pm.product_id
            JOIN materials m
                ON pm.material_id = m.id
            WHERE po.status = 'PENDING'
              AND m.is_active = 1
            GROUP BY m.id, m.material_name, m.current_stock
            HAVING shortage > 0
        """)).fetchall()

        print("\n2. MATERIAL SHORTAGES")

        if shortages:
            for item in shortages:
                print(
                    f"{item.material_name}: "
                    f"{item.shortage} units required"
                )
        else:
            print("No material shortages found.")

        # 3. Check active machines
        machines = db.execute(text("""
            SELECT COUNT(*)
            FROM machines
            WHERE is_active = 1
        """)).scalar()

        print("\n3. ACTIVE MACHINES")
        print("Total:", machines)

        # 4. Check planned machine downtime
        downtimes = db.execute(text("""
            SELECT COUNT(*)
            FROM machine_downtimes
            WHERE status = 'PLANNED'
        """)).scalar()

        print("\n4. PLANNED MACHINE DOWNTIMES")
        print("Total:", downtimes)

        print("\nCONSTRAINT CHECK COMPLETED")

    except Exception as error:
        print("Constraint check failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    check_production_constraints()