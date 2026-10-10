---
name: instagram-scraper
description: Mira el Instagram del Creador (o de un competidor/referente) vía Apify.
platforms: [linux, macos, windows]
version: 1.0.0
author: IREAL (RICK)
license: MIT
category: ireal
metadata:
  hermes:
    tags: [ireal, instagram, apify, scraping, investigacion]
---

# Skill INSTAGRAM-SCRAPER — los ojos de RICK en IG

Deja que RICK **mire un perfil de Instagram** (los últimos posts del Creador, o de un competidor/referente) para informar el contenido: qué
publicó, qué enganchó, qué ángulos usa. Usa **Apify** (el mismo scraper que IREAL).

## Cuándo usar
- El Creador dice "mira mi IG", "qué pasó en mi perfil", "analiza a @fulano".
- Antes de proponer contenido proactivo, para anclarlo a lo que ya publica.

## ⚠️ Presupuesto (IMPORTANTE)
El plan de Apify es **FREE (~25 scrapes/mes)**. **NO scrapees en cada corrida ni
en cada cron.** Scrapea solo cuando el Creador lo pida o máximo 1×/semana. Un scrape
= un perfil. Si ya miraste hoy, reusa lo que viste.

## Cómo scrapear (usa el HELPER — NO construyas curl a mano)
Corre esto en el `terminal` (el helper lee el token solo y formatea la salida):

```
powershell -NoProfile -ExecutionPolicy Bypass -File "tools/ig-scrape.ps1" -User <handle> -Limit 8
```

- `-User`: el handle (`@` opcional), O una URL de reel/post pegada (le quita el `?igsh=...` solo). Con un handle trae sus reels recientes; con una URL de reel trae ese reel.
- `-Limit`: cuántos posts (default 8; usa menos para cuidar la cuota FREE).

Devuelve `POSTS: N` + **una línea JSON por reel** con `type, likes, comments, views, date, url, caption` (usa el Actor `instagram-reel-scraper`, el mismo que IREAL — trae los reels recientes con engagement). Lee esos captions + engagement para tu análisis. NO uses el navegador — el helper es el único camino confiable a IG.

## Qué hacer con lo que ves
1. Lee los captions + engagement de los últimos posts.
2. Detecta patrones: qué temas/ganchos enganchan más, el ritmo, el tono.
3. Alimenta eso a las skills de contenido (`ireal-hook-writer`, `ireal-guionista`,
   `content-pattern-analyzer-sms`) para proponer piezas ancladas a lo que YA funciona.
4. Nunca copies un post literal — extrae el patrón, escribe en la voz del Creador.

## Salida
Un resumen corto: 2-3 patrones observados + 1 oportunidad concreta de contenido.
El detalle crudo NO se le muestra al Creador; se destila.

## Pitfalls
- No quemes la cuota (ver presupuesto). Si el scrape falla o está vacío, dilo y sigue sin inventar datos.
- Los captions pueden traer @handles/plataformas — está bien nombrarlas (RICK-Hermes no tiene la línea no-social).
