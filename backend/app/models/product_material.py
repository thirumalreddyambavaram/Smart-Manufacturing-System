
from sqlalchemy import Column, Integer, Float, ForeignKey
from app.models.base import Base


class ProductMaterial(Base):
    __tablename__ = "product_materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)

    quantity_required = Column(Float, nullable=False)
