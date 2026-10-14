# Registro de Conexiones y Herramientas del Taller (RICK 2.0)

Este documento mantiene el inventario vivo de los servicios y herramientas del motor multitenant de RICK.

---

## 🧠 1. Modelos de Lenguaje & Razonamiento

| Proveedor | Variable de Entorno | Estado | Rol en el Sistema |
| :--- | :--- | :--- | :--- |
| **OpenAI (Principal)** | `OPENAI_API_KEY` | 🟢 Activo | Motor principal de conversación y Function Calling (`gpt-4o`, fallback `gpt-4o-mini`). |
| **Google GenAI (Fallback & Audio)** | `GEMINI_API_KEY` | 🟢 Activo | Transcripción de notas de voz en Telegram, embeddings y fallback de orquestación. |

---

## 🗄️ 2. Base de Datos & Almacenamiento Multitenant

| Recurso | Tipo | Estado | Propósito |
| :--- | :--- | :--- | :--- |
| **Supabase Postgres** | Nube | Primario | Almacena `user_profiles`, `brand_assets`, `pieces`, `rick_threads`, `agent_telemetry`. |
| **Virtual File System (VFS)** | Híbrido | Activo | Expone una interfaz tipo filesystem sobre las tablas de Supabase por cada `user_id`. |
| **Canon Filosófico (`brain/`)** | Local | Primario | 81 capítulos y principios canónicos de Rick Rubin inyectados en runtime. |

---

## 📲 3. Canales de Comunicación

| Canal | Adaptador | Variable de Entorno | Estado |
| :--- | :--- | :--- | :--- |
| **Telegram Bot** | `src/services/telegram_bot.py` | `TELEGRAM_BOT_TOKEN` | 🟢 Operativo (Long Polling & Audio Handler) |
| **WhatsApp Cloud API** | `src/api/routers/webhook.py` | `WHATSAPP_TOKEN`, `META_APP_SECRET` | 🟢 Operativo (<200ms ACK + Background Worker) |
| **Simulación REST** | `POST /api/chat-simulation` | Ninguna requerida | 🟢 Para testing automatizado y depuración local |

---

## 👁️ 4. Inteligencia de Redes & Scraping (Opcional)

| Capacidad | Variable en .env | Estado | Propósito |
| :--- | :--- | :--- | :--- |
| **Apify / RapidAPI** | `APIFY_API_TOKEN` / `RAPIDAPI_KEY` | Opcional | Extracción y auditoría de perfiles y reels de Instagram. |
