"""
Tests for deterministic synthetic data generation at full and starter scales.
"""

from scripts.generate_synthetic_data import generate_dataset, SCALE_CONFIG


def test_full_dataset_generation_volume():
    ds = generate_dataset(scale_name="full", seed=20261022)

    assert len(ds["products"]) == 100
    assert len(ds["machines"]) == 40
    assert len(ds["production_orders"]) == 500
    assert len(ds["operations"]) == 2000
    assert len(ds["materials"]) == 200
    assert len(ds["routings"]) == 100
    assert len(ds["machine_calendars"]) == 120  # 40 machines * 3 shifts
    assert len(ds["tools"]) == 20
    assert len(ds["labor_shifts"]) == 3
    assert len(ds["ground_truth"]) == 5


def test_starter_dataset_generation_volume():
    ds = generate_dataset(scale_name="starter", seed=20261022)

    assert len(ds["products"]) == 10
    assert len(ds["machines"]) == 5
    assert len(ds["production_orders"]) == 50
    assert len(ds["operations"]) == 200
    assert len(ds["materials"]) == 20
    assert len(ds["routings"]) == 10
    assert len(ds["tools"]) == 5


def test_custom_seed_variance():
    ds1 = generate_dataset(scale_name="starter", seed=111)
    ds2 = generate_dataset(scale_name="starter", seed=222)

    # Different seeds produce different randomized order quantities/dates
    quantities1 = [o["quantity"] for o in ds1["production_orders"]]
    quantities2 = [o["quantity"] for o in ds2["production_orders"]]
    assert quantities1 != quantities2
