"""
Script to execute the 15-rule automated validation suite.
"""

import sys
from pathlib import Path

# Add backend to python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.validators.system_validator import run_system_validation_report

if __name__ == "__main__":
    report = run_system_validation_report()
    print(f"\nOverall Validation Status: {report['overall_status']}")
    print(f"Passed Checks: {report['passed_checks']} / {report['total_checks']}")
    print(f"Deliberate Anomalies Verified: {report['ground_truth_anomalies_accounted']}")
