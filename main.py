import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.core.config import config
from src.api.routers.webhook import router as webhook_router, orchestrator, db_service

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rick.main")

app = FastAPI(
    title="RICK Multi-Tenant Agent Engine",
    description="Motor de Agentes y Mentor Creativo para WhatsApp (Inspirado en Rick Rubin & Hermes Agent)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar webhook de WhatsApp
app.include_router(webhook_router, tags=["WhatsApp Webhook"])

# -----------------------------------------------------------------------------
# Endpoint de Salud y Estado
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"])
def health_check():
    return {
        "status": "online",
        "engine": "RICK 2.0 Multitenant",
        "orchestrator_model": config.ORCHESTRATOR_MODEL,
        "writer_model": config.WRITER_MODEL,
        "supabase_connected": bool(config.SUPABASE_URL),
        "whatsapp_configured": bool(config.WHATSAPP_PHONE_NUMBER_ID and config.WHATSAPP_TOKEN),
    }

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

@app.post("/api/chat-simulation", response_model=ChatSimulationResponse, tags=["Testing"])
def simulate_chat(req: ChatSimulationRequest):
    """
    Permite probar el flujo completo de WhatsApp desde Postman, Swagger o cURL
    sin necesidad de conectar la cuenta de Meta de inmediato.
    """
    user_id, identity, is_new = db_service.get_or_create_whatsapp_identity(
        phone_e164=req.phone_number,
        display_name=req.display_name
    )

    thread = db_service.get_or_create_whatsapp_thread(user_id)
    thread_id = thread.get("id")

    # Guardar mensaje en transcript
    db_service.append_thread_message(thread_id, "user", req.message)

    # Procesar con RICK
    reply = orchestrator.process_message(
        user_message=req.message,
        user_id=user_id,
        channel="simulation",
        thread_id=thread_id
    )

    # Guardar respuesta en transcript
    db_service.append_thread_message(thread_id, "assistant", reply)

    # Estado activo
    mem = db_service.get_active_memory(user_id)
    active_topic = mem.get("state", {}).get("active_topic")

    return ChatSimulationResponse(
        user_id=user_id,
        reply=reply,
        thread_id=thread_id,
        active_topic=active_topic,
        is_new_user=is_new
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=config.DEBUG)
