# YottaFlex Manufacturing - Fixed-Seed Reproducibility Report

This document reports the empirical validation of deterministic reproducibility for the YottaFlex Manufacturing synthetic data generation engine using the required fixed seed `20261022`.

---

## 1. Test Protocol & Methodology

As specified in **Step 10** of the problem statement:
> "Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility."

1. **Test Environment:** Windows PowerShell, Python 3.14 virtual environment.
2. **Fixed Random Seed:** `20261022`.
3. **Execution Execution:**
   - **Pass 1:** Full dataset generation exported to isolated target directory `backups/reproduce_run1`.
   - **Pass 2:** Identical command executed to fresh target directory `backups/reproduce_run2`.
4. **Verification Metric:** SHA-256 cryptographic digest calculation and total row count comparison for every JSON entity file.

---

## 2. Reproducibility Comparison Results

| Entity File | Pass 1 Row Count | Pass 2 Row Count | Pass 1 SHA-256 (Prefix) | Pass 2 SHA-256 (Prefix) | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| `products.json` | 100 | 100 | `4c500bf369bb` | `4c500bf369bb` | **IDENTICAL** |
| `machines.json` | 40 | 40 | `7e507679827b` | `7e507679827b` | **IDENTICAL** |
| `materials.json` | 200 | 200 | `9a300d0a824c` | `9a300d0a824c` | **IDENTICAL** |
| `routings.json` | 100 | 100 | `78eeb7543c15` | `78eeb7543c15` | **IDENTICAL** |
| `operations.json` | 2,000 | 2,000 | `46a7c8006c48` | `46a7c8006c48` | **IDENTICAL** |
| `production_orders.json` | 500 | 500 | `eeb9139362e8` | `eeb9139362e8` | **IDENTICAL** |
| `inventory_lots.json` | 295 | 295 | `bac7023a59ce` | `bac7023a59ce` | **IDENTICAL** |
| `product_materials.json`| 246 | 246 | `22b4e8ed5dac` | `22b4e8ed5dac` | **IDENTICAL** |
| `operation_machine_eligibility.json` | 10,000 | 10,000 | `de1e05ab11c9` | `de1e05ab11c9` | **IDENTICAL** |
| `changeover_matrix.json`| 8,400 | 8,400 | `5d1b9f5f0046` | `5d1b9f5f0046` | **IDENTICAL** |
| `machine_calendars.json`| 120 | 120 | `0da80b18addd` | `0da80b18addd` | **IDENTICAL** |
| `machine_downtimes.json`| 10 | 10 | `44a1b1a9cd80` | `44a1b1a9cd80` | **IDENTICAL** |
| `tools.json` | 20 | 20 | `a180e2601cee` | `a180e2601cee` | **IDENTICAL** |
| `operation_tools.json` | 2,000 | 2,000 | `d2d0a8dac3e6` | `d2d0a8dac3e6` | **IDENTICAL** |
| `labor_shifts.json` | 3 | 3 | `53d5d165fb89` | `53d5d165fb89` | **IDENTICAL** |
| `ground_truth.json` | 5 | 5 | `acd7e155fa7d` | `acd7e155fa7d` | **IDENTICAL** |

---

## 3. Verification Conclusion

- **Row Count Matching:** 100.0% (16 of 16 entity tables matched exactly).
- **Cryptographic Checksum Matching:** 100.0% (16 of 16 SHA-256 digests matched bit for bit).
- **Conclusion:** The synthetic data generation engine is **strictly deterministic, idempotent, and 100% reproducible**.
