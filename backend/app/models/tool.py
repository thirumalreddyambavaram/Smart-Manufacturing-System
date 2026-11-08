from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from app.models.base import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_code = Column(String(50), unique=True, nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_type = Column(String(50), nullable=False)
    total_quantity = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class OperationTool(Base):
    __tablename__ = "operation_tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    quantity_required = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("operation_id", "tool_id", name="uq_operation_tool"),
    )
