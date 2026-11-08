
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# PRODUCTS

class ProductCreate(BaseModel):
    product_code: str = Field(min_length=1, max_length=50)
    product_name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    unit_of_measure: str = Field(default="PCS", max_length=20)
    is_active: bool = True


class ProductUpdate(BaseModel):
    product_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class ProductResponse(APIModel):
    id: int
    product_code: str
    product_name: str
    description: Optional[str]
    unit_of_measure: str
    is_active: bool


# MACHINES

class MachineCreate(BaseModel):
    machine_code: str = Field(min_length=1, max_length=50)
    machine_name: str = Field(min_length=1, max_length=100)
    machine_type: str = Field(min_length=1, max_length=50)
    capacity_per_hour: int = Field(gt=0)
    is_active: bool = True


class MachineUpdate(BaseModel):
    machine_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    machine_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    machine_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    capacity_per_hour: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class MachineResponse(APIModel):
    id: int
    machine_code: str
    machine_name: str
    machine_type: str
    capacity_per_hour: int
    is_active: bool


# MATERIALS

class MaterialCreate(BaseModel):
    material_code: str = Field(min_length=1, max_length=50)
    material_name: str = Field(min_length=1, max_length=100)
    unit_of_measure: str = Field(default="KG", max_length=20)
    current_stock: float = Field(default=0, ge=0)
    minimum_stock: float = Field(default=0, ge=0)
    is_active: bool = True


class MaterialUpdate(BaseModel):
    material_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    material_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    current_stock: Optional[float] = Field(default=None, ge=0)
    minimum_stock: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class MaterialResponse(APIModel):
    id: int
    material_code: str
    material_name: str
    unit_of_measure: str
    current_stock: float
    minimum_stock: float
    is_active: bool


# PRODUCTION ORDERS

class ProductionOrderCreate(BaseModel):
    order_number: str = Field(min_length=1, max_length=50)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    priority: str = "NORMAL"
    order_date: date
    due_date: date
    status: str = "PENDING"


class ProductionOrderUpdate(BaseModel):
    order_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    product_id: Optional[int] = Field(default=None, gt=0)
    quantity: Optional[int] = Field(default=None, gt=0)
    priority: Optional[str] = None
    order_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None


class ProductionOrderResponse(APIModel):
    id: int
    order_number: str
    product_id: int
    quantity: int
    priority: str
    order_date: date
    due_date: date
    status: str
