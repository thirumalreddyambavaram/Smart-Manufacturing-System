
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    unit_of_measure = Column(String(20), default="PCS", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
