from sqlalchemy import text

from app.database import SessionLocal


def check_material_availability():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                m.material_code,
                m.material_name,
                m.unit_of_measure,
                m.current_stock,
                m.minimum_stock,
                SUM(po.quantity * pm.quantity_required)
                    AS total_required
            FROM production_orders po
            JOIN product_materials pm
                ON po.product_id = pm.product_id
            JOIN materials m
                ON pm.material_id = m.id
            WHERE po.status = 'PENDING'
              AND m.is_active = 1
            GROUP BY
                m.id,
                m.material_code,
                m.material_name,
                m.unit_of_measure,
                m.current_stock,
                m.minimum_stock
            ORDER BY m.material_code
        """)

        materials = db.execute(query).fetchall()

        print("\nMATERIAL AVAILABILITY REPORT")
        print("=" * 70)

        for material in materials:
            shortage = max(
                material.total_required - material.current_stock,
                0
            )

            if shortage > 0:
                status = "INSUFFICIENT STOCK"
            else:
                status = "AVAILABLE"

            print(f"\nMaterial       : {material.material_name}")
            print(f"Material Code  : {material.material_code}")
            print(f"Required       : {material.total_required} {material.unit_of_measure}")
            print(f"Current Stock  : {material.current_stock} {material.unit_of_measure}")
            print(f"Minimum Stock  : {material.minimum_stock} {material.unit_of_measure}")
            print(f"Shortage       : {shortage} {material.unit_of_measure}")
            print(f"Status         : {status}")
            print("-" * 45)

        print("\nTotal materials checked:", len(materials))

    except Exception as error:
        print("Material availability check failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    check_material_availability()