import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
q = text("""
    SELECT s1.id AS id1, s1.schedule_code AS code1, s2.id AS id2, s2.schedule_code AS code2,
           s1.machine_id, s1.planned_start AS s1_start, s1.planned_end AS s1_end,
           s2.planned_start AS s2_start, s2.planned_end AS s2_end
    FROM operation_schedules s1
    JOIN operation_schedules s2
      ON s1.machine_id = s2.machine_id
     AND s1.id < s2.id
     AND s1.schedule_run_id = s2.schedule_run_id
     AND s1.schedule_run_id = (SELECT MAX(id) FROM schedule_runs WHERE status = 'COMPLETED')
     AND s1.status IN ('SCHEDULED', 'IN_PROGRESS')
     AND s2.status IN ('SCHEDULED', 'IN_PROGRESS')
     AND s1.planned_start < s2.planned_end
     AND s1.planned_end > s2.planned_start
""")
rows = db.execute(q).fetchall()
print("Total overlapping schedule pairs:", len(rows))
for r in rows[:10]:
    print(dict(r._mapping))

db.close()
