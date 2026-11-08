
from sqlalchemy import Column, Integer, String, Time, Boolean, ForeignKey
from app.models.base import Base


class MachineCalendar(Base):
    __tablename__ = "machine_calendars"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)

    shift_name = Column(String(50), nullable=False)

    start_time = Column(Time, nullable=False)

    end_time = Column(Time, nullable=False)

    is_working_day = Column(Boolean, default=True, nullable=False)
