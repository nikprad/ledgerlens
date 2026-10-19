"""
Data models and schemas for LedgerLens.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class TransactionItem(BaseModel):
    id: Optional[int] = None
    date: str = Field(description="Normalized date in YYYY-MM-DD format")
    party: str = Field(description="Name of customer, vendor, or counter party")
    item: str = Field(description="Item name or service description")
    quantity: float = Field(default=1.0, description="Quantity of items")
    amount: float = Field(description="Total transaction amount")
    currency: str = Field(default="INR", description="Currency code (e.g. INR)")
    type: Literal["sale", "expense"] = Field(description="Transaction type: sale or expense")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (0 to 1)")
    flagged: bool = Field(default=False, description="Flagged for human review or anomaly")
    flag_reason: Optional[str] = Field(default=None, description="Reason why the row is flagged")

    @field_validator("type", mode="before")
    def normalize_type(cls, v):
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if any(w in v_lower for w in ["sale", "jama", "income", "credit", "जमा"]):
                return "sale"
            if any(w in v_lower for w in ["exp", "kharch", "debit", "खर्च", "खर्चा"]):
                return "expense"
        return v

class RawExtractionOutput(BaseModel):
    transactions: List[TransactionItem] = Field(default_factory=list)
    raw_text: Optional[str] = None

class ExtractionResponse(BaseModel):
    status: str
    image_name: str
    items: List[TransactionItem]
    latency_ms: float
    token_count: Optional[int] = 0
    retried: bool = False
    model: str

class ValidationResult(BaseModel):
    valid_items: List[TransactionItem]
    dropped_duplicates: int
    flagged_items_count: int
    summary_message: str

class AnomalyFlag(BaseModel):
    transaction_id: Optional[int] = None
    item: str
    party: str
    amount: float
    type: str
    date: str
    reason: str
    score: float = 0.0

class AnomalyResponse(BaseModel):
    total_analyzed: int
    anomalies_found: int
    anomalies: List[AnomalyFlag]
    local_execution: bool

class ForecastPoint(BaseModel):
    date: str
    predicted_net_cash_flow: float
    lower_bound: float
    upper_bound: float

class ForecastResponse(BaseModel):
    status: str
    message: str
    historical_points_count: int
    forecast_points: List[ForecastPoint]
    model_used: str
    local_execution: bool

class FinancialSummary(BaseModel):
    period: str
    total_sales: float
    total_expenses: float
    net_cash_flow: float
    plain_language_summary: str
    generated_by: str

class PrivacyStatus(BaseModel):
    ollama_endpoint: str
    ollama_model: str
    ollama_is_local: bool
    tabpfn_mode: str
    tabpfn_api_enabled: bool
    storage_type: str
    data_egress_status: str
    zero_cloud_pii: bool
