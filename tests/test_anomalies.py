"""
Unit tests for TabPFN anomaly detection.
"""

from backend.anomalies import detect_anomalies_with_tabpfn

def test_anomaly_detection_high_expense_and_duplicates():
    # Transactions with normal expenses + 1 unusually high expense + 1 duplicate pair
    txs = [
        {"id": 1, "date": "2026-10-10", "party": "Milk Supply", "item": "Daily Milk", "amount": 300.0, "type": "expense"},
        {"id": 2, "date": "2026-10-11", "party": "Milk Supply", "item": "Daily Milk", "amount": 310.0, "type": "expense"},
        {"id": 3, "date": "2026-10-12", "party": "Transport", "item": "Tempo", "amount": 200.0, "type": "expense"},
        {"id": 4, "date": "2026-10-13", "party": "Tea Agency", "item": "Tea leaves", "amount": 250.0, "type": "expense"},
        # Duplicate transaction
        {"id": 5, "date": "2026-10-14", "party": "Tea Agency", "item": "Tea leaves", "amount": 250.0, "type": "expense"},
        # Unusually high expense
        {"id": 6, "date": "2026-10-15", "party": "Wholesale Dist", "item": "Machinery repair", "amount": 19500.0, "type": "expense"},
    ]
    
    res = detect_anomalies_with_tabpfn(txs)
    assert res.total_analyzed == 6
    assert res.anomalies_found >= 2
    
    reasons = [a.reason for a in res.anomalies]
    assert any("Unusually high expense" in r or "19,500" in r for r in reasons)
    assert any("Potential duplicate" in r for r in reasons)
