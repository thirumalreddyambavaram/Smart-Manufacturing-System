
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.models.base import Base


class MachineDowntime(Base):
    __tablename__ = "machine_downtimes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    machine_id = Column(
        Integer,
        ForeignKey("machines.id"),
        nullable=False
    )

    reason = Column(String(100), nullable=False)

    start_time = Column(DateTime, nullable=False)

    end_time = Column(DateTime, nullable=False)

    status = Column(String(30), default="PLANNED", nullable=False)
