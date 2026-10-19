"""
Validation & Normalization Module for LedgerLens.
Normalizes dates and currencies, drops exact duplicates, and flags suspicious amounts without mutating them.
"""

import re
from datetime import datetime
from typing import List, Tuple
from backend.models import TransactionItem, ValidationResult
from backend.observability import logger
import time

def normalize_date_string(date_str: str) -> Tuple[str, bool]:
    """
    Normalizes diverse date formats into YYYY-MM-DD.
    Returns (normalized_date, success_flag).
    """
    date_str = date_str.strip()
    
    # Standard YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str, True

    # Try common formats
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
        "%Y/%m/%d", "%Y.%m.%d",
        "%d %b %Y", "%d %B %Y",
        "%b %d, %Y", "%B %d, %Y"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d"), True
        except ValueError:
            continue

    # Return original string if unparseable
    return date_str, False

def normalize_currency_string(currency_str: str) -> str:
    """Standardize currency notation."""
    c = currency_str.strip().upper()
    if c in ["₹", "RS", "RS.", "INR", "RUPEE", "RUPEES", "रुपये"]:
        return "INR"
    if c in ["$", "USD", "DOLLAR"]:
        return "USD"
    if c in ["€", "EUR", "EURO"]:
        return "EUR"
    return "INR"

def validate_and_clean_transactions(items: List[TransactionItem]) -> ValidationResult:
    """
    Validation pipeline:
    1. Normalizes date and currency
    2. Drops exact duplicates
    3. Never silently corrects amounts - flags suspicious amounts
    4. Ensures low confidence (< 0.7) is flagged for human review
    """
    start_time = time.time()
    seen = set()
    cleaned: List[TransactionItem] = []
    dropped_duplicates = 0
    flagged_count = 0

    for item in items:
        # 1. Normalize date
        norm_date, date_ok = normalize_date_string(item.date)
        item.date = norm_date
        if not date_ok:
            item.flagged = True
            item.flag_reason = (item.flag_reason + " | " if item.flag_reason else "") + "Unrecognized date format"

        # 2. Normalize currency
        item.currency = normalize_currency_string(item.currency)

        # 3. Check for exact duplicate
        # Signature: (date, party, item, quantity, amount, type)
        sig = (
            item.date.strip().lower(),
            item.party.strip().lower(),
            item.item.strip().lower(),
            round(item.quantity, 2),
            round(item.amount, 2),
            item.type.lower()
        )
        if sig in seen:
            dropped_duplicates += 1
            continue
        seen.add(sig)

        # 4. Never silently correct amounts; flag suspicious amounts
        if item.amount <= 0:
            item.flagged = True
            reason = "Zero or negative amount recorded; requires human verification"
            item.flag_reason = (item.flag_reason + " | " if item.flag_reason else "") + reason

        # 5. Low confidence check (< 0.7)
        if item.confidence < 0.7:
            item.flagged = True
            reason = f"Low confidence ({item.confidence:.2f}); verify handwritten entry"
            if not item.flag_reason or reason not in item.flag_reason:
                item.flag_reason = (item.flag_reason + " | " if item.flag_reason else "") + reason

        if item.flagged:
            flagged_count += 1

        cleaned.append(item)

    latency_ms = (time.time() - start_time) * 1000
    logger.log_step(
        "validate",
        latency_ms,
        metadata={
            "input_items": len(items),
            "output_items": len(cleaned),
            "dropped_duplicates": dropped_duplicates,
            "flagged_items": flagged_count
        }
    )

    msg = f"Validated {len(cleaned)} transactions. Dropped {dropped_duplicates} exact duplicates. {flagged_count} items flagged for human review."
    return ValidationResult(
        valid_items=cleaned,
        dropped_duplicates=dropped_duplicates,
        flagged_items_count=flagged_count,
        summary_message=msg
    )
