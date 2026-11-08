
from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base


class Routing(Base):
    __tablename__ = "routings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    routing_code = Column(String(50), unique=True, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    routing_name = Column(String(100), nullable=False)

    description = Column(String(255), nullable=True)

    is_active = Column(Integer, default=1, nullable=False)
