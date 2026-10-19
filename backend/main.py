"""
FastAPI Backend Service for LedgerLens.
Exposes REST endpoints for vision extraction, validation, SQLite storage,
TabPFN anomaly detection, cash-flow forecasting, summaries, and exports.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os

from backend.config import settings
from backend.models import (
    TransactionItem,
    ExtractionResponse,
    ValidationResult,
    AnomalyResponse,
    ForecastResponse,
    FinancialSummary,
    PrivacyStatus
)
from backend.extractor import extract_ledger_from_image
from backend.validator import validate_and_clean_transactions
from backend.database import (
    init_db,
    insert_transactions,
    get_all_transactions,
    clear_all_transactions,
    seed_demo_history
)
from backend.anomalies import detect_anomalies_with_tabpfn
from backend.forecaster import forecast_cash_flow
from backend.summarizer import generate_weekly_summary
from backend.exporter import export_transactions_to_csv, export_transactions_to_xlsx
from backend.observability import logger

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="LedgerLens API",
    description="Local-first agent API for handwritten ledger extraction, TabPFN anomaly detection, and cash-flow forecasting.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend and Mastra workflow access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "app": "LedgerLens",
        "status": "online",
        "vision_model": settings.GEMMA_VISION_MODEL,
        "tabpfn_mode": settings.TABPFN_MODE,
        "tabpfn_api_enabled": settings.ENABLE_TABPFN_API,
        "storage": "Local SQLite"
    }

@app.post("/extract", response_model=ExtractionResponse)
async def extract_endpoint(
    file: Optional[UploadFile] = File(None),
    image_path: Optional[str] = Form(None)
):
    """
    Extract line items from a ledger or receipt image.
    Accepts either an uploaded file or a local image path.
    """
    if file:
        content = await file.read()
        return extract_ledger_from_image(content, image_name=file.filename or "uploaded_image.png")
    elif image_path and os.path.exists(image_path):
        return extract_ledger_from_image(image_path, image_name=os.path.basename(image_path))
    else:
        raise HTTPException(status_code=400, detail="Must provide either a file upload or valid image_path")

@app.post("/validate", response_model=ValidationResult)
def validate_endpoint(items: List[TransactionItem]):
    """
    Normalize dates/currencies, drop exact duplicates, flag amounts without silent mutation.
    """
    return validate_and_clean_transactions(items)

@app.post("/store")
def store_endpoint(items: List[TransactionItem]):
    """
    Store validated transactions into local SQLite database.
    """
    inserted_ids = insert_transactions(items)
    return {
        "status": "success",
        "inserted_count": len(inserted_ids),
        "ids": inserted_ids
    }

@app.get("/transactions")
def get_transactions_endpoint():
    """
    Retrieve all stored transactions.
    """
    return get_all_transactions()

@app.delete("/transactions")
def clear_transactions_endpoint():
    """
    Clear all local transactions.
    """
    clear_all_transactions()
    return {"status": "success", "message": "All transactions and anomalies cleared"}

@app.post("/seed-demo")
def seed_demo_endpoint(days: int = 35):
    """
    Seed 35 days of realistic Indian shopkeeper transactions for immediate forecasting tests.
    """
    count = seed_demo_history(days=days)
    return {
        "status": "success",
        "message": f"Successfully seeded {count} transactions across past {days} days.",
        "count": count
    }

@app.post("/anomalies", response_model=AnomalyResponse)
def anomalies_endpoint(items: Optional[List[Dict[str, Any]]] = None):
    """
    Run TabPFN anomaly detection on transactions.
    If no items provided in request body, analyzes all transactions in SQLite.
    """
    data = items if items is not None else get_all_transactions()
    return detect_anomalies_with_tabpfn(data)

@app.post("/forecast", response_model=ForecastResponse)
def forecast_endpoint(
    items: Optional[List[Dict[str, Any]]] = None,
    days: int = 30
):
    """
    Run TabPFN cash-flow forecast for next 30 days with uncertainty bounds.
    Falls back gracefully if fewer than ~20 data points exist.
    """
    data = items if items is not None else get_all_transactions()
    return forecast_cash_flow(data, forecast_days=days)

@app.post("/summarize", response_model=FinancialSummary)
def summarize_endpoint(items: Optional[List[Dict[str, Any]]] = None):
    """
    Generate plain-language weekly summary comparing sales and expenses.
    """
    data = items if items is not None else get_all_transactions()
    return generate_weekly_summary(data)

@app.get("/export/csv")
def export_csv_endpoint():
    """
    Download transactions as CSV.
    """
    txs = get_all_transactions()
    csv_data = export_transactions_to_csv(txs)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ledgerlens_transactions.csv"}
    )

@app.get("/export/xlsx")
def export_xlsx_endpoint():
    """
    Download transactions as styled Excel workbook.
    """
    txs = get_all_transactions()
    xlsx_data = export_transactions_to_xlsx(txs)
    return Response(
        content=xlsx_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ledgerlens_transactions.xlsx"}
    )

@app.get("/privacy-status", response_model=PrivacyStatus)
def privacy_status_endpoint():
    """
    Return local-first privacy status for dashboard display.
    """
    is_local_ollama = "localhost" in settings.OLLAMA_BASE_URL or "127.0.0.1" in settings.OLLAMA_BASE_URL
    egress_desc = (
        "Cloud API Active (Strictly Anonymized Numeric Matrices Only - Zero PII)"
        if settings.ENABLE_TABPFN_API
        else "100% On-Device / Local (Zero Data Egress)"
    )
    return PrivacyStatus(
        ollama_endpoint=settings.OLLAMA_BASE_URL,
        ollama_model=settings.GEMMA_VISION_MODEL,
        ollama_is_local=is_local_ollama,
        tabpfn_mode="CLIENT (API)" if settings.ENABLE_TABPFN_API else "LOCAL (CPU/GPU)",
        tabpfn_api_enabled=settings.ENABLE_TABPFN_API,
        storage_type="Local SQLite (ledgerlens.db)",
        data_egress_status=egress_desc,
        zero_cloud_pii=True
    )

@app.post("/toggle-tabpfn-api")
def toggle_tabpfn_api_endpoint(enable: Optional[bool] = None):
    """
    Toggle TabPFN Cloud API vs Local mode.
    """
    if enable is not None:
        settings.ENABLE_TABPFN_API = enable
    else:
        settings.ENABLE_TABPFN_API = not settings.ENABLE_TABPFN_API

    settings.TABPFN_MODE = "CLIENT" if settings.ENABLE_TABPFN_API else "LOCAL"
    return {
        "status": "success",
        "enable_tabpfn_api": settings.ENABLE_TABPFN_API,
        "tabpfn_mode": settings.TABPFN_MODE
    }

@app.get("/observability")
def observability_endpoint():
    """
    Retrieve logged latencies and token counts.
    """
    return logger.get_summary()
