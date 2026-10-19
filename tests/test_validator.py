"""
Unit tests for validator module.
"""

from backend.models import TransactionItem
from backend.validator import validate_and_clean_transactions, normalize_date_string, normalize_currency_string

def test_normalize_date_formats():
    assert normalize_date_string("12/10/2026")[0] == "2026-10-12"
    assert normalize_date_string("14-10-2026")[0] == "2026-10-14"
    assert normalize_date_string("2026-10-15")[0] == "2026-10-15"

def test_normalize_currency():
    assert normalize_currency_string("₹") == "INR"
    assert normalize_currency_string("Rs.") == "INR"
    assert normalize_currency_string("inr") == "INR"
    assert normalize_currency_string("$") == "USD"

def test_validator_drops_duplicates_and_flags_low_confidence():
    items = [
        TransactionItem(date="12/10/2026", party="Sharma", item="Atta", quantity=1.0, amount=380.0, currency="Rs", type="sale", confidence=0.95),
        # Exact duplicate
        TransactionItem(date="12/10/2026", party="Sharma", item="Atta", quantity=1.0, amount=380.0, currency="Rs", type="sale", confidence=0.95),
        # Low confidence (< 0.7)
        TransactionItem(date="12/10/2026", party="Unknown", item="Messy handwriting", quantity=1.0, amount=50.0, currency="INR", type="expense", confidence=0.55),
        # Suspicious negative amount
        TransactionItem(date="12/10/2026", party="Vendor", item="Negative", quantity=1.0, amount=-100.0, currency="INR", type="expense", confidence=0.9)
    ]
    
    result = validate_and_clean_transactions(items)
    
    # Check duplicate dropped
    assert len(result.valid_items) == 3
    assert result.dropped_duplicates == 1
    
    # Check date normalized
    assert result.valid_items[0].date == "2026-10-12"
    assert result.valid_items[0].currency == "INR"
    
    # Check low confidence flagged
    low_conf_item = [i for i in result.valid_items if i.item == "Messy handwriting"][0]
    assert low_conf_item.flagged is True
    assert "Low confidence" in low_conf_item.flag_reason
    
    # Check negative amount flagged without silent modification
    neg_item = [i for i in result.valid_items if i.item == "Negative"][0]
    assert neg_item.flagged is True
    assert neg_item.amount == -100.0  # Not silently modified!
