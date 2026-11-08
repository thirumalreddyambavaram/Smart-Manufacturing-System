import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import engine
from sqlalchemy import inspect

insp = inspect(engine)
print("=== OPERATIONS COLUMNS ===")
for c in insp.get_columns("operations"):
    print(c["name"], c["type"])

print("\n=== LABOR SHIFTS COLUMNS ===")
for c in insp.get_columns("labor_shifts"):
    print(c["name"], c["type"])

print("\n=== EXISTING TABLES IN DB ===")
print(insp.get_table_names())
