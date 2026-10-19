"""
FastAPI integration tests for all endpoints.
"""

from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "LedgerLens"

def test_extract_endpoint_with_sample_image():
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "samples", "sample_1_kiranastore.png")
    with open(sample_path, "rb") as f:
        res = client.post("/extract", files={"file": ("sample_1.png", f, "image/png")})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["items"]) >= 3

def test_validate_and_store_endpoints():
    items = [
        {"date": "12/10/2026", "party": "Sharma Store", "item": "Atta", "quantity": 1.0, "amount": 380.0, "currency": "INR", "type": "sale", "confidence": 0.95},
        {"date": "12/10/2026", "party": "Amul", "item": "Milk", "quantity": 2.0, "amount": 120.0, "currency": "INR", "type": "expense", "confidence": 0.9}
    ]
    val_res = client.post("/validate", json=items)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert len(val_data["valid_items"]) == 2

    # Store
    store_res = client.post("/store", json=val_data["valid_items"])
    assert store_res.status_code == 200
    assert store_res.json()["inserted_count"] == 2

    # Get transactions
    get_res = client.get("/transactions")
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 2

def test_seed_demo_and_forecast_anomalies_summarize():
    # Seed 30 days
    seed_res = client.post("/seed-demo?days=30")
    assert seed_res.status_code == 200

    # Anomalies
    anom_res = client.post("/anomalies")
    assert anom_res.status_code == 200

    # Forecast
    fc_res = client.post("/forecast?days=30")
    assert fc_res.status_code == 200
    assert fc_res.json()["status"] == "success"
    assert len(fc_res.json()["forecast_points"]) == 30

    # Summarize
    sum_res = client.post("/summarize")
    assert sum_res.status_code == 200
    assert len(sum_res.json()["plain_language_summary"]) > 10

def test_privacy_status_and_export():
    p_res = client.get("/privacy-status")
    assert p_res.status_code == 200
    assert p_res.json()["zero_cloud_pii"] is True

    # CSV Export
    csv_res = client.get("/export/csv")
    assert csv_res.status_code == 200
    assert "date,party,item" in csv_res.text

    # XLSX Export
    xlsx_res = client.get("/export/xlsx")
    assert xlsx_res.status_code == 200
    assert xlsx_res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
