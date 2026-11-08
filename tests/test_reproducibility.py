"""
Tests for deterministic generator reproducibility:
Generates two separate passes with fixed seed 20261022 and verifies row counts and record data match 100%.
"""

from scripts.generate_synthetic_data import generate_dataset


def test_fixed_seed_reproducibility():
    seed = 20261022

    pass1 = generate_dataset(scale_name="starter", seed=seed)
    pass2 = generate_dataset(scale_name="starter", seed=seed)

    # 1. Compare all table record counts
    for table_name in pass1.keys():
        assert len(pass1[table_name]) == len(pass2[table_name]), (
            f"Row count mismatch in table {table_name}: "
            f"pass1={len(pass1[table_name])}, pass2={len(pass2[table_name])}"
        )

    # 2. Compare exact products records
    assert pass1["products"] == pass2["products"]

    # 3. Compare exact machines records
    assert pass1["machines"] == pass2["machines"]

    # 4. Compare exact production orders
    assert pass1["production_orders"] == pass2["production_orders"]

    # 5. Compare operations
    assert pass1["operations"] == pass2["operations"]

    # 6. Compare ground truth anomalies
    assert pass1["ground_truth"] == pass2["ground_truth"]
