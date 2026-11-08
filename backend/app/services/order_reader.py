from sqlalchemy import text

from app.database import SessionLocal


def get_production_orders():
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                po.order_number,
                p.product_name,
                po.quantity,
                po.priority,
                po.order_date,
                po.due_date,
                po.status
            FROM production_orders po
            JOIN products p
                ON po.product_id = p.id
            ORDER BY
                CASE po.priority
                    WHEN 'URGENT' THEN 1
                    WHEN 'HIGH' THEN 2
                    ELSE 3
                END,
                po.due_date ASC
        """)

        orders = db.execute(query).fetchall()

        print("\nPRODUCTION ORDERS")
        print("=" * 75)

        for order in orders:
            print(f"\nOrder Number : {order.order_number}")
            print(f"Product      : {order.product_name}")
            print(f"Quantity     : {order.quantity}")
            print(f"Priority     : {order.priority}")
            print(f"Order Date   : {order.order_date}")
            print(f"Due Date     : {order.due_date}")
            print(f"Status       : {order.status}")

        print("\nTotal Orders:", len(orders))

    except Exception as error:
        print("Error reading production orders:", error)

    finally:
        db.close()


if __name__ == "__main__":
    get_production_orders()