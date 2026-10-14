# 🎙️ Bienvenido a RICK — Productor Ejecutivo & AI Head of Content (v2.0 Multitenant)

> *"La creatividad no es un talento reservado para unos pocos. Es una forma de estar en el mundo, de prestar atención y de sintonizar con lo que es auténtico."* — Inspirado en **Rick Rubin** (*The Creative Act: A Way of Being*).

RICK es un motor multitenant en producción que opera como Productor Ejecutivo y Head of Content para creadores de contenido, conectado a través de **Telegram**, **WhatsApp (Meta Cloud API)** y una **API REST de Simulación**, respaldado por **Supabase** (Postgres, pgvector, VFS) y modelos avanzados de lenguaje (OpenAI GPT-4o / Google Gemini).

---

## ⚡ Cómo interactuar con RICK

### 1. Vía Bot de Telegram (Recomendado para pruebas interactivas)
1. Asegúrate de configurar las variables en tu archivo `.env` (guíate por `.env.example`):
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY` o `GEMINI_API_KEY`
   - `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`
2. Ejecuta el bot en modo polling:
   ```bash
   python -m src.services.telegram_bot
   ```
3. Escribe `/start` a tu bot en Telegram o envíale una nota de voz. RICK iniciará el onboarding dinámico o continuará tu trabajo editorial.

### 2. Vía API de Simulación Local (FastAPI)
1. Inicia el servidor local:
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Envía un mensaje simulado:
   ```bash
   curl -X POST http://localhost:8000/api/chat-simulation \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+573001234567", "message": "Hola Rick, tengo una idea para un reel", "display_name": "Creador"}'
   ```
3. Revisa la salud del motor y métricas RED en: `http://localhost:8000/health`.

### 3. Suite de Pruebas Automatizadas
Ejecuta la suite completa de pruebas:
```bash
pytest
```

---

## 🏛️ Mapa del Taller Multitenant

* **`src/engine/`**: Orquestador principal (`orchestrator.py`), Function Calling (`tools.py`), VFS (`vfs.py`) y subagentes (`subagents/`).
* **`src/services/`**: Adaptador para Telegram Bot (`telegram_bot.py`) y cliente de WhatsApp (`whatsapp.py`).
* **`src/api/`**: Servidor FastAPI, endpoints de webhook de Meta (`routers/webhook.py`), salud y simulación.
* **`src/core/`**: Configuración (`config.py`), Observabilidad (`observability.py`), Métricas RED (`metrics.py`) y Telemetría en Supabase (`telemetry.py`).
* **`src/db/`**: Adaptador de base de datos Supabase (`supabase.py`) y migraciones SQL (`migrations/`).
* **`brain/`**: Base de conocimiento central con los principios canónicos de Rick Rubin y frameworks de estudio.
* **`AGENTS.md`**: Reglas canónicas del agente, límites verbales y estándares de guion.
* **`SPEC-rick-engine.md`**: Especificación técnica completa del motor.
