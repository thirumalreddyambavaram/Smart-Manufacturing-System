
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    order_number = Column(String(50), unique=True, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)

    priority = Column(String(20), default="NORMAL", nullable=False)

    order_date = Column(Date, nullable=False)

    due_date = Column(Date, nullable=False)

    status = Column(String(30), default="PENDING", nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
