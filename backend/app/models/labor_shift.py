from sqlalchemy import Column, Integer, String, Time, Boolean
from app.models.base import Base


class LaborShift(Base):
    __tablename__ = "labor_shifts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shift_code = Column(String(50), unique=True, nullable=False)
    shift_name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    available_workers = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
