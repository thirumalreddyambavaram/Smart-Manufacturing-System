
from sqlalchemy import Column, Integer, String, Boolean, Float
from app.models.base import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_code = Column(String(50), unique=True, nullable=False)
    material_name = Column(String(100), nullable=False)
    unit_of_measure = Column(String(20), default="KG", nullable=False)
    current_stock = Column(Float, default=0.0, nullable=False)
    minimum_stock = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
