"""
SQLite database storage for LedgerLens.
Stores transactions, anomalies, and logs locally with zero cloud egress.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from backend.config import settings
from backend.models import TransactionItem

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                party TEXT NOT NULL,
                item TEXT NOT NULL,
                quantity REAL DEFAULT 1.0,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'INR',
                type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                flagged INTEGER DEFAULT 0,
                flag_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                date TEXT,
                party TEXT,
                item TEXT,
                amount REAL,
                type TEXT,
                reason TEXT NOT NULL,
                score REAL DEFAULT 0.0,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

def insert_transactions(items: List[TransactionItem]) -> List[int]:
    """Insert clean transactions into SQLite and return generated IDs."""
    init_db()
    inserted_ids = []
    with get_connection() as conn:
        cursor = conn.cursor()
        for it in items:
            cursor.execute("""
                INSERT INTO transactions (date, party, item, quantity, amount, currency, type, confidence, flagged, flag_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                it.date,
                it.party,
                it.item,
                it.quantity,
                it.amount,
                it.currency,
                it.type,
                it.confidence,
                1 if it.flagged else 0,
                it.flag_reason
            ))
            inserted_ids.append(cursor.lastrowid)
        conn.commit()
    return inserted_ids

def get_all_transactions() -> List[Dict[str, Any]]:
    """Retrieve all stored transactions ordered by date descending."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def clear_all_transactions():
    """Clear transactions and anomalies."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM anomalies")
        conn.commit()

def seed_demo_history(days: int = 35):
    """
    Seed ~35 days of realistic Indian shop ledger transactions.
    Enables testing the TabPFN 30-day cash-flow forecast immediately.
    """
    init_db()
    clear_all_transactions()
    
    today = datetime.now().date()
    start_date = today - timedelta(days=days)
    
    sample_sales = [
        ("Sharma Store", "Atta 10kg", 1.0, 380.0),
        ("Sharma Store", "Mustard Oil", 2.0, 320.0),
        ("Raju Bhai", "Basmati Rice 5kg", 1.0, 450.0),
        ("Gupta Ji", "Special Masala Chai", 20.0, 200.0),
        ("Local Customer", "Spices & Masala", 3.0, 150.0),
        ("Vikram", "Mobile Recharge", 1.0, 499.0),
        ("Counter Sale", "Dairy Milk & Snacks", 5.0, 250.0),
        ("Sunil Kirana", "Toor Dal 2kg", 2.0, 280.0),
    ]
    
    sample_expenses = [
        ("Amul Supply", "Daily Milk Cans", 5.0, 310.0),
        ("Transport", "Tempo Transport fare", 1.0, 150.0),
        ("Electric Board", "Shop Bijli Bill", 1.0, 800.0),
        ("Vegetable Mandi", "Potatoes & Onions", 10.0, 350.0),
        ("Staff", "Daily Cleaning & Helper", 1.0, 200.0),
        ("Gas Agency", "LPG Commercial cylinder", 1.0, 950.0),
    ]
    
    items_to_insert = []
    
    for d in range(days):
        current_date = (start_date + timedelta(days=d)).strftime("%Y-%m-%d")
        
        # 2 to 4 sales per day
        num_sales = random.randint(2, 4)
        for _ in range(num_sales):
            p, itm, q, a = random.choice(sample_sales)
            jitter = random.uniform(0.9, 1.15)
            items_to_insert.append(TransactionItem(
                date=current_date,
                party=p,
                item=itm,
                quantity=round(q, 1),
                amount=round(a * jitter, 2),
                currency="INR",
                type="sale",
                confidence=0.95
            ))
            
        # 1 to 2 expenses per day
        num_exp = random.randint(1, 2)
        for _ in range(num_exp):
            p, itm, q, a = random.choice(sample_expenses)
            jitter = random.uniform(0.9, 1.1)
            items_to_insert.append(TransactionItem(
                date=current_date,
                party=p,
                item=itm,
                quantity=round(q, 1),
                amount=round(a * jitter, 2),
                currency="INR",
                type="expense",
                confidence=0.92
            ))
            
    insert_transactions(items_to_insert)
    return len(items_to_insert)
