"""
Tests for 15-rule automated validation system.
"""

from app.database import SessionLocal
from app.validators.system_validator import SystemValidator


def test_system_validator_execution():
    db = SessionLocal()
    try:
        validator = SystemValidator(db)
        summary = validator.run_all_validations()

        assert summary["total_checks"] == 15
        assert summary["passed_checks"] == 15
        assert summary["failed_checks"] == 0
        assert summary["overall_status"] == "PASSED"
        assert summary["ground_truth_anomalies_accounted"] == 5

        # Check all 15 rules are included
        rule_names = [c["rule"] for c in summary["checks"]]
        assert len(rule_names) == 15
        assert any("Primary-Key Uniqueness" in r for r in rule_names)
        assert any("Foreign-Key Integrity" in r for r in rule_names)
        assert any("Duplicate Records" in r for r in rule_names)
        assert any("Allowed Enum Values" in r for r in rule_names)
        assert any("Date Ordering" in r for r in rule_names)
        assert any("Material Balance" in r for r in rule_names)
        assert any("Machine Capacity" in r for r in rule_names)
        assert any("Shift Calendar" in r for r in rule_names)
        assert any("Machine Overlap" in r for r in rule_names)
        assert any("Operation Precedence" in r for r in rule_names)
        assert any("Material Availability" in r for r in rule_names)
        assert any("Changeover Correctness" in r for r in rule_names)
        assert any("Labor Availability" in r for r in rule_names)
        assert any("Shared Tooling" in r for r in rule_names)
        assert any("Lifecycle Transitions" in r for r in rule_names)
    finally:
        db.close()
