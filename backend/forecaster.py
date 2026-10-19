"""
TabPFN Cash-Flow Forecasting Module for LedgerLens.
Predicts next 30 days of net cash flow from history with uncertainty bounds.
Gracefully falls back if there are fewer than 20 historical data points.
"""

import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from backend.config import settings
from backend.models import ForecastPoint, ForecastResponse
from backend.observability import logger

def forecast_cash_flow(
    transactions: List[Dict[str, Any]],
    forecast_days: int = 30
) -> ForecastResponse:
    """
    Predict next 30 days of daily net cash flow from history.
    Daily Net Cash Flow = sum(sales) - sum(expenses).
    
    Returns uncertainty range [lower_bound, upper_bound].
    Falls back gracefully if fewer than 20 daily points are available.
    """
    start_time = time.time()
    if not transactions:
        return ForecastResponse(
            status="insufficient_data",
            message="No transactions found in history. Add receipts or click 'Load Demo Data' to generate a 30-day cash flow forecast.",
            historical_points_count=0,
            forecast_points=[],
            model_used="TabPFN",
            local_execution=not settings.ENABLE_TABPFN_API
        )

    df = pd.DataFrame(transactions)
    # Parse dates
    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values("dt")
    
    if df.empty:
        return ForecastResponse(
            status="insufficient_data",
            message="Could not parse transaction dates.",
            historical_points_count=0,
            forecast_points=[],
            model_used="TabPFN",
            local_execution=not settings.ENABLE_TABPFN_API
        )

    # Compute daily sales, expenses, and net cash flow
    df["sales_amt"] = df.apply(lambda r: float(r["amount"]) if str(r["type"]).lower() == "sale" else 0.0, axis=1)
    df["expense_amt"] = df.apply(lambda r: float(r["amount"]) if str(r["type"]).lower() == "expense" else 0.0, axis=1)
    
    daily = df.groupby(df["dt"].dt.strftime("%Y-%m-%d")).agg({
        "sales_amt": "sum",
        "expense_amt": "sum"
    }).reset_index()
    daily["net_cash_flow"] = daily["sales_amt"] - daily["expense_amt"]
    daily["dt"] = pd.to_datetime(daily["dt"])
    daily = daily.sort_values("dt").reset_index(drop=True)

    points_count = len(daily)
    # Requirement: Gracefully fall back if fewer than ~20 data points
    if points_count < 20:
        latency_ms = (time.time() - start_time) * 1000
        msg = (
            f"Fewer than 20 historical daily data points available (found {points_count}). "
            "TabPFN requires at least 20 historical days for reliable time series forecasting. "
            "Upload more ledger pages or click 'Load 35-Day Demo History' in the UI to test forecasting."
        )
        logger.log_step(
            "forecast",
            latency_ms,
            metadata={"status": "insufficient_data", "points_count": points_count}
        )
        return ForecastResponse(
            status="insufficient_data",
            message=msg,
            historical_points_count=points_count,
            forecast_points=[],
            model_used="TabPFN",
            local_execution=not settings.ENABLE_TABPFN_API
        )

    # Build time-series tabular features for TabPFN
    daily["day_index"] = np.arange(len(daily))
    daily["day_of_week"] = daily["dt"].dt.dayofweek
    daily["day_of_month"] = daily["dt"].dt.day
    daily["lag_1"] = daily["net_cash_flow"].shift(1).bfill()
    daily["lag_7"] = daily["net_cash_flow"].shift(7).bfill()
    daily["rolling_mean_7"] = daily["net_cash_flow"].rolling(window=7, min_periods=1).mean()

    feature_cols = ["day_index", "day_of_week", "day_of_month", "lag_1", "lag_7", "rolling_mean_7"]
    X_train = daily[feature_cols].to_numpy()
    y_train = daily["net_cash_flow"].to_numpy()

    # Fit TabPFN model (Strictly anonymized numeric array)
    use_tabpfn_api = settings.ENABLE_TABPFN_API
    model_name = "TabPFN-Local (CPU)"
    model = None

    try:
        if use_tabpfn_api and settings.TABPFN_TOKEN:
            from tabpfn_client import TabPFNRegressor
            model = TabPFNRegressor()
            model.fit(X_train, y_train)
            model_name = "TabPFN Cloud Client (Anonymized numeric)"
        else:
            from tabpfn import TabPFNRegressor
            model = TabPFNRegressor()
            model.fit(X_train, y_train)
            model_name = "TabPFN-v2 (Local On-Device)"
    except Exception as e:
        # Fallback to local linear/trend regression if weights are compiling
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        model_name = "Local Ensemble Forecaster (Fallback)"

    # Compute training residual variance for empirical uncertainty bounds
    train_preds = model.predict(X_train)
    residuals = y_train - train_preds
    residual_std = float(np.std(residuals)) if np.std(residuals) > 0 else float(np.std(y_train) * 0.25 + 50.0)

    # Iterative multi-step 30-day forecast
    last_date = daily["dt"].iloc[-1]
    last_idx = daily["day_index"].iloc[-1]
    history_net = list(daily["net_cash_flow"].values)
    
    forecast_points: List[ForecastPoint] = []

    for step in range(1, forecast_days + 1):
        target_date = last_date + timedelta(days=step)
        target_idx = last_idx + step
        dow = target_date.weekday()
        dom = target_date.day
        
        lag_1 = history_net[-1] if len(history_net) >= 1 else 0.0
        lag_7 = history_net[-7] if len(history_net) >= 7 else lag_1
        rolling_7 = float(np.mean(history_net[-7:])) if len(history_net) >= 7 else lag_1

        X_step = np.array([[target_idx, dow, dom, lag_1, lag_7, rolling_7]])
        pred_val = float(model.predict(X_step)[0])
        history_net.append(pred_val)

        # Expanding uncertainty bound over forecast horizon
        uncertainty_expansion = 1.0 + (step / float(forecast_days)) * 0.4
        margin = 1.96 * residual_std * uncertainty_expansion

        forecast_points.append(ForecastPoint(
            date=target_date.strftime("%Y-%m-%d"),
            predicted_net_cash_flow=round(pred_val, 2),
            lower_bound=round(pred_val - margin, 2),
            upper_bound=round(pred_val + margin, 2)
        ))

    latency_ms = (time.time() - start_time) * 1000
    logger.log_step(
        "forecast",
        latency_ms,
        metadata={
            "historical_points": points_count,
            "forecast_days": forecast_days,
            "model_used": model_name,
            "local_execution": not settings.ENABLE_TABPFN_API
        }
    )

    return ForecastResponse(
        status="success",
        message=f"Successfully projected 30-day cash flow using {model_name} with 95% uncertainty interval.",
        historical_points_count=points_count,
        forecast_points=forecast_points,
        model_used=model_name,
        local_execution=not settings.ENABLE_TABPFN_API
    )
