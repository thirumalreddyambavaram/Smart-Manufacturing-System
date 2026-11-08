"""
Tests for FastAPI backend REST endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_products_endpoint():
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert isinstance(products, list)
    assert len(products) >= 100


def test_machines_endpoint():
    res = client.get("/api/machines")
    assert res.status_code == 200
    machines = res.json()
    assert isinstance(machines, list)
    assert len(machines) == 40


def test_materials_endpoint():
    res = client.get("/api/materials")
    assert res.status_code == 200
    materials = res.json()
    assert isinstance(materials, list)
    assert len(materials) == 200


def test_production_orders_endpoint():
    res = client.get("/api/production-orders")
    assert res.status_code == 200
    orders = res.json()
    assert isinstance(orders, list)
    assert len(orders) >= 500


def test_routings_endpoint():
    res = client.get("/api/routings")
    assert res.status_code == 200
    routings = res.json()
    assert isinstance(routings, list)
    assert len(routings) > 0


def test_changeovers_endpoint():
    res = client.get("/api/changeovers")
    assert res.status_code == 200
    changeovers = res.json()
    assert isinstance(changeovers, list)
    assert len(changeovers) > 0


def test_tools_endpoint():
    res = client.get("/api/tools")
    assert res.status_code == 200
    tools = res.json()
    assert isinstance(tools, list)
    assert len(tools) == 20


def test_labor_shifts_endpoint():
    res = client.get("/api/labor-shifts")
    assert res.status_code == 200
    shifts = res.json()
    assert isinstance(shifts, list)
    assert len(shifts) >= 3


def test_metrics_endpoint():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "makespan_hours" in metrics
    assert "machine_utilization_pct" in metrics
    assert "on_time_delivery_pct" in metrics


def test_validation_summary_endpoint():
    res = client.get("/api/validation/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["overall_status"] == "PASSED"
    assert summary["total_checks"] == 15


def test_ground_truth_endpoint():
    res = client.get("/api/ground-truth")
    assert res.status_code == 200
    anomalies = res.json()
    assert len(anomalies) == 5


def test_material_reservations_endpoint():
    res = client.get("/api/material-reservations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_material_consumptions_endpoint():
    res = client.get("/api/material-consumptions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_labor_assignments_endpoint():
    res = client.get("/api/labor-assignments")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_machine_calendars_endpoint():
    res = client.get("/api/machine-calendars")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 120


def test_inventory_lots_endpoint():
    res = client.get("/api/inventory-lots")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 200
