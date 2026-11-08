
from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

try:
    query = text("""
        SELECT
            os.id,
            os.schedule_code,
            po.order_number,
            o.operation_name,
            m.machine_code,
            os.status,
            os.schedule_run_id
        FROM operation_schedules os
        JOIN production_orders po
            ON po.id = os.production_order_id
        JOIN operations o
            ON o.id = os.operation_id
        JOIN machines m
            ON m.id = os.machine_id
        WHERE os.status IN (:s1, :s2)
        ORDER BY os.id
    """)

    rows = db.execute(
        query,
        {
            "s1": "SCHEDULED",
            "s2": "IN_PROGRESS",
        },
    ).fetchall()

    for row in rows:
        print(row)

    print("\nTotal active schedules:", len(rows))

finally:
    db.close()
