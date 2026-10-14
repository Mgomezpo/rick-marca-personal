import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from src.core.metrics import metrics_tracker
from src.core.observability import (
    get_correlation_id,
    get_entry_point,
    get_user_id,
    log_event,
)

logger = logging.getLogger("rick.telemetry")

# Precios aproximados por millón de tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gemini-2.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
    "gemini-2.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
    "text-embedding-004": {"input": 0.025 / 1_000_000, "output": 0.0},
}

def estimate_cost(model_name: str, prompt_tokens: Optional[int], completion_tokens: Optional[int]) -> float:
    p_tokens = prompt_tokens or 0
    c_tokens = completion_tokens or 0
    for model_key, prices in MODEL_PRICING.items():
        if model_key in model_name.lower():
            cost = (p_tokens * prices["input"]) + (c_tokens * prices["output"])
            return round(cost, 6)
    # Default fallback rate
    return round((p_tokens * 0.10 + c_tokens * 0.40) / 1_000_000, 6)

class TelemetryTracker:
    def __init__(self, supabase_client: Any = None):
        self.supabase = supabase_client

    def log_turn(
        self,
        phase: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> float:
        cost = estimate_cost(model_name, prompt_tokens, completion_tokens)
        meta = dict(metadata or {})
        
        # Enlazar con contexto de observabilidad
        resolved_channel = channel or get_entry_point() or "unknown"
        resolved_user = user_id or get_user_id()
        resolved_corr_id = meta.get("correlation_id") or get_correlation_id()

        meta["status"] = status
        meta["correlation_id"] = resolved_corr_id
        meta["entry_point"] = resolved_channel
        if error_type:
            meta["error_type"] = error_type
        if error_message:
            meta["error_message"] = error_message

        # Registrar métricas en memoria RED
        metrics_tracker.record_request(
            channel=resolved_channel,
            duration_ms=latency_ms,
            is_error=(status != "success"),
            model=model_name
        )

        level = logging.INFO if status == "success" else logging.ERROR
        log_event(
            logger,
            level,
            event=f"telemetry_turn_{status}",
            message=f"Turno {phase} ({model_name}) {status} en {latency_ms}ms (${cost:.6f})",
            phase=phase,
            model=model_name,
            tokens_in=prompt_tokens,
            tokens_out=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            status=status,
            channel=resolved_channel,
            user_id=resolved_user or "anon"
        )

        if self.supabase and resolved_user and resolved_user != "anonymous":
            try:
                self.supabase.table("agent_telemetry").insert({
                    "user_id": resolved_user,
                    "thread_id": thread_id,
                    "channel": resolved_channel,
                    "phase": phase,
                    "model_name": model_name,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "metadata": meta,
                }).execute()
            except Exception as e:
                log_event(
                    logger,
                    logging.WARNING,
                    event="telemetry_supabase_insert_failed",
                    message=f"No se pudo guardar la telemetría en Supabase: {e}",
                    error_message=str(e)
                )

        return cost
