
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api", tags=["Operations"])


# ---------------- ROUTINGS ----------------

@router.get("/routings")
def get_routings(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            r.id AS routing_id,
            r.routing_code,
            r.routing_name,
            r.description,
            r.is_active,
            p.product_code,
            p.product_name,
            o.id AS operation_id,
            o.operation_code,
            o.operation_name,
            o.sequence_number,
            o.estimated_time_minutes
        FROM routings r
        JOIN products p ON p.id = r.product_id
        LEFT JOIN operations o ON o.routing_id = r.id
        ORDER BY r.id, o.sequence_number
    """)

    return [dict(row) for row in db.execute(query).mappings().all()]


# ---------------- CHANGEOVERS ----------------

@router.get("/changeovers")
def get_changeovers(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            cm.id,
            m.machine_code,
            m.machine_name,
            fp.product_code AS from_product_code,
            fp.product_name AS from_product_name,
            tp.product_code AS to_product_code,
            tp.product_name AS to_product_name,
            cm.duration_minutes
        FROM changeover_matrix cm
        JOIN machines m ON m.id = cm.machine_id
        JOIN products fp ON fp.id = cm.from_product_id
        JOIN products tp ON tp.id = cm.to_product_id
        ORDER BY m.machine_code, fp.product_code, tp.product_code
    """)

    return [dict(row) for row in db.execute(query).mappings().all()]


# ---------------- EXCEPTIONS ----------------

@router.get("/exceptions")
def get_exceptions(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            cv.id,
            sr.run_code,
            po.order_number,
            o.operation_code,
            o.operation_name,
            m.machine_code,
            cv.issue_type,
            cv.severity,
            cv.description,
            cv.ground_truth,
            cv.detected_at
        FROM constraint_violations cv
        JOIN schedule_runs sr ON sr.id = cv.schedule_run_id
        LEFT JOIN production_orders po
            ON po.id = cv.production_order_id
        LEFT JOIN operations o
            ON o.id = cv.operation_id
        LEFT JOIN machines m
            ON m.id = cv.machine_id
        ORDER BY cv.detected_at DESC, cv.id DESC
    """)

    return [dict(row) for row in db.execute(query).mappings().all()]
