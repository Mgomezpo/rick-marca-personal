# ADR-001: Despliegue en DigitalOcean Droplet con Docker y Gestión de Secretos en Runtime

## Estado
Aceptado (Accepted)

## Fecha
2026-10-14

## Contexto
El motor **RICK 2.0 Multitenant** integra múltiples canales y modelos de lenguaje:
- **WhatsApp Cloud API:** Requiere un servidor HTTP escuchando permanentemente (FastAPI en puerto 8000) para recibir webhooks con respuesta `<200ms ACK`.
- **Telegram Bot API:** Opera mediante *Long Polling* asíncrono para recibir comandos y notas de voz (`.ogg`/`.oga`).
- **Modelos de IA:** Conexión hacia OpenAI (`gpt-4o`, `gpt-4o-mini`) para orquestación y redacción, y Google Gemini para transcripción multimodal de audio.
- **Persistencia:** Supabase Postgres gestiona el aislamiento multitenant, el Virtual File System (VFS), memorias y telemetría de costos.

### Restricciones y Riesgos Identificados
1. **Seguridad de Secretos:** Las API Keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `TELEGRAM_BOT_TOKEN`, `WHATSAPP_TOKEN`) jamás deben empaquetarse en imágenes Docker (`COPY . .`) ni subirse a repositorios de código.
2. **Ciclo de Vida de Procesos:** Telegram Long Polling requiere un proceso demonio 24/7 continuo, incompatible con plataformas Serverless que se apagan por inactividad.
3. **Resiliencia Operativa:** Si un servicio falla o la máquina se reinicia, el motor debe levantarse de forma autónoma.

## Decisión
Desplegar RICK en una máquina virtual dedicada (**DigitalOcean Droplet**) utilizando **Docker Compose**, separando las responsabilidades en dos servicios orquestados bajo la misma red:

1. **`rick-api`:** Servidor FastAPI en `0.0.0.0:8000` con middlewares de seguridad, métricas RED y receptor de webhooks de WhatsApp y endpoints de simulación.
2. **`rick-telegram`:** Worker continuo de Telegram con despacho asíncrono y transcripción de notas de voz.

### Estrategia de Gestión de Secretos (Runtime Injection)
- Se añade un `.dockerignore` estricto que excluye `.env*`, `.git`, caches y temporales del contexto de compilación.
- En el Droplet de producción, el archivo `.env` se aprovisiona manualmente o mediante CI Secrets con permisos restringidos (`chmod 600 .env`).
- Docker Compose inyecta las variables en memoria RAM al instanciar los contenedores (`env_file: .env`).

## Arquitectura de Conexiones

```
[ Usuarios WhatsApp ] ──► [ Nginx / SSL (443) ] ──► [ rick-api:8000 ]
                                                          │
[ Usuarios Telegram ] ◄────────(Long Polling)─────── [ rick-telegram ]
                                                          │
                                                          ▼
                                            ┌───────────────────────────┐
                                            │ Orquestador RICK & VFS    │
                                            └─────────────┬─────────────┘
                                                          │
                             ┌────────────────────────────┼────────────────────────────┐
                             ▼                            ▼                            ▼
                    [ OpenAI GPT-4o ]             [ Google Gemini ]          [ Supabase Postgres ]
                    (Razonamiento/Tools)           (Audio / Embeddings)         (Tenant DB / VFS)
```

## Alternativas Consideradas

### 1. Serverless (Google Cloud Run / AWS Lambda)
- **Ventajas:** Escalado a cero, bajo costo en bajo tráfico.
- **Desventajas:** El bot de Telegram en Long Polling requiere un proceso activo ininterrumpido. Para Serverless se requeriría configurar Webhooks de Telegram con dominio HTTPS público adicional, lo cual agrega fricción.
- **Veredicto:** Descartado para la fase actual; el Droplet unifica API y Bot con costo fijo predecible ($6-$12 USD/mes).

### 2. Bare-Metal (Python nativo con systemd en el Droplet)
- **Ventajas:** No requiere capas de virtualización Docker.
- **Desventajas:** Dependencias de sistema propensas a diferencias entre entornos, mayor dificultad para replicar o migrar el droplet.
- **Veredicto:** Descartado. Docker garantiza paridad exacta entre desarrollo local y producción.

## Consecuencias y Guía de Operaciones en Producción

### Despliegue Inicial en el Droplet
```bash
# 1. Conectarse al Droplet
ssh root@<IP_DEL_DROPLET>

# 2. Clonar el repositorio
git clone <URL_REPOSITORIO> rick-engine
cd rick-engine

# 3. Crear el archivo .env protegido
cp .env.example .env
nano .env   # Pegar credenciales reales
chmod 600 .env

# 4. Construir y levantar en segundo plano
docker compose up -d --build
```

### Comandos de Mantenimiento
* **Ver logs en tiempo real:**
  ```bash
  docker compose logs -f --tail=100
  ```
* **Ver estado de salud:**
  ```bash
  curl http://localhost:8000/health
  ```
* **Actualizar a la última versión:**
  ```bash
  git pull origin main
  docker compose up -d --build
  ```
