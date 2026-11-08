import sys
import os
import csv
import json
from pathlib import Path

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
out_dir = Path("data")
out_dir.mkdir(parents=True, exist_ok=True)

tables_to_export = [
    ("operation_schedules", "SELECT * FROM operation_schedules ORDER BY id"),
    ("schedule_runs", "SELECT * FROM schedule_runs ORDER BY id"),
    ("schedule_segments", "SELECT * FROM schedule_segments ORDER BY id"),
    ("constraint_violations", "SELECT * FROM constraint_violations ORDER BY id"),
    ("material_reservations", "SELECT * FROM material_reservations ORDER BY id"),
    ("material_consumptions", "SELECT * FROM material_consumptions ORDER BY id"),
    ("labor_assignments", "SELECT * FROM labor_assignments ORDER BY id"),
]

print("Exporting scheduling and transaction tables to data/...")
for table_name, query in tables_to_export:
    rows = db.execute(text(query)).fetchall()
    if not rows:
        records = []
    else:
        records = [dict(r._mapping) for r in rows]

    # Export JSON
    json_path = out_dir / f"{table_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)

    # Export CSV
    csv_path = out_dir / f"{table_name}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        if records:
            headers = list(records[0].keys())
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in records:
                row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        row[k] = json.dumps(v)
                    else:
                        row[k] = v
                writer.writerow(row)
        else:
            f.write("id,info\n")

    print(f"  {table_name}: {len(records)} records exported to CSV & JSON")

db.close()
print("Scheduling export completed successfully!")
