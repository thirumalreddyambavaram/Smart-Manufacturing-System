from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()

query = text("""
    SELECT
        a.machine_id,
        a.id AS schedule_1,
        b.id AS schedule_2,
        a.planned_start AS start_1,
        a.planned_end AS end_1,
        b.planned_start AS start_2,
        b.planned_end AS end_2
    FROM operation_schedules a
    JOIN operation_schedules b
        ON a.machine_id = b.machine_id
        AND a.id < b.id
        AND a.planned_start < b.planned_end
        AND b.planned_start < a.planned_end
    WHERE a.status IN ('SCHEDULED', 'IN_PROGRESS')
      AND b.status IN ('SCHEDULED', 'IN_PROGRESS')
    ORDER BY a.machine_id, a.planned_start
""")

try:
    rows = db.execute(query).fetchall()

    if rows:
        print("MACHINE-TIME OVERLAPS FOUND:")
        for row in rows:
            print(row)
    else:
        print("No machine-time overlaps found.")

finally:
    db.close()