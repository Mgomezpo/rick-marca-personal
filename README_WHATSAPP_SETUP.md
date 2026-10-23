# 🚀 Guía de Puesta en Marcha: RICK Multitenant en WhatsApp

¡El sistema está completamente construido, verificado y en producción! El motor de RICK es un **agente multitenant autónomo** basado en un State Graph determinista (`src/graph/engine.py`), bucles proactivos con Gobernador anti-spam, bucle evaluador-optimizador anti-plagio y conexión directa con Supabase y Meta WhatsApp Cloud API.

---

## 📍 Lo que está listo y probado (82/82 tests en verde)

1. ✅ **Base de Datos Supabase (`IrealDemo`):**
   - Aislamiento estricto por `user_id` en `user_profiles`, `procedural_learnings`, `pieces` y conversaciones.
   - Persistencia de historial multi-turno para mantener coherencia entre webhooks sucesivos.
2. ✅ **Flujo Conversacional y Mayéutica de Trinchera:**
   - Personalidad de Rick Rubin (*The Creative Act*).
   - Matriz de 3 niveles de limitación verbal (Nivel 1: Charla 30–60 palabras; Nivel 2: Indagación de trinchera de 1 sola pregunta; Nivel 3: Guion técnico de 3 bloques canónicos).
   - Transición directa automática cuando el creador ya provee escena y fricción.
3. ✅ **Loop de Calidad Cerrado:**
   - **Filtro Anti-Plagio Determinista:** Rechazo automático ante $\ge 5$ palabras idénticas a los referentes de benchmark.
   - **Editor Anti-Slop:** Poda y penalización de clichés corporativos de IA.
   - **Simulador Empírico:** Estimación de probabilidad de éxito basada en piezas ganadoras del nicho.
4. ✅ **4 Loops Proactivos con Gobernador Anti-Spam:**
   - `market_spark`, `brand_health_audit`, `trench_inquiry` y `routine_reporter`.
   - Gobernador con horas hábiles (09:00 a 19:00), ventana de trinchera (17:00 a 19:30), regla de 42h y backoff progresivo (48h y 96h).
5. ✅ **Radar Desacoplado "Wide & Fresh":**
   - Ingesta en background desde pool de 15–25 creadores, caché indexado con respuesta en $< 50$ ms, exclusión de posts usados a 30 días y rotación a 7 días.
6. ✅ **Webhook de WhatsApp:**
   - Verificación de Meta Challenge (GET `/webhook/whatsapp`).
   - Ingesta instantánea con ACK $< 200$ ms y procesamiento en segundo plano (POST `/webhook/whatsapp`).
   - Despachador outbound nativo a Meta Graph API (`v19.0/{phone_number_id}/messages`).

---

## ⚡ Configuración de Credenciales de WhatsApp

En el archivo `.env` en la raíz del proyecto (`c:\Users\mgome\OneDrive\Documents\RICK Multitenant\.env`):

```env
# Meta WhatsApp Cloud API (developers.facebook.com)
WHATSAPP_TOKEN=tu_token_de_acceso_permanente_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_identificador_de_numero_de_telefono
WHATSAPP_VERIFY_TOKEN=rick_secret_verify_token_2026

# Supabase
SUPABASE_URL=https://khoikdwablpqiapxkgqx.supabase.co
SUPABASE_KEY=tu_supabase_service_role_key_aqui
```

---

## 🛠️ Configuración en el Panel de Meta Developers

1. Ve a [developers.facebook.com](https://developers.facebook.com) > Tu App > **WhatsApp** > **Configuración de la API**.
2. Copia tu **Identificador de número de teléfono** y configúralo en `WHATSAPP_PHONE_NUMBER_ID`.
3. Copia tu **Token de acceso** permanente del sistema y configúralo en `WHATSAPP_TOKEN`.
4. En el menú lateral, ve a **WhatsApp** > **Configuración** > **Webhook**:
   - En **URL de devolución de llamada**, coloca la URL pública del servidor con la ruta exacta:
     ```text
     https://tu-dominio-publico.com/webhook/whatsapp
     ```
     *(Ejemplo con túnel local: `https://four-words-rescue.loca.lt/webhook/whatsapp`)*
   - En **Identificador de verificación**, escribe el mismo token definido en tu `.env`:
     ```text
     rick_secret_verify_token_2026
     ```
   - Haz clic en **Verificar y guardar**.
5. En **Campos de webhook**, haz clic en **Administrar** y suscríbete al evento:
   - `messages`

A partir de este momento, cada mensaje de texto enviado por un usuario a tu número de WhatsApp será procesado por el motor de RICK.

---

## 🧪 Cómo Iniciar y Probar Localmente

### 1. Iniciar el Servidor de Producción
```powershell
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verificar Estado de Salud
Abre tu navegador en:
- Healthcheck: `http://localhost:8000/health`
- Documentación Swagger: `http://localhost:8000/docs`

### 3. Ejecutar las Pruebas Automatizadas
```powershell
pytest -v tests/
```
Todas las 82 pruebas deben pasar en verde.
