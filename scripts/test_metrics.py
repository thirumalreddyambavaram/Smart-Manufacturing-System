import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app.services.evaluation_metrics import calculate_evaluation_metrics

db = SessionLocal()
metrics = calculate_evaluation_metrics(db)
print("=== EVALUATION METRICS ===")
for k, v in metrics.items():
    print(f"  {k}: {v}")
db.close()
