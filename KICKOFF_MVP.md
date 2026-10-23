# [HISTÓRICO / ARCHIVADO] RICK — KICKOFF MVP

> [!NOTE]
> **Estado del Documento:** Histórico / Archivado.  
> Este documento representa la nota inicial de arranque exploratorio (clon de UI de Stanley, interfaz web en Next.js, etc.).  
> La implementación oficial de RICK ha evolucionado y se consolidó como un **Motor Multitenant Autónomo para WhatsApp** basado en State Graphs de LangGraph.  
> Para la documentación arquitectónica vigente y el estado actual de producción, consulte:
> - [**ARQUITECTURA_RICK_MULTITENANT.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/ARQUITECTURA_RICK_MULTITENANT.md)
> - [**README.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/README.md)
> - [**docs/decisions/**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/README.md)

---

## 1. El Objetivo Inicial del Kickoff

Construir la experiencia validada de **Stanley (`https://x.getstanley.ai/ideate`)** para RICK:
1. **Frontend Web:** Exploración inicial de clon e ingeniería inversa de la pantalla de Stanley (`/ideate`) usando **REA (`C:\Users\mgome\OneDrive\Documents\IrealREA\rea`)** para extraer su interfaz, componentes y flujo, adaptándolo con el diseño editorial de RICK (Fraunces + Outfit + Paper/Ink/Crimson) y conectándolo a Supabase.
2. **Canales Móviles Nativos:**
   - Telegram Bot exploratorio (`src/services/telegram_bot.py`).
   - WhatsApp oficial mediante **Meta Cloud API** (`src/services/whatsapp.py`).
3. **Motor RICK:**
   - Subagentes modulares en `src/engine/subagents/`.
   - Guarda y actualiza las piezas directamente en Supabase (`pieces`, `platform_connections`).

---

## 2. Estado de Evolución

El alcance de este kickoff inicial fue completado y reemplazado por la implementación del motor en `src/graph/engine.py`, integrando el canal nativo de WhatsApp, el loop de calidad anti-plagio/anti-slop y los 4 loops proactivos con Gobernador.
