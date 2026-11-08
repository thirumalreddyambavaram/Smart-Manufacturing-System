"""
Comprehensive tests for formal manufacturing evaluation metrics calculation:
- Makespan (hours and days)
- Total tardiness
- Number of late orders
- On-time delivery percentage
- Machine utilization from actual machine calendars
- Feasibility rate
- Changeover time
- Material shortage count
- Number of unscheduled operations
- Empty dataset / division-by-zero protection
- Known input records with exact expected numerical outputs
"""

import pytest
from datetime import datetime, date, time, timedelta
from sqlalchemy import text

from app.database import SessionLocal
from app.models import ScheduleRun, OperationSchedule, ProductionOrder, Machine, MachineCalendar
from app.services.evaluation_metrics import calculate_evaluation_metrics, convert_time_to_minutes


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_time_to_minutes_helper():
    """Test duration calculation handles regular and midnight-wrapping shifts."""
    # Regular 8-hour shift
    assert convert_time_to_minutes(time(6, 0), time(14, 0)) == 480
    # Evening 8-hour shift
    assert convert_time_to_minutes(time(14, 0), time(22, 0)) == 480
    # Night shift wrapping midnight
    assert convert_time_to_minutes(time(22, 0), time(6, 0)) == 480


def test_empty_dataset_handling(db_session):
    """Test calling evaluation metrics with a non-existent run ID safely returns zeroed metrics without ZeroDivisionError."""
    metrics = calculate_evaluation_metrics(db=db_session, schedule_run_id=99999999)
    assert metrics["run_code"] == "NONE"
    assert metrics["makespan_hours"] == 0.0
    assert metrics["makespan_days"] == 0.0
    assert metrics["total_tardiness_days"] == 0
    assert metrics["late_orders_count"] == 0
    assert metrics["on_time_delivery_pct"] == 100.0
    assert metrics["machine_utilization_pct"] == 0.0
    assert metrics["schedule_feasibility_pct"] == 0.0
    assert metrics["total_changeover_hours"] == 0.0
    assert metrics["material_shortage_count"] == 0


def test_known_input_records_numerical_outputs(db_session):
    """
    Test evaluation metrics against a synthetic test run with strictly known records and deterministic expectations:
    - 2 orders: Order A (finished on-time), Order B (finished 2 days late)
    - Schedule window: 2026-11-10 06:00 to 2026-11-10 18:00 (12.0 hours)
    - Expected Makespan: exactly 12.0 hours (0.5 days)
    - Expected Late Orders: exactly 1
    - Expected Total Tardiness: exactly 2 days
    - Expected OTD %: exactly 50.0%
    """
    # 1. Create test ScheduleRun
    test_run = ScheduleRun(
        run_code="RUN-TEST-METRICS-001",
        status="COMPLETED",
        algorithm="HEURISTIC",
        notes="Total changeover: 45 mins",
    )
    db_session.add(test_run)
    db_session.flush()

    # Query valid product and machine
    prod_id = db_session.execute(text("SELECT id FROM products LIMIT 1")).scalar() or 1
    mach_id = db_session.execute(text("SELECT id FROM machines LIMIT 1")).scalar() or 1
    op_id = db_session.execute(text("SELECT id FROM operations LIMIT 1")).scalar() or 1

    # Order A: due 2026-11-12, planned completion 2026-11-10 12:00 -> ON TIME (delay 0)
    order_a = ProductionOrder(
        order_number="ORD-TEST-METRICS-A",
        product_id=prod_id,
        quantity=10,
        priority="NORMAL",
        order_date=date(2026, 11, 1),
        due_date=date(2026, 11, 12),
        status="SCHEDULED",
    )
    # Order B: due 2026-11-08, planned completion 2026-11-10 18:00 -> LATE by exactly 2 days
    order_b = ProductionOrder(
        order_number="ORD-TEST-METRICS-B",
        product_id=prod_id,
        quantity=10,
        priority="HIGH",
        order_date=date(2026, 11, 1),
        due_date=date(2026, 11, 8),
        status="SCHEDULED",
    )
    db_session.add_all([order_a, order_b])
    db_session.flush()

    # Schedule for Order A
    sched_a = OperationSchedule(
        schedule_code="SCH-TEST-METRICS-A",
        production_order_id=order_a.id,
        operation_id=op_id,
        machine_id=mach_id,
        schedule_run_id=test_run.id,
        planned_start=datetime(2026, 11, 10, 6, 0, 0),
        planned_end=datetime(2026, 11, 10, 12, 0, 0),
        changeover_minutes=15,
        status="SCHEDULED",
    )
    # Schedule for Order B
    sched_b = OperationSchedule(
        schedule_code="SCH-TEST-METRICS-B",
        production_order_id=order_b.id,
        operation_id=op_id,
        machine_id=mach_id,
        schedule_run_id=test_run.id,
        planned_start=datetime(2026, 11, 10, 12, 0, 0),
        planned_end=datetime(2026, 11, 10, 18, 0, 0),
        changeover_minutes=30,
        status="SCHEDULED",
    )
    db_session.add_all([sched_a, sched_b])
    db_session.commit()

    try:
        metrics = calculate_evaluation_metrics(db=db_session, schedule_run_id=test_run.id)

        # 1. Makespan: 06:00 to 18:00 = 12.0 hours = 0.5 days
        assert metrics["makespan_hours"] == 12.0
        assert metrics["makespan_days"] == 0.5

        # 2. Tardiness: Order A delay 0, Order B delay 2 days (Nov 10 - Nov 8)
        assert metrics["total_tardiness_days"] == 2

        # 3. Late orders count: 1 of 2
        assert metrics["late_orders_count"] == 1
        assert metrics["scheduled_orders_count"] == 2

        # 4. On-time delivery %: (2 - 1) / 2 = 50.0%
        assert metrics["on_time_delivery_pct"] == 50.0

        # 5. Persisted changeovers: 15 + 30 = 45 mins = 0.75 hours
        assert metrics["total_changeover_minutes"] == 45
        assert metrics["total_changeover_hours"] == 0.75

        # 6. Scheduled ops
        assert metrics["scheduled_operations"] == 2

    finally:
        # Clean up test records
        db_session.delete(sched_a)
        db_session.delete(sched_b)
        db_session.delete(order_a)
        db_session.delete(order_b)
        db_session.delete(test_run)
        db_session.commit()


def test_calculate_evaluation_metrics_live_run(db_session):
    """Test evaluation metrics calculation for active completed run from real database."""
    metrics = calculate_evaluation_metrics(db_session)

    assert "makespan_hours" in metrics
    assert "makespan_days" in metrics
    assert "total_tardiness_days" in metrics
    assert "late_orders_count" in metrics
    assert "on_time_delivery_pct" in metrics
    assert "machine_utilization_pct" in metrics
    assert "schedule_feasibility_pct" in metrics
    assert "material_shortage_count" in metrics
    assert "total_changeover_hours" in metrics
    assert "total_changeover_minutes" in metrics
    assert "scheduled_operations" in metrics
    assert "unscheduled_operations" in metrics
    assert "total_operations" in metrics

    assert metrics["makespan_hours"] >= 0.0
    assert 0.0 <= metrics["on_time_delivery_pct"] <= 100.0
    assert 0.0 <= metrics["machine_utilization_pct"] <= 100.0
    assert 0.0 <= metrics["schedule_feasibility_pct"] <= 100.0
