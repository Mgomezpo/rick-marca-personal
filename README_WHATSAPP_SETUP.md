# 🚀 Guía de Puesta en Marcha: RICK Multitenant en WhatsApp

¡Todo el sistema está construido, probado y listo! El motor de RICK ahora es un **agente multitenant autónomo** que navega su cerebro mediante un Sistema de Archivos Virtual (VFS), delega a subagentes especialistas (Guionista, Hooks, Entrevistador, Editor Anti-Slop) y se conecta directamente con Supabase (`IrealDemo`) y WhatsApp.

---

## 📍 Lo que ya está listo y probado (100% verde)

1. ✅ **Base de Datos Supabase (`IrealDemo`):**
   - Tablas aditivas creadas: `whatsapp_identities`, `rick_active_memory`, `whatsapp_messages`, `agent_telemetry`.
   - Onboarding automático: cuando un número nuevo escribe a WhatsApp, se crea su usuario en `auth.users` y el trigger existente le activa su **suscripción trial automáticamente**.
2. ✅ **Cerebro Virtual (VFS):**
   - RICK navega `/filosofia`, `/studio` y `/skills` desde el repositorio de código.
   - RICK lee `/creator`, `/memorias` y `/produccion` dinámicamente desde Supabase para cada usuario sin mezclar datos.
3. ✅ **Subagentes Especialistas:**
   - **Guionista:** Estructura guiones en 5 actos por beats (dirección de escena, intención emocional, sin teleprompter) y guarda la pieza en la tabla `pieces`.
   - **Hook Writer:** Diseña 5 ganchos de alta retención basados en quiebre cognitivo.
   - **Editor Anti-Slop:** Audita y purga clichés corporativos y frases robóticas antes de enviar a WhatsApp.
   - **Entrevistador:** Conduce la entrevista socrática inicial (una sola pregunta por turno) y sintetiza el ADN de voz en `brand_assets`.
4. ✅ **Webhook de WhatsApp:**
   - Verificación de Meta Challenge (GET).
   - Ingesta instantánea con ACK < 200ms y procesamiento en segundo plano (POST).
   - Fragmentación automática de guiones para que se lean cómodamente en el celular.
   - Soporte para transcripción de notas de voz con Gemini Multimodal.
5. ✅ **Suite de Pruebas (11/11 tests pasando):**
   - VFS, subagentes, anti-slop, webhook y simulación de chat probados con éxito.

---

## ⚡ Lo ÚNICO que te queda por hacer: Conectar WhatsApp

En el archivo `.env` (`c:\Users\mgome\OneDrive\Documents\RICK Multitenant\RICK! Guía de Marca Personal\.env`), solo debes pegar las credenciales de tu app de Meta:

```env
# Meta WhatsApp Cloud API (developers.facebook.com)
WHATSAPP_TOKEN=tu_token_de_acceso_permanente_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_identificador_de_numero_de_telefono
WHATSAPP_VERIFY_TOKEN=rick_secret_verify_token_2026
```

### ¿Cómo configurarlo en el panel de Meta?
1. Ve a [developers.facebook.com](https://developers.facebook.com) > Tu App > **WhatsApp** > **Configuración de la API**.
2. Copia tu **Identificador de número de teléfono** y pégalo en `WHATSAPP_PHONE_NUMBER_ID`.
3. Copia tu **Token de acceso** temporal o permanente del sistema y pégalo en `WHATSAPP_TOKEN`.
4. En el menú lateral, ve a **WhatsApp** > **Configuración** > **Webhook**:
   - En **URL de devolución de llamada**, pon tu URL pública: `https://tu-dominio.com/webhook` (o tu túnel de ngrok si pruebas local: `https://xxxx.ngrok-free.app/webhook`).
   - En **Identificador de verificación**, escribe exactamente el mismo valor que pusiste en `.env`: `rick_secret_verify_token_2026`.
   - Haz clic en **Verificar y guardar**.
5. En **Campos de webhook**, suscríbete a `messages`.

¡Listo! A partir de ese segundo, cada mensaje o audio que llegue a ese número de WhatsApp será atendido por RICK.

---

## 🧪 Cómo probarlo LOCALMENTE ahora mismo (Sin Meta)

Si quieres chatear con RICK antes de poner el túnel de Meta:

### 1. Inicia el servidor
Doble clic en `run_server.bat` o desde la terminal:
```powershell
cd "c:\Users\mgome\OneDrive\Documents\RICK Multitenant\RICK! Guía de Marca Personal"
python -m uvicorn main:app --port 8000 --reload
```

### 2. Abre Swagger UI en tu navegador
Ve a: [http://localhost:8000/docs](http://localhost:8000/docs)

Verás el endpoint:
`POST /api/chat-simulation`

Envíale un JSON como este:
```json
{
  "phone_number": "+573001234567",
  "message": "Hola Rick, quiero empezar a crear contenido",
  "display_name": "Miguel"
}
```

Verás cómo:
1. RICK detecta que es tu primer mensaje.
2. Crea tu cuenta en Supabase con trial activo.
3. Te da la bienvenida con el tono de Rick Rubin y arranca la entrevista de voz.
4. Cuando le respondes con tus ideas, las guarda en tu cerebro y te estructura guiones por beats listos para rodar.

---

## 🚢 Despliegue a Producción (Railway / Cloud Run)

Para tenerlo 24/7 disponible para WhatsApp sin tener tu PC encendida:

- El repositorio incluye un `Dockerfile` y `requirements.txt`.
- Puedes conectar esta carpeta a **Railway** o **Google Cloud Run**:
  1. Conectar repo.
  2. Configurar las variables de entorno de `.env`.
  3. Railway te da una URL HTTPS automática (ej. `https://rick-agent.up.railway.app`).
  4. Pones esa URL en el panel de Meta Webhook: `https://rick-agent.up.railway.app/webhook`.
