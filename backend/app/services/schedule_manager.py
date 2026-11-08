from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    OperationSchedule,
    ScheduleSegment,
    EventHistory,
    ScheduleRun,
)


def save_operation_schedule(
    db: Session,
    schedule_run_id: int,
    production_order_id: int,
    operation_id: int,
    machine_id: int,
    segments: list,
    status: str = "SCHEDULED",
    changeover_minutes: int = 0,
):
    """
    Save one operation schedule, changeover duration, and all its working segments.
    All records are saved in one transaction.
    """

    if not segments:
        raise ValueError("At least one working segment is required.")

    if status not in {"SCHEDULED", "IN_PROGRESS", "COMPLETED"}:
        raise ValueError("Invalid schedule status.")

    ordered_segments = sorted(
        segments,
        key=lambda segment: segment[0]
    )

    total_minutes = 0
    previous_end = None

    for start, end in ordered_segments:
        if end <= start:
            raise ValueError("Segment end must be after segment start.")

        if previous_end is not None and start < previous_end:
            raise ValueError("Working segments cannot overlap.")

        minutes = int((end - start).total_seconds() / 60)
        if minutes <= 0:
            raise ValueError("Segment duration must be positive.")

        total_minutes += minutes
        previous_end = end

    try:
        schedule = OperationSchedule(
            production_order_id=production_order_id,
            operation_id=operation_id,
            machine_id=machine_id,
            schedule_run_id=schedule_run_id,
            planned_start=ordered_segments[0][0],
            planned_end=ordered_segments[-1][1],
            status=status,
            changeover_minutes=changeover_minutes,
        )

        db.add(schedule)
        db.flush()

        year = ordered_segments[0][0].year
        schedule.schedule_code = f"SCH-{year}-{schedule.id:06d}"

        for index, (start, end) in enumerate(ordered_segments, start=1):
            segment = ScheduleSegment(
                operation_schedule_id=schedule.id,
                segment_number=index,
                segment_start=start,
                segment_end=end,
                duration_minutes=int((end - start).total_seconds() / 60),
            )
            db.add(segment)

        event = EventHistory(
            entity_type="OperationSchedule",
            entity_id=schedule.id,
            event_type="SCHEDULE_CREATED",
            old_values=None,
            new_values={
                "schedule_code": schedule.schedule_code,
                "schedule_run_id": schedule_run_id,
                "production_order_id": production_order_id,
                "operation_id": operation_id,
                "machine_id": machine_id,
                "planned_start": schedule.planned_start.isoformat(),
                "planned_end": schedule.planned_end.isoformat(),
                "total_working_minutes": total_minutes,
                "changeover_minutes": changeover_minutes,
                "segment_count": len(ordered_segments),
                "status": status,
            },
            actor="SYSTEM",
            occurred_at=datetime.now(),
        )

        db.add(event)
        # The scheduler owns the transaction boundary so an order's schedules,
        # labor, tooling, and material movements can commit or roll back together.
        db.flush()
        return schedule

    except Exception:
        db.rollback()
        raise


def create_schedule_run(db, work_date, notes=None):
    count = db.query(ScheduleRun).count()
    run_code = f"RUN-{count + 1:06d}"

    run = ScheduleRun(
        run_code=run_code,
        started_at=datetime.now(),
        status="RUNNING",
        notes=notes,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def finish_schedule_run(db, run_id, status="COMPLETED", notes=None):
    run = db.query(ScheduleRun).filter(ScheduleRun.id == run_id).first()

    if not run:
        raise ValueError("Schedule run not found.")

    run.status = status
    run.completed_at = datetime.now()

    if notes:
        run.notes = notes

    db.commit()
    db.refresh(run)

    return run
