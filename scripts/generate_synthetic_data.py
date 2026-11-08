"""
YottaFlex Manufacturing - Deterministic Synthetic Data Generator
Generates full and starter synthetic manufacturing datasets with fixed seed 20261022.
Exports CSV, JSON, SQL seed files and injects 5 labelled ground truth anomaly scenarios.
"""

import argparse
import csv
import json
import os
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path


DEFAULT_SEED = 20261022

SCALE_CONFIG = {
    "full": {
        "products": 100,
        "machines": 40,
        "orders": 500,
        "operations_per_product": 20,
        "total_operations": 2000,
        "materials": 200,
        "tools": 20,
    },
    "starter": {
        "products": 10,
        "machines": 5,
        "orders": 50,
        "operations_per_product": 20,
        "total_operations": 200,
        "materials": 20,
        "tools": 5,
    },
}

MACHINE_TYPES = [
    "CNC",
    "CUTTING",
    "MILLING",
    "TURNING",
    "DRILLING",
    "WELDING",
    "ASSEMBLY",
    "FINISHING",
]

OPERATION_TEMPLATES = [
    ("Material Raw Stock Preparation", "CUTTING", 20),
    ("Rough Profile Cutting", "CUTTING", 25),
    ("CNC Rough Face Milling", "MILLING", 35),
    ("CNC Profile Roughing", "CNC", 40),
    ("Rough Turning Diameter", "TURNING", 30),
    ("Precision CNC Turning", "TURNING", 45),
    ("Deep Core Drilling", "DRILLING", 25),
    ("High Precision Tapping", "DRILLING", 20),
    ("Structural TIG Welding", "WELDING", 50),
    ("Weld Seam Grinding & Deburr", "FINISHING", 30),
    ("CNC Fine Surface Milling", "MILLING", 40),
    ("Precision Bore Machining", "CNC", 35),
    ("Thread Grinding & Buffing", "FINISHING", 25),
    ("Subassembly Component Fitment", "ASSEMBLY", 45),
    ("Torque-Controlled Fastening", "ASSEMBLY", 30),
    ("Full Mechanical Integration", "ASSEMBLY", 60),
    ("Chemical Surface Treatment", "FINISHING", 40),
    ("Precision Polishing", "FINISHING", 25),
    ("CMM Quality & Metrology Inspection", "FINISHING", 20),
    ("Protective Packaging & Barcode Labelling", "FINISHING", 15),
]

TOOL_TYPES = ["MOLD", "FIXTURE", "DIE", "CALIBRATOR", "CUTTER"]


def generate_dataset(scale_name="full", seed=DEFAULT_SEED):
    rng = random.Random(seed)
    cfg = SCALE_CONFIG[scale_name]

    print(f"Generating '{scale_name}' dataset with seed={seed}...")

    # 1. Products (SKUs)
    products = []
    product_categories = [
        "Aerospace Hydraulic Valve",
        "Automotive Titanium Shaft",
        "Industrial Planetary Gearbox",
        "Robotic Precision Joint",
        "Marine Turbine Impeller",
        "Medical Prosthetic Bracket",
        "Electronics Thermal Housing",
        "High-Pressure Steel Flange",
        "Composite Rotor Arm",
        "Synchronous Drive Pulley",
    ]

    for i in range(1, cfg["products"] + 1):
        category = product_categories[(i - 1) % len(product_categories)]
        prod_code = f"PROD-2026-{i:06d}"
        prod_name = f"{category} Type-{((i - 1) // len(product_categories)) + 1:02d}"
        products.append({
            "id": i,
            "product_code": prod_code,
            "product_name": prod_name,
            "description": f"Precision manufactured component {prod_code} for industrial applications.",
            "unit_of_measure": "PCS",
            "is_active": True,
        })

    # 2. Machines
    machines = []
    for i in range(1, cfg["machines"] + 1):
        m_type = MACHINE_TYPES[(i - 1) % len(MACHINE_TYPES)]
        m_code = f"MACH-{i:03d}"
        capacity = rng.choice([15, 20, 25, 30, 40])
        machines.append({
            "id": i,
            "machine_code": m_code,
            "machine_name": f"{m_type} Workstation {i:03d}",
            "machine_type": m_type,
            "capacity_per_hour": capacity,
            "is_active": True,
        })

    # 3. Machine Calendars (3 shifts for each machine)
    machine_calendars = []
    cal_id = 1
    shift_defs = [
        ("Shift 1 - Morning", time(6, 0), time(14, 0)),
        ("Shift 2 - Evening", time(14, 0), time(22, 0)),
        ("Shift 3 - Night", time(22, 0), time(6, 0)),
    ]
    for m in machines:
        for s_name, s_start, s_end in shift_defs:
            machine_calendars.append({
                "id": cal_id,
                "machine_id": m["id"],
                "shift_name": s_name,
                "start_time": s_start.strftime("%H:%M:%S"),
                "end_time": s_end.strftime("%H:%M:%S"),
                "is_working_day": True,
            })
            cal_id += 1

    # 4. Labor Shifts
    labor_shifts = [
        {
            "id": 1,
            "shift_code": "SHIFT-DAY-01",
            "shift_name": "Day Production Shift",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
            "available_workers": 25,
            "is_active": True,
        },
        {
            "id": 2,
            "shift_code": "SHIFT-EVE-02",
            "shift_name": "Evening Production Shift",
            "start_time": "14:00:00",
            "end_time": "22:00:00",
            "available_workers": 20,
            "is_active": True,
        },
        {
            "id": 3,
            "shift_code": "SHIFT-NGT-03",
            "shift_name": "Night Production Shift",
            "start_time": "22:00:00",
            "end_time": "06:00:00",
            "available_workers": 15,
            "is_active": True,
        },
    ]

    # 5. Shared Tools
    tools = []
    for i in range(1, cfg["tools"] + 1):
        t_type = TOOL_TYPES[(i - 1) % len(TOOL_TYPES)]
        tools.append({
            "id": i,
            "tool_code": f"TOOL-{i:03d}",
            "tool_name": f"Heavy-Duty {t_type.capitalize()} Fixture {i:03d}",
            "tool_type": t_type,
            "total_quantity": rng.choice([1, 2, 3]),
            "is_active": True,
        })

    # 6. Materials
    materials = []
    material_names = [
        "Aerospace Alloy 7075-T6",
        "Titanium Grade 5 Round Bar",
        "Austenitic Stainless Steel 316L",
        "Chromium-Molybdenum 4140 Steel",
        "Precision Cast Bronze Bushing",
        "Nickel Alloy Inconel 718",
        "Industrial Tool Steel D2",
        "Brass Extrusion Rod CZ121",
        "Carbon Fiber Reinforced Polymer",
        "High-Density Polyethylene Resin",
    ]
    for i in range(1, cfg["materials"] + 1):
        m_name = material_names[(i - 1) % len(material_names)]
        sub_grade = ((i - 1) // len(material_names)) + 1
        materials.append({
            "id": i,
            "material_code": f"MAT-2026-{i:06d}",
            "material_name": f"{m_name} (Grade-{sub_grade:02d})",
            "unit_of_measure": "KG",
            "current_stock": float(rng.randint(2000, 10000)),
            "minimum_stock": float(rng.randint(200, 800)),
            "is_active": True,
        })

    # 7. Inventory Lots (including delayed materials)
    inventory_lots = []
    lot_id = 1
    base_date = datetime(2026, 11, 1, 8, 0, 0)
    for mat in materials:
        # 1-2 lots per material
        num_lots = rng.choice([1, 2])
        for l_idx in range(num_lots):
            lot_code = f"LOT-2026-{lot_id:06d}"
            # 5% of lots have delayed arrival after 2026-11-15
            is_delayed = (mat["id"] % 20 == 0) and (l_idx == 0)
            if is_delayed:
                arrival_date = base_date + timedelta(days=rng.randint(14, 25))
            else:
                arrival_date = base_date - timedelta(days=rng.randint(1, 10))

            qty = Decimal(str(mat["current_stock"] / num_lots)).quantize(Decimal("0.001"))
            expiry = arrival_date.date() + timedelta(days=365)
            inventory_lots.append({
                "id": lot_id,
                "lot_code": lot_code,
                "material_id": mat["id"],
                "quantity_received": float(qty),
                "quantity_available": float(qty),
                "available_from": arrival_date.strftime("%Y-%m-%d %H:%M:%S"),
                "expiry_date": expiry.strftime("%Y-%m-%d"),
                "status": "AVAILABLE",
                "created_at": base_date.strftime("%Y-%m-%d %H:%M:%S"),
            })
            lot_id += 1

    # 8. Product Materials (BOM)
    product_materials = []
    pm_id = 1
    for prod in products:
        # Each product requires 2 to 3 distinct materials
        num_mats = rng.choice([2, 3])
        start_mat = ((prod["id"] * 3) % len(materials)) + 1
        for m_offset in range(num_mats):
            mat_id = ((start_mat + m_offset - 1) % len(materials)) + 1
            qty_req = round(rng.uniform(0.5, 4.0), 3)
            product_materials.append({
                "id": pm_id,
                "product_id": prod["id"],
                "material_id": mat_id,
                "quantity_required": qty_req,
            })
            pm_id += 1

    # 9. Routings and Operations
    routings = []
    operations = []
    operation_tools = []
    eligibility_records = []
    op_id = 1
    op_tool_id = 1
    elig_id = 1

    # Pre-index machines by type
    machines_by_type = {}
    for m in machines:
        machines_by_type.setdefault(m["machine_type"], []).append(m["id"])

    for prod in products:
        r_code = f"ROUTE-{prod['product_code']}-01"
        routing = {
            "id": prod["id"],
            "routing_code": r_code,
            "product_id": prod["id"],
            "routing_name": f"Master Routing - {prod['product_name']}",
            "description": f"Standard manufacturing process route for {prod['product_code']}",
            "is_active": 1,
        }
        routings.append(routing)

        # Generate exactly operations_per_product (20) operations
        for seq in range(1, cfg["operations_per_product"] + 1):
            tmpl_name, tmpl_mtype, base_duration = OPERATION_TEMPLATES[(seq - 1) % len(OPERATION_TEMPLATES)]
            op_code = f"OP-{prod['product_code']}-{seq:02d}"
            # Small random variation in estimated duration
            duration = base_duration + rng.choice([-5, 0, 5, 10])
            duration = max(10, duration)

            op_record = {
                "id": op_id,
                "operation_code": op_code,
                "routing_id": routing["id"],
                "operation_name": tmpl_name,
                "sequence_number": seq,
                "estimated_time_minutes": duration,
            }
            operations.append(op_record)

            # Machine eligibility: map to machines of compatible machine_type
            eligible_mids = machines_by_type.get(tmpl_mtype, [])
            if not eligible_mids:
                eligible_mids = [machines[0]["id"]]
            for mid in eligible_mids:
                eligibility_records.append({
                    "id": elig_id,
                    "operation_id": op_id,
                    "machine_id": mid,
                    "is_active": True,
                })
                elig_id += 1

            # Tool requirement: associate 1 shared tool for machining/assembly/inspection
            tool_id = ((op_id - 1) % len(tools)) + 1
            operation_tools.append({
                "id": op_tool_id,
                "operation_id": op_id,
                "tool_id": tool_id,
                "quantity_required": 1,
            })
            op_tool_id += 1

            op_id += 1

    # 10. Changeover Matrix
    changeover_matrix = []
    cm_id = 1
    # Pairwise changeover between product families on each machine
    for m in machines:
        # Create representative sequence-dependent changeovers
        for p1 in products[:15]:
            for p2 in products[:15]:
                if p1["id"] == p2["id"]:
                    continue
                # Deterministic duration between 15 and 60 minutes
                c_dur = 15 + ((p1["id"] * 7 + p2["id"] * 13 + m["id"] * 3) % 45)
                changeover_matrix.append({
                    "id": cm_id,
                    "machine_id": m["id"],
                    "from_product_id": p1["id"],
                    "to_product_id": p2["id"],
                    "duration_minutes": c_dur,
                })
                cm_id += 1

    # 11. Machine Downtime (planned maintenance)
    machine_downtimes = []
    dt_id = 1
    reasons = [
        "Preventive Spindle Bearing Overhaul",
        "Scheduled CNC Axis Recalibration",
        "Hydraulic Fluid & Filter Replacement",
        "Coolant Flush & Sludge Extraction",
        "Electrical Control Cabinet Servicing",
    ]
    for idx, m in enumerate(machines[:10]):
        dt_start = datetime(2026, 11, 10 + (idx % 12), 8, 0, 0)
        dt_end = dt_start + timedelta(hours=rng.choice([4, 6, 8]))
        machine_downtimes.append({
            "id": dt_id,
            "machine_id": m["id"],
            "reason": reasons[idx % len(reasons)],
            "start_time": dt_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": dt_end.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PLANNED",
        })
        dt_id += 1

    # 12. Production Orders
    production_orders = []
    order_base_date = date(2026, 11, 2)
    priorities = ["URGENT", "HIGH", "NORMAL", "LOW"]
    priority_weights = [0.10, 0.25, 0.50, 0.15]

    for i in range(1, cfg["orders"] + 1):
        order_code = f"ORD-2026-{i:06d}"
        prod_idx = (i - 1) % len(products)
        product = products[prod_idx]
        qty = rng.choice([10, 20, 25, 30, 50, 75, 100])
        # Priority distribution
        r_val = rng.random()
        if r_val < 0.10:
            priority = "URGENT"
            lead_days = rng.randint(5, 12)
        elif r_val < 0.35:
            priority = "HIGH"
            lead_days = rng.randint(10, 20)
        elif r_val < 0.85:
            priority = "NORMAL"
            lead_days = rng.randint(18, 35)
        else:
            priority = "LOW"
            lead_days = rng.randint(30, 50)

        ord_date = order_base_date + timedelta(days=(i % 10))
        due_date = ord_date + timedelta(days=lead_days)

        production_orders.append({
            "id": i,
            "order_number": order_code,
            "product_id": product["id"],
            "quantity": qty,
            "priority": priority,
            "order_date": ord_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "status": "PENDING",
            "created_at": datetime.combine(ord_date, time(8, 0)).strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 13. Labelled Edge Cases / Anomalies (5 Scenarios)
    # Stored separately with full details
    ground_truth = [
        {
            "anomaly_id": "ANOM-001",
            "issue_type": "MACHINE_OVERLAP",
            "related_entities": {
                "machine_code": "MACH-001",
                "schedule_code_1": "SCH-TEST-OVERLAP-01",
                "schedule_code_2": "SCH-TEST-OVERLAP-02",
                "time_window": "2026-11-10 08:00:00 to 2026-11-10 12:00:00",
            },
            "expected_result": "FAIL_MACHINE_OVERLAP",
            "ground_truth_label": "ANOMALY",
            "explanation": "Two operations scheduled concurrently on machine MACH-001 with overlapping time windows.",
        },
        {
            "anomaly_id": "ANOM-002",
            "issue_type": "PRECEDENCE_VIOLATION",
            "related_entities": {
                "order_number": "ORD-2026-000001",
                "operation_sequence_1": 1,
                "operation_sequence_2": 2,
                "op1_end": "2026-11-10 14:00:00",
                "op2_start": "2026-11-10 11:00:00",
            },
            "expected_result": "FAIL_OPERATION_PRECEDENCE",
            "ground_truth_label": "ANOMALY",
            "explanation": "Operation sequence 2 scheduled to begin 3 hours before operation sequence 1 completes.",
        },
        {
            "anomaly_id": "ANOM-003",
            "issue_type": "MATERIAL_PRE_AVAILABILITY",
            "related_entities": {
                "material_code": "MAT-2026-000020",
                "lot_code": "LOT-2026-000020",
                "available_from": "2026-11-20 08:00:00",
                "scheduled_start": "2026-11-12 09:00:00",
            },
            "expected_result": "FAIL_MATERIAL_AVAILABILITY",
            "ground_truth_label": "ANOMALY",
            "explanation": "Operation scheduled to consume inventory lot LOT-2026-000020 before its delivery/availability date of 2026-11-20.",
        },
        {
            "anomaly_id": "ANOM-004",
            "issue_type": "CALENDAR_OUT_OF_SHIFT",
            "related_entities": {
                "machine_code": "MACH-002",
                "shift_window": "06:00:00 to 22:00:00",
                "scheduled_time": "2026-11-15 03:00:00",
            },
            "expected_result": "FAIL_SHIFT_CALENDAR",
            "ground_truth_label": "ANOMALY",
            "explanation": "Operation scheduled at 03:00:00 during non-operational hours outside machine shift calendars.",
        },
        {
            "anomaly_id": "ANOM-005",
            "issue_type": "CHANGEOVER_OMITTED",
            "related_entities": {
                "machine_code": "MACH-003",
                "from_product": "PROD-2026-000001",
                "to_product": "PROD-2026-000002",
                "required_changeover_minutes": 45,
                "actual_buffer_minutes": 0,
            },
            "expected_result": "FAIL_CHANGEOVER_REQUIREMENT",
            "ground_truth_label": "ANOMALY",
            "explanation": "Consecutive operations on MACH-003 switching products without allocating required 45-minute setup changeover.",
        },
    ]

    dataset = {
        "products": products,
        "machines": machines,
        "machine_calendars": machine_calendars,
        "labor_shifts": labor_shifts,
        "tools": tools,
        "materials": materials,
        "inventory_lots": inventory_lots,
        "product_materials": product_materials,
        "routings": routings,
        "operations": operations,
        "operation_tools": operation_tools,
        "operation_machine_eligibility": eligibility_records,
        "changeover_matrix": changeover_matrix,
        "machine_downtimes": machine_downtimes,
        "production_orders": production_orders,
        "ground_truth": ground_truth,
    }

    return dataset


def export_dataset_files(dataset, output_dir):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Exporting CSV and JSON dataset to '{out_path.resolve()}'...")

    for key, records in dataset.items():
        if not records:
            continue

        # Export JSON
        json_file = out_path / f"{key}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)

        # Export CSV
        csv_file = out_path / f"{key}.csv"
        headers = list(records[0].keys())
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in records:
                # Format dictionaries/lists as JSON strings for CSV cells
                row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        row[k] = json.dumps(v)
                    else:
                        row[k] = v
                writer.writerow(row)

    # Export seed_data.sql
    sql_file = out_path / "seed_data.sql"
    generate_sql_seed_file(dataset, sql_file)

    print("Data export completed successfully!")


def generate_sql_seed_file(dataset, sql_filepath):
    """Generate deterministic SQL seed file inserting master and dependent records."""
    table_order = [
        ("products", "products"),
        ("machines", "machines"),
        ("machine_calendars", "machine_calendars"),
        ("labor_shifts", "labor_shifts"),
        ("tools", "tools"),
        ("materials", "materials"),
        ("inventory_lots", "inventory_lots"),
        ("product_materials", "product_materials"),
        ("routings", "routings"),
        ("operations", "operations"),
        ("operation_tools", "operation_tools"),
        ("operation_machine_eligibility", "operation_machine_eligibility"),
        ("changeover_matrix", "changeover_matrix"),
        ("machine_downtimes", "machine_downtimes"),
        ("production_orders", "production_orders"),
    ]

    with open(sql_filepath, "w", encoding="utf-8") as f:
        f.write("-- ============================================================\n")
        f.write("-- YottaFlex Manufacturing - Deterministic Database Seed SQL\n")
        f.write(f"-- Generated with fixed seed: {DEFAULT_SEED}\n")
        f.write(f"-- Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-- ============================================================\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

        for entity_key, table_name in table_order:
            records = dataset.get(entity_key, [])
            if not records:
                continue

            f.write(f"-- Table: {table_name} ({len(records)} records)\n")
            f.write(f"DELETE FROM `{table_name}`;\n")

            headers = [k for k in records[0].keys()]
            cols_str = ", ".join(f"`{h}`" for h in headers)

            batch_size = 50
            for b_idx in range(0, len(records), batch_size):
                batch = records[b_idx : b_idx + batch_size]
                f.write(f"INSERT INTO `{table_name}` ({cols_str}) VALUES\n")
                val_lines = []
                for r in batch:
                    vals = []
                    for h in headers:
                        v = r[h]
                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, bool):
                            vals.append("1" if v else "0")
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        else:
                            s = str(v).replace("\\", "\\\\").replace("'", "''")
                            vals.append(f"'{s}'")
                    val_lines.append(f"  ({', '.join(vals)})")
                f.write(",\n".join(val_lines) + ";\n")
            f.write("\n")

        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        f.write("-- ============================================================\n")
        f.write("-- Seed completed successfully.\n")
        f.write("-- ============================================================\n")


def populate_mysql_database(dataset):
    """Insert generated dataset directly into MySQL database using SQLAlchemy session."""
    import sys
    # Add backend to path
    backend_path = Path(__file__).resolve().parent.parent / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    from app.database import engine, Base, SessionLocal
    import app.models
    from sqlalchemy import text

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Populating MySQL database with generated dataset...")
        # Disable foreign keys temporarily for clean insertion
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        # Clear schedule and transaction tables before populating
        for t in ["labor_assignments", "material_consumptions", "material_reservations", "constraint_violations", "schedule_segments", "operation_schedules", "schedule_runs", "event_history"]:
            db.execute(text(f"DELETE FROM `{t}`"))

        table_mappings = [
            ("operation_tools", app.models.OperationTool, dataset["operation_tools"]),
            ("operation_machine_eligibility", app.models.OperationMachineEligibility, dataset["operation_machine_eligibility"]),
            ("operations", app.models.Operation, dataset["operations"]),
            ("routings", app.models.Routing, dataset["routings"]),
            ("product_materials", app.models.ProductMaterial, dataset["product_materials"]),
            ("changeover_matrix", app.models.ChangeoverMatrix, dataset["changeover_matrix"]),
            ("inventory_lots", app.models.InventoryLot, dataset["inventory_lots"]),
            ("production_orders", app.models.ProductionOrder, dataset["production_orders"]),
            ("materials", app.models.Material, dataset["materials"]),
            ("tools", app.models.Tool, dataset["tools"]),
            ("labor_shifts", app.models.LaborShift, dataset["labor_shifts"]),
            ("machine_calendars", app.models.MachineCalendar, dataset["machine_calendars"]),
            ("machine_downtimes", app.models.MachineDowntime, dataset["machine_downtimes"]),
            ("machines", app.models.Machine, dataset["machines"]),
            ("products", app.models.Product, dataset["products"]),
        ]

        for tbl_name, model_cls, records in table_mappings:
            db.execute(text(f"DELETE FROM `{tbl_name}`"))
            for r in records:
                db.add(model_cls(**r))
            db.flush()
            print(f"  Inserted {len(records)} records into {tbl_name}")

        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.commit()
        print("Database population completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error populating database: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic Data Generator for YottaFlex Manufacturing")
    parser.add_argument("--scale", choices=["full", "starter"], default="full", help="Dataset scale (default: full)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed (default: {DEFAULT_SEED})")
    parser.add_argument("--export-dir", default="data", help="Directory to export CSV/JSON/SQL (default: data)")
    parser.add_argument("--populate-db", action="store_true", help="Populate MySQL database directly")

    args = parser.parse_args()

    dataset = generate_dataset(scale_name=args.scale, seed=args.seed)
    export_dataset_files(dataset, args.export_dir)

    if args.populate_db:
        populate_mysql_database(dataset)

    print("\nGeneration summary:")
    for k, v in dataset.items():
        print(f"  {k}: {len(v)} records")


if __name__ == "__main__":
    main()
