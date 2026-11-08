"""
YottaFlex dataset correction with backup and safety checks.

DEFAULT: DRY RUN ONLY (no data changes)
Apply only after reviewing the dry-run output:
    $env:PYTHONPATH = "$PWD\backend"
    python .\scripts\correct_dataset_targets.py
    python .\scripts\correct_dataset_targets.py --apply

Targets:
  products=100, machines=40, materials=200, production_orders=500,
  routings=100, operations=2000.
All existing operation_schedules rows are protected and must remain unchanged.

The script:
- creates a mysqldump backup before any write;
- protects all rows reachable from operation_schedules through declared FKs;
- reassigns unscheduled orders from products selected for removal to retained products;
- deletes only unprotected rows and their dependent FK rows;
- adds operation rows to reach exactly 2,000;
- validates targets and the original schedule rows within one transaction.

If any exact target cannot be reached safely, it aborts and rolls back.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from sqlalchemy import MetaData, Table, and_, delete, func, inspect, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine
import app.models  # noqa: F401: register project models


TARGETS = {
    "products": 100,
    "machines": 40,
    "materials": 200,
    "production_orders": 500,
    "routings": 100,
    "operations": 2000,
}
SCHEDULE_TABLE = "operation_schedules"
OPERATION_NAMES = [
    "Cutting", "Machining", "Drilling", "Milling", "Turning",
    "Welding", "Assembly", "Finishing", "Quality Inspection",
    "Packaging", "Surface Treatment", "Testing",
]


def quote_ident(value):
    return "`" + value.replace("`", "``") + "`"


def create_backup():
    """Create a full SQL dump using the credentials already loaded by app.config."""
    executable = shutil.which("mysqldump")
    if not executable:
        raise RuntimeError(
            "mysqldump was not found in PATH. Install/add the MySQL client tools, "
            "then rerun. No database changes have been made."
        )

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = (backup_dir / f"yottaflex_before_correction_{stamp}.sql").resolve()

    # Use a short-lived option file so the password is not placed in command arguments.
    def cnf_escape(value):
        return str(value).replace("\\", "\\\\").replace('"', '\\"')

    cnf = (
        "[client]\n"
        f'user="{cnf_escape(settings.DB_USER)}"\n'
        f'password="{cnf_escape(settings.DB_PASSWORD)}"\n'
        f'host="{cnf_escape(settings.DB_HOST)}"\n'
        f'port="{int(settings.DB_PORT)}"\n'
        "protocol=tcp\n"
    )
    fd, cnf_path = tempfile.mkstemp(prefix="yottaflex_mysql_", suffix=".cnf")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(cnf)
        # mysqldump requires --defaults-extra-file as its first option.
        command = [
            executable,
            f"--defaults-extra-file={cnf_path}",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            "--databases",
            str(settings.DB_NAME),
            f"--result-file={str(backup_path)}",
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            try:
                backup_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(
                "MySQL backup failed. No database changes were made.\n"
                + (result.stderr.strip() or result.stdout.strip())
            )
    finally:
        try:
            os.remove(cnf_path)
        except OSError:
            pass

    if not backup_path.exists() or backup_path.stat().st_size == 0:
        raise RuntimeError("Backup file is missing or empty. No database changes were made.")
    return backup_path


def load_schema():
    metadata = MetaData()
    metadata.reflect(bind=engine)
    tables = metadata.tables
    inspector = inspect(engine)

    incoming = defaultdict(list)
    for child_name in tables:
        for fk in inspector.get_foreign_keys(child_name):
            parent = fk.get("referred_table")
            child_cols = fk.get("constrained_columns") or []
            parent_cols = fk.get("referred_columns") or []
            if parent in tables and len(child_cols) == 1 and len(parent_cols) == 1:
                incoming[parent].append((child_name, child_cols[0], parent_cols[0]))
            elif parent in tables:
                raise RuntimeError(
                    f"Composite foreign key detected: {child_name} -> {parent}. "
                    "This script will not guess how to delete it."
                )
    return tables, incoming


def single_pk(table):
    columns = list(table.primary_key.columns)
    if len(columns) != 1:
        raise RuntimeError(f"{table.name} does not have a single-column primary key.")
    return columns[0]


def all_ids(conn, table):
    pk = single_pk(table)
    return set(conn.execute(select(pk)).scalars().all())


def protect_schedule_graph(conn, tables, incoming):
    """Protect schedule rows and every parent row they reference, recursively."""
    if SCHEDULE_TABLE not in tables:
        raise RuntimeError(f"Required table {SCHEDULE_TABLE} is missing.")

    protected = defaultdict(set)
    schedule = tables[SCHEDULE_TABLE]
    schedule_pk = single_pk(schedule)
    seed_ids = set(conn.execute(select(schedule_pk)).scalars().all())
    protected[SCHEDULE_TABLE].update(seed_ids)

    # Traverse from each protected child row to its referenced parent row.
    queue = deque((SCHEDULE_TABLE, row_id) for row_id in seed_ids)
    visited = set(queue)

    while queue:
        child_name, child_id = queue.popleft()
        child = tables[child_name]
        child_pk = single_pk(child)
        child_row = conn.execute(
            select(child).where(child_pk == child_id)
        ).mappings().first()
        if child_row is None:
            continue

        for fk in child.foreign_keys:
            parent_name = fk.column.table.name
            if parent_name not in tables:
                continue
            child_col = fk.parent.name
            parent_col = fk.column.name
            parent_id = child_row[child_col]
            if parent_id is None:
                continue
            parent_table = tables[parent_name]
            parent_pk = single_pk(parent_table)
            if parent_col != parent_pk.name:
                # Parent references a non-PK unique key; still protect by key value.
                parent_ids = conn.execute(
                    select(parent_pk).where(parent_table.c[parent_col] == parent_id)
                ).scalars().all()
            else:
                parent_ids = [parent_id]
            for parent_id_value in parent_ids:
                protected[parent_name].add(parent_id_value)
                item = (parent_name, parent_id_value)
                if item not in visited:
                    visited.add(item)
                    queue.append(item)

    return protected, seed_ids


def deletion_closure(conn, root_table_name, root_id, tables, incoming, protected, skip_children=None):
    """
    Return a complete child-row deletion closure for one candidate parent row.
    A closure is rejected if it touches protected rows or scheduled operations.
    """
    skip_children = skip_children or set()
    planned = defaultdict(set)
    queue = deque([(root_table_name, root_id)])
    visited = set()

    while queue:
        table_name, row_id = queue.popleft()
        item = (table_name, row_id)
        if item in visited:
            continue
        visited.add(item)

        if row_id in protected.get(table_name, set()):
            return None
        if table_name == SCHEDULE_TABLE:
            return None

        table = tables[table_name]
        pk = single_pk(table)
        if row_id not in planned[table_name]:
            planned[table_name].add(row_id)

        # Any child row referencing this row must also be deleted.
        row = conn.execute(select(table).where(pk == row_id)).mappings().first()
        if row is None:
            continue

        for child_name, child_col, parent_col in incoming.get(table_name, []):
            if (table_name, child_name) in skip_children:
                continue
            child_table = tables[child_name]
            matching = conn.execute(
                select(single_pk(child_table)).where(
                    child_table.c[child_col] == row[parent_col]
                )
            ).scalars().all()
            for child_id in matching:
                if child_id in protected.get(child_name, set()) or child_name == SCHEDULE_TABLE:
                    return None
                queue.append((child_name, child_id))

    return planned


def merge_plan(total, addition):
    for table_name, ids in addition.items():
        total[table_name].update(ids)


def plan_deletions(conn, tables, incoming, protected):
    plan = defaultdict(set)
    current_counts = {
        name: conn.execute(select(func.count()).select_from(tables[name])).scalar_one()
        for name in TARGETS
    }

    # Select 32 products first. Their dependent routings/operations and other
    # FK children are removed as a unit. Orders are reassigned before this step.
    product_table = tables["products"]
    product_pk = single_pk(product_table)
    product_candidates = conn.execute(
        select(product_pk).order_by(product_pk.desc())
    ).scalars().all()
    product_to_remove = []
    for candidate in product_candidates:
        if current_counts["products"] - len(plan["products"]) <= TARGETS["products"]:
            break
        closure = deletion_closure(
            conn, "products", candidate, tables, incoming, protected,
            skip_children={("products", "production_orders")},
        )
        if closure is not None:
            merge_plan(plan, closure)
            product_to_remove.append(candidate)

    if current_counts["products"] - len(plan["products"]) != TARGETS["products"]:
        raise RuntimeError(
            "Cannot safely reduce products to 100 while protecting scheduled records. "
            f"Safe removals found: {len(plan['products'])}. No changes applied."
        )

    # Reassign orders belonging to removed products rather than losing them.
    # Orders selected for the separate 20-row reduction are handled below.
    retained_products = [
        pid for pid in conn.execute(
            select(product_pk).where(~product_pk.in_(plan["products"]))
        ).scalars().all()
    ]
    if not retained_products:
        raise RuntimeError("No retained products available for order reassignment.")

    # The caller performs reassignment within the transaction after this plan is built.
    plan["_removed_product_ids"] = set(product_to_remove)
    plan["_retained_product_ids"] = set(retained_products)

    # Machines: cascade only through unprotected dependencies.
    for table_name in ("machines", "materials"):
        table = tables[table_name]
        pk = single_pk(table)
        count_now = current_counts[table_name]
        already = len(plan[table_name])
        candidates = conn.execute(select(pk).order_by(pk.desc())).scalars().all()
        for candidate in candidates:
            if count_now - len(plan[table_name]) <= TARGETS[table_name]:
                break
            if candidate in protected.get(table_name, set()):
                continue
            closure = deletion_closure(conn, table_name, candidate, tables, incoming, protected)
            if closure is not None:
                merge_plan(plan, closure)
        if count_now - len(plan[table_name]) != TARGETS[table_name]:
            raise RuntimeError(
                f"Cannot safely reduce {table_name} to {TARGETS[table_name]}. "
                "A dependent row is protected or a dependency cannot be resolved."
            )

    # Production orders: retain scheduled ones, remove only 20 other orders.
    table = tables["production_orders"]
    pk = single_pk(table)
    candidates = conn.execute(select(pk).order_by(pk.desc())).scalars().all()
    for candidate in candidates:
        if current_counts["production_orders"] - len(plan["production_orders"]) <= TARGETS["production_orders"]:
            break
        if candidate in protected.get("production_orders", set()):
            continue
        closure = deletion_closure(conn, "production_orders", candidate, tables, incoming, protected)
        if closure is not None:
            merge_plan(plan, closure)
    if current_counts["production_orders"] - len(plan["production_orders"]) != TARGETS["production_orders"]:
        raise RuntimeError("Cannot safely reduce production_orders to 500.")

    # Routing target must be exactly 100 after product cascades. If not, remove
    # additional unprotected routes (and their operations) or stop.
    table = tables["routings"]
    route_count = current_counts["routings"] - len(plan["routings"])
    if route_count > TARGETS["routings"]:
        pk = single_pk(table)
        candidates = conn.execute(select(pk).order_by(pk.desc())).scalars().all()
        for candidate in candidates:
            if route_count <= TARGETS["routings"]:
                break
            if candidate in plan["routings"] or candidate in protected.get("routings", set()):
                continue
            closure = deletion_closure(conn, "routings", candidate, tables, incoming, protected)
            if closure is not None:
                merge_plan(plan, closure)
                route_count = current_counts["routings"] - len(plan["routings"])
    if route_count != TARGETS["routings"]:
        raise RuntimeError(
            f"Expected 100 routings after safe product/routing cleanup; planned count is {route_count}."
        )

    return plan


def execute_deletions(conn, tables, plan):
    # Delete children before parents. Repeated passes handle dependency depth.
    names = [name for name in plan if not name.startswith("_") and plan[name]]
    remaining = set(names)
    while remaining:
        progressed = False
        for name in list(remaining):
            # A table is ready when none of its child tables remain pending.
            child_pending = False
            for other in remaining:
                if other == name:
                    continue
                for fk in tables[other].foreign_keys:
                    if fk.column.table.name == name:
                        child_pending = True
                        break
                if child_pending:
                    break
            if child_pending:
                continue
            table = tables[name]
            pk = single_pk(table)
            conn.execute(delete(table).where(pk.in_(list(plan[name]))))
            remaining.remove(name)
            progressed = True
        if not progressed:
            raise RuntimeError(
                "Foreign-key cycle detected among rows selected for deletion. "
                "Aborting rather than guessing a deletion order."
            )


def add_operations(conn, tables):
    operation = tables["operations"]
    routing = tables["routings"]
    op_pk = single_pk(operation)
    route_pk = single_pk(routing)

    current = conn.execute(select(func.count()).select_from(operation)).scalar_one()
    needed = TARGETS["operations"] - current
    if needed < 0:
        raise RuntimeError(
            f"Operations count is {current}, above target 2,000. "
            "This script will not remove operation rows outside a verified routing cleanup."
        )
    if needed == 0:
        return

    route_ids = conn.execute(select(route_pk).order_by(route_pk)).scalars().all()
    if len(route_ids) != TARGETS["routings"]:
        raise RuntimeError("Expected exactly 100 routings before adding operations.")

    # Determine a safe next sequence per routing and unique generated code.
    max_seq = {}
    for rid in route_ids:
        max_seq[rid] = conn.execute(
            select(func.max(operation.c.sequence_number)).where(operation.c.routing_id == rid)
        ).scalar_one() or 0

    rows = []
    for i in range(needed):
        rid = route_ids[i % len(route_ids)]
        seq = int(max_seq[rid]) + 1
        max_seq[rid] = seq
        rows.append({
            "operation_code": f"YF-AUTO-{datetime.now():%y%m%d%H%M%S}-{i:05d}",
            "routing_id": rid,
            "operation_name": OPERATION_NAMES[i % len(OPERATION_NAMES)],
            "sequence_number": seq,
            "estimated_time_minutes": 15 + (i % 46),
        })
    conn.execute(operation.insert(), rows)


def schedule_snapshot(conn, schedule_table):
    """Capture every schedule column, not only schedule primary keys."""
    columns = list(schedule_table.columns)
    rows = conn.execute(select(schedule_table).order_by(single_pk(schedule_table))).mappings().all()
    return tuple(tuple(row[column.name] for column in columns) for row in rows)


def verify(conn, tables, original_schedule_snapshot):
    errors = []
    for name, target in TARGETS.items():
        actual = conn.execute(
            select(func.count()).select_from(tables[name])
        ).scalar_one()
        if actual != target:
            errors.append(f"{name}: expected {target}, got {actual}")

    schedule = tables[SCHEDULE_TABLE]
    final_snapshot = schedule_snapshot(conn, schedule)
    if final_snapshot != original_schedule_snapshot:
        errors.append(
            "operation_schedules data changed (the complete rows must remain identical)"
        )

    if errors:
        raise RuntimeError("Final validation failed:\n - " + "\n - ".join(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create backup and apply changes. Without this flag, only a dry run is performed.",
    )
    args = parser.parse_args()

    tables, incoming = load_schema()
    missing = [name for name in list(TARGETS) + [SCHEDULE_TABLE] if name not in tables]
    if missing:
        raise RuntimeError("Missing required database tables: " + ", ".join(missing))

    with engine.connect() as conn:
        protected, original_schedule_ids = protect_schedule_graph(conn, tables, incoming)
        original_schedule_snapshot = schedule_snapshot(conn, tables[SCHEDULE_TABLE])
        print("Current counts:")
        for name, target in TARGETS.items():
            count = conn.execute(select(func.count()).select_from(tables[name])).scalar_one()
            print(f"  {name}: {count} (target {target})")
        print(f"  {SCHEDULE_TABLE}: {len(original_schedule_ids)} rows to preserve")

        plan = plan_deletions(conn, tables, incoming, protected)
        print("\nPlanned cleanup:")
        for name, ids in plan.items():
            if name.startswith("_"):
                continue
            if ids:
                print(f"  {name}: delete {len(ids)} rows")
        print("  production_orders linked to removed products will be reassigned")
        print(f"  operations: add rows after cleanup to reach {TARGETS['operations']}")

        if not args.apply:
            print("\nDRY RUN ONLY. No records were changed.")
            print("If the plan is acceptable, create a backup and apply with --apply.")
            return

    backup_path = create_backup()
    print(f"\nBackup created: {backup_path}")

    try:
        with engine.begin() as conn:
            # Re-reflect inside the transaction to avoid relying on a stale plan.
            tables, incoming = load_schema()
            protected, original_schedule_ids = protect_schedule_graph(conn, tables, incoming)
            original_schedule_snapshot = schedule_snapshot(conn, tables[SCHEDULE_TABLE])
            plan = plan_deletions(conn, tables, incoming, protected)

            # Reassign every unscheduled order attached to a product being removed.
            removed_products = plan["_removed_product_ids"]
            retained_products = sorted(plan["_retained_product_ids"])
            orders = tables["production_orders"]
            product_col = orders.c.product_id
            order_pk = single_pk(orders)
            schedule_orders = set()
            if "production_order_id" in tables[SCHEDULE_TABLE].c:
                schedule_orders = set(conn.execute(
                    select(tables[SCHEDULE_TABLE].c.production_order_id)
                ).scalars().all())

            reassignment_rows = conn.execute(
                select(order_pk).where(product_col.in_(removed_products))
            ).scalars().all()
            for index, order_id in enumerate(reassignment_rows):
                if order_id in schedule_orders:
                    raise RuntimeError(
                        "A scheduled production order belongs to a product selected for removal. "
                        "Safety check stopped the correction."
                    )
                new_product = retained_products[index % len(retained_products)]
                conn.execute(
                    update(orders).where(order_pk == order_id).values(product_id=new_product)
                )

            execute_deletions(conn, tables, plan)
            add_operations(conn, tables)
            verify(conn, tables, original_schedule_snapshot)

        print("\nSUCCESS: all target counts reached exactly.")
        print(f"Backup: {backup_path}")
        print("All original operation_schedules rows were preserved.")
    except Exception:
        print("\nCorrection failed. The database transaction was rolled back.")
        print(f"Your pre-correction backup is here: {backup_path}")
        raise


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, SQLAlchemyError) as exc:
        print(f"\nSTOPPED SAFELY: {exc}")
        raise SystemExit(1)
