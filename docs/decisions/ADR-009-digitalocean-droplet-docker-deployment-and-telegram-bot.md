# ADR-009: Despliegue en DigitalOcean Droplet con Docker y Orquestación de Canales (Telegram Bot y WhatsApp Webhook)

## Status
Accepted

## Date
2026-10-23

## Context
El motor **RICK Multitenant** atiende interacciones creativas a través de dos canales principales con requerimientos de red y arquitectura de procesos radicalmente diferentes:

1. **Meta WhatsApp Cloud API (Canal HTTP Reactivo):**
   - Requiere un servidor HTTP escuchando permanentemente en el puerto `8000` (FastAPI) para recibir webhooks de Meta con verificación de challenge y procesamiento con acuse de recibo inmediato (`ACK < 200 ms`).
2. **Telegram Bot API (Canal de Long Polling Asíncrono):**
   - Opera mediante una conexión persistente bidireccional (*Long Polling*) con los servidores de Telegram (`api.telegram.org`), consumiendo actualizaciones, notas de voz y mensajes sin necesidad de exponer un endpoint HTTPS público ni gestionar certificados SSL para Telegram.

### El Problema Operativo y Causa Raíz de Confusión
- A diferencia de plataformas PaaS/Serverless gestionadas (como Vercel o Railway) que cuentan con hooks automáticos vinculados a GitHub, el entorno de producción de RICK está alojado en una máquina virtual dedicada: **DigitalOcean Droplet** (IP pública: `68.183.30.218`).
- En un Droplet VPS, los contenedores Docker en ejecución corren de forma inmutable hasta que se reconstruyen. Un comando `git push origin main:multitenant` actualiza el repositorio remoto en GitHub, pero **no actualiza automáticamente el contenedor que corre en el Droplet** a menos que se ejecute la secuencia de compilación y despliegue dentro del servidor.
- Esta asimetría generaba dudas sobre si los cambios estaban "desplegados" tras un push a GitHub.

---

## Decision

Establecer y documentar la arquitectura oficial de despliegue en el **DigitalOcean Droplet con Docker Compose**, consolidar el protocolo operativo de actualización (Runbook) y definir las sondas de verificación automáticas.

### 1. Topología de Infraestructura en Producción

```
                                  DigitalOcean Droplet (68.183.30.218)
 ┌──────────────────────┐         ┌────────────────────────────────────────────────────────┐
 │ Meta WhatsApp API    │───────► │ Puerto 8000 (FastAPI)                                 │
 │ (Webhook HTTP Inbound│         │   └── Contenedor: rick-multitenant-api                │
 └──────────────────────┘         │       ├── /health                                      │
                                  │       ├── /webhook/whatsapp                            │
 ┌──────────────────────┐         │       └── /api/proactive/tick                          │
 │ Telegram Bot API     │◄──────► │                                                        │
 │ (Long Polling 24/7)  │         │ Worker Asíncrono: rick-telegram-bot                    │
 └──────────────────────┘         │   └── Proceso continuo en background                   │
                                  └────────────────────────────────────────────────────────┘
```

### 2. Gestión de Secretos en Runtime
- Las variables de entorno críticas (`SUPABASE_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `WHATSAPP_TOKEN`, `APIFY_API_TOKEN`) se almacenan exclusivamente en el archivo `.env` del Droplet con permisos estrictos (`chmod 600 .env`).
- Están excluidas del repositorio de código mediante `.gitignore` y de las capas de Docker mediante `.dockerignore`.
- Docker Compose inyecta las variables en RAM al instanciar los contenedores (`env_file: .env`).

### 3. Protocolo Canónico de Despliegue (Runbook Operativo)

Para publicar cualquier nueva versión (ej. de `1.1.0` a `1.2.0`):

#### Paso 1: Confirmar y subir cambios desde el entorno local
```bash
git push origin main:multitenant
```

#### Paso 2: Conectarse vía SSH al Droplet de DigitalOcean
```bash
ssh root@68.183.30.218
```

#### Paso 3: Actualizar el código y reconstruir contenedores
```bash
cd /root/rick-engine    # O directorio donde reside el repositorio
git fetch origin
git checkout multitenant
git pull origin multitenant

# Reconstruir y levantar los contenedores sin tiempo de inactividad prolongado
docker compose up -d --build
```

#### Paso 4: Validar la sonda de salud (Probe Verification)
Desde el servidor o desde cualquier terminal externa:
```bash
curl.exe http://68.183.30.218:8000/health
```
**Respuesta esperada:**
```json
{
  "status": "healthy",
  "service": "rick-multitenant",
  "version": "1.2.0",
  "database": "connected"
}
```

#### Paso 5: Inspeccionar logs en vivo para descartar anomalías
```bash
docker compose logs -f --tail=50
```

---

## Alternatives Considered

### 1. Serverless Puro (Vercel / Cloud Run)
- **Pros:** Despliegue automático con cada push a GitHub.
- **Cons:** El worker de Telegram en Long Polling requiere un proceso demonio 24/7 activo. En Serverless, el contenedor se apaga tras unos segundos de inactividad, rompiendo la recepción de mensajes de Telegram a menos que se configure una arquitectura compleja con Webhook HTTPS público y certificados SSL para Telegram.
- **Rejected:** El costo y complejidad de migrar Telegram a Webhook supera los beneficios frente al costo fijo predecible y la estabilidad del Droplet de DigitalOcean ($6-$12 USD/mes).

### 2. Despliegue Bare-Metal sin Docker (Systemd)
- **Pros:** Evita la sobrecarga de virtualización de Docker.
- **Cons:** Alto riesgo de deriva de dependencias (*environment drift*) entre Python local y el sistema operativo del Droplet.
- **Rejected:** Docker garantiza paridad exacta de dependencias (Python 3.11-slim) y reproduce de forma idéntica los resultados de los 110 tests locales.

---

## Consequences

### Positivas:
1. **Cero Ambigüedad:** Queda claramente diferenciado el rol de GitHub (repositorio de código) frente al Droplet de DigitalOcean (entorno de ejecución VPS que requiere comando de actualización).
2. **Sonda de Verificación Inequívoca:** El endpoint `/health` expone el campo `"version"`, permitiendo confirmar de inmediato si el Droplet corre la versión `1.1.0` o la actualizada `1.2.0`.
3. **Persistencia Dual:** Soporte simultáneo para WhatsApp (FastAPI) y Telegram (Long Polling) bajo una misma red Docker interna.

### Operativas:
- Toda actualización requiere el paso de SSH al Droplet o la configuración de un webhook/action CI/CD automatizado para ejecutar el script de pull y build.
