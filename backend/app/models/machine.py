
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_code = Column(String(50), unique=True, nullable=False)
    machine_name = Column(String(100), nullable=False)
    machine_type = Column(String(50), nullable=False)
    capacity_per_hour = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
