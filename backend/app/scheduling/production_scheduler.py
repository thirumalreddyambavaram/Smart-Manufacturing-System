"""
YottaFlex Production Scheduling Engine
Schedules manufacturing operations across eligible machines respecting:
- Product routing and operation sequence precedence
- Machine eligibility and capacity
- Machine working shift calendars
- Sequence-dependent changeover matrix
- Planned machine downtimes
- Material availability dates and quantities (BOM)
- Shared tooling constraints
- Production order priorities and due dates
- Infeasibility logging with explicit constraint violations
- Event history logging and schedule run tracking
"""

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    ConstraintViolation,
    EventHistory,
    OperationSchedule,
    ProductionOrder,
    ScheduleRun,
    ScheduleSegment,
)
from app.services.schedule_manager import (
    create_schedule_run,
    finish_schedule_run,
    save_operation_schedule,
)
from app.services.scheduling_rules import (
    calculate_operation_duration,
    calculate_changeover_time,
)
from app.services.material_service import (
    reserve_material_for_order,
    consume_reserved_material,
    InsufficientInventoryError,
    MaterialNotYetAvailableError,
)
from app.services.labor_service import (
    get_active_labor_shifts,
    find_shift_for_window,
    check_labor_availability,
    assign_labor_to_schedule,
)


def record_violation(
    db: Session,
    run_id: int,
    order_id: Optional[int],
    operation_id: Optional[int],
    issue_type: str,
    description: str,
    machine_id: Optional[int] = None,
    ground_truth: bool = False,
):
    """Log an explicit constraint violation with full traceability."""
    violation = ConstraintViolation(
        schedule_run_id=run_id,
        production_order_id=order_id,
        operation_id=operation_id,
        machine_id=machine_id,
        issue_type=issue_type,
        severity="HIGH" if not ground_truth else "CRITICAL",
        description=description,
        ground_truth=ground_truth,
        detected_at=datetime.now(),
    )
    db.add(violation)


def convert_time_to_obj(val) -> time:
    """Helper to convert db time / timedelta into datetime.time object."""
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total_sec = int(val.total_seconds())
        h = (total_sec // 3600) % 24
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        return time(h, m, s)
    if isinstance(val, str):
        parts = [int(p) for p in val.split(":")]
        return time(parts[0], parts[1], parts[2] if len(parts) > 2 else 0)
    return time(6, 0)


def prefetch_scheduling_master_data(db: Session):
    """
    Prefetch master data into memory for high-performance scheduling.
    Eliminates thousands of repetitive database roundtrips.
    """
    # 1. Calendars by machine
    cal_rows = db.execute(text("""
        SELECT machine_id, shift_name, start_time, end_time, is_working_day
        FROM machine_calendars
        WHERE is_working_day = 1
        ORDER BY machine_id, start_time
    """)).fetchall()

    calendars_by_machine: Dict[int, List[dict]] = {}
    for r in cal_rows:
        calendars_by_machine.setdefault(r.machine_id, []).append({
            "shift_name": r.shift_name,
            "start_time": convert_time_to_obj(r.start_time),
            "end_time": convert_time_to_obj(r.end_time),
        })

    # 2. Eligible machines by operation
    elig_rows = db.execute(text("""
        SELECT e.operation_id, m.id, m.machine_code, m.machine_type, m.capacity_per_hour
        FROM operation_machine_eligibility e
        JOIN machines m ON m.id = e.machine_id
        WHERE e.is_active = 1 AND m.is_active = 1
        ORDER BY m.id
    """)).fetchall()

    eligibility_by_op: Dict[int, List[dict]] = {}
    for r in elig_rows:
        eligibility_by_op.setdefault(r.operation_id, []).append({
            "id": r.id,
            "machine_code": r.machine_code,
            "machine_type": r.machine_type,
            "capacity_per_hour": float(r.capacity_per_hour),
        })

    # 3. Product BOM requirements
    bom_rows = db.execute(text("""
        SELECT pm.product_id, pm.material_id, pm.quantity_required, m.material_code, m.material_name, m.unit_of_measure
        FROM product_materials pm
        JOIN materials m ON m.id = pm.material_id
        WHERE m.is_active = 1
    """)).fetchall()

    bom_by_product: Dict[int, List[dict]] = {}
    for r in bom_rows:
        bom_by_product.setdefault(r.product_id, []).append({
            "material_id": r.material_id,
            "quantity_required": float(r.quantity_required),
            "material_code": r.material_code,
            "material_name": r.material_name,
            "unit_of_measure": r.unit_of_measure,
        })

    # 4. Changeover matrix
    cm_rows = db.execute(text("""
        SELECT machine_id, from_product_id, to_product_id, duration_minutes
        FROM changeover_matrix
    """)).fetchall()

    changeovers: Dict[Tuple[int, int, int], int] = {}
    for r in cm_rows:
        changeovers[(r.machine_id, r.from_product_id, r.to_product_id)] = int(r.duration_minutes)

    # 5. Planned machine downtime
    dt_rows = db.execute(text("""
        SELECT machine_id, start_time, end_time, reason
        FROM machine_downtimes
        WHERE status = 'PLANNED'
        ORDER BY start_time
    """)).fetchall()

    downtimes_by_machine: Dict[int, List[Tuple[datetime, datetime]]] = {}
    for r in dt_rows:
        downtimes_by_machine.setdefault(r.machine_id, []).append((r.start_time, r.end_time))

    # 6. Shared tools by operation
    tool_rows = db.execute(text("""
        SELECT ot.operation_id, ot.tool_id, t.tool_code, t.tool_name, t.total_quantity
        FROM operation_tools ot
        JOIN tools t ON t.id = ot.tool_id
        WHERE t.is_active = 1
    """)).fetchall()

    tools_by_op: Dict[int, List[dict]] = {}
    for r in tool_rows:
        tools_by_op.setdefault(r.operation_id, []).append({
            "tool_id": r.tool_id,
            "tool_code": r.tool_code,
            "tool_name": r.tool_name,
            "total_quantity": r.total_quantity,
        })

    # 7. Existing active schedule bookings per machine
    existing_scheds = db.execute(text("""
        SELECT os.machine_id, os.planned_start, os.planned_end, po.product_id
        FROM operation_schedules os
        JOIN production_orders po ON po.id = os.production_order_id
        WHERE os.status IN ('SCHEDULED', 'IN_PROGRESS')
        ORDER BY os.planned_start
    """)).fetchall()

    bookings_by_machine: Dict[int, List[Tuple[datetime, datetime]]] = {}
    last_product_on_machine: Dict[int, int] = {}
    for r in existing_scheds:
        bookings_by_machine.setdefault(r.machine_id, []).append((r.planned_start, r.planned_end))
        last_product_on_machine[r.machine_id] = r.product_id

    # 8. Existing shared-tool bookings from previously persisted schedules.
    existing_tool_rows = db.execute(text("""
        SELECT ot.tool_id, os.planned_start, os.planned_end
        FROM operation_schedules os
        JOIN operation_tools ot ON ot.operation_id = os.operation_id
        WHERE os.status IN ('SCHEDULED', 'IN_PROGRESS')
    """)).fetchall()
    tool_bookings: Dict[int, List[Tuple[datetime, datetime]]] = {}
    for r in existing_tool_rows:
        tool_bookings.setdefault(r.tool_id, []).append((r.planned_start, r.planned_end))

    # 9. Existing labor allocations must consume capacity in later runs too.
    labor_rows = db.execute(text("""
        SELECT assigned_start, assigned_end, workers_assigned
        FROM labor_assignments
        WHERE status = 'ASSIGNED'
    """)).fetchall()
    labor_bookings = [
        {"assigned_start": r.assigned_start, "assigned_end": r.assigned_end,
         "workers_assigned": int(r.workers_assigned or 1)} for r in labor_rows
    ]

    # 10. Active Labor Shifts
    labor_shifts = get_active_labor_shifts(db)

    return {
        "calendars": calendars_by_machine,
        "eligibility": eligibility_by_op,
        "bom": bom_by_product,
        "changeovers": changeovers,
        "downtimes": downtimes_by_machine,
        "tools": tools_by_op,
        "bookings": bookings_by_machine,
        "last_product": last_product_on_machine,
        "labor_shifts": labor_shifts,
        "tool_bookings": tool_bookings,
        "labor_bookings": labor_bookings,
    }


def get_tool_busy_intervals(
    bookings: List[Tuple[datetime, datetime]], capacity: int
) -> List[Tuple[datetime, datetime]]:
    """
    Given a list of (start, end) bookings and tool capacity,
    returns intervals where capacity is fully occupied.
    """
    if not bookings or capacity <= 0:
        return []
    if capacity == 1:
        sorted_b = sorted(bookings, key=lambda x: x[0])
        merged = []
        for s, e in sorted_b:
            if not merged or s > merged[-1][1]:
                merged.append((s, e))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        return merged

    events = []
    for s, e in bookings:
        events.append((s, 1))
        events.append((e, -1))
    events.sort(key=lambda x: (x[0], -x[1]))

    busy_intervals = []
    curr = 0
    busy_start = None
    for t, delta in events:
        prev = curr
        curr += delta
        if prev < capacity and curr >= capacity:
            busy_start = t
        elif prev >= capacity and curr < capacity:
            if busy_start and busy_start < t:
                busy_intervals.append((busy_start, t))
            busy_start = None
    return busy_intervals


def find_feasible_machine_slot(
    machine_id: int,
    requested_start: datetime,
    duration_minutes: int,
    calendars: List[dict],
    downtimes: List[Tuple[datetime, datetime]],
    bookings: List[Tuple[datetime, datetime]],
    extra_blocked: Optional[List[Tuple[datetime, datetime]]] = None,
    max_days: int = 400,
) -> Optional[List[Tuple[datetime, datetime]]]:
    """
    Find contiguous working shift segments for an operation on a machine respecting:
    - Non-preemption by other jobs (operations run without being interleaved by other bookings)
    - Shift working calendars
    - Planned maintenance downtimes
    - Shared tooling availability (extra_blocked)
    """
    if not calendars or duration_minutes <= 0:
        return None

    # Sort existing bookings on this machine
    sorted_bookings = sorted(bookings, key=lambda x: x[0])

    # Candidate windows where this machine is free of other jobs:
    windows: List[Tuple[datetime, Optional[datetime]]] = []
    c_start = requested_start
    for bk_s, bk_e in sorted_bookings:
        if bk_e <= c_start:
            continue
        if bk_s > c_start:
            windows.append((c_start, bk_s))
        c_start = max(c_start, bk_e)
    windows.append((c_start, None))  # after all bookings

    for w_start, w_end in windows:
        if w_start < requested_start:
            w_start = requested_start
        if w_end is not None and w_start >= w_end:
            continue

        remaining = duration_minutes
        segments = []
        curr_date = w_start.date()
        limit_date = (w_end.date() if w_end else (w_start.date() + timedelta(days=max_days)))

        while curr_date <= limit_date:
            for cal in calendars:
                shift_start = datetime.combine(curr_date, cal["start_time"])
                shift_end = datetime.combine(curr_date, cal["end_time"])
                if shift_end <= shift_start:
                    shift_end += timedelta(days=1)

                if shift_end <= w_start:
                    continue
                actual_shift_start = max(shift_start, w_start)
                actual_shift_end = min(shift_end, w_end) if w_end else shift_end

                if actual_shift_start >= actual_shift_end:
                    continue

                blocks = []
                for dt_s, dt_e in downtimes:
                    if dt_s < actual_shift_end and dt_e > actual_shift_start:
                        blocks.append((max(dt_s, actual_shift_start), min(dt_e, actual_shift_end)))
                if extra_blocked:
                    for eb_s, eb_e in extra_blocked:
                        if eb_s < actual_shift_end and eb_e > actual_shift_start:
                            blocks.append((max(eb_s, actual_shift_start), min(eb_e, actual_shift_end)))

                blocks.sort(key=lambda x: x[0])
                merged = []
                for b_s, b_e in blocks:
                    if not merged or b_s > merged[-1][1]:
                        merged.append([b_s, b_e])
                    else:
                        merged[-1][1] = max(merged[-1][1], b_e)

                cursor = actual_shift_start
                for b_s, b_e in merged:
                    if cursor < b_s and remaining > 0:
                        avail = int((b_s - cursor).total_seconds() / 60)
                        worked = min(remaining, avail)
                        if worked > 0:
                            segments.append((cursor, cursor + timedelta(minutes=worked)))
                            remaining -= worked
                        if remaining == 0:
                            return segments
                    cursor = max(cursor, b_e)

                if cursor < actual_shift_end and remaining > 0:
                    avail = int((actual_shift_end - cursor).total_seconds() / 60)
                    worked = min(remaining, avail)
                    if worked > 0:
                        segments.append((cursor, cursor + timedelta(minutes=worked)))
                        remaining -= worked
                    if remaining == 0:
                        return segments

            curr_date += timedelta(days=1)

    return None


def run_production_scheduler(
    work_date: Optional[date] = None,
    max_orders: Optional[int] = None,
    algorithm: str = "HEURISTIC",
    random_seed: int = 20261022,
) -> dict:
    """
    Execute end-to-end production scheduling across machines with full constraint satisfaction.
    Returns metrics and summary dict.
    """
    if work_date is None:
        work_date = date(2026, 11, 2)

    db = SessionLocal()
    run = None

    try:
        run = create_schedule_run(
            db,
            work_date,
            notes=(
                f"Production scheduling run on {work_date} using {algorithm} engine "
                "with routing, shift calendars, changeovers, materials and tooling constraints."
            ),
        )

        # Prefetch master tables
        master = prefetch_scheduling_master_data(db)

        # Load inventory lots and calculate available material balances & earliest availability dates
        lot_rows = db.execute(text("""
            SELECT material_id, SUM(quantity_available) AS total_qty, MIN(available_from) AS min_available_from
            FROM inventory_lots
            WHERE status = 'AVAILABLE'
            GROUP BY material_id
        """)).fetchall()

        material_stock: Dict[int, float] = {r.material_id: float(r.total_qty or 0) for r in lot_rows}
        material_dates: Dict[int, datetime] = {r.material_id: r.min_available_from for r in lot_rows}

        # Query pending orders and their operations
        query = text("""
            SELECT
                po.id AS order_id,
                po.order_number,
                po.product_id,
                po.quantity,
                po.priority,
                po.order_date,
                po.due_date,
                p.product_code,
                p.product_name,
                o.id AS operation_id,
                o.operation_code,
                o.operation_name,
                o.sequence_number,
                o.estimated_time_minutes
            FROM production_orders po
            JOIN products p ON p.id = po.product_id
            JOIN routings r ON r.product_id = p.id AND r.is_active = 1
            JOIN operations o ON o.routing_id = r.id
            WHERE po.status = 'PENDING'
              AND NOT EXISTS (
                  SELECT 1 FROM operation_schedules os
                  WHERE os.production_order_id = po.id
                    AND os.status IN ('SCHEDULED', 'IN_PROGRESS')
              )
            ORDER BY
                CASE po.priority
                    WHEN 'URGENT' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'NORMAL' THEN 3
                    ELSE 4
                END,
                po.due_date ASC,
                po.id ASC,
                o.sequence_number ASC
        """)
        all_ops = db.execute(query).fetchall()

        if not all_ops:
            finish_schedule_run(db, run.id, "COMPLETED", notes="No pending unscheduled orders.")
            return {"run_code": run.run_code, "status": "COMPLETED", "scheduled": 0, "unscheduled": 0}

        # Group operations by production order
        orders_dict = {}
        for row in all_ops:
            orders_dict.setdefault(row.order_id, []).append(row)

        order_list = list(orders_dict.items())
        if max_orders is not None:
            order_list = order_list[:max_orders]

        scheduled_ops_count = 0
        unscheduled_ops_count = 0
        scheduled_orders_count = 0
        material_shortage_orders = 0
        total_changeover_minutes = 0

        # Tool booking timeline: tool_id -> list of (start, end)
        tool_bookings: Dict[int, List[Tuple[datetime, datetime]]] = {
            key: list(value) for key, value in master["tool_bookings"].items()
        }
        labor_bookings = list(master["labor_bookings"])

        # Schedule order by order
        for order_id, op_rows in order_list:
            first_row = op_rows[0]
            prod_id = first_row.product_id
            order_qty = first_row.quantity

            # 1. Check Material Availability (BOM)
            bom_items = master["bom"].get(prod_id, [])
            shortage_found = False
            earliest_mat_date = datetime.combine(work_date, time(6, 0))

            for item in bom_items:
                needed = item["quantity_required"] * order_qty
                avail = material_stock.get(item["material_id"], 0.0)
                if avail < needed:
                    shortage_found = True
                    material_shortage_orders += 1
                    desc = (
                        f"Order {first_row.order_number}: Material shortage for {item['material_name']} "
                        f"({item['material_code']}). Required: {needed:.2f} {item['unit_of_measure']}, "
                        f"Available: {avail:.2f}."
                    )
                    record_violation(db, run.id, order_id, first_row.operation_id, "MATERIAL_SHORTAGE", desc)
                    break
                else:
                    mat_avail_date = material_dates.get(item["material_id"])
                    if mat_avail_date and mat_avail_date > earliest_mat_date:
                        earliest_mat_date = mat_avail_date

            if shortage_found:
                unscheduled_ops_count += len(op_rows)
                continue

            # Reserve materials only after a complete machine-feasible plan exists.
            order_reservations = []

            # 2. Schedule operations sequentially for this order
            order_possible = True
            order_schedules = []
            prev_op_end = earliest_mat_date

            for op in op_rows:
                # Find eligible machines
                eligible_machs = master["eligibility"].get(op.operation_id, [])
                if not eligible_machs:
                    record_violation(
                        db, run.id, order_id, op.operation_id, "NO_ELIGIBLE_MACHINE",
                        f"No eligible active machines found for operation {op.operation_code}."
                    )
                    order_possible = False
                    break

                # Gather shared tool busy intervals for this operation
                op_tools = master["tools"].get(op.operation_id, [])
                tool_busy_intervals: List[Tuple[datetime, datetime]] = []
                for t in op_tools:
                    t_id = t["tool_id"]
                    t_capacity = t["total_quantity"]
                    busy = get_tool_busy_intervals(tool_bookings.get(t_id, []), t_capacity)
                    tool_busy_intervals.extend(busy)

                # Evaluate machines
                best_completion = None
                best_mach = None
                best_segments = None
                best_changeover = 0

                for m in eligible_machs:
                    m_id = m["id"]
                    proc_duration = calculate_operation_duration(
                        order_qty, op.estimated_time_minutes, m["capacity_per_hour"]
                    )

                    # Changeover calculation
                    prev_p = master["last_product"].get(m_id)
                    if prev_p is not None and prev_p != prod_id:
                        changeover_min = master["changeovers"].get((m_id, prev_p, prod_id), 30)
                    else:
                        changeover_min = 0

                    total_op_min = proc_duration + changeover_min

                    m_calendars = master["calendars"].get(m_id, [])
                    m_downtimes = master["downtimes"].get(m_id, [])
                    m_bookings = master["bookings"].get(m_id, [])

                    # Append after the machine's latest committed booking. This keeps
                    # sequence-dependent setup tied to the actual predecessor product;
                    # inserting into an earlier gap would require reconstructing both
                    # predecessor and successor changeovers.
                    machine_bookings = master["bookings"].get(m_id, [])
                    machine_ready_at = max(
                        [prev_op_end] + [booking_end for _booking_start, booking_end in machine_bookings]
                    )
                    segments = find_feasible_machine_slot(
                        machine_id=m_id,
                        requested_start=machine_ready_at,
                        duration_minutes=total_op_min,
                        calendars=m_calendars,
                        downtimes=m_downtimes,
                        bookings=m_bookings,
                        extra_blocked=tool_busy_intervals,
                    )

                    if segments:
                        labor_ok = True
                        labor_failure = None
                        for seg_start, seg_end in segments:
                            available, explanation, _shift_id = check_labor_availability(
                                db=db, target_start=seg_start, target_end=seg_end,
                                required_workers=1, existing_assignments=labor_bookings,
                                shifts=master["labor_shifts"],
                            )
                            if not available:
                                labor_ok = False
                                labor_failure = explanation
                                break
                        if not labor_ok:
                            record_violation(
                                db, run.id, order_id, op.operation_id,
                                "LABOR_UNAVAILABLE", labor_failure or "No labor capacity for operation.",
                                machine_id=m_id,
                            )
                            continue
                        op_end = segments[-1][1]
                        if best_completion is None or op_end < best_completion:
                            best_completion = op_end
                            best_mach = m
                            best_segments = segments
                            best_changeover = changeover_min

                if not best_segments:
                    record_violation(
                        db, run.id, order_id, op.operation_id, "NO_AVAILABLE_MACHINE_SLOT",
                        f"Could not find a feasible schedule slot on any eligible machine for {op.operation_code}."
                    )
                    order_possible = False
                    break

                # Buffer plan
                order_schedules.append({
                    "operation_id": op.operation_id,
                    "machine_id": best_mach["id"],
                    "segments": best_segments,
                    "changeover_minutes": best_changeover,
                    "planned_start": best_segments[0][0],
                    "planned_end": best_segments[-1][1],
                    "tools": op_tools,
                })
                prev_op_end = best_segments[-1][1]

            if not order_possible:
                unscheduled_ops_count += len(op_rows)
                continue

            # Reserve against inventory available by the planned first-operation start.
            reservation_failed = False
            required_material_date = order_schedules[0]["planned_start"]
            try:
                for item in bom_items:
                    needed = item["quantity_required"] * order_qty
                    res_list = reserve_material_for_order(
                        db=db,
                        production_order_id=order_id,
                        material_id=item["material_id"],
                        quantity_required=needed,
                        operation_id=first_row.operation_id,
                        required_date=required_material_date,
                    )
                    order_reservations.extend(res_list)
            except Exception as ex:
                from app.services.material_service import release_reserved_material_for_order
                release_reserved_material_for_order(
                    db, order_id, reason=f"Scheduling material reservation failed: {ex}"
                )
                record_violation(
                    db, run.id, order_id, first_row.operation_id,
                    "MATERIAL_RESERVATION_ERROR", str(ex)
                )
                reservation_failed = True

            if reservation_failed:
                unscheduled_ops_count += len(op_rows)
                continue

            for item in bom_items:
                material_stock[item["material_id"]] -= item["quantity_required"] * order_qty

            # 4. Commit schedules for this valid order
            for plan in order_schedules:
                sched = save_operation_schedule(
                    db=db,
                    schedule_run_id=run.id,
                    production_order_id=order_id,
                    operation_id=plan["operation_id"],
                    machine_id=plan["machine_id"],
                    segments=plan["segments"],
                    status="SCHEDULED",
                    changeover_minutes=plan["changeover_minutes"],
                )
                scheduled_ops_count += 1
                total_changeover_minutes += plan["changeover_minutes"]

                # Register machine booking
                m_id = plan["machine_id"]
                master["bookings"].setdefault(m_id, []).append((plan["planned_start"], plan["planned_end"]))
                master["last_product"][m_id] = prod_id

                # Register tool bookings
                for t in plan["tools"]:
                    tool_bookings.setdefault(t["tool_id"], []).append((plan["planned_start"], plan["planned_end"]))

                # Persist Labor Assignments for each segment
                for seg_s, seg_e in plan["segments"]:
                    cov_shift = find_shift_for_window(master["labor_shifts"], seg_s, seg_e)
                    if cov_shift is None:
                        raise RuntimeError(
                            f"Labor shift coverage disappeared for {seg_s} to {seg_e}; refusing invalid assignment."
                        )
                    shift_id = cov_shift["id"]
                    assign_labor_to_schedule(
                        db=db,
                        schedule_run_id=run.id,
                        operation_schedule_id=sched.id,
                        labor_shift_id=shift_id,
                        workers_assigned=1,
                        assigned_start=seg_s,
                        assigned_end=seg_e,
                    )
                    labor_bookings.append({
                        "assigned_start": seg_s, "assigned_end": seg_e,
                        "workers_assigned": 1,
                    })

            # Consume reserved materials upon order scheduling
            consumption_failed = False
            for res in order_reservations:
                try:
                    consume_reserved_material(
                        db=db,
                        reservation_id=res.id,
                        consumed_at=order_schedules[0]["planned_start"],
                    )
                except Exception as ex:
                    record_violation(
                        db, run.id, order_id, first_row.operation_id,
                        "MATERIAL_CONSUMPTION_ERROR", str(ex)
                    )
                    consumption_failed = True

            if consumption_failed:
                # Roll back this order as one unit: schedules, labor assignments,
                # reservations, and any partial consumption all share this transaction.
                db.rollback()
                for item in bom_items:
                    material_stock[item["material_id"]] += item["quantity_required"] * order_qty
                record_violation(
                    db, run.id, order_id, first_row.operation_id,
                    "MATERIAL_CONSUMPTION_ERROR",
                    "Order transaction rolled back because reserved material could not be consumed.",
                )
                unscheduled_ops_count += len(op_rows)
                continue

            # Mark order as SCHEDULED and commit the complete order atomically.
            order_record = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
            if order_record:
                order_record.status = "SCHEDULED"
            scheduled_orders_count += 1
            db.commit()

        db.commit()

        summary_note = (
            f"Scheduled: {scheduled_ops_count} operations across {scheduled_orders_count} orders; "
            f"Unscheduled: {unscheduled_ops_count} operations; "
            f"Material shortages: {material_shortage_orders}; "
            f"Total changeover: {total_changeover_minutes} mins."
        )
        finish_schedule_run(db, run.id, "COMPLETED", notes=summary_note)

        print(f"\nScheduling run {run.run_code} completed successfully!")
        print(f"  {summary_note}")

        return {
            "run_id": run.id,
            "run_code": run.run_code,
            "status": "COMPLETED",
            "scheduled_operations": scheduled_ops_count,
            "unscheduled_operations": unscheduled_ops_count,
            "scheduled_orders": scheduled_orders_count,
            "material_shortage_orders": material_shortage_orders,
            "total_changeover_minutes": total_changeover_minutes,
            "constraint_violations": db.query(ConstraintViolation).filter(
                ConstraintViolation.schedule_run_id == run.id
            ).count(),
            "message": summary_note,

        }

    except Exception as e:
        db.rollback()
        if run:
            try:
                finish_schedule_run(db, run.id, "FAILED", notes=str(e)[:1000])
            except Exception:
                db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    result = run_production_scheduler(
        work_date=date(2026, 11, 2),
        max_orders=100,
    )
    print("Result:", result)
