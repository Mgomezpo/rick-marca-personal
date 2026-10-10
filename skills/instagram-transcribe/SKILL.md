---
name: instagram-transcribe
description: Saca el GUION hablado de un reel de Instagram (transcript + gancho + CTA) con Gemini, como el Scrapbook de IREAL.
platforms: [linux, macos, windows]
version: 1.0.0
author: IREAL (RICK)
license: MIT
category: ireal
metadata:
  hermes:
    tags: [ireal, instagram, gemini, transcript, guion, scraping, investigacion]
---

# Skill INSTAGRAM-TRANSCRIBE — los oidos de RICK en IG

Deja que RICK **saque el guion completo de un reel** (lo que se dice palabra por
palabra + el gancho + el CTA), no solo la metadata. Replica el pipeline del
Scrapbook de IREAL: **Apify trae el video, Gemini lo MIRA y transcribe.**

## Cuando usar
- El Creador dice "sacame el guion de este reel", "que dice este video", "analiza a
  fondo este reel", "como esta hecho este video de @fulano".
- Antes de **replicar/copiar** un video de un referente: primero saca su guion,
  luego se lo pasas a `ireal-guionista` / `ireal-hook-writer` para reescribirlo
  en la voz del Creador y en habla hispana.

## Diferencia con `instagram-scraper`
- `instagram-scraper` = los OJOS: metrica + caption de los reels de un perfil (barato).
- `instagram-transcribe` = los OIDOS: el guion hablado de UN reel (mas caro: 1 scrape + tokens de video de Gemini).

## Como sacar el guion (usa el HELPER — NO construyas curl a mano)
Corre esto en el `terminal` (lee las llaves solo y devuelve el guion en JSON):

```
powershell -NoProfile -ExecutionPolicy Bypass -File "tools/ig-transcribe.ps1" -Url "https://www.instagram.com/reel/SHORTCODE/"
```

- `-Url`: la URL del reel (puedes pegarla con el `?igsh=...`, el helper lo limpia solo).
- `-MaxMb` (opcional, default 18): tope del tamano del video para caber en Gemini.

Devuelve una linea de contexto (`GUION @autor | ~Ns | likes/comments/views`),
un `---`, y luego el **JSON del guion**: `full_transcript`, `hook` (text/type/strength),
`body` + `key_points`, `cta`, `language`, `confidence`.

## ⚠️ Presupuesto (IMPORTANTE)
Cada llamada gasta **1 scrape del plan FREE de Apify (~25/mes)** + **tokens de
video de Gemini**. NO transcribas en cada corrida ni en cron. Solo cuando el Creador
lo pida, y un reel a la vez. Si ya sacaste este guion hoy, reusalo.

## Que hacer con el guion
1. Lee `hook.text` + `hook.type`: ahi esta por que engancha.
2. Lee `full_transcript` + `key_points`: la estructura del video.
3. Lee `cta`: la mecanica (ej. "comenta X y te lo mando al DM" = lead magnet por comentario).
4. Para replicar: NUNCA copies literal. Extrae el patron (gancho + estructura + CTA)
   y reescribe en la voz del Creador con `ireal-guionista` / `ireal-hook-writer`.

## Pitfalls
- **Timeout en videos largos/lentos:** El proceso de descargar y analizar un video puede tardar más de 60 segundos. Si el comando falla por timeout, reinténtalo con un margen mayor, por ejemplo: `timeout=600` en la llamada a `terminal`.
- Si el reel es privado/restringido o no es video, el helper dice `ERROR: ...` — dilo y sigue, no inventes el guion.
- Si `confidence` es bajo, Gemini no pudo oir bien el audio; avisa que es una reconstruccion aproximada.
- Los captions/guiones pueden traer @handles/plataformas — esta bien nombrarlas (RICK-Hermes no tiene la linea no-social).
