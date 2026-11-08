# YottaFlex Manufacturing - Synthetic Data Generator Configuration

This document specifies the deterministic synthetic data generation engine, seed parameters, dataset scales, execution commands, and injection rules for edge cases.

---

## 1. Fixed Random Seed

- **Deterministic Seed Value:** `20261022`
- **Reproducibility Guarantee:** All pseudo-random sampling (order priorities, lead times, quantities, machine selections) is seeded strictly via Python's standard `random.Random(seed)`. Regenerating with seed `20261022` produces bit-for-bit identical row counts, IDs, timestamps, and checksums.

---

## 2. Dataset Scale Configurations

The generator parameterizes dataset volume to allow generating either a lightweight development starter set or the full-scale industrial manufacturing dataset using the exact same generator codebase.

| Entity | Starter Scale (`--scale starter`) | Full Production Scale (`--scale full`) |
|---|:---:|:---:|
| Products / SKUs | 10 | **100** |
| Machines / Workstations | 5 | **40** |
| Production Orders | 50 | **500** |
| Operations per Product | 20 | **20** |
| Total Operations Catalog | 200 | **2,000** |
| Raw Materials | 20 | **200** |
| Inventory Lots | ~30 | **295** |
| Product BOM Multipliers | ~25 | **246** |
| Machine Calendars (Shifts) | 15 | **120** |
| Machine Downtimes | 2 | **10** |
| Shared Tooling Fixtures | 5 | **20** |
| Labor Shifts | 3 | **3** |
| Operation Machine Links | 1,000 | **10,000** |
| Changeover Matrix Rules | 800 | **8,400** |

---

## 3. ID and Nomenclature Conventions

Counters are strictly zero-padded, deterministic, and consistent across all export files and database tables:

- **Products:** `PROD-2026-000001` through `PROD-2026-000100`
- **Machines:** `MACH-001` through `MACH-040`
- **Materials:** `MAT-2026-000001` through `MAT-2026-000200`
- **Production Orders:** `ORD-2026-000001` through `ORD-2026-000500`
- **Routings:** `ROUTE-<sku>-01` (e.g. `ROUTE-PROD-2026-000001-01`)
- **Operations:** `OP-<sku>-XX` (e.g. `OP-PROD-2026-000001-01` to `OP-PROD-2026-000100-20`)
- **Inventory Lots:** `LOT-2026-000001` through `LOT-2026-000295`
- **Operation Schedules:** `SCH-2026-000001` upwards
- **Shared Tools:** `TOOL-001` through `TOOL-020`
- **Labor Shifts:** `SHIFT-DAY-01`, `SHIFT-EVE-02`, `SHIFT-NGT-03`

---

## 4. Generation Workflow Order

To guarantee foreign-key validity and avoid orphaned records, data generation executes strictly in dependency order:

1. **Master Records First:**
   - Products & Categories
   - Machines & Capabilities
   - Materials & Physical Units
   - Shared Tools & Categories
   - Labor Shifts
2. **Resource Calendars & Process Rules:**
   - Machine Calendars (3 shifts per machine, working days)
   - Product Routings (Master process route per product)
   - Operations (20 steps per routing with standard cycle durations)
   - Machine Eligibility (Compatible workstations by machine type)
   - Operation Tool Links (Required shared fixtures per operation)
   - Product Materials (BOM multipliers connecting products to materials)
   - Sequence-Dependent Changeover Matrix
3. **Transactional Demand & Availability Records:**
   - Inventory Lots (Physical lot quantities and arrival dates, including delayed lots)
   - Machine Downtimes (Planned maintenance windows)
   - Production Orders (Priorities, batch sizes, release and due dates)
4. **Derived Values:**
   - Material inventory balance totals
   - Hourly capacity ratings
   - Operation scheduled start/end windows
5. **Ground Truth Injection & Separation:**
   - 5 isolated anomaly test scenarios recorded to `data/ground_truth.json` and `data/ground_truth.csv`.

---

## 5. Generator Execution Commands

### Generate Full Dataset (Export to CSV, JSON, and SQL)
```powershell
python scripts/generate_synthetic_data.py --scale full --export-dir data
```

### Generate Starter Dataset
```powershell
python scripts/generate_synthetic_data.py --scale starter --export-dir data
```

### Populate Local MySQL Database Directly
```powershell
python scripts/generate_synthetic_data.py --scale full --populate-db
```
