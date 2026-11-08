import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
print("=== OPERATION SCHEDULES BY RUN ===")
rows = db.execute(text("""
    SELECT schedule_run_id, COUNT(id) as cnt, MIN(planned_start) as min_s, MAX(planned_end) as max_e 
    FROM operation_schedules 
    GROUP BY schedule_run_id
    ORDER BY schedule_run_id
""")).fetchall()
for r in rows:
    print(dict(r._mapping))

print("\n=== CONSTRAINT VIOLATIONS BY RUN ===")
v_rows = db.execute(text("""
    SELECT schedule_run_id, issue_type, COUNT(id) as cnt 
    FROM constraint_violations 
    GROUP BY schedule_run_id, issue_type
""")).fetchall()
for r in v_rows:
    print(dict(r._mapping))

print("\n=== PRODUCTION ORDERS BY STATUS ===")
p_rows = db.execute(text("""
    SELECT status, COUNT(id) as cnt 
    FROM production_orders 
    GROUP BY status
""")).fetchall()
for r in p_rows:
    print(dict(r._mapping))

db.close()
