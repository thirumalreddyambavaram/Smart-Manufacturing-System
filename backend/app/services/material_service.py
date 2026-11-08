"""
YottaFlex Manufacturing - Persistent Material Reservation & Consumption Service
Manages ACID-compliant database transactions for raw material allocation,
lot-level traceability, anti-duplicate protections, availability date enforcement,
and inventory balance reconciliation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import (
    Material,
    InventoryLot,
    ProductionOrder,
    Operation,
    MaterialReservation,
    MaterialConsumption,
    EventHistory,
)


class InsufficientInventoryError(Exception):
    """Raised when available inventory is lower than required quantity."""
    pass


class MaterialNotYetAvailableError(Exception):
    """Raised when material consumption is attempted prior to lot availability date."""
    pass


class DuplicateReservationError(Exception):
    """Raised when an identical material reservation already exists."""
    pass


class DoubleConsumptionError(Exception):
    """Raised when an already consumed reservation is submitted for re-consumption."""
    pass


class InvalidMaterialTransactionError(Exception):
    """Raised when transaction parameters are inconsistent or corrupted."""
    pass


def reserve_material_for_order(
    db: Session,
    production_order_id: int,
    material_id: int,
    quantity_required: float,
    operation_id: Optional[int] = None,
    required_date: Optional[datetime] = None,
) -> List[MaterialReservation]:
    """
    Reserve required quantity of material from available inventory lots using FIFO.
    Executed in a persistent database transaction.
    """
    if quantity_required <= 0:
        raise InvalidMaterialTransactionError("Reserved quantity must be strictly positive.")

    # 1. Prevent duplicate reservation for same order, material and operation
    existing = db.query(MaterialReservation).filter(
        MaterialReservation.production_order_id == production_order_id,
        MaterialReservation.material_id == material_id,
        MaterialReservation.operation_id == operation_id,
        MaterialReservation.status == "RESERVED",
    ).first()
    if existing:
        raise DuplicateReservationError(
            f"Active reservation {existing.reservation_code} already exists for order {production_order_id} and material {material_id}."
        )

    # 2. Query available lots for this material in FIFO order
    lot_query = db.query(InventoryLot).filter(
        InventoryLot.material_id == material_id,
        InventoryLot.status == "AVAILABLE",
        InventoryLot.quantity_available > 0,
    )
    if required_date is not None:
        lot_query = lot_query.filter(InventoryLot.available_from <= required_date)
    lots = lot_query.order_by(InventoryLot.available_from.asc(), InventoryLot.id.asc()).all()

    total_avail = sum(float(l.quantity_available) for l in lots)
    if total_avail < quantity_required:
        raise InsufficientInventoryError(
            f"Insufficient inventory for material ID {material_id}. Required: {quantity_required:.3f}, Available: {total_avail:.3f}."
        )

    reservations: List[MaterialReservation] = []
    remaining = Decimal(str(quantity_required))

    # 3. Deduct across lots transactionally
    for lot in lots:
        if remaining <= 0:
            break

        lot_avail = Decimal(str(lot.quantity_available))
        alloc = min(remaining, lot_avail)

        lot.quantity_available = lot_avail - alloc
        if lot.quantity_available == 0:
            lot.status = "RESERVED"

        # Unique reservation code
        max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM material_reservations")).scalar() or 0
        uncommitted = sum(1 for obj in db.new if isinstance(obj, MaterialReservation))
        res_code = f"RES-2026-{max_id + uncommitted + 1:06d}"

        reservation = MaterialReservation(
            reservation_code=res_code,
            production_order_id=production_order_id,
            operation_id=operation_id,
            material_id=material_id,
            inventory_lot_id=lot.id,
            quantity_reserved=alloc,
            status="RESERVED",
            reserved_at=datetime.now(),
            notes=f"Allocated {alloc:.3f} from lot {lot.lot_code} (Available from: {lot.available_from})",
        )
        db.add(reservation)
        reservations.append(reservation)
        remaining -= alloc

    # Update material aggregate stock
    mat = db.query(Material).filter(Material.id == material_id).first()
    if mat:
        mat.current_stock = max(0.0, float(mat.current_stock) - quantity_required)

    return reservations



def release_reserved_material_for_order(
    db: Session,
    production_order_id: int,
    reason: str = "Production order cancelled or scheduling failed",
) -> int:
    """Release all still-active reservations for an order, restoring lot and aggregate stock.

    Safe to call repeatedly: only RESERVED transactions are restored.
    The caller owns the transaction and must commit or roll it back.
    """
    reservations = (
        db.query(MaterialReservation)
        .filter(
            MaterialReservation.production_order_id == production_order_id,
            MaterialReservation.status == "RESERVED",
        )
        .with_for_update()
        .all()
    )
    released = 0
    for reservation in reservations:
        lot = (
            db.query(InventoryLot)
            .filter(InventoryLot.id == reservation.inventory_lot_id)
            .with_for_update()
            .first()
        )
        material = (
            db.query(Material)
            .filter(Material.id == reservation.material_id)
            .with_for_update()
            .first()
        )
        if lot is None or material is None:
            raise InvalidMaterialTransactionError(
                f"Cannot release reservation {reservation.reservation_code}: inventory lot or material is missing."
            )

        qty = Decimal(str(reservation.quantity_reserved))
        lot.quantity_available = Decimal(str(lot.quantity_available)) + qty
        lot.status = "AVAILABLE"
        material.current_stock = float(material.current_stock) + float(qty)
        reservation.status = "CANCELLED"
        reservation.notes = (reservation.notes or "") + f" | Released: {reason}"

        db.add(EventHistory(
            entity_type="material_reservation",
            entity_id=reservation.id,
            event_type="MATERIAL_RESERVATION_RELEASED",
            old_values={"status": "RESERVED"},
            new_values={
                "status": "CANCELLED",
                "quantity": float(qty),
                "lot_id": lot.id,
                "reason": reason,
            },
            actor="SYSTEM",
        ))
        released += 1
    return released


def consume_reserved_material(
    db: Session,
    reservation_id: int,
    consumed_at: Optional[datetime] = None,
) -> MaterialConsumption:
    """
    Record physical consumption of reserved material.
    Enforces anti-double consumption and verifies consumption is not prior to lot availability.
    """
    reservation = db.query(MaterialReservation).filter(MaterialReservation.id == reservation_id).first()
    if not reservation:
        raise InvalidMaterialTransactionError(f"Material reservation with ID {reservation_id} not found.")

    if reservation.status == "CONSUMED":
        raise DoubleConsumptionError(
            f"Double consumption prevented: Reservation {reservation.reservation_code} has already been consumed."
        )

    if reservation.status != "RESERVED":
        raise InvalidMaterialTransactionError(
            f"Cannot consume reservation {reservation.reservation_code} in status '{reservation.status}'."
        )

    lot = db.query(InventoryLot).filter(InventoryLot.id == reservation.inventory_lot_id).first()
    if not lot:
        raise InvalidMaterialTransactionError(f"Referenced inventory lot ID {reservation.inventory_lot_id} not found.")

    actual_consumed_time = consumed_at or datetime.now()

    # Enforce availability date constraint
    if actual_consumed_time < lot.available_from:
        raise MaterialNotYetAvailableError(
            f"Material lot {lot.lot_code} is not available until {lot.available_from}. "
            f"Consumption attempted at {actual_consumed_time} is premature."
        )

    max_id = db.execute(text("SELECT COALESCE(MAX(id), 0) FROM material_consumptions")).scalar() or 0
    uncommitted = sum(1 for obj in db.new if isinstance(obj, MaterialConsumption))
    cns_code = f"CNS-2026-{max_id + uncommitted + 1:06d}"

    consumption = MaterialConsumption(
        consumption_code=cns_code,
        reservation_id=reservation.id,
        production_order_id=reservation.production_order_id,
        operation_id=reservation.operation_id,
        material_id=reservation.material_id,
        inventory_lot_id=lot.id,
        quantity_consumed=reservation.quantity_reserved,
        consumed_at=actual_consumed_time,
        notes=f"Consumed against reservation {reservation.reservation_code} from lot {lot.lot_code}",
    )
    db.add(consumption)

    # Mark reservation as consumed
    reservation.status = "CONSUMED"

    # Audit event history
    event = EventHistory(
        entity_type="material_consumption",
        entity_id=consumption.id or 0,
        event_type="MATERIAL_CONSUMED",
        new_values={
            "consumption_code": cns_code,
            "reservation_code": reservation.reservation_code,
            "quantity": float(reservation.quantity_reserved),
            "lot_code": lot.lot_code,
            "consumed_at": str(actual_consumed_time),
        },
        actor="PRODUCTION_SCHEDULER",
    )
    db.add(event)

    return consumption


def reconcile_material_stock(db: Session, material_id: int) -> Dict[str, any]:
    """
    Perform formal arithmetic balance reconciliation for a material:
    initial_received == remaining_available + active_reserved + total_consumed.
    """
    mat = db.query(Material).filter(Material.id == material_id).first()
    if not mat:
        raise InvalidMaterialTransactionError(f"Material ID {material_id} not found.")

    # Lots: initial received & available
    lot_totals = db.execute(
        text("SELECT COALESCE(SUM(quantity_received), 0) AS total_rec, COALESCE(SUM(quantity_available), 0) AS total_avail FROM inventory_lots WHERE material_id = :mid"),
        {"mid": material_id},
    ).fetchone()
    total_received = float(lot_totals.total_rec or 0.0)
    current_available = float(lot_totals.total_avail or 0.0)

    # Active reservations (reserved, not yet consumed)
    total_reserved = float(db.execute(
        text("SELECT COALESCE(SUM(quantity_reserved), 0) FROM material_reservations WHERE material_id = :mid AND status = 'RESERVED'"),
        {"mid": material_id},
    ).scalar() or 0.0)

    # Consumed
    total_consumed = float(db.execute(
        text("SELECT COALESCE(SUM(quantity_consumed), 0) FROM material_consumptions WHERE material_id = :mid"),
        {"mid": material_id},
    ).scalar() or 0.0)

    accounted_for = current_available + total_reserved + total_consumed
    discrepancy = round(total_received - accounted_for, 3)
    is_balanced = abs(discrepancy) < 0.001

    return {
        "material_id": material_id,
        "material_code": mat.material_code,
        "material_name": mat.material_name,
        "initial_received": round(total_received, 3),
        "current_available": round(current_available, 3),
        "total_reserved": round(total_reserved, 3),
        "total_consumed": round(total_consumed, 3),
        "accounted_for": round(accounted_for, 3),
        "discrepancy": discrepancy,
        "is_balanced": is_balanced,
    }
