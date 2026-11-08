from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.models.base import Base


class LaborAssignment(Base):
    __tablename__ = "labor_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assignment_code = Column(String(50), unique=True, nullable=False, index=True)
    schedule_run_id = Column(Integer, ForeignKey("schedule_runs.id"), nullable=False, index=True)
    operation_schedule_id = Column(Integer, ForeignKey("operation_schedules.id"), nullable=False, index=True)
    labor_shift_id = Column(Integer, ForeignKey("labor_shifts.id"), nullable=False, index=True)
    workers_assigned = Column(Integer, nullable=False, default=1)
    assigned_start = Column(DateTime, nullable=False)
    assigned_end = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default="ASSIGNED")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
