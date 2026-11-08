import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import engine, Base
import app.models
from sqlalchemy import inspect, text

print("Applying schema migrations...")
# Create any missing tables
Base.metadata.create_all(bind=engine)

insp = inspect(engine)

# Add required_workers to operations if missing
op_cols = [c["name"] for c in insp.get_columns("operations")]
if "required_workers" not in op_cols:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE operations ADD COLUMN required_workers INT NOT NULL DEFAULT 1"))
        conn.commit()
    print("  Added 'required_workers' column to 'operations'.")
else:
    print("  'required_workers' column already present in 'operations'.")

# Add changeover_minutes to operation_schedules if missing
sched_cols = [c["name"] for c in insp.get_columns("operation_schedules")]
if "changeover_minutes" not in sched_cols:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE operation_schedules ADD COLUMN changeover_minutes INT NOT NULL DEFAULT 0"))
        conn.commit()
    print("  Added 'changeover_minutes' column to 'operation_schedules'.")
else:
    print("  'changeover_minutes' column already present in 'operation_schedules'.")

print("Migration completed successfully!")
