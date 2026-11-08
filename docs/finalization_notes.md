# Finalization Notes — 2026-11-08

## Completed code changes

1. **Labor capacity is now a scheduling constraint.** Each proposed work segment is checked against an active labor shift and concurrent worker assignments. Existing persisted assignments and assignments created earlier in the current run both count against headcount. The scheduler refuses to fall back to an arbitrary shift ID.
2. **Shared-tool occupancy includes earlier runs.** Existing active schedules are joined to operation/tool requirements before a new run. The capacity timeline is combined with current-run bookings and handles half-open interval boundaries.
3. **Order-level transaction integrity.** Schedule creation now flushes rather than committing each operation. The scheduler commits a complete order only after its labor, schedules, and material consumption succeed. A material-consumption failure rolls back that order's work rather than leaving partial schedule rows.
4. **Failure reporting is more actionable.** Labor unavailability is recorded as a constraint violation with operation and machine context. The returned run summary includes the violation count and a human-readable summary.
5. **Changeover sequencing is conservative and deterministic.** A machine's new work is appended after its latest committed booking, so the predecessor product used for sequence-dependent setup is unambiguous. Missing prior product means no setup; a cross-product transition uses the matrix duration, with the existing 30-minute fallback retained when a matrix entry is absent.
6. **Evaluation metrics are run-scoped.** The feasibility denominator counts operations only for orders represented in the selected run. Productive time excludes recorded setup time, changeover remains a separate metric, machines without calendars contribute zero capacity, and utilization is not silently capped.
7. **Acceptance tests and documentation.** Added focused checks for labor headcount, shared-tool capacity intervals, and machine booking behavior. Updated the README with local startup, acceptance-test commands, and constraint behavior.

## Validation performed while packaging

- Python bytecode compilation: `python -m compileall -q backend/app tests` — passed.
- Pytest execution was attempted, but this packaging environment does not contain the `pymysql` dependency and outbound package installation is unavailable. The DB-backed test suite therefore could not be executed here. Install the declared `requirements.txt` in the target environment, configure MySQL, and run the commands in the README.
- Frontend production build was not rerun in this environment because the frontend dependencies are not installed here. The existing package lockfile is included.

## Data safety

No database was connected, reset, seeded, or modified while preparing this ZIP. The archive contains the project source, its existing submission data/exports, and documentation. The existing local database and its backup remain outside this archive and untouched.
