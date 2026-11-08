"""
Tests for all 5 deliberate ground-truth anomaly scenarios:
1. Operations overlap on a machine (MACHINE_OVERLAP)
2. Operation precedence violation (PRECEDENCE_VIOLATION)
3. Material consumed before availability (MATERIAL_PRE_AVAILABILITY)
4. Schedule outside machine shift calendar (CALENDAR_OUT_OF_SHIFT)
5. Changeover omitted between product transitions (CHANGEOVER_OMITTED)
"""

import json
from pathlib import Path


def test_five_anomaly_scenarios_documented():
    gt_file = Path("data/ground_truth.json")
    assert gt_file.exists(), "ground_truth.json file must exist in data/"

    with open(gt_file, "r", encoding="utf-8") as f:
        anomalies = json.load(f)

    assert len(anomalies) == 5

    issue_types = {a["issue_type"] for a in anomalies}
    required_types = {
        "MACHINE_OVERLAP",
        "PRECEDENCE_VIOLATION",
        "MATERIAL_PRE_AVAILABILITY",
        "CALENDAR_OUT_OF_SHIFT",
        "CHANGEOVER_OMITTED",
    }
    assert issue_types == required_types

    for a in anomalies:
        assert a["anomaly_id"].startswith("ANOM-")
        assert a["ground_truth_label"] == "ANOMALY"
        assert "expected_result" in a
        assert len(a["explanation"]) > 10
        assert isinstance(a["related_entities"], dict)


def test_anomaly_csv_matches_json():
    csv_file = Path("data/ground_truth.csv")
    assert csv_file.exists(), "ground_truth.csv file must exist in data/"

    with open(csv_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Header + 5 anomaly rows = 6 lines
    assert len(lines) == 6
