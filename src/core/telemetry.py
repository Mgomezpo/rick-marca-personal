import time
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger("rick.telemetry")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Precios aproximados por millón de tokens (USD)
# Pricing por millón de tokens (USD)
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
        channel: str = "whatsapp",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        cost = estimate_cost(model_name, prompt_tokens, completion_tokens)
        meta = metadata or {}
        
        logger.info(
            f"⚡ [Telemetry] Phase={phase} | Model={model_name} | Latency={latency_ms}ms "
            f"| Tokens={prompt_tokens}+{completion_tokens} | Cost=${cost:.6f} | User={user_id or 'anon'}"
        )

        if self.supabase and user_id:
            try:
                self.supabase.table("agent_telemetry").insert({
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "channel": channel,
                    "phase": phase,
                    "model_name": model_name,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "metadata": meta,
                }).execute()
            except Exception as e:
                logger.warning(f"No se pudo guardar la telemetría en Supabase: {e}")

        return cost
