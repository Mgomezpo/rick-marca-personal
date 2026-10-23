# ADR-005: Aislamiento Multi-Tenant y Persistencia de Sesión

## Status
Accepted

## Date
2026-10-19

## Context
El sistema RICK debe atender a múltiples creadores de contenido simultáneamente a través de WhatsApp. Cada creador tiene su propio perfil, ADN de voz, pilares de contenido, historial de aprendizajes procedimentales (`procedural_learnings`), borradores de guiones (`pieces`) y contexto de conversación multi-turno.
Se requerían tres garantías críticas:
1. **Aislamiento Total (Zero Cross-Contamination):** Ningún creador debe poder acceder, consultar o contaminar el contexto, guiones o aprendizajes de otro.
2. **Persistencia Multi-Turno en WhatsApp:** Debido a que Meta Cloud API envía cada mensaje entrante como una llamada HTTP POST independiente sin estado, el motor debe persistir y reconstruir el historial conversacional entre webhook y webhook.
3. **Despacho Outbound Nativo:** Enviar la respuesta del motor de vuelta al teléfono del creador sin depender de plataformas intermedias de pago como Twilio.

## Decision
Implementar el repositorio centralizado `SupabaseRepository` (`src/db/repository.py`) y el despachador nativo en `src/api/webhook.py`:
1. **Identidad del Tenant vía Teléfono:**
   - Cada número de WhatsApp entrante se mapea a un identificador canónico `user_id = f"wa_{sender_phone}"`.
2. **Scoping Estricto por `user_id`:**
   - Todos los métodos del repositorio (`get_creator_profile`, `get_learnings`, `save_learning`, `save_piece`, `save_message`, `get_conversation`, `clear_conversation`) exigen el parámetro `user_id` y aplican filtros obligatorios `.eq("user_id", user_id)` en PostgreSQL con Row-Level Security (RLS).
3. **Persistencia Conversacional Multi-Turno:**
   - Cada turno de usuario y de asistente se persiste cronológicamente en el repositorio.
   - Al recibir un nuevo webhook, se recupera el hilo completo del creador, permitiendo que la mayéutica socrática y la extracción de historias mantengan coherencia a lo largo del tiempo.
4. **Despachador Outbound Directo a Meta Graph API:**
   - La función `send_whatsapp_message` envía mensajes directamente al endpoint oficial `https://graph.facebook.com/v19.0/{phone_number_id}/messages` autenticado con Bearer Token de Meta Cloud API, con simulación transparente para entornos de test locales.

## Alternatives Considered

### 1. Despliegue de un contenedor / proceso aislado por cada usuario
- **Pros:** Aislamiento a nivel de sistema operativo.
- **Cons:** Costo de infraestructura prohibitivo, operaciones complejas, inicio lento en frío y desperdicio masivo de recursos de cómputo para cientos de creadores.
- **Rejected:** Inviable económicamente para una arquitectura SaaS escalable.

### 2. Estado en memoria RAM del servidor sin persistencia en base de datos
- **Pros:** Rápido de programar.
- **Cons:** Si el servidor se reinicia, se escala horizontalmente a múltiples réplicas o se despliega una nueva versión, se pierde todo el contexto conversacional del usuario.
- **Rejected:** Incompatible con producción.

## Consequences
- **Positivas:**
  - Garantía verificada de aislamiento multi-tenant probada en `tests/test_api_webhook.py::test_supabase_multitenant_isolation`.
  - Continuidad fluida de conversaciones en WhatsApp a través de múltiples mensajes.
  - Cero costos adicionales de intermediarios gracias a la conexión directa con Meta Cloud API.
- **Compromisos:**
  - Requiere credenciales de Supabase válidas en producción (con fallback simulado seguro para testing automatizado).
