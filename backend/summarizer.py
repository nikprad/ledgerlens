"""
Financial Summary Module for LedgerLens.
Generates short plain-language weekly summaries comparing recent expenses and revenue.
"""

import time
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.models import FinancialSummary
from backend.observability import logger

def generate_weekly_summary(
    transactions: List[Dict[str, Any]]
) -> FinancialSummary:
    """
    Generate a plain-language financial summary comparing the latest week to prior periods.
    Uses local Gemma model if Ollama is running; otherwise produces analytical rule-based summary.
    """
    start_time = time.time()
    if not transactions:
        return FinancialSummary(
            period="Past 7 Days",
            total_sales=0.0,
            total_expenses=0.0,
            net_cash_flow=0.0,
            plain_language_summary="No transactions available yet to generate a financial summary.",
            generated_by="System"
        )

    df = pd.DataFrame(transactions)
    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values("dt")
    
    if df.empty:
        return FinancialSummary(
            period="Past 7 Days",
            total_sales=0.0,
            total_expenses=0.0,
            net_cash_flow=0.0,
            plain_language_summary="Transactions could not be dated.",
            generated_by="System"
        )

    max_date = df["dt"].max()
    curr_week_start = max_date - timedelta(days=6)
    prev_week_start = max_date - timedelta(days=13)
    prev_week_end = curr_week_start - timedelta(seconds=1)

    curr_df = df[df["dt"] >= curr_week_start]
    prev_df = df[(df["dt"] >= prev_week_start) & (df["dt"] <= prev_week_end)]

    curr_sales = float(curr_df[curr_df["type"] == "sale"]["amount"].sum())
    curr_expenses = float(curr_df[curr_df["type"] == "expense"]["amount"].sum())
    curr_net = curr_sales - curr_expenses

    prev_expenses = float(prev_df[prev_df["type"] == "expense"]["amount"].sum()) if not prev_df.empty else 0.0

    exp_change_pct = 0.0
    if prev_expenses > 0:
        exp_change_pct = round(((curr_expenses - prev_expenses) / prev_expenses) * 100, 1)

    top_expense_party = "store supplies"
    if not curr_df[curr_df["type"] == "expense"].empty:
        top_exp = curr_df[curr_df["type"] == "expense"].groupby("party")["amount"].sum().idxmax()
        top_expense_party = str(top_exp)

    # Prompt for local Gemma model
    prompt = (
        f"You are a friendly financial assistant for an Indian shopkeeper. Write a 2-3 sentence plain language summary:\n"
        f"- Current Week Sales: Rs {curr_sales:,.2f}\n"
        f"- Current Week Expenses: Rs {curr_expenses:,.2f}\n"
        f"- Net Cash Flow: Rs {curr_net:,.2f}\n"
        f"- Expense Change compared to previous week: {exp_change_pct:+.1f}%\n"
        f"- Main expense category: {top_expense_party}\n"
        f"Format example: 'You made Rs 12,400 in sales this week with a positive net cash flow of Rs 4,200. You spent 18% more on supplies this week due to wholesale restocking.'"
    )

    summary_text = ""
    generator_name = settings.GEMMA_VISION_MODEL

    try:
        ollama_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(ollama_url, json={
                "model": settings.GEMMA_VISION_MODEL,
                "prompt": prompt,
                "stream": False
            })
            if resp.status_code == 200:
                summary_text = resp.json().get("response", "").strip()
            else:
                raise ConnectionError()
    except Exception:
        # High quality analytical rule-based summary
        generator_name = "Local Financial Engine (Analytical)"
        direction = "more" if exp_change_pct >= 0 else "less"
        abs_pct = abs(exp_change_pct)
        if prev_expenses > 0:
            summary_text = (
                f"You generated Rs {curr_sales:,.2f} in sales and had Rs {curr_expenses:,.2f} in expenses this week, "
                f"resulting in a net cash flow of Rs {curr_net:+,.2f}. "
                f"You spent {abs_pct:.1f}% {direction} on expenses this week compared to last week, with the largest outgoing payment to {top_expense_party}."
            )
        else:
            summary_text = (
                f"You recorded Rs {curr_sales:,.2f} in total sales and Rs {curr_expenses:,.2f} in operating expenses, "
                f"closing the period with a healthy net balance of Rs {curr_net:+,.2f}."
            )

    latency_ms = (time.time() - start_time) * 1000
    logger.log_step(
        "summarize",
        latency_ms,
        metadata={"curr_sales": curr_sales, "curr_expenses": curr_expenses, "model": generator_name}
    )

    return FinancialSummary(
        period=f"{curr_week_start.strftime('%d %b')} - {max_date.strftime('%d %b %Y')}",
        total_sales=round(curr_sales, 2),
        total_expenses=round(curr_expenses, 2),
        net_cash_flow=round(curr_net, 2),
        plain_language_summary=summary_text,
        generated_by=generator_name
    )
