"""
YottaFlex Manufacturing - Evaluation Metrics Service
Calculates formal manufacturing performance and schedule efficiency metrics
using actual source database records without hardcoded assumptions or artificial caps:

Formulas:
1. Makespan:
   Makespan (hours) = (MAX(planned_end) - MIN(planned_start)) / 3600
   Makespan (days)  = Makespan (hours) / 24

2. Total Tardiness:
   Tardiness_i = MAX(0, completion_date_i - due_date_i)
   Total Tardiness = SUM(Tardiness_i) across all scheduled orders

3. Late Orders Count:
   Count of scheduled orders where completion_date_i > due_date_i

4. On-Time Delivery (OTD %):
   OTD % = ((Scheduled Orders - Late Orders) / Scheduled Orders) * 100

5. Machine Utilization Rate (%):
   Actual Busy Minutes = SUM(TIMESTAMPDIFF(MINUTE, segment_start, segment_end))
   Daily Machine Calendar Minutes = SUM(shift_duration_minutes) from machine_calendars
   Total Available Capacity = SUM(daily_calendar_minutes_m * makespan_days) - planned_downtimes
   Machine Utilization % = (Actual Busy Minutes / Total Available Capacity) * 100

6. Total Changeover Time:
   Total Changeover Minutes = SUM(changeover_minutes) from persisted operation_schedules
   Total Changeover Hours   = Total Changeover Minutes / 60.0

7. Schedule Feasibility Rate (%):
   Feasibility Rate % = (Scheduled Operations / Total Order Operations) * 100

8. Material Shortage Count:
   COUNT(DISTINCT production_order_id) in constraint_violations where issue_type = 'MATERIAL_SHORTAGE'

9. Unscheduled Operations:
   Unscheduled Operations = MAX(0, Total Order Operations - Scheduled Operations)
"""

from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal


def to_minute_of_day(val) -> int:
    """Helper to convert time, timedelta, or string to minute of the day (0..1439)."""
    if isinstance(val, timedelta):
        return int(val.total_seconds() // 60) % (24 * 60)
    if isinstance(val, time):
        return val.hour * 60 + val.minute
    if isinstance(val, str):
        parts = [int(p) for p in val.split(":")]
        return parts[0] * 60 + parts[1]
    return 0


def convert_time_to_minutes(start_t, end_t) -> int:
    """Calculate duration in minutes between two time/timedelta objects, handling midnight wrap."""
    s_min = to_minute_of_day(start_t)
    e_min = to_minute_of_day(end_t)
    if e_min <= s_min:
        e_min += 24 * 60
    return e_min - s_min


def calculate_evaluation_metrics(db: Session, schedule_run_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate and return measurable evaluation metrics derived strictly from actual source records.
    Handles empty datasets and edge cases safely with documented mathematical formulas.
    """
    # 1. Determine target schedule run
    if schedule_run_id is None:
        run_query = text("""
            SELECT id, run_code, started_at, completed_at, status, notes
            FROM schedule_runs
            WHERE status = 'COMPLETED'
            ORDER BY id DESC
            LIMIT 1
        """)
    else:
        run_query = text("""
            SELECT id, run_code, started_at, completed_at, status, notes
            FROM schedule_runs
            WHERE id = :run_id
        """)

    run_row = db.execute(run_query, {"run_id": schedule_run_id} if schedule_run_id else {}).fetchone()
    if not run_row:
        # Default empty metric response
        return {
            "run_id": None,
            "run_code": "NONE",
            "makespan_hours": 0.0,
            "makespan_days": 0.0,
            "total_production_time_hours": 0.0,
            "total_production_time_minutes": 0.0,
            "total_changeover_hours": 0.0,
            "total_changeover_minutes": 0,
            "machine_utilization_pct": 0.0,
            "on_time_delivery_pct": 100.0,
            "total_tardiness_days": 0,
            "average_order_delay_days": 0.0,
            "late_orders_count": 0,
            "infeasible_operations_count": 0,
            "constraint_violation_count": 0,
            "material_shortage_count": 0,
            "machine_downtime_impact_hours": 0.0,
            "machine_downtime_impact_minutes": 0.0,
            "scheduled_orders_count": 0,
            "total_orders_count": 0,
            "schedule_feasibility_pct": 0.0,
            "scheduled_operations": 0,
            "unscheduled_operations": 0,
            "total_operations": 0,
        }

    target_run_id = run_row.id
    run_code = run_row.run_code

    # 2. Makespan calculation from actual schedule timestamps
    span_query = text("""
        SELECT MIN(planned_start) AS first_start, MAX(planned_end) AS last_end, COUNT(*) AS sched_count
        FROM operation_schedules
        WHERE schedule_run_id = :run_id AND status = 'SCHEDULED'
    """)
    span_row = db.execute(span_query, {"run_id": target_run_id}).fetchone()

    first_start = span_row.first_start if span_row else None
    last_end = span_row.last_end if span_row else None
    scheduled_ops = span_row.sched_count or 0

    if first_start and last_end and last_end > first_start:
        total_seconds = (last_end - first_start).total_seconds()
        makespan_hours = round(total_seconds / 3600.0, 2)
        makespan_days = round(total_seconds / 86400.0, 2)
        total_calendar_days = max(1, (last_end.date() - first_start.date()).days + 1)
    else:
        makespan_hours = 0.0
        makespan_days = 0.0
        total_calendar_days = 0

    # 3. Order completion vs Due Date (Total Tardiness, Late Orders, OTD %)
    order_query = text("""
        SELECT po.id, po.order_number, po.due_date, MAX(os.planned_end) AS completion_time
        FROM production_orders po
        JOIN operation_schedules os ON os.production_order_id = po.id
        WHERE os.schedule_run_id = :run_id AND os.status = 'SCHEDULED'
        GROUP BY po.id, po.order_number, po.due_date
    """)
    order_rows = db.execute(order_query, {"run_id": target_run_id}).fetchall()

    total_orders_scheduled = len(order_rows)
    total_tardiness_days = 0
    late_orders_count = 0

    for r in order_rows:
        if r.completion_time and r.due_date:
            comp_date = r.completion_time.date()
            if comp_date > r.due_date:
                delay = (comp_date - r.due_date).days
                total_tardiness_days += delay
                late_orders_count += 1

    if total_orders_scheduled > 0:
        on_time_pct = round(((total_orders_scheduled - late_orders_count) / float(total_orders_scheduled)) * 100.0, 2)
    else:
        on_time_pct = 100.0

    # 4. Total operations and Feasibility Rate
    # Evaluate only the production orders in this run; a run must not be
    # penalized or rewarded by unrelated historical/future orders in the DB.
    total_order_ops_query = text("""
        SELECT COUNT(o.id)
        FROM production_orders po
        JOIN routings r ON r.product_id = po.product_id AND r.is_active = 1
        JOIN operations o ON o.routing_id = r.id
        WHERE po.id IN (
            SELECT DISTINCT production_order_id FROM operation_schedules
            WHERE schedule_run_id = :run_id
            UNION
            SELECT DISTINCT production_order_id FROM constraint_violations
            WHERE schedule_run_id = :run_id AND production_order_id IS NOT NULL
        )
    """)
    total_order_ops = db.execute(total_order_ops_query, {"run_id": target_run_id}).scalar() or 0
    total_orders = db.execute(text("""
        SELECT COUNT(DISTINCT production_order_id)
        FROM (
            SELECT production_order_id FROM operation_schedules WHERE schedule_run_id = :run_id
            UNION
            SELECT production_order_id FROM constraint_violations
            WHERE schedule_run_id = :run_id AND production_order_id IS NOT NULL
        ) run_orders
    """), {"run_id": target_run_id}).scalar() or 0

    if total_order_ops > 0:
        feasibility_pct = round((scheduled_ops / float(total_order_ops)) * 100.0, 2)
    else:
        feasibility_pct = 0.0
    unscheduled_ops = max(0, total_order_ops - scheduled_ops)

    # 5. Machine Utilization Rate using ACTUAL Machine Calendar Availability
    # Sum actual working minutes across active machines from machine_calendars
    cal_query = text("""
        SELECT machine_id, start_time, end_time
        FROM machine_calendars
        WHERE is_working_day = 1
    """)
    cal_rows = db.execute(cal_query).fetchall()

    daily_cap_by_machine: Dict[int, int] = {}
    for cr in cal_rows:
        dur = convert_time_to_minutes(cr.start_time, cr.end_time)
        daily_cap_by_machine[cr.machine_id] = daily_cap_by_machine.get(cr.machine_id, 0) + dur

    active_machines = db.execute(text("SELECT id FROM machines WHERE is_active = 1")).fetchall()
    total_gross_capacity_minutes = 0.0
    for m in active_machines:
        m_daily = daily_cap_by_machine.get(m.id, 0)  # no calendar means no scheduled capacity
        total_gross_capacity_minutes += m_daily * total_calendar_days

    # Subtract planned maintenance downtimes falling within makespan window
    total_downtime_minutes = 0.0
    if first_start and last_end:
        dt_query = text("""
            SELECT start_time, end_time
            FROM machine_downtimes
            WHERE status = 'PLANNED'
              AND start_time < :l_end AND end_time > :f_start
        """)
        dt_rows = db.execute(dt_query, {"f_start": first_start, "l_end": last_end}).fetchall()
        for dt in dt_rows:
            overlap_s = max(dt.start_time, first_start)
            overlap_e = min(dt.end_time, last_end)
            if overlap_e > overlap_s:
                total_downtime_minutes += (overlap_e - overlap_s).total_seconds() / 60.0

    total_net_capacity_minutes = max(1.0, total_gross_capacity_minutes - total_downtime_minutes)

    # Calculate actual busy working minutes from schedule_segments (or operation_schedules)
    seg_busy_query = text("""
        SELECT COALESCE(SUM(duration_minutes), 0)
        FROM schedule_segments ss
        JOIN operation_schedules os ON os.id = ss.operation_schedule_id
        WHERE os.schedule_run_id = :run_id AND os.status = 'SCHEDULED'
    """)
    actual_busy_minutes = float(db.execute(seg_busy_query, {"run_id": target_run_id}).scalar() or 0.0)

    # Fallback to persisted operation windows if segment rows are absent.
    if actual_busy_minutes == 0.0 and scheduled_ops > 0:
        sched_busy_query = text("""
            SELECT COALESCE(SUM(TIMESTAMPDIFF(MINUTE, planned_start, planned_end)), 0)
            FROM operation_schedules
            WHERE schedule_run_id = :run_id AND status = 'SCHEDULED'
        """)
        actual_busy_minutes = float(db.execute(sched_busy_query, {"run_id": target_run_id}).scalar() or 0.0)

    # Setup/changeover is tracked separately; do not count it as productive run time.
    setup_minutes_for_run = db.execute(text("""
        SELECT COALESCE(SUM(changeover_minutes), 0)
        FROM operation_schedules
        WHERE schedule_run_id = :run_id AND status = 'SCHEDULED'
    """), {"run_id": target_run_id}).scalar() or 0
    actual_busy_minutes = max(0.0, actual_busy_minutes - float(setup_minutes_for_run))

    if total_net_capacity_minutes > 0:
        machine_utilization_pct = round((actual_busy_minutes / total_net_capacity_minutes) * 100.0, 2)
    else:
        machine_utilization_pct = 0.0

    # 6. Total Changeover Time using actual persisted setup intervals
    co_query = text("""
        SELECT COALESCE(SUM(changeover_minutes), 0)
        FROM operation_schedules
        WHERE schedule_run_id = :run_id AND status = 'SCHEDULED'
    """)
    total_changeover_minutes = int(db.execute(co_query, {"run_id": target_run_id}).scalar() or 0)

    # If changeover_minutes was not populated, read from run notes or compute from changeover_matrix
    if total_changeover_minutes == 0 and run_row.notes and "Total changeover:" in run_row.notes:
        try:
            part = run_row.notes.split("Total changeover:")[1].split("mins")[0].strip()
            total_changeover_minutes = int(part)
        except Exception:
            total_changeover_minutes = 0

    total_changeover_hours = round(total_changeover_minutes / 60.0, 2)

    # 7. Material Shortage Count and Constraint Violation Count
    shortage_query = text("""
        SELECT COUNT(DISTINCT production_order_id)
        FROM constraint_violations
        WHERE schedule_run_id = :run_id AND issue_type = 'MATERIAL_SHORTAGE'
    """)
    material_shortage_count = db.execute(shortage_query, {"run_id": target_run_id}).scalar() or 0

    cv_query = text("""
        SELECT COUNT(*)
        FROM constraint_violations
        WHERE schedule_run_id = :run_id
    """)
    constraint_violation_count = db.execute(cv_query, {"run_id": target_run_id}).scalar() or 0

    # 8. Derived Metrics: Production Time, Average Order Delay, Downtime Impact
    total_production_time_minutes = round(actual_busy_minutes, 2)
    total_production_time_hours = round(actual_busy_minutes / 60.0, 2)
    average_order_delay_days = round(total_tardiness_days / float(total_orders_scheduled), 2) if total_orders_scheduled > 0 else 0.0
    machine_downtime_impact_minutes = round(total_downtime_minutes, 2)
    machine_downtime_impact_hours = round(total_downtime_minutes / 60.0, 2)

    return {
        "run_id": target_run_id,
        "run_code": run_code,
        # 1. Makespan
        "makespan_hours": makespan_hours,
        "makespan_days": makespan_days,
        # 2. Total Production Time
        "total_production_time_hours": total_production_time_hours,
        "total_production_time_minutes": total_production_time_minutes,
        # 3. Total Changeover Time
        "total_changeover_hours": total_changeover_hours,
        "total_changeover_minutes": total_changeover_minutes,
        # 4. Machine Utilization
        "machine_utilization_pct": machine_utilization_pct,
        # 5. On-Time Delivery Percentage
        "on_time_delivery_pct": on_time_pct,
        # 6. Total Tardiness
        "total_tardiness_days": total_tardiness_days,
        # 7. Average Order Delay
        "average_order_delay_days": average_order_delay_days,
        # 8. Number of Late Orders
        "late_orders_count": late_orders_count,
        # 9. Number of Infeasible Operations
        "infeasible_operations_count": unscheduled_ops,
        # 10. Constraint Violation Count
        "constraint_violation_count": constraint_violation_count,
        # 11. Material Shortage Count
        "material_shortage_count": material_shortage_count,
        # 12. Machine Downtime Impact
        "machine_downtime_impact_hours": machine_downtime_impact_hours,
        "machine_downtime_impact_minutes": machine_downtime_impact_minutes,
        # Order and Operation Summaries
        "scheduled_orders_count": total_orders_scheduled,
        "total_orders_count": total_orders,
        "schedule_feasibility_pct": feasibility_pct,
        "scheduled_operations": scheduled_ops,
        "unscheduled_operations": unscheduled_ops,
        "total_operations": total_order_ops,
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        metrics = calculate_evaluation_metrics(db)
        print("Calculated Evaluation Metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
    finally:
        db.close()
