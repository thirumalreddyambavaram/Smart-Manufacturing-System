"""
Unit and integration tests for persistent material reservations, consumption,
lot traceability, transaction rollback, and inventory reconciliation.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import text

from app.database import SessionLocal
from app.models import (
    Material,
    InventoryLot,
    ProductionOrder,
    MaterialReservation,
    MaterialConsumption,
)
from app.services.material_service import (
    reserve_material_for_order,
    consume_reserved_material,
    reconcile_material_stock,
    InsufficientInventoryError,
    MaterialNotYetAvailableError,
    DuplicateReservationError,
    DoubleConsumptionError,
)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def test_order(db_session):
    order = db_session.query(ProductionOrder).first()
    return order


def test_successful_material_reservation(db_session, test_order):
    """Test standard valid reservation creates persistent records and updates lot availability."""
    mat = db_session.query(Material).filter(Material.id == 1).first()
    assert mat is not None

    lot = db_session.query(InventoryLot).filter(
        InventoryLot.material_id == 1,
        InventoryLot.quantity_available >= 5.0,
    ).first()
    assert lot is not None

    initial_lot_avail = float(lot.quantity_available)

    # Clean up previous test runs if any
    db_session.execute(text("DELETE FROM material_consumptions WHERE production_order_id = :oid AND notes LIKE 'TEST_RES_%'"), {"oid": test_order.id})
    db_session.execute(text("DELETE FROM material_reservations WHERE production_order_id = :oid AND notes LIKE 'TEST_RES_%'"), {"oid": test_order.id})
    db_session.commit()

    reservations = reserve_material_for_order(
        db=db_session,
        production_order_id=test_order.id,
        material_id=1,
        quantity_required=5.0,
        operation_id=None,
    )
    for r in reservations:
        r.notes = "TEST_RES_1"
    db_session.commit()

    assert len(reservations) > 0
    assert reservations[0].reservation_code.startswith("RES-2026-")
    assert reservations[0].status == "RESERVED"
    assert float(reservations[0].quantity_reserved) == 5.0

    # Verify lot availability reduced
    db_session.refresh(lot)
    assert float(lot.quantity_available) == pytest.approx(initial_lot_avail - 5.0, 0.001)

    # Clean up
    for r in reservations:
        db_session.delete(r)
    lot.quantity_available = initial_lot_avail
    lot.status = "AVAILABLE"
    db_session.commit()


def test_insufficient_inventory_error(db_session, test_order):
    """Test requesting more quantity than available raises InsufficientInventoryError."""
    with pytest.raises(InsufficientInventoryError) as exc_info:
        reserve_material_for_order(
            db=db_session,
            production_order_id=test_order.id,
            material_id=1,
            quantity_required=99999999.0,
        )
    assert "Insufficient inventory" in str(exc_info.value)


def test_duplicate_reservation_prevention(db_session, test_order):
    """Test duplicate reservation for the same order and material is prevented."""
    db_session.execute(text("DELETE FROM material_reservations WHERE production_order_id = :oid AND notes = 'TEST_DUP'"), {"oid": test_order.id})
    db_session.commit()

    # First reservation succeeds
    res1 = reserve_material_for_order(
        db=db_session,
        production_order_id=test_order.id,
        material_id=1,
        quantity_required=2.0,
        operation_id=1,
    )
    for r in res1:
        r.notes = "TEST_DUP"
    db_session.commit()

    # Duplicate reservation must fail
    with pytest.raises(DuplicateReservationError) as exc_info:
        reserve_material_for_order(
            db=db_session,
            production_order_id=test_order.id,
            material_id=1,
            quantity_required=2.0,
            operation_id=1,
        )
    assert "already exists" in str(exc_info.value)

    # Clean up
    lot = db_session.query(InventoryLot).filter(InventoryLot.id == res1[0].inventory_lot_id).first()
    lot.quantity_available = float(lot.quantity_available) + 2.0
    lot.status = "AVAILABLE"
    for r in res1:
        db_session.delete(r)
    db_session.commit()


def test_material_consumption_before_availability_date_prevented(db_session, test_order):
    """Test consuming material before its lot available_from timestamp raises MaterialNotYetAvailableError."""
    # Create a lot with future availability
    future_date = datetime(2027, 12, 1, 8, 0, 0)
    lot = InventoryLot(
        lot_code="LOT-TEST-FUTURE-001",
        material_id=1,
        quantity_received=Decimal("100.000"),
        quantity_available=Decimal("100.000"),
        available_from=future_date,
        status="AVAILABLE",
    )
    db_session.add(lot)
    db_session.flush()

    res = MaterialReservation(
        reservation_code="RES-TEST-FUTURE-001",
        production_order_id=test_order.id,
        material_id=1,
        inventory_lot_id=lot.id,
        quantity_reserved=Decimal("10.000"),
        status="RESERVED",
    )
    db_session.add(res)
    db_session.commit()

    # Attempt consumption prior to future_date
    premature_time = datetime(2027, 11, 15, 8, 0, 0)
    with pytest.raises(MaterialNotYetAvailableError) as exc_info:
        consume_reserved_material(db=db_session, reservation_id=res.id, consumed_at=premature_time)
    assert "is not available until" in str(exc_info.value)

    # Clean up
    db_session.delete(res)
    db_session.delete(lot)
    db_session.commit()


def test_double_consumption_prevention(db_session, test_order):
    """Test that consuming an already consumed reservation raises DoubleConsumptionError."""
    lot = db_session.query(InventoryLot).filter(InventoryLot.material_id == 1).first()
    res = MaterialReservation(
        reservation_code="RES-TEST-DOUBLE-001",
        production_order_id=test_order.id,
        material_id=1,
        inventory_lot_id=lot.id,
        quantity_reserved=Decimal("5.000"),
        status="RESERVED",
    )
    db_session.add(res)
    db_session.commit()

    # First consumption succeeds
    valid_time = lot.available_from + timedelta(days=1)
    cns = consume_reserved_material(db=db_session, reservation_id=res.id, consumed_at=valid_time)
    db_session.commit()
    assert cns.consumption_code.startswith("CNS-2026-")
    assert res.status == "CONSUMED"

    # Second consumption must be rejected
    with pytest.raises(DoubleConsumptionError) as exc_info:
        consume_reserved_material(db=db_session, reservation_id=res.id, consumed_at=valid_time)
    assert "Double consumption prevented" in str(exc_info.value)

    # Clean up
    db_session.delete(cns)
    db_session.delete(res)
    db_session.commit()


def test_transaction_rollback(db_session):
    """Test that if an error occurs mid-transaction, inventory changes are fully rolled back."""
    lot = db_session.query(InventoryLot).filter(InventoryLot.material_id == 1).first()
    original_avail = float(lot.quantity_available)

    try:
        # Simulate failed transaction with manual error
        lot.quantity_available = float(lot.quantity_available) - 10.0
        raise RuntimeError("Simulated mid-transaction failure")
    except RuntimeError:
        db_session.rollback()

    db_session.refresh(lot)
    assert float(lot.quantity_available) == original_avail


def test_inventory_balance_reconciliation(db_session):
    """Test mathematical stock reconciliation: received == available + reserved + consumed."""
    reconciliation = reconcile_material_stock(db=db_session, material_id=1)
    assert reconciliation["is_balanced"] is True
    assert abs(reconciliation["discrepancy"]) < 0.001
    assert reconciliation["accounted_for"] == reconciliation["initial_received"]
