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
    version="1.0.0",
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
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "memory": {
            "total_mb": round(memory_info.total / (1024 * 1024), 1),
            "available_mb": round(memory_info.available / (1024 * 1024), 1),
            "percent_used": memory_info.percent,
        },
    }
