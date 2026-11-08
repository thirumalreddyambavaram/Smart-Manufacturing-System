from sqlalchemy import text

from app.database import SessionLocal


def get_order_routings():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                po.order_number,
                p.product_name,
                po.quantity,
                r.routing_code,
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
            ORDER BY
                po.id,
                o.sequence_number
        """)

        results = db.execute(query).fetchall()

        print("\nPRODUCTION ORDER ROUTINGS")
        print("=" * 75)

        for row in results:
            print(f"\nOrder       : {row.order_number}")
            print(f"Product     : {row.product_name}")
            print(f"Quantity    : {row.quantity}")
            print(f"Routing     : {row.routing_code}")
            print(f"Operation   : {row.operation_code} - {row.operation_name}")
            print(f"Sequence    : {row.sequence_number}")
            print(f"Time/unit   : {row.estimated_time_minutes} minutes")
            print("-" * 50)

        print("\nTotal operation records:", len(results))

    except Exception as error:
        print("Error reading routing operations:", error)

    finally:
        db.close()


if __name__ == "__main__":
    get_order_routings()