# Security & Hardening Policy: RICK Multitenant Agent Engine

> **Versión:** 1.0.0  
> **Fecha:** Octubre 2026  
> **Auditoría:** `security-auditor` + `web-performance-auditor`  

---

## 🛡️ 1. Modelo de Amenazas (STRIDE) y Límites de Confianza

| Amenaza | Riesgo Mitigado | Control Implementado |
| :--- | :--- | :--- |
| **Spoofing** | Suplantación de Meta / WhatsApp | Verificación de token `hub.verify_token` y validación estricta de estructura payload. |
| **Tampering** | Alteración de estado o guiones en tránsito | Conexión forzada HTTPS / TLS 1.3 y tipado inmutable en `GraphState`. |
| **Repudiation** | Desconocimiento de eventos procesados | Logs estructurados JSON con timestamp y ID único de mensaje (`wamid`). |
| **Information Disclosure** | Fuga de datos entre usuarios (Cross-Tenant) | Aislamiento estricto RLS por `user_id` en Supabase; un usuario jamás accede a datos de otro. |
| **Denial of Service** | Bloqueo del webhook por carga computacional | ACK inmediato en $< 200\text{ ms}$ delegando el grafo completo a `BackgroundTasks`. |
| **Elevation of Privilege** | Acceso a endpoints administrativos sin permisos | Todas las mutaciones de perfiles requieren `user_id` verificado. |

---

## 🔒 2. Aislamiento Multi-Tenant (Supabase `IrealDemo`)

- **Partición estricta por `user_id`:** Todas las tablas (`user_profiles`, `procedural_learnings`, `pieces`, `brand_referents`) están indexadas por `user_id`.
- **Zero Cross-Contamination:** En runtime, el repositorio `SupabaseRepository` solo expone métodos que exigen `user_id` explícito (`eq("user_id", user_id)`), garantizando que ningún hilo, memoria o guion sea visible fuera de su tenant.
- **RLS (Row Level Security):** Políticas activas en PostgreSQL que impiden consultas cruzadas incluso si el cliente intentara inyectar filtros externos.

---

## 🔑 3. Gestión de Secretos y Variables de Entorno

- **Cero secretos en código:** Todos los tokens (`WHATSAPP_TOKEN`, `SUPABASE_KEY`, `OPENAI_API_KEY`) provienen de variables de entorno del sistema operativo o `.env` protegido.
- **Protección de Git:** `.gitignore` excluye `.env`, `.env.*`, `*.pem`, `*.key`, `.venv/` y `.agents/`.
- **Plantilla Segura:** `.env.example` provee la guía de configuración con valores ficticios.

---

## ⚡ 4. SLA de Rendimiento y Latencia

- **SLA de WhatsApp:** ACK devuelto en menos de **200 ms** (promedio verificado en pruebas unitarias e integración: $< 15\text{ ms}$).
- **Procesamiento Asíncrono:** La generación técnica de guiones, el loop anti-plagio y la auditoría de cuenta se ejecutan en segundo plano sin degradar la recepción de nuevos webhooks.

---

## 🔬 5. Auditoría de Dependencias

- Dependencias inspeccionadas con `pip-audit`.
- FastAPI, Pydantic v2, Uvicorn y Supabase fijados en versiones estables y mantenidas.
