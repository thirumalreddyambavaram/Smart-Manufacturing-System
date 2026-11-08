# YottaFlex Manufacturing - Automated Validation Summary

**Execution Timestamp:** 2026-11-08T02:59:55.595505

**Overall Status:** `PASSED`

**Summary:** 15 of 15 checks passed. 5 deliberate ground-truth anomaly scenarios cataloged and verified.

| # | Validation Rule | Status | Description |
|---|---|:---:|---|
| 1 | 1. Primary-Key Uniqueness | `PASS` | All entity primary keys and code identifiers are strictly unique. |
| 2 | 2. Foreign-Key Integrity | `PASS` | All foreign key relationships are valid and referentially intact. |
| 3 | 3. Duplicate Records Check | `PASS` | No redundant duplicate rows found across bridge and mapping tables. |
| 4 | 4. Allowed Enum Values | `PASS` | All record status and priority fields adhere to allowed enum values. |
| 5 | 5. Date Ordering | `PASS` | All dates obey chronological ordering (start < end, order_date <= due_date). |
| 6 | 6. Material Balance Reconciliation | `PASS` | Material stock balances and lot quantities reconcile accurately. |
| 7 | 7. Machine Capacity Compliance | `PASS` | Machine capacity ratings are positive and within operational bounds. |
| 8 | 8. Shift Calendar Compliance | `PASS` | Baseline operation schedules are strictly within defined working shift calendars. Ground-truth edge case ANOM-004 (CALENDAR_OUT_OF_SHIFT) is registered and verified. |
| 9 | 9. Machine Overlap Check | `PASS` | 0 machine schedule overlaps in active production schedules. Ground-truth edge case ANOM-001 (MACHINE_OVERLAP) is registered and isolated. |
| 10 | 10. Operation Precedence | `PASS` | Strict sequential precedence maintained across all scheduled order operations. Ground-truth edge case ANOM-002 (PRECEDENCE_VIOLATION) is documented. |
| 11 | 11. Material Availability | `PASS` | Material availability dates are strictly respected by all production schedules. Ground-truth edge case ANOM-003 (MATERIAL_PRE_AVAILABILITY) is verified. |
| 12 | 12. Changeover Correctness | `PASS` | Sequence-dependent changeovers are correctly calculated and applied. Ground-truth edge case ANOM-005 (CHANGEOVER_OMITTED) is verified. |
| 13 | 13. Labor Availability | `PASS` | Active labor shifts defined (3 shifts) supporting plant staffing with 42916 labor assignments recorded. |
| 14 | 14. Shared Tooling Availability | `PASS` | Shared tooling registry active (20 tools) with conflict-free concurrent allocation. |
| 15 | 15. Lifecycle Transitions | `PASS` | Audit trail maintained with 11234 state change events recorded in event_history. |

## Ground-Truth Anomaly Scenarios (Deliberately Injected Edge Cases)

| Anomaly ID | Issue Type | Expected Decision | Ground-Truth Label | Description |
|---|---|---|:---:|---|
| `ANOM-001` | `MACHINE_OVERLAP` | `FAIL_MACHINE_OVERLAP` | `ANOMALY` | Two operations scheduled concurrently on machine MACH-001 with overlapping time windows. |
| `ANOM-002` | `PRECEDENCE_VIOLATION` | `FAIL_OPERATION_PRECEDENCE` | `ANOMALY` | Operation sequence 2 scheduled to begin 3 hours before operation sequence 1 completes. |
| `ANOM-003` | `MATERIAL_PRE_AVAILABILITY` | `FAIL_MATERIAL_AVAILABILITY` | `ANOMALY` | Operation scheduled to consume inventory lot LOT-2026-000020 before its delivery/availability date of 2026-11-20. |
| `ANOM-004` | `CALENDAR_OUT_OF_SHIFT` | `FAIL_SHIFT_CALENDAR` | `ANOMALY` | Operation scheduled at 03:00:00 during non-operational hours outside machine shift calendars. |
| `ANOM-005` | `CHANGEOVER_OMITTED` | `FAIL_CHANGEOVER_REQUIREMENT` | `ANOMALY` | Consecutive operations on MACH-003 switching products without allocating required 45-minute setup changeover. |
