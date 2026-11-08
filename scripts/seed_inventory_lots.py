from datetime import datetime
from decimal import Decimal

from app.database import SessionLocal
from app.models import Material, InventoryLot


def seed_inventory_lots():
    db = SessionLocal()

    try:
        materials = db.query(Material).all()

        if not materials:
            raise RuntimeError("No materials found in database.")

        lots_added = 0

        for material in materials:
            lot_code = f"LOT-{material.material_code}-001"

            existing_lot = (
                db.query(InventoryLot)
                .filter_by(lot_code=lot_code)
                .first()
            )

            if existing_lot:
                continue

            quantity = Decimal(str(material.current_stock))

            if quantity <= 0:
                continue

            lot = InventoryLot(
                lot_code=lot_code,
                material_id=material.id,
                quantity_received=quantity,
                quantity_available=quantity,
                available_from=datetime.now(),
                status="AVAILABLE",
            )

            db.add(lot)
            lots_added += 1

        db.commit()

        print("Inventory lots saved successfully.")
        print(f"New inventory lots: {lots_added}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_inventory_lots()