
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from sqlalchemy import text
from app.models import Product, Machine, Material, ProductionOrder, MachineCalendar
from app.models.planning_models import InventoryLot
from app.services.material_service import release_reserved_material_for_order

from app.schemas.master_data import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionOrderResponse,
)


router = APIRouter(prefix="/api", tags=["Manufacturing Data"])


def save_record(db, record):
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate value or invalid database relationship."
        )


def update_record(db, record, changes):
    for field, value in changes.items():
        setattr(record, field, value)

    try:
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate value or invalid database relationship."
        )


# ---------------- PRODUCTS ----------------

@router.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.model_dump())
    return save_record(db, product)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return update_record(
        db, product, data.model_dump(exclude_unset=True)
    )


@router.delete("/products/{product_id}")
def deactivate_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()

    return {"message": "Product deactivated successfully"}


# ---------------- MACHINES ----------------

@router.get("/machines", response_model=list[MachineResponse])
def get_machines(db: Session = Depends(get_db)):
    return db.query(Machine).order_by(Machine.id).all()


@router.post(
    "/machines",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED
)
def create_machine(data: MachineCreate, db: Session = Depends(get_db)):
    machine = Machine(**data.model_dump())
    return save_record(db, machine)


@router.put("/machines/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    data: MachineUpdate,
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()

    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    return update_record(
        db, machine, data.model_dump(exclude_unset=True)
    )


@router.delete("/machines/{machine_id}")
def deactivate_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()

    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    machine.is_active = False
    db.commit()

    return {"message": "Machine deactivated successfully"}


# ---------------- MATERIALS ----------------

@router.get("/materials", response_model=list[MaterialResponse])
def get_materials(db: Session = Depends(get_db)):
    return db.query(Material).order_by(Material.id).all()


@router.post(
    "/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED
)
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    material = Material(**data.model_dump())
    return save_record(db, material)


@router.put("/materials/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    data: MaterialUpdate,
    db: Session = Depends(get_db)
):
    material = db.query(Material).filter(Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    return update_record(
        db, material, data.model_dump(exclude_unset=True)
    )


@router.delete("/materials/{material_id}")
def deactivate_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    material.is_active = False
    db.commit()

    return {"message": "Material deactivated successfully"}


# ---------------- PRODUCTION ORDERS ----------------

@router.get(
    "/production-orders",
    response_model=list[ProductionOrderResponse]
)
def get_production_orders(db: Session = Depends(get_db)):
    return (
        db.query(ProductionOrder)
        .order_by(ProductionOrder.due_date, ProductionOrder.id)
        .all()
    )


@router.post(
    "/production-orders",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_production_order(
    data: ProductionOrderCreate,
    db: Session = Depends(get_db)
):
    if data.due_date < data.order_date:
        raise HTTPException(
            status_code=422,
            detail="Due date cannot be earlier than order date."
        )

    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.is_active.is_(True)
    ).first()

    if not product:
        raise HTTPException(
            status_code=422,
            detail="Selected product does not exist or is inactive."
        )

    order = ProductionOrder(**data.model_dump())
    return save_record(db, order)


@router.put(
    "/production-orders/{order_id}",
    response_model=ProductionOrderResponse
)
def update_production_order(
    order_id: int,
    data: ProductionOrderUpdate,
    db: Session = Depends(get_db)
):
    order = (
        db.query(ProductionOrder)
        .filter(ProductionOrder.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")

    changes = data.model_dump(exclude_unset=True)

    order_date = changes.get("order_date", order.order_date)
    due_date = changes.get("due_date", order.due_date)

    if due_date < order_date:
        raise HTTPException(
            status_code=422,
            detail="Due date cannot be earlier than order date."
        )

    if "product_id" in changes:
        product = db.query(Product).filter(
            Product.id == changes["product_id"],
            Product.is_active.is_(True)
        ).first()

        if not product:
            raise HTTPException(
                status_code=422,
                detail="Selected product does not exist or is inactive."
            )

    return update_record(db, order, changes)


@router.delete("/production-orders/{order_id}")
def cancel_production_order(order_id: int, db: Session = Depends(get_db)):
    order = (
        db.query(ProductionOrder)
        .filter(ProductionOrder.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")

    if order.status == "CANCELLED":
        return {"message": "Production order is already cancelled"}

    try:
        released_count = release_reserved_material_for_order(
            db,
            production_order_id=order.id,
            reason="Production order cancelled by user",
        )
        order.status = "CANCELLED"
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Order cancellation failed; inventory changes were rolled back.",
        )

    return {
        "message": "Production order cancelled successfully",
        "released_reservations": released_count,
    }


# ---------------- DASHBOARD SUMMARY ----------------

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return {
        "total_products": db.query(Product).filter(
            Product.is_active.is_(True)
        ).count(),
        "active_machines": db.query(Machine).filter(
            Machine.is_active.is_(True)
        ).count(),
        "active_materials": db.query(Material).filter(
            Material.is_active.is_(True)
        ).count(),
        "total_orders": db.query(ProductionOrder).count(),
        "pending_orders": db.query(ProductionOrder).filter(
            ProductionOrder.status == "PENDING"
        ).count(),
        "scheduled_orders": db.query(ProductionOrder).filter(
            ProductionOrder.status == "SCHEDULED"
        ).count(),
    }


# ---------------- MACHINE CALENDARS ----------------

@router.get("/machine-calendars")
def get_machine_calendars(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            mc.id,
            mc.machine_id,
            m.machine_code,
            m.machine_name,
            mc.shift_name,
            mc.start_time,
            mc.end_time,
            mc.is_working_day
        FROM machine_calendars mc
        JOIN machines m ON m.id = mc.machine_id
        ORDER BY m.machine_code, mc.start_time
    """)
    rows = db.execute(query).mappings().all()
    res = []
    for r in rows:
        d = dict(r)
        d["start_time"] = str(d["start_time"])
        d["end_time"] = str(d["end_time"])
        res.append(d)
    return res


# ---------------- INVENTORY LOTS ----------------

@router.get("/inventory-lots")
def get_inventory_lots(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            il.id,
            il.material_id,
            il.lot_code,
            m.material_code,
            m.material_name,
            il.quantity_received,
            il.quantity_available,
            il.available_from,
            il.status
        FROM inventory_lots il
        JOIN materials m ON m.id = il.material_id
        ORDER BY il.available_from ASC, il.id ASC
    """)
    rows = db.execute(query).mappings().all()
    res = []
    for r in rows:
        d = dict(r)
        d["quantity_received"] = float(d["quantity_received"])
        d["quantity_available"] = float(d["quantity_available"])
        d["available_from"] = str(d["available_from"])
        res.append(d)
    return res
