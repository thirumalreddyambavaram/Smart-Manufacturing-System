"""
Tests for foreign key relationships, referential integrity, and join validity.
"""

from scripts.generate_synthetic_data import generate_dataset


def test_referential_integrity():
    ds = generate_dataset(scale_name="starter", seed=20261022)

    product_ids = {p["id"] for p in ds["products"]}
    machine_ids = {m["id"] for m in ds["machines"]}
    material_ids = {mat["id"] for mat in ds["materials"]}
    routing_ids = {r["id"] for r in ds["routings"]}
    operation_ids = {op["id"] for op in ds["operations"]}
    tool_ids = {t["id"] for t in ds["tools"]}

    # Routings -> Products
    for r in ds["routings"]:
        assert r["product_id"] in product_ids

    # Operations -> Routings
    for op in ds["operations"]:
        assert op["routing_id"] in routing_ids

    # Production Orders -> Products
    for o in ds["production_orders"]:
        assert o["product_id"] in product_ids

    # Product Materials -> Products & Materials
    for pm in ds["product_materials"]:
        assert pm["product_id"] in product_ids
        assert pm["material_id"] in material_ids

    # Inventory Lots -> Materials
    for lot in ds["inventory_lots"]:
        assert lot["material_id"] in material_ids

    # Machine Calendars -> Machines
    for cal in ds["machine_calendars"]:
        assert cal["machine_id"] in machine_ids

    # Operation Machine Eligibility -> Operations & Machines
    for elig in ds["operation_machine_eligibility"]:
        assert elig["operation_id"] in operation_ids
        assert elig["machine_id"] in machine_ids

    # Operation Tools -> Operations & Tools
    for ot in ds["operation_tools"]:
        assert ot["operation_id"] in operation_ids
        assert ot["tool_id"] in tool_ids

    # Changeover Matrix -> Machines & Products
    for cm in ds["changeover_matrix"]:
        assert cm["machine_id"] in machine_ids
        assert cm["from_product_id"] in product_ids
        assert cm["to_product_id"] in product_ids
