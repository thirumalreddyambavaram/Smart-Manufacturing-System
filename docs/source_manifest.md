# YottaFlex Manufacturing - Source Manifest & Lawful Use Statement

This manifest documents the provenance, licensing, lawful access, and synthetic generation methodology for all datasets used by the YottaFlex Manufacturing Planning and Scheduling System.

---

## 1. Provenance Statement

All product records, machines, materials, routings, operations, production orders, inventory batches, and machine calendars contained in this repository were **synthetically generated** using algorithmic domain-logic procedures implemented in `scripts/generate_synthetic_data.py`.

- **No Proprietary or Confidential Data:** No real-world customer identifiers, proprietary blueprints, commercial order books, private personnel records, or Protected Health Information (PHI) were accessed or ingested.
- **Lawful Access & Zero Bypass:** No access controls, authentication paywalls, or terms-of-service limitations were bypassed.
- **Deterministic Generation:** Every entity record is derived deterministically from the fixed pseudo-random seed `20261022` and standard discrete manufacturing domain principles.

---

## 2. Public Data Guidance & Inspiration Reference

Manufacturing process steps, machine classification typologies, and setup changeover patterns were modeled after standard industrial engineering literature and publicly available manufacturing schemas:

| Reference Domain | Public Reference / Standard | Purpose | Transformations / Usage |
|---|---|---|---|
| Machine Classification | Standard CNC & Machine Tool Taxonomy (ISO 14649 / ISO 230) | Standard machine types (`CNC`, `MILLING`, `TURNING`, `DRILLING`, `FINISHING`, `WELDING`) | Adopted terminology for workstation classification |
| Routing Operations | Standard Machining Sequence Templates (SME Machining Handbook) | 20-step sequential manufacturing process flow | Synthesized realistic operation cycle durations (15–60 min) |
| Materials Catalog | Metallic Alloys Designation Handbook (AISI/SAE, ASTM, AMS) | Raw stock nomenclature (`Titanium Gr.5`, `316L SS`, `7075-T6 Alloy`) | Synthesized material names, units (`KG`), and inventory stock bounds |
| Changeover Modeling | SMED (Single-Minute Exchange of Die) Principles | Sequence-dependent product setup matrices | Synthesized pairwise transition penalties (15–60 min) |

---

## 3. License and Redistribution Terms

- **Source Code License:** MIT License (or project declared license).
- **Dataset License:** Open Data Synthetic Domain Commons — free to inspect, reproduce, evaluate, and benchmark.
- **Redistribution Rights:** Because the dataset is 100% synthetically generated with explicit fixed-seed procedures, it contains no third-party copyright encumbrances and may be freely distributed and cloned.

---

## 4. Entity Attribution Manifest

| Artifact File | Record Count | Generation Source | Purpose |
|---|:---:|---|---|
| `data/products.csv / .json` | 100 | `scripts/generate_synthetic_data.py` | SKUs and finished product catalog |
| `data/machines.csv / .json` | 40 | `scripts/generate_synthetic_data.py` | Workstations and capacity limits |
| `data/materials.csv / .json` | 200 | `scripts/generate_synthetic_data.py` | Raw material stock catalog |
| `data/routings.csv / .json` | 100 | `scripts/generate_synthetic_data.py` | Process route headers |
| `data/operations.csv / .json` | 2,000 | `scripts/generate_synthetic_data.py` | Routing operation steps |
| `data/production_orders.csv / .json`| 500 | `scripts/generate_synthetic_data.py` | Manufacturing demand orders |
| `data/inventory_lots.csv / .json` | 295 | `scripts/generate_synthetic_data.py` | Batched stock with arrival dates |
| `data/changeover_matrix.csv / .json`| 8,400 | `scripts/generate_synthetic_data.py` | Machine-specific setup matrices |
| `data/machine_calendars.csv / .json`| 120 | `scripts/generate_synthetic_data.py` | 3-shift daily operating calendars |
| `data/tools.csv / .json` | 20 | `scripts/generate_synthetic_data.py` | Shared plant fixtures and tooling |
| `data/ground_truth.csv / .json` | 5 | `scripts/generate_synthetic_data.py` | Labelled edge-case anomaly ground truth |
