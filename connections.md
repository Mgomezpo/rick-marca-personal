# Registro de Conexiones y Herramientas del Taller

Este documento mantiene el inventario vivo de los servicios y herramientas del taller de RICK.

---

## 🧠 1. Entorno de Ejecución (Runtime del Asistente)

| Entorno | Estado | Cómo opera |
| :--- | :--- | :--- |
| **Claude Code / Cursor / Antigravity** | 🟢 Nativo | No requiere API keys en .env. RICK responde directamente a través del modelo de tu asistente con las instrucciones de AGENTS.md o CLAUDE.md. |

---

## 👁️ 2. Inteligencia de Redes & Scraping (Opcional)

| Capacidad | Variable en .env | Estado | Propósito |
| :--- | :--- | :--- | :--- |
| **Instagram Scraper** | APIFY_API_TOKEN | Opcional | Si deseas raspar perfiles completos o reels automáticamente vía Apify. |

---

## 🗄️ 3. Almacenamiento & Memoria

| Recurso | Tipo | Estado | Propósito |
| :--- | :--- | :--- | :--- |
| **Markdown Soberano** | Local (brain/, memories/) | Primario | Todo tu conocimiento, voz, guiones y decisiones viven en archivos locales en tu disco. |
