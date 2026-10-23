"""FastAPI application for RICK Multitenant Agent Engine."""
import os
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.webhook import router as webhook_router
from src.db.repository import SupabaseRepository

app = FastAPI(
    title="RICK Multitenant Agent Engine",
    description="Autonomous Brand Strategist with Graph & Loop Engineering for WhatsApp",
    version="1.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Webhook router
app.include_router(webhook_router)

repo = SupabaseRepository()


@app.get("/health", tags=["Health"])
def health_check():
    """Production health check verifying database and system memory status."""
    db_ok = repo.is_healthy()
    memory_info = psutil.virtual_memory()

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "rick-multitenant",
        "version": "1.2.0",
        "database": "connected" if db_ok else "disconnected",
        "memory": {
            "total_mb": round(memory_info.total / (1024 * 1024), 1),
            "available_mb": round(memory_info.available / (1024 * 1024), 1),
            "percent_used": memory_info.percent,
        },
    }


from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.services.proactive_worker import run_proactive_cycle_for_tenant
from src.api.webhook import send_whatsapp_message


class ProactiveTickRequest(BaseModel):
    """Payload for invoking a proactive cycle for a creator."""
    user_id: str
    trigger_type: str = Field(default="market_spark", description="brand_health_audit, market_spark, trench_inquiry")
    phone_number: Optional[str] = Field(default=None, description="Optional phone number to dispatch WhatsApp")
    proactive_context: Optional[Dict[str, Any]] = Field(default_factory=dict)


@app.post("/api/proactive/tick", tags=["Proactive Loops"])
def proactive_tick(payload: ProactiveTickRequest):
    """
    Triggers an autonomous proactive cycle for a tenant (called via Cron / Timer).
    Passes through the Anti-Spam Governor before sending any WhatsApp message.
    """
    profile = repo.get_creator_profile(payload.user_id)
    result = run_proactive_cycle_for_tenant(
        user_id=payload.user_id,
        trigger_type=payload.trigger_type,
        creator_profile=profile,
        proactive_context=payload.proactive_context,
    )

    # If approved and message produced, persist to conversation history for multi-turn context
    if result["dispatched"] and result.get("message"):
        from src.graph.state import ConversationMessage
        repo.save_message(
            payload.user_id,
            ConversationMessage(
                role="assistant",
                content=result["message"],
            ),
        )
        if payload.phone_number:
            send_whatsapp_message(to_phone=payload.phone_number, text=result["message"])

    return result


