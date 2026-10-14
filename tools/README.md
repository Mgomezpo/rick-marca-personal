# Tools y Scripts Operativos del Estudio RICK

---
**Pilar:** `tools/`  
**Propósito:** Repositorio centralizado de herramientas, scripts de ejecución (PowerShell/Python) y utilidades de automatización del estudio.  
**Regla de Arquitectura:** En la carpeta `brain/` residen única y exclusivamente archivos de conocimiento, frameworks y fichas (`.md` / `.json`). Todo script ejecutable debe vivir aquí en `tools/`.  
---

## 🛠️ Scripts Disponibles

| Script | Descripción | Uso / Comando |
| :--- | :--- | :--- |
| [`check-scraper-health.ps1`](file:///c:/Users/mgome/OneDrive/Documents/RICK/tools/check-scraper-health.ps1) | Diagnóstico en tiempo real del estado de salud del scraper, saldo de Apify y verificación de token en `.env`. | `powershell -File tools/check-scraper-health.ps1` |
| [`ig-scrape.ps1`](file:///c:/Users/mgome/OneDrive/Documents/RICK/tools/ig-scrape.ps1) | Extracción en lote de posts recientes (metadata, likes, comments, captions) de un handle de Instagram vía Apify. | `powershell -File tools/ig-scrape.ps1 -User <handle> -Limit 4` |
| [`ig-transcribe.ps1`](file:///c:/Users/mgome/OneDrive/Documents/RICK/tools/ig-transcribe.ps1) | Descarga y transcripción con Gemini del guion hablado (palabra por palabra + gancho + CTA) de un Reel específico. | `powershell -File tools/ig-transcribe.ps1 -Url "<url_del_reel>"` |
