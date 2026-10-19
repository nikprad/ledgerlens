"""
Observability Logger for LedgerLens.
Logs step latencies, token counts, and execution metrics to a local JSON file.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.config import settings

LOG_FILE = settings.OBSERVABILITY_LOG_FILE

class ObservabilityLogger:
    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
            except Exception:
                pass

    def log_step(
        self,
        step_name: str,
        latency_ms: float,
        token_count: Optional[int] = 0,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a single execution step to the JSON log."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step_name,
            "latency_ms": round(latency_ms, 2),
            "token_count": token_count or 0,
            "status": status,
            "metadata": metadata or {},
            "error": error
        }

        try:
            records = []
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    try:
                        records = json.load(f)
                    except Exception:
                        records = []
            records.append(record)
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            print(f"[Observability Error] Could not write to log: {e}")

        return record

    def get_summary(self) -> Dict[str, Any]:
        """Compute aggregate latency and token metrics."""
        if not os.path.exists(self.log_file):
            return {"total_steps": 0, "total_latency_ms": 0, "total_tokens": 0, "steps": {}}
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            return {"total_steps": 0, "total_latency_ms": 0, "total_tokens": 0, "steps": {}}

        total_latency = sum(r.get("latency_ms", 0) for r in records)
        total_tokens = sum(r.get("token_count", 0) for r in records)
        by_step = {}
        for r in records:
            step = r.get("step", "unknown")
            if step not in by_step:
                by_step[step] = {"count": 0, "total_ms": 0.0, "total_tokens": 0}
            by_step[step]["count"] += 1
            by_step[step]["total_ms"] += r.get("latency_ms", 0)
            by_step[step]["total_tokens"] += r.get("token_count", 0)

        for step in by_step:
            c = by_step[step]["count"]
            by_step[step]["avg_ms"] = round(by_step[step]["total_ms"] / c, 2) if c else 0

        return {
            "total_steps": len(records),
            "total_latency_ms": round(total_latency, 2),
            "total_tokens": total_tokens,
            "by_step": by_step
        }

logger = ObservabilityLogger()
