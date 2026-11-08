# YottaFlex Manufacturing - Comprehensive Data Dictionary

This data dictionary documents all core entities, child transaction tables, bridge tables, and system auditing entities in the YottaFlex Manufacturing Planning and Scheduling System.

---

## 1. Product (SKU Master)
Represents manufactured goods and finished products scheduled across the plant.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `product_code` | String(50) | Required | Pattern: `PROD-2026-XXXXXX` | — | Unique | Immutable, zero-padded 6-digit identifier |
| `product_name` | String(100) | Required | Non-empty text | — | No | Max length 100 characters |
| `description` | String(255) | Optional | Free text | — | No | Optional product specifications |
| `unit_of_measure` | String(20) | Required | `PCS`, `KG`, `LITRE`, `METER` | — | No | Must belong to allowed unit enum |
| `is_active` | Boolean | Required | `true`, `false` (1/0) | — | No | Default `true`. Deactivation soft-deletes |

---

## 2. Machine (Resource Master)
Represents workstations and machines capable of performing manufacturing operations.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `machine_code` | String(50) | Required | Pattern: `MACH-XXX` | — | Unique | Zero-padded 3-digit identifier |
| `machine_name` | String(100) | Required | Non-empty text | — | No | Descriptive equipment name |
| `machine_type` | String(50) | Required | `CNC`, `CUTTING`, `MILLING`, `TURNING`, `DRILLING`, `WELDING`, `ASSEMBLY`, `FINISHING` | — | No | Must match standard equipment capability type |
| `capacity_per_hour` | Integer | Required | 1 to 200 | Parts/Hour | No | Must be strictly positive integer |
| `is_active` | Boolean | Required | `true`, `false` (1/0) | — | No | Default `true` |

---

## 3. MachineCalendar (Work Shift Master)
Defines operating hours, recurring shifts, and working days for each machine.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `machine_id` | Integer | Required | Valid `machines.id` | — | No (Composite) | Foreign key to `machines.id` |
| `shift_name` | String(50) | Required | Shift 1, Shift 2, Shift 3 | — | No | Descriptive shift designation |
| `start_time` | Time | Required | `00:00:00` to `23:59:59` | HH:MM:SS | No | Valid daily time value |
| `end_time` | Time | Required | `00:00:00` to `23:59:59` | HH:MM:SS | No | Valid daily time value |
| `is_working_day` | Boolean | Required | `true`, `false` | — | No | Boolean flag indicating working availability |

---

## 4. Material (Raw Material Master)
Catalog of raw materials, metal stock, alloys, and hardware required to manufacture products.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `material_code` | String(50) | Required | Pattern: `MAT-2026-XXXXXX` | — | Unique | Zero-padded 6-digit identifier |
| `material_name` | String(100) | Required | Non-empty text | — | No | Descriptive alloy or material specification |
| `unit_of_measure` | String(20) | Required | `KG`, `PCS`, `LTR`, `METER` | — | No | Standard physical units |
| `current_stock` | Float | Required | >= 0.0 | Unit | No | Non-negative on-hand stock balance |
| `minimum_stock` | Float | Required | >= 0.0 | Unit | No | Non-negative safety reorder point |
| `is_active` | Boolean | Required | `true`, `false` | — | No | Default `true` |

---

## 5. InventoryLot (Traceable Inventory Batch)
Represents discrete inventory receipts with physical arrival dates and expiration tracking.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `lot_code` | String(50) | Required | Pattern: `LOT-2026-XXXXXX` | — | Unique | Zero-padded 6-digit identifier |
| `material_id` | Integer | Required | Valid `materials.id` | — | No | Foreign key to `materials.id` |
| `quantity_received` | Decimal(14,3)| Required | > 0.000 | Unit | No | Strictly positive receipt quantity |
| `quantity_available`| Decimal(14,3)| Required | 0.000 to `quantity_received`| Unit | No | Available stock cannot exceed received |
| `available_from` | DateTime | Required | Valid ISO timestamp | Timestamp | No | Material arrival and release date |
| `expiry_date` | Date | Optional | YYYY-MM-DD | Date | No | Must be later than `available_from` |
| `status` | String(30) | Required | `AVAILABLE`, `RESERVED`, `CONSUMED`, `EXPIRED` | — | No | Valid inventory lot status enum |
| `created_at` | DateTime | Required | Server default timestamp | Timestamp | No | Audit creation timestamp |

---

## 6. Routing (Product Route Header)
Defines the standard process route associated with manufacturing a product.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `routing_code` | String(50) | Required | Pattern: `ROUTE-<sku>-01` | — | Unique | Linked to product code |
| `product_id` | Integer | Required | Valid `products.id` | — | Unique/1:1 | Foreign key to `products.id` |
| `routing_name` | String(100) | Required | Non-empty text | — | No | Descriptive routing title |
| `description` | String(255) | Optional | Free text | — | No | Optional process description |
| `is_active` | Integer | Required | 1, 0 | — | No | 1 = Active, 0 = Inactive |

---

## 7. Operation (Routing Step)
Sequential manufacturing operations belonging to a routing.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `operation_code` | String(50) | Required | Pattern: `OP-<sku>-XX` | — | Unique | Step code with sequence padding |
| `routing_id` | Integer | Required | Valid `routings.id` | — | No | Foreign key to `routings.id` |
| `operation_name` | String(100) | Required | Non-empty text | — | No | Process operation step name |
| `sequence_number` | Integer | Required | 1 to 20 | Number | No | Monotonically increasing sequence step |
| `estimated_time_minutes`| Integer | Required | 10 to 180 | Minutes | No | Estimated cycle time per unit |

---

## 8. ProductMaterial (Bill of Materials Bridge)
Many-to-Many relationship between products and required raw materials.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `product_id` | Integer | Required | Valid `products.id` | — | No | Foreign key to `products.id` |
| `material_id` | Integer | Required | Valid `materials.id` | — | No | Foreign key to `materials.id` |
| `quantity_required` | Float | Required | > 0.0 | Unit/Part | Unique (prod, mat) | BOM multiplier required per finished unit |

---

## 9. ChangeoverMatrix (Sequence-Dependent Setups)
Defines tool and setup changeover times when transitioning between different products on a machine.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `machine_id` | Integer | Required | Valid `machines.id` | — | No | Foreign key to `machines.id` |
| `from_product_id` | Integer | Required | Valid `products.id` | — | No | Origin product foreign key |
| `to_product_id` | Integer | Required | Valid `products.id` | — | No | Destination product foreign key |
| `duration_minutes` | Integer | Required | 0 to 180 | Minutes | Unique (m, from, to) | Setup time required between product switch |

---

## 10. ProductionOrder (Customer & Manufacturing Order)
Represents customer demand and internal production orders requiring scheduling.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `order_number` | String(50) | Required | Pattern: `ORD-2026-XXXXXX` | — | Unique | Immutable order identifier |
| `product_id` | Integer | Required | Valid `products.id` | — | No | Foreign key to `products.id` |
| `quantity` | Integer | Required | 1 to 500 | PCS | No | Strictly positive batch quantity |
| `priority` | String(20) | Required | `LOW`, `NORMAL`, `HIGH`, `URGENT` | — | No | Scheduling dispatch priority tier |
| `order_date` | Date | Required | YYYY-MM-DD | Date | No | Creation date |
| `due_date` | Date | Required | YYYY-MM-DD | Date | No | Must be >= `order_date` |
| `status` | String(30) | Required | `PENDING`, `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | — | No | Production order lifecycle status |
| `created_at` | DateTime | Required | Server default timestamp | Timestamp | No | Audit creation timestamp |

---

## 11. OperationSchedule (Scheduled Job Allocation)
Represents machine assignments, start times, and completion times for scheduled operations.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `schedule_code` | String(30) | Required | Pattern: `SCH-2026-XXXXXX` | — | Unique | Unique schedule identifier |
| `schedule_run_id` | Integer | Required | Valid `schedule_runs.id` | — | No | Foreign key to `schedule_runs.id` |
| `production_order_id`| Integer | Required | Valid `production_orders.id` | — | No | Foreign key to `production_orders.id` |
| `operation_id` | Integer | Required | Valid `operations.id` | — | No | Foreign key to `operations.id` |
| `machine_id` | Integer | Required | Valid `machines.id` | — | No | Foreign key to `machines.id` |
| `planned_start` | DateTime | Required | Valid ISO timestamp | Timestamp | No | Must be < `planned_end` |
| `planned_end` | DateTime | Required | Valid ISO timestamp | Timestamp | No | Calculated completion timestamp |
| `status` | String(30) | Required | `SCHEDULED`, `IN_PROGRESS`, `COMPLETED` | — | No | Schedule lifecycle state |

---

## 12. Tool & OperationTool (Shared Tooling Registry)
Represents specialized fixtures, dies, molds, and cutters shared across machines.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `tool_code` | String(50) | Required | Pattern: `TOOL-XXX` | — | Unique | Unique tool identifier |
| `tool_name` | String(100) | Required | Non-empty text | — | No | Equipment tooling title |
| `tool_type` | String(50) | Required | `MOLD`, `FIXTURE`, `DIE`, `CALIBRATOR`, `CUTTER` | — | No | Allowed tooling classification |
| `total_quantity` | Integer | Required | >= 1 | Units | No | Concurrent capacity pool limit |
| `is_active` | Boolean | Required | `true`, `false` | — | No | Default `true` |

---

## 13. LaborShift (Workforce Allocation)
Represents shop-floor labor availability and crew capacity per shift.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `shift_code` | String(50) | Required | Pattern: `SHIFT-XXX-XX` | — | Unique | Unique shift identifier |
| `shift_name` | String(100) | Required | Day, Evening, Night Shift | — | No | Shift title |
| `start_time` | Time | Required | `00:00:00` to `23:59:59` | HH:MM:SS | No | Daily shift start |
| `end_time` | Time | Required | `00:00:00` to `23:59:59` | HH:MM:SS | No | Daily shift end |
| `available_workers` | Integer | Required | >= 1 | Workers | No | Worker count allocated per shift |
| `is_active` | Boolean | Required | `true`, `false` | — | No | Default `true` |


---

## 14. LaborAssignment (Personnel Operation Shift Allocation)
Represents the explicit allocation of plant operators and technicians to scheduled operation segments.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `assignment_code` | String(50) | Required | Pattern: `LBR-2026-XXXXXX` | — | Unique | Unique labor assignment code |
| `schedule_run_id` | Integer | Required | Valid `schedule_runs.id` | — | No | Foreign key to schedule run |
| `operation_schedule_id` | Integer | Required | Valid `operation_schedules.id` | — | No | Foreign key to scheduled operation |
| `labor_shift_id` | Integer | Required | Valid `labor_shifts.id` | — | No | Foreign key to labor shift window |
| `workers_assigned` | Integer | Required | >= 1 | Workers | No | Number of operators assigned (Default 1) |
| `assigned_start` | DateTime | Required | Valid ISO timestamp | Timestamp | No | Assignment start within shift hours |
| `assigned_end` | DateTime | Required | Valid ISO timestamp | Timestamp | No | Assignment end within shift hours |
| `status` | String(30) | Required | `ASSIGNED`, `RELEASED`, `REASSIGNED` | — | No | Lifecycle assignment status |
| `created_at` | DateTime | Required | Server default timestamp | Timestamp | No | Audit creation timestamp |

---

## 15. MaterialReservation (Pre-Production Inventory Allocation)
Represents persistent pre-allocation of specific inventory lots against production orders and operations.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `reservation_code` | String(50) | Required | Pattern: `RES-2026-XXXXXX` | — | Unique | Unique reservation tracking code |
| `production_order_id` | Integer | Required | Valid `production_orders.id` | — | No | Foreign key to production order |
| `operation_id` | Integer | Optional | Valid `operations.id` | — | No | Foreign key to consuming operation |
| `material_id` | Integer | Required | Valid `materials.id` | — | No | Foreign key to raw material master |
| `inventory_lot_id` | Integer | Required | Valid `inventory_lots.id` | — | No | Foreign key to allocated inventory lot |
| `quantity_reserved` | Decimal(14,3) | Required | > 0.000 | Physical Unit | No | Strictly positive allocation quantity |
| `status` | String(30) | Required | `RESERVED`, `CONSUMED`, `CANCELLED` | — | No | Reservation lifecycle state |
| `reserved_at` | DateTime | Required | Server default timestamp | Timestamp | No | Timestamp of transactional reservation |
| `notes` | Text | Optional | Free text | — | No | Allocation notes and lot trace |

---

## 16. MaterialConsumption (Physical Raw Material Consumption Event)
Represents the actual physical consumption of reserved inventory lots upon order dispatch and processing.

| Field Name | Type | Required / Optional | Allowed Values | Units | Uniqueness | Validation Rule |
|---|---|---|---|---|---|---|
| `id` | Integer | Required | 1, 2, 3... | — | PK, Unique | Auto-increment primary key |
| `consumption_code` | String(50) | Required | Pattern: `CNS-2026-XXXXXX` | — | Unique | Unique physical consumption code |
| `reservation_id` | Integer | Optional | Valid `material_reservations.id` | — | No | Traceability foreign key to reservation |
| `production_order_id` | Integer | Required | Valid `production_orders.id` | — | No | Foreign key to production order |
| `operation_id` | Integer | Optional | Valid `operations.id` | — | No | Foreign key to consuming operation |
| `material_id` | Integer | Required | Valid `materials.id` | — | No | Foreign key to raw material master |
| `inventory_lot_id` | Integer | Required | Valid `inventory_lots.id` | — | No | Foreign key to consumed inventory lot |
| `quantity_consumed` | Decimal(14,3) | Required | > 0.000 | Physical Unit | No | Strictly positive quantity consumed |
| `consumed_at` | DateTime | Required | Server default timestamp | Timestamp | No | Timestamp of consumption (>= lot available_from) |
| `notes` | Text | Optional | Free text | — | No | Audit trace and confirmation details |
