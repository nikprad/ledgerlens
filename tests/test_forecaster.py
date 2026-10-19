"""
Unit tests for TabPFN cash flow forecasting.
"""

from backend.forecaster import forecast_cash_flow
from datetime import datetime, timedelta

def test_forecast_insufficient_data_fallback():
    # Only 5 days of history (< 20)
    txs = []
    base = datetime(2026, 10, 1)
    for i in range(5):
        d = (base + timedelta(days=i)).strftime("%Y-%m-%d")
        txs.append({"date": d, "party": "Counter", "item": "Sales", "amount": 1000.0, "type": "sale"})
        txs.append({"date": d, "party": "Vendor", "item": "Exp", "amount": 400.0, "type": "expense"})

    res = forecast_cash_flow(txs)
    assert res.status == "insufficient_data"
    assert res.historical_points_count == 5
    assert len(res.forecast_points) == 0
    assert "Fewer than 20 historical" in res.message

def test_forecast_success_with_sufficient_data():
    # 25 days of history (>= 20)
    txs = []
    base = datetime(2026, 9, 1)
    for i in range(25):
        d = (base + timedelta(days=i)).strftime("%Y-%m-%d")
        txs.append({"date": d, "party": "Counter", "item": "Daily Sale", "amount": 1200.0 + (i % 5) * 50, "type": "sale"})
        txs.append({"date": d, "party": "Vendor", "item": "Daily Exp", "amount": 500.0 + (i % 3) * 30, "type": "expense"})

    res = forecast_cash_flow(txs, forecast_days=30)
    assert res.status == "success"
    assert res.historical_points_count == 25
    assert len(res.forecast_points) == 30
    
    # Check uncertainty bounds
    for pt in res.forecast_points:
        assert pt.lower_bound <= pt.predicted_net_cash_flow <= pt.upper_bound
