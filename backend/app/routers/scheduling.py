import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tool, LaborShift
from app.scheduling.production_scheduler import run_production_scheduler
from app.services.evaluation_metrics import calculate_evaluation_metrics
from app.validators.system_validator import SystemValidator, run_system_validation_report

router = APIRouter(prefix="/api", tags=["Production Scheduling"])


class ScheduleRunRequest(BaseModel):
    work_date: Optional[str] = None
    max_orders: Optional[int] = 50


@router.get("/schedules")
def get_production_schedules(
    run: str = "latest",
    db: Session = Depends(get_db)
):
    base_query = """
        SELECT
            os.id AS schedule_id,
            os.schedule_code,
            sr.run_code,
            po.order_number,
            p.product_code,
            p.product_name,
            o.operation_code,
            o.operation_name,
            o.sequence_number,
            m.machine_code,
            m.machine_name,
            os.planned_start,
            os.planned_end,
            os.status
        FROM operation_schedules os
        JOIN production_orders po ON po.id = os.production_order_id
        JOIN products p ON p.id = po.product_id
        JOIN operations o ON o.id = os.operation_id
        JOIN machines m ON m.id = os.machine_id
        JOIN schedule_runs sr ON sr.id = os.schedule_run_id
    """

    if run == "latest":
        query = text(base_query + """
            WHERE sr.id = (
                SELECT MAX(id)
                FROM schedule_runs
                WHERE status = 'COMPLETED'
            )
            ORDER BY os.planned_start ASC,
                     m.machine_code ASC,
                     o.sequence_number ASC
        """)
        results = db.execute(query).mappings().all()

    elif run == "all":
        query = text(base_query + """
            ORDER BY os.planned_start ASC,
                     m.machine_code ASC,
                     o.sequence_number ASC
        """)
        results = db.execute(query).mappings().all()

    else:
        query = text(base_query + """
            WHERE sr.run_code = :run_code
            ORDER BY os.planned_start ASC,
                     m.machine_code ASC,
                     o.sequence_number ASC
        """)
        results = db.execute(
            query, {"run_code": run}
        ).mappings().all()

    return [dict(row) for row in results]


@router.get("/schedule-runs")
def get_schedule_runs(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            sr.id,
            sr.run_code,
            sr.started_at,
            sr.completed_at,
            sr.status,
            COUNT(os.id) AS operation_count
        FROM schedule_runs sr
        LEFT JOIN operation_schedules os
            ON os.schedule_run_id = sr.id
        GROUP BY
            sr.id,
            sr.run_code,
            sr.started_at,
            sr.completed_at,
            sr.status
        ORDER BY sr.id DESC
    """)

    results = db.execute(query).mappings().all()
    return [dict(row) for row in results]


@router.post("/schedule/run")
def trigger_production_schedule(
    payload: Optional[ScheduleRunRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger an execution run of the production scheduling engine.
    """
    w_date = None
    max_orders = 50
    if payload:
        if payload.work_date:
            try:
                w_date = datetime.strptime(payload.work_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        if payload.max_orders is not None:
            max_orders = payload.max_orders

    try:
        result = run_production_scheduler(work_date=w_date, max_orders=max_orders)
        return {
            "message": "Production schedule run completed successfully",
            "run_summary": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduling execution failed: {str(e)}")


@router.get("/metrics")
def get_evaluation_metrics(
    run: Optional[str] = "latest",
    db: Session = Depends(get_db)
):
    """
    Get evaluation metrics (Makespan, Tardiness, Late Orders, Utilization, OTD %, etc.).
    """
    run_id = None
    if run and run != "latest" and run != "all":
        row = db.execute(text("SELECT id FROM schedule_runs WHERE run_code = :rc"), {"rc": run}).fetchone()
        if row:
            run_id = row.id
    elif run == "latest":
        # Ignore empty completed runs so a second no-op scheduling attempt
        # does not hide the most recent run that actually scheduled work.
        row = db.execute(text("""
            SELECT sr.id
            FROM schedule_runs sr
            JOIN operation_schedules os ON os.schedule_run_id = sr.id
            WHERE sr.status = 'COMPLETED' AND os.status = 'SCHEDULED'
            GROUP BY sr.id
            ORDER BY sr.id DESC
            LIMIT 1
        """)).fetchone()
        if row:
            run_id = row.id

    metrics = calculate_evaluation_metrics(db, schedule_run_id=run_id)
    return metrics


@router.get("/validation/summary")
def get_validation_summary(db: Session = Depends(get_db)):
    """
    Get the summary of the 15 automated validation checks.
    """
    validator = SystemValidator(db)
    summary = validator.run_all_validations()
    return summary


@router.post("/validation/run")
def execute_validation_run(db: Session = Depends(get_db)):
    """
    Execute validation check and write report to disk.
    """
    summary = run_system_validation_report()
    return {
        "message": "System validation completed successfully",
        "summary": summary
    }


@router.get("/ground-truth")
def get_ground_truth_anomalies():
    """
    Get the 5 deliberate ground truth anomaly scenarios.
    """
    gt_file = Path("data/ground_truth.json")
    if not gt_file.exists():
        gt_file = Path("../data/ground_truth.json")

    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return []


@router.get("/tools")
def get_tools(db: Session = Depends(get_db)):
    """
    Get all tools in the registry.
    """
    tools = db.query(Tool).order_by(Tool.id).all()
    return [
        {
            "id": t.id,
            "tool_code": t.tool_code,
            "tool_name": t.tool_name,
            "tool_type": t.tool_type,
            "total_quantity": t.total_quantity,
            "is_active": t.is_active,
        }
        for t in tools
    ]


@router.get("/labor-shifts")
def get_labor_shifts(db: Session = Depends(get_db)):
    """
    Get all labor shifts.
    """
    shifts = db.query(LaborShift).order_by(LaborShift.id).all()
    return [
        {
            "id": s.id,
            "shift_code": s.shift_code,
            "shift_name": s.shift_name,
            "start_time": s.start_time.strftime("%H:%M:%S") if s.start_time else "00:00:00",
            "end_time": s.end_time.strftime("%H:%M:%S") if s.end_time else "00:00:00",
            "available_workers": s.available_workers,
            "is_active": s.is_active,
        }
        for s in shifts
    ]


@router.get("/material-reservations")
def get_material_reservations(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get persistent material reservations.
    """
    q = text("""
        SELECT mr.id, mr.reservation_code, po.order_number, m.material_code, m.material_name,
               il.lot_code, mr.quantity_reserved, mr.status, mr.reserved_at
        FROM material_reservations mr
        JOIN production_orders po ON po.id = mr.production_order_id
        JOIN materials m ON m.id = mr.material_id
        JOIN inventory_lots il ON il.id = mr.inventory_lot_id
        ORDER BY mr.id DESC
        LIMIT :lim
    """)
    rows = db.execute(q, {"lim": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/material-consumptions")
def get_material_consumptions(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get persistent material consumption records.
    """
    q = text("""
        SELECT mc.id, mc.consumption_code, mr.reservation_code, po.order_number,
               m.material_code, m.material_name, il.lot_code, mc.quantity_consumed, mc.consumed_at
        FROM material_consumptions mc
        LEFT JOIN material_reservations mr ON mr.id = mc.reservation_id
        JOIN production_orders po ON po.id = mc.production_order_id
        JOIN materials m ON m.id = mc.material_id
        JOIN inventory_lots il ON il.id = mc.inventory_lot_id
        ORDER BY mc.id DESC
        LIMIT :lim
    """)
    rows = db.execute(q, {"lim": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/labor-assignments")
def get_labor_assignments(limit: int = 100, db: Session = Depends(get_db)):
    """
    Get persistent labor shift assignments.
    """
    q = text("""
        SELECT la.id, la.assignment_code, os.schedule_code, ls.shift_name, ls.shift_code,
               la.workers_assigned, la.assigned_start, la.assigned_end, la.status
        FROM labor_assignments la
        JOIN operation_schedules os ON os.id = la.operation_schedule_id
        JOIN labor_shifts ls ON ls.id = la.labor_shift_id
        ORDER BY la.id DESC
        LIMIT :lim
    """)
    rows = db.execute(q, {"lim": limit}).mappings().all()
    return [dict(r) for r in rows]


# ---------------- SIMPLE RESOURCE CRUD ----------------

def _save_sql_record(db, statement, values):
    try:
        result = db.execute(text(statement), values)
        db.commit()
        return {"id": result.lastrowid, "message": "Record saved successfully"}
    except Exception as exc:
        db.rollback()
        if "Duplicate" in str(exc) or "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="That code already exists.")
        raise HTTPException(status_code=400, detail=f"Unable to save record: {exc}")


@router.post("/machine-calendars", status_code=201)
def create_machine_calendar(data: dict = Body(...), db: Session = Depends(get_db)):
    required = ["machine_id", "shift_name", "start_time", "end_time"]
    if any(data.get(k) in (None, "") for k in required):
        raise HTTPException(422, detail="Machine, shift name, start time and end time are required.")
    if data["start_time"] == data["end_time"]:
        raise HTTPException(422, detail="Shift start and end times cannot be the same.")
    return _save_sql_record(db, """
        INSERT INTO machine_calendars (machine_id, shift_name, start_time, end_time, is_working_day)
        VALUES (:machine_id, :shift_name, :start_time, :end_time, :is_working_day)
    """, {**data, "is_working_day": bool(data.get("is_working_day", True))})


@router.put("/machine-calendars/{record_id}")
def update_machine_calendar(record_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    allowed = {k: data[k] for k in ("machine_id", "shift_name", "start_time", "end_time", "is_working_day") if k in data}
    if not allowed:
        raise HTTPException(422, detail="No changes supplied.")
    row = db.execute(text("SELECT id FROM machine_calendars WHERE id=:id"), {"id": record_id}).first()
    if not row: raise HTTPException(404, detail="Machine calendar not found.")
    sets = ", ".join(f"{k}=:{k}" for k in allowed)
    allowed["id"] = record_id
    db.execute(text(f"UPDATE machine_calendars SET {sets} WHERE id=:id"), allowed)
    db.commit()
    return {"message": "Machine calendar updated successfully"}


@router.delete("/machine-calendars/{record_id}")
def deactivate_machine_calendar(record_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("UPDATE machine_calendars SET is_working_day=0 WHERE id=:id"), {"id": record_id})
    if not result.rowcount: raise HTTPException(404, detail="Machine calendar not found.")
    db.commit()
    return {"message": "Machine calendar deactivated (marked non-working)."}


@router.post("/inventory-lots", status_code=201)
def create_inventory_lot(data: dict = Body(...), db: Session = Depends(get_db)):
    required = ["lot_code", "material_id", "quantity_received", "quantity_available", "available_from"]
    if any(data.get(k) in (None, "") for k in required):
        raise HTTPException(422, detail="Lot code, material, quantities and availability date are required.")
    received, available = float(data["quantity_received"]), float(data["quantity_available"])
    if received <= 0 or available < 0 or available > received:
        raise HTTPException(422, detail="Received quantity must be positive; available quantity must be between zero and received quantity.")
    return _save_sql_record(db, """
        INSERT INTO inventory_lots (lot_code, material_id, quantity_received, quantity_available, available_from, expiry_date, status)
        VALUES (:lot_code, :material_id, :quantity_received, :quantity_available, :available_from, :expiry_date, :status)
    """, {**data, "status": data.get("status", "AVAILABLE")})


@router.put("/inventory-lots/{record_id}")
def update_inventory_lot(record_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    allowed = {k: data[k] for k in ("lot_code", "material_id", "quantity_received", "quantity_available", "available_from", "expiry_date", "status") if k in data}
    if not allowed: raise HTTPException(422, detail="No changes supplied.")
    if "quantity_received" in allowed and "quantity_available" in allowed and float(allowed["quantity_available"]) > float(allowed["quantity_received"]):
        raise HTTPException(422, detail="Available quantity cannot exceed received quantity.")
    row = db.execute(text("SELECT id FROM inventory_lots WHERE id=:id"), {"id": record_id}).first()
    if not row: raise HTTPException(404, detail="Inventory lot not found.")
    sets = ", ".join(f"{k}=:{k}" for k in allowed)
    allowed["id"] = record_id
    db.execute(text(f"UPDATE inventory_lots SET {sets} WHERE id=:id"), allowed)
    db.commit()
    return {"message": "Inventory lot updated successfully"}


@router.delete("/inventory-lots/{record_id}")
def deactivate_inventory_lot(record_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("UPDATE inventory_lots SET status='INACTIVE' WHERE id=:id"), {"id": record_id})
    if not result.rowcount: raise HTTPException(404, detail="Inventory lot not found.")
    db.commit()
    return {"message": "Inventory lot deactivated successfully"}


@router.post("/labor-shifts", status_code=201)
def create_labor_shift(data: dict = Body(...), db: Session = Depends(get_db)):
    required = ["shift_code", "shift_name", "start_time", "end_time", "available_workers"]
    if any(data.get(k) in (None, "") for k in required):
        raise HTTPException(422, detail="All shift fields are required.")
    if int(data["available_workers"]) < 1: raise HTTPException(422, detail="Available workers must be at least 1.")
    shift = LaborShift(**{k: data[k] for k in required}, is_active=bool(data.get("is_active", True)))
    db.add(shift)
    try: db.commit(); db.refresh(shift)
    except Exception as exc:
        db.rollback()
        raise HTTPException(409, detail="Shift code already exists or the data is invalid.") from exc
    return {"id": shift.id, "message": "Labor shift created successfully"}


@router.put("/labor-shifts/{record_id}")
def update_labor_shift(record_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    shift = db.query(LaborShift).filter(LaborShift.id == record_id).first()
    if not shift: raise HTTPException(404, detail="Labor shift not found.")
    for key in ("shift_code", "shift_name", "start_time", "end_time", "available_workers", "is_active"):
        if key in data: setattr(shift, key, data[key])
    try: db.commit()
    except Exception as exc:
        db.rollback(); raise HTTPException(409, detail="Shift code already exists or the data is invalid.") from exc
    return {"message": "Labor shift updated successfully"}


@router.delete("/labor-shifts/{record_id}")
def deactivate_labor_shift(record_id: int, db: Session = Depends(get_db)):
    shift = db.query(LaborShift).filter(LaborShift.id == record_id).first()
    if not shift: raise HTTPException(404, detail="Labor shift not found.")
    shift.is_active = False
    db.commit()
    return {"message": "Labor shift deactivated successfully"}


@router.post("/tools", status_code=201)
def create_tool(data: dict = Body(...), db: Session = Depends(get_db)):
    required = ["tool_code", "tool_name", "tool_type", "total_quantity"]
    if any(data.get(k) in (None, "") for k in required):
        raise HTTPException(422, detail="Tool code, name, type and quantity are required.")
    if int(data["total_quantity"]) < 1: raise HTTPException(422, detail="Tool quantity must be at least 1.")
    tool = Tool(**{k: data[k] for k in required}, is_active=bool(data.get("is_active", True)))
    db.add(tool)
    try: db.commit(); db.refresh(tool)
    except Exception as exc:
        db.rollback(); raise HTTPException(409, detail="Tool code already exists or the data is invalid.") from exc
    return {"id": tool.id, "message": "Tool created successfully"}


@router.put("/tools/{record_id}")
def update_tool(record_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.id == record_id).first()
    if not tool: raise HTTPException(404, detail="Tool not found.")
    for key in ("tool_code", "tool_name", "tool_type", "total_quantity", "is_active"):
        if key in data: setattr(tool, key, data[key])
    try: db.commit()
    except Exception as exc:
        db.rollback(); raise HTTPException(409, detail="Tool code already exists or the data is invalid.") from exc
    return {"message": "Tool updated successfully"}


@router.delete("/tools/{record_id}")
def deactivate_tool(record_id: int, db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.id == record_id).first()
    if not tool: raise HTTPException(404, detail="Tool not found.")
    tool.is_active = False
    db.commit()
    return {"message": "Tool deactivated successfully"}
