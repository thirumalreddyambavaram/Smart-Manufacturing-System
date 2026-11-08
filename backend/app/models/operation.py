from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operation_code = Column(String(50), unique=True, nullable=False)
    routing_id = Column(Integer, ForeignKey("routings.id"), nullable=False)
    operation_name = Column(String(100), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    estimated_time_minutes = Column(Integer, nullable=False)
    required_workers = Column(Integer, default=1, nullable=False)
