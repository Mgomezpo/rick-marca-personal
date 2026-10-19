# RICK — KICKOFF MVP (Documento de Arranque Limpio)

> **Propósito:** Contexto consolidado para arrancar la nueva sesión limpia en Antigravity sin arrastrar peso ni ruido de conversaciones anteriores.

---

## 1. El Objetivo del MVP

Construir la experiencia validada de **Stanley (`https://x.getstanley.ai/ideate`)** para RICK:
1. **Frontend Web:** Clon e ingeniería inversa de la pantalla de Stanley (`/ideate`) usando **REA (`C:\Users\mgome\OneDrive\Documents\IrealREA\rea`)** para extraer su interfaz, componentes y flujo, adaptándolo con el diseño editorial de RICK (Fraunces + Outfit + Paper/Ink/Crimson) y conectándolo a Supabase.
2. **Canales Móviles Nativos (Cero Twilio):**
   - Telegram Bot (`src/services/telegram_bot.py`).
   - WhatsApp oficial mediante **Meta Cloud API** (`src/services/whatsapp.py`).
3. **Motor RICK (Python FastAPI):**
   - Subagentes modulares en `src/engine/subagents/` (`hook_writer.py`, `guionista.py`, `anti_slop_editor.py`).
   - Guarda y actualiza las piezas directamente en Supabase (`pieces`, `platform_connections`).
4. **Conexiones & Autoposteo:** Meta (Instagram), TikTok y X.

---

## 2. Hoja de Ruta

- **Sprint 1: Extracción con REA y Clon de Stanley (`/ideate`):**
  - Conectar REA vía Chrome con remote debugging port `9222` para capturar la estructura de componentes, estilos y API de `https://x.getstanley.ai/ideate`.
  - Recrear la pantalla en Next.js conectada a la tabla `pieces` de Supabase.
- **Sprint 2: Pipeline de Mensajería (Telegram + WhatsApp Meta Cloud API):**
  - Conectar la entrada de voz/texto al orquestador y los subagentes, reflejando las ideas en la interfaz clonada.
- **Sprint 3: Conexión de Redes y Publicación Automática.**

---

## Mensaje para arrancar la nueva sesión:

Abre un nuevo chat (`+`) y escribe:
> *"Arrancamos el Sprint 1 según @KICKOFF_MVP.md para usar REA e inspeccionar la pantalla de Stanley /ideate."*
