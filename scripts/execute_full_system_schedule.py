import sys
import os
import time

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import engine, Base, SessionLocal
from app.scheduling.production_scheduler import run_production_scheduler
from app.services.evaluation_metrics import calculate_evaluation_metrics
from app.validators.system_validator import run_system_validation_report
from sqlalchemy import text

print("=== 1. RESETTING TRANSACTION & SCHEDULE TABLES ===")
db = SessionLocal()
db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
for t in ["labor_assignments", "material_consumptions", "material_reservations", "constraint_violations", "schedule_segments", "operation_schedules", "schedule_runs", "event_history"]:
    db.execute(text(f"DELETE FROM `{t}`"))

# Reset lot quantities to received
db.execute(text("UPDATE inventory_lots SET quantity_available = quantity_received, status = 'AVAILABLE'"))
# Reset material stock to sum of lots
db.execute(text("""
    UPDATE materials m
    SET current_stock = (
        SELECT COALESCE(SUM(il.quantity_received), 0)
        FROM inventory_lots il
        WHERE il.material_id = m.id
    )
"""))
db.execute(text("UPDATE production_orders SET status = 'PENDING'"))
db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
db.commit()
db.close()
print("Tables reset cleanly.")

print("\n=== 2. EXECUTING PRODUCTION SCHEDULER ===")
t0 = time.time()
result = run_production_scheduler(max_orders=None)
t1 = time.time()
print(f"Scheduler finished in {t1 - t0:.2f} seconds.")
print("Summary:", result)

print("\n=== 3. COMPUTING EVALUATION METRICS ===")
db = SessionLocal()
metrics = calculate_evaluation_metrics(db)
for k, v in metrics.items():
    print(f"  {k}: {v}")
db.close()

print("\n=== 4. RUNNING 15-RULE SYSTEM VALIDATION ===")
val_summary = run_system_validation_report()
print(f"Validation Status: {val_summary['overall_status']}, Passed Checks: {val_summary['passed_checks']}/{val_summary['total_checks']}")

print("\n=== FULL SYSTEM SCHEDULE EXECUTION COMPLETED ===")
