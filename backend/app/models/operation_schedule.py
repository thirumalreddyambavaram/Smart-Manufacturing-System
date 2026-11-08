from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.models.base import Base


class OperationSchedule(Base):
    __tablename__ = "operation_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    production_order_id = Column(
        Integer,
        ForeignKey("production_orders.id"),
        nullable=False,
    )
    operation_id = Column(
        Integer,
        ForeignKey("operations.id"),
        nullable=False,
    )
    machine_id = Column(
        Integer,
        ForeignKey("machines.id"),
        nullable=False,
    )
    planned_start = Column(DateTime, nullable=False)
    planned_end = Column(DateTime, nullable=False)
    status = Column(String(30), default="SCHEDULED", nullable=False)
    schedule_code = Column(
        String(30),
        unique=True,
        nullable=True,
    )
    schedule_run_id = Column(
        Integer,
        ForeignKey("schedule_runs.id"),
        nullable=True,
    )
    changeover_minutes = Column(Integer, default=0, nullable=False)
