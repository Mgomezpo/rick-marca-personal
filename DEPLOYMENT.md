# 🚢 Guía Canónica de Despliegue en Producción (DigitalOcean + Docker)

> **Servidor en Producción:** DigitalOcean Droplet  
> **IP Pública:** `68.183.30.218`  
> **Puerto HTTP / API:** `8000`  
> **Canales Activos:** Meta WhatsApp Cloud API (Webhook) + Telegram Bot (Long Polling)  
> **Versión Actual del Sistema:** `1.2.0`  
> **Referencia Arquitectónica:** [ADR-009: Despliegue en DigitalOcean Droplet con Docker](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-009-digitalocean-droplet-docker-deployment-and-telegram-bot.md)

---

## 🧭 ¿Por qué un `git push` no actualiza el servidor automáticamente?

- **GitHub** aloja el código fuente y las ramas (`origin/multitenant`).
- **DigitalOcean** es una máquina virtual privada (VPS / Droplet). Los contenedores de Docker corren en la memoria del servidor de forma inmutable.
- Hasta que no te conectas al Droplet y ejecutas `git pull` + `docker compose up -d --build`, el servidor continuará ejecutando la versión previa en memoria.

---

## ⚡ Protocolo de Actualización en 3 Pasos (Runbook Rápido)

### Paso 1: Subir tus cambios locales a GitHub
Desde tu máquina local:
```powershell
git push origin main:multitenant
```

### Paso 2: Conectarte por SSH al Droplet y reconstruir los contenedores
```bash
ssh root@68.183.30.218
```
Una vez dentro del Droplet:
```bash
# Navegar a la carpeta del proyecto
cd /root/rick-engine    # O la ruta donde se clonó el repositorio

# Traer los últimos cambios de la rama multitenant
git fetch origin
git checkout multitenant
git pull origin multitenant

# Recompilar la imagen de Docker y reiniciar el servicio en segundo plano
docker compose up -d --build
```

### Paso 3: Verificar que la nueva versión esté activa
Desde tu máquina local o terminal:
```powershell
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

---

## 🛠️ Comandos Útiles de Mantenimiento en el Droplet

| Acción | Comando |
| :--- | :--- |
| **Ver estado de los contenedores** | `docker compose ps` |
| **Ver logs en tiempo real** | `docker compose logs -f --tail=50` |
| **Reiniciar los servicios** | `docker compose restart` |
| **Detener los servicios** | `docker compose down` |
| **Liberar espacio de imágenes antiguas** | `docker image prune -f` |

---

## 🔐 Variables de Entorno en el Droplet (`.env`)

En el Droplet, el archivo `.env` reside en `/root/rick-engine/.env` con permisos restringidos (`chmod 600 .env`). Debe contener:

```env
# --- Supabase Multi-Tenant ---
SUPABASE_URL=https://khoikdwablpqiapxkgqx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key

# --- Modelos de IA ---
OPENAI_API_KEY=tu_openai_key
GEMINI_API_KEY=tu_gemini_key

# --- Meta WhatsApp Cloud API ---
WHATSAPP_TOKEN=tu_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_VERIFY_TOKEN=rick_secret_verify_token_2026

# --- Telegram Bot API ---
TELEGRAM_BOT_TOKEN=tu_telegram_bot_token

# --- Apify Scraper ---
APIFY_API_TOKEN=tu_apify_token

# --- Runtime ---
PORT=8000
TZ=America/Bogota
```
