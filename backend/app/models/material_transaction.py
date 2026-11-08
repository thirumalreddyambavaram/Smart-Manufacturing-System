from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, func
from app.models.base import Base


class MaterialReservation(Base):
    __tablename__ = "material_reservations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reservation_code = Column(String(50), unique=True, nullable=False, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id"), nullable=False, index=True)
    quantity_reserved = Column(Numeric(14, 3), nullable=False)
    status = Column(String(30), nullable=False, default="RESERVED")  # RESERVED, CONSUMED, CANCELLED
    reserved_at = Column(DateTime, nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)


class MaterialConsumption(Base):
    __tablename__ = "material_consumptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    consumption_code = Column(String(50), unique=True, nullable=False, index=True)
    reservation_id = Column(Integer, ForeignKey("material_reservations.id"), nullable=True, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    inventory_lot_id = Column(Integer, ForeignKey("inventory_lots.id"), nullable=False, index=True)
    quantity_consumed = Column(Numeric(14, 3), nullable=False)
    consumed_at = Column(DateTime, nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)
