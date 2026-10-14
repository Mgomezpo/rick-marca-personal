import logging
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.config import config
from src.core.metrics import metrics_tracker
from src.core.observability import (
    generate_correlation_id,
    set_request_context,
    get_correlation_id,
    log_event,
)
from src.api.routers.webhook import router as webhook_router, orchestrator, db_service

logger = logging.getLogger("rick.main")

app = FastAPI(
    title="RICK Multi-Tenant Agent Engine",
    description="Motor de Agentes y Mentor Creativo para WhatsApp & Telegram (Inspirado en Rick Rubin)",
    version="2.0.0",
)

# Configuración segura de CORS
is_wildcard = config.ALLOWED_ORIGINS == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de Correlation ID y Headers de Seguridad HTTP (OWASP A05)
@app.middleware("http")
async def correlation_and_security_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or generate_correlation_id("http")
    set_request_context(correlation_id=corr_id, entry_point="http_api")

    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Registrar webhook de WhatsApp
app.include_router(webhook_router, tags=["WhatsApp Webhook"])

# -----------------------------------------------------------------------------
# Endpoint de Salud y Estado (RED Metrics)
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"])
def health_check():
    """
    Retorna el estado del sistema enriquecido con métricas RED (Rate, Errors, Duration)
    y latencia agregada.
    """
    metrics = metrics_tracker.get_summary()
    return {
        "status": "online",
        "engine": "RICK 2.0 Multitenant",
        "orchestrator_model": config.ORCHESTRATOR_MODEL,
        "writer_model": config.WRITER_MODEL,
        "supabase_connected": bool(config.SUPABASE_URL),
        "whatsapp_configured": bool(config.WHATSAPP_PHONE_NUMBER_ID and config.WHATSAPP_TOKEN),
        "metrics": metrics,
    }

@app.get("/metrics", tags=["Sistema"])
def get_metrics():
    """Retorna las métricas RED operativas en detalle."""
    return metrics_tracker.get_summary()

# -----------------------------------------------------------------------------
# Simulador de Conversación Local (para probar sin Meta Cloud API)
# -----------------------------------------------------------------------------
class ChatSimulationRequest(BaseModel):
    phone_number: str
    message: str
    display_name: str = "Creador Test"

class ChatSimulationResponse(BaseModel):
    user_id: str
    reply: str
    thread_id: str
    active_topic: str | None = None
    is_new_user: bool
    correlation_id: str | None = None

@app.post("/api/chat-simulation", response_model=ChatSimulationResponse, tags=["Testing"])
def simulate_chat(req: ChatSimulationRequest):
    """
    Permite probar el flujo completo de WhatsApp desde Postman, Swagger o cURL
    sin necesidad de conectar la cuenta de Meta de inmediato.
    """
    corr_id = generate_correlation_id("sim")
    set_request_context(correlation_id=corr_id, entry_point="simulation")

    user_id, identity, is_new = db_service.get_or_create_whatsapp_identity(
        phone_e164=req.phone_number,
        display_name=req.display_name
    )

    set_request_context(user_id=user_id)

    thread = db_service.get_or_create_whatsapp_thread(user_id)
    thread_id = thread.get("id")

    log_event(
        logger,
        logging.INFO,
        event="simulation_turn_started",
        message=f"Simulación para {req.phone_number} ({req.display_name})",
        user_id=user_id,
        phone=req.phone_number
    )

    # Guardar mensaje en transcript
    db_service.append_thread_message(thread_id, "user", req.message)

    # Procesar con RICK
    reply = orchestrator.process_message(
        user_message=req.message,
        user_id=user_id,
        channel="simulation",
        thread_id=thread_id,
        correlation_id=corr_id
    )

    # Guardar respuesta en transcript
    db_service.append_thread_message(thread_id, "assistant", reply)

    # Estado activo
    mem = db_service.get_active_memory(user_id)
    active_topic = mem.get("state", {}).get("active_topic")

    log_event(
        logger,
        logging.INFO,
        event="simulation_turn_completed",
        message=f"Simulación completada para {user_id}",
        user_id=user_id
    )

    return ChatSimulationResponse(
        user_id=user_id,
        reply=reply,
        thread_id=thread_id,
        active_topic=active_topic,
        is_new_user=is_new,
        correlation_id=corr_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=config.DEBUG)
