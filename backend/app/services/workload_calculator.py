from sqlalchemy import text

from app.database import SessionLocal


def calculate_workloads():
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
                o.estimated_time_minutes,
                (po.quantity * o.estimated_time_minutes)
                    AS total_workload_minutes
            FROM production_orders po
            JOIN products p
                ON po.product_id = p.id
            JOIN routings r
                ON r.product_id = p.id
                AND r.is_active = 1
            JOIN operations o
                ON o.routing_id = r.id
            ORDER BY
                po.id,
                o.sequence_number
        """)

        results = db.execute(query).fetchall()

        print("\nPRODUCTION WORKLOAD REPORT")
        print("=" * 75)

        total_workload = 0

        for row in results:
            print(f"\nOrder       : {row.order_number}")
            print(f"Product     : {row.product_name}")
            print(f"Operation   : {row.operation_name}")
            print(f"Quantity    : {row.quantity}")
            print(f"Minutes/unit: {row.estimated_time_minutes}")
            print(f"Workload    : {row.total_workload_minutes} minutes")

            total_workload += row.total_workload_minutes

            print("-" * 45)

        print("\nTOTAL WORKLOAD")
        print("=" * 45)
        print("Operation records:", len(results))
        print("Total minutes:", total_workload)
        print("Total hours:", round(total_workload / 60, 2))

    except Exception as error:
        print("Workload calculation failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    calculate_workloads()