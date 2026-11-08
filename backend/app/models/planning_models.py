
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Numeric,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    UniqueConstraint,
    Index,
    func,
)

from app.models.base import Base


class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    id = Column(Integer, primary_key=True, index=True)
    lot_code = Column(String(50), unique=True, nullable=False)
    material_id = Column(
        Integer, ForeignKey("materials.id"), nullable=False
    )
    quantity_received = Column(Numeric(14, 3), nullable=False)
    quantity_available = Column(Numeric(14, 3), nullable=False)
    available_from = Column(DateTime, nullable=False)
    expiry_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="AVAILABLE")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ChangeoverMatrix(Base):
    __tablename__ = "changeover_matrix"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(
        Integer, ForeignKey("machines.id"), nullable=False
    )
    from_product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    to_product_id = Column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    duration_minutes = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "machine_id",
            "from_product_id",
            "to_product_id",
            name="uq_machine_changeover",
        ),
    )


class OperationMachineEligibility(Base):
    __tablename__ = "operation_machine_eligibility"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(
        Integer, ForeignKey("operations.id"), nullable=False
    )
    machine_id = Column(
        Integer, ForeignKey("machines.id"), nullable=False
    )
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "operation_id",
            "machine_id",
            name="uq_operation_machine",
        ),
    )


class ScheduleRun(Base):
    __tablename__ = "schedule_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_code = Column(String(50), unique=True, nullable=False)
    started_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False, default="RUNNING")
    algorithm = Column(String(50), nullable=False, default="HEURISTIC")
    random_seed = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)


class ConstraintViolation(Base):
    __tablename__ = "constraint_violations"

    id = Column(Integer, primary_key=True, index=True)
    schedule_run_id = Column(
        Integer, ForeignKey("schedule_runs.id"), nullable=False
    )
    production_order_id = Column(
        Integer, ForeignKey("production_orders.id"), nullable=True
    )
    operation_id = Column(
        Integer, ForeignKey("operations.id"), nullable=True
    )
    machine_id = Column(
        Integer, ForeignKey("machines.id"), nullable=True
    )
    issue_type = Column(String(60), nullable=False)
    severity = Column(String(20), nullable=False, default="ERROR")
    description = Column(Text, nullable=False)
    ground_truth = Column(Boolean, nullable=False, default=False)
    detected_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_violation_run", "schedule_run_id"),
        Index("ix_violation_type", "issue_type"),
    )


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(60), nullable=False)
    entity_id = Column(Integer, nullable=False)
    event_type = Column(String(60), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    actor = Column(String(100), nullable=True)
    occurred_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_event_entity", "entity_type", "entity_id"),
        Index("ix_event_time", "occurred_at"),
    )


from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)

from app.database import Base


class ScheduleSegment(Base):
    __tablename__ = "schedule_segments"

    id = Column(Integer, primary_key=True, index=True)

    operation_schedule_id = Column(
        Integer,
        ForeignKey("operation_schedules.id"),
        nullable=False
    )

    segment_number = Column(Integer, nullable=False)

    segment_start = Column(DateTime, nullable=False)

    segment_end = Column(DateTime, nullable=False)

    duration_minutes = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "operation_schedule_id",
            "segment_number",
            name="uq_schedule_segment_number"
        ),
        Index(
            "ix_schedule_segment_machine_time",
            "operation_schedule_id",
            "segment_start",
            "segment_end"
        ),
    )
