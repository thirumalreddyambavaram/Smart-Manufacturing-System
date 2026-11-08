"""
Tests for deterministic ID formatting and nomenclature conventions:
- Products: PROD-2026-000001
- Routings: ROUTE-<sku>-01
- Operations: OP-<sku>-XX
- Machines: MACH-001
- Orders: ORD-2026-000001
- Materials: MAT-2026-000001
- Tools: TOOL-001
"""

import re
from scripts.generate_synthetic_data import generate_dataset


def test_deterministic_id_conventions():
    ds = generate_dataset(scale_name="starter", seed=20261022)

    # Product pattern: PROD-2026-000001
    prod_pattern = re.compile(r"^PROD-2026-\d{6}$")
    for p in ds["products"]:
        assert prod_pattern.match(p["product_code"]), f"Invalid product_code: {p['product_code']}"

    # Machine pattern: MACH-001
    mach_pattern = re.compile(r"^MACH-\d{3}$")
    for m in ds["machines"]:
        assert mach_pattern.match(m["machine_code"]), f"Invalid machine_code: {m['machine_code']}"

    # Material pattern: MAT-2026-000001
    mat_pattern = re.compile(r"^MAT-2026-\d{6}$")
    for mat in ds["materials"]:
        assert mat_pattern.match(mat["material_code"]), f"Invalid material_code: {mat['material_code']}"

    # Order pattern: ORD-2026-000001
    ord_pattern = re.compile(r"^ORD-2026-\d{6}$")
    for o in ds["production_orders"]:
        assert ord_pattern.match(o["order_number"]), f"Invalid order_number: {o['order_number']}"

    # Routing pattern: ROUTE-<sku>-01
    for r in ds["routings"]:
        assert r["routing_code"].startswith("ROUTE-PROD-2026-")
        assert r["routing_code"].endswith("-01")

    # Operation pattern: OP-<sku>-XX
    for op in ds["operations"]:
        assert op["operation_code"].startswith("OP-PROD-2026-")

    # Tool pattern: TOOL-001
    tool_pattern = re.compile(r"^TOOL-\d{3}$")
    for t in ds["tools"]:
        assert tool_pattern.match(t["tool_code"]), f"Invalid tool_code: {t['tool_code']}"
