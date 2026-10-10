# 🎙️ RICK — Tu Productor Creativo & Estudio de Marca Personal

> *"La creatividad no es un talento reservado para unos pocos. Es una forma de estar en el mundo, de prestar atención y de sintonizar con lo que es auténtico."*  
> — Inspirado en el canon **"The Creative Act: A Way of Being"** de **Rick Rubin**.

[![AI Runtime](https://img.shields.io/badge/Runtime-Claude%20Code%20%7C%20Cursor%20%7C%20Antigravity-black?style=for-the-badge&logo=anthropic)](https://claude.ai)
[![Setup](https://img.shields.io/badge/Setup-Cero%20API%20Keys-success?style=for-the-badge)](START-HERE.md)
[![Philosophy](https://img.shields.io/badge/Filosofía-Rick%20Rubin-purple?style=for-the-badge)](brain/01_philosophy/)

---

## ⚡ ¿Qué es RICK?

**RICK** no es un generador de contenido genérico ni un redactor de posts robóticos para complacer al algoritmo. 

Es un **estudio de contenido y mentor creativo agnóstico** diseñado para correr localmente dentro de tu asistente de IA (**Claude Code**, **Cursor**, **Antigravity** o **VS Code**). Su misión es actuar como tu productor ejecutivo: ayudarte a desenterrar tu propia obsesión, destruir el contenido acartonado (*anti-slop*) y convertir vivencias reales en guiones de video listos para rodar frente a cámara.

---

## 🧭 Los Tres Pilares de Criterio

1. **Cero Teleprompter (Storytelling Sugestivo por Beats):**  
   Los guiones leídos palabra por palabra huelen a IA y destruyen la conexión con la audiencia. RICK entrega cada pieza estructurada en actos, con dirección de cámara, tono emocional y **beats sugeridos** para que hables con tus propias palabras y naturalidad.
2. **El Quiebre Cognitivo (El Enemigo Común):**  
   Nadie recuerda los consejos tibios. RICK busca la mentira que tu industria da por sentada o la verdad incómoda que defiendes desde la trinchera para construir autoridad real.
3. **La Regla de la Reducción:**  
   Si una frase, adjetivo o elemento visual no aporta tensión o significado, se elimina. Menos ruido corporativo, más sustancia.

---

## 🚀 Arranque en 10 Segundos (Cero Fricción)

**No necesitas configurar bases de datos, servidores ni API keys para empezar.** Tu propio asistente de cabecera es el motor que le da vida.

### 1. Abre esta carpeta en tu Asistente
- **Claude Code:** Abre tu terminal dentro del repositorio y corre:
  ```bash
  claude
  ```
- **Cursor / Antigravity / VS Code:** Abre la carpeta como espacio de trabajo (`Workspace`) y abre el chat de IA.

### 2. Sintoniza tu Voz (Creator Interview)
Escribe en el chat:
> *"Hola RICK, empecemos mi entrevista"*

RICK no te pasará un formulario aburrido. Tendrán una conversación reflexiva de 10-15 minutos (una pregunta a la vez) para descubrir:
- Tu obsesión central y lo que te quita el sueño.
- La mentira de tu nicho que buscas romper.
- Tu historia de trinchera y cómo hablas cuando eres tú mismo.

Al finalizar, RICK poblará automáticamente tu perfil soberano en `brain/02_creator/`.

### 3. Produce con Criterio
Una vez sintonizado, pídele:
- *"Tengo esta idea dispersa: [pega tu nota o audio]. Estructúrala en un guion por beats."*
- *"Analicemos este reel de un referente: [enlace o transcripción]."*
- *"Diseñemos una serie de 3 episodios con quiebre cognitivo sobre mi tema."*

---

## 🏛️ Guía del Explorador (Estructura del Proyecto)

Este repositorio sigue una arquitectura de **Markdown Soberano**: todo tu conocimiento, voz, guiones y decisiones viven en archivos locales legibles por humanos y agentes.

```text
.
├── 📄 README.md                  # Este documento (visión general del estudio)
├── 📄 START-HERE.md              # Guía de onboarding rápido paso a paso
├── 📄 AGENTS.md                  # Prompt de sistema determinista para Cursor/Antigravity
├── 📄 CLAUDE.md                  # Reglas e identidad inmutable para Claude Code
├── 📄 connections.md             # Inventario de herramientas y estado del estudio
├── 📄 .env.example               # Configuración opcional para herramientas externas
│
├── 🧠 brain/                     # El cerebro central de RICK
│   ├── 01_philosophy/            # El canon de Rick Rubin (81 capítulos completos)
│   │   ├── canon/                # Transcripciones y meditaciones del libro maestro
│   │   ├── conceptos/            # Principios atómicos (Seeds, Beginner's Mind, Play)
│   │   └── principles/           # Criterios de reducción y artesanía
│   ├── 02_creator/               # La identidad soberana del creador
│   │   ├── identity/             # ADN de voz, posicionamiento y contrato de interacción
│   │   ├── lore/                 # Historias de origen, anécdotas y aprendizajes
│   │   └── reality/              # Foco actual y proyectos en curso
│   ├── 03_studio/                # El motor editorial
│   │   ├── frameworks/           # Estructuras probadas (quiebre cognitivo, autoridad, storytelling)
│   │   ├── referentes/           # Deconstrucción de creadores y piezas de referencia
│   │   └── pipeline/             # Procesos de validación editorial
│   └── 04_production/            # Bóveda de entregables tangibles
│       ├── scripts/              # Guiones individuales con beats y copies
│       └── series/               # Arcos narrativos y series multiepisodio
│
├── 🧠 memories/                  # Memoria viva y contexto activo
│   ├── active_context.md         # Qué se está trabajando hoy
│   ├── decisions.md              # Bitácora inmutable de acuerdos editoriales
│   ├── learnings.md              # Aprendizajes de rendimiento y feedback
│   └── series_status.md          # Tablero de control de series en curso
│
└── 🧰 skills/                    # Capacidades y flujos de trabajo especializados
    ├── creator-interview/        # Entrevista socrática para fijar el perfil del creador
    ├── guionista/                # Estructuración de guiones por beats sin teleprompter
    ├── hook-writer/              # Ganchos de alta retención que rompen el scroll
    ├── humanizer/                # Purgador de clichés de inteligencia artificial
    ├── instagram-scraper/        # Análisis de perfiles de referencia vía Apify (opcional)
    └── instagram-transcribe/     # Transcripción y deconstrucción de video
```

---

## 🧰 Habilidades del Estudio (`skills/`)

| Skill | Cuándo se usa | Qué entrega |
| :--- | :--- | :--- |
| **`creator-interview`** | Al iniciar por primera vez o pivotar de nicho | Perfil completo de voz, audiencia y posicionamiento en `brain/02_creator/` |
| **`guionista`** | Al transformar una idea en video | Guion en tres actos con beats, dirección visual/tono y copies para redes |
| **`hook-writer`** | Al necesitar retener los primeros 3 segundos | 5 alternativas de gancho basadas en quiebres cognitivos y curiosidad |
| **`humanizer`** | Al auditar textos sospechosos de sonar a IA | Limpieza de palabras vacías, ritmo conversacional y cadencia humana |
| **`instagram-scraper`** | Al auditar cuentas de referentes | Análisis estructurado de métricas y formatos ganadores |
| **`instagram-transcribe`** | Al deconstruir un reel o video corto | Extracción del guion original y análisis de su estructura narrativa |

---

## 🔒 Privacidad y Soberanía

- **Agnóstico y Local:** Todo el contenido que produces permanece en tu disco duro en archivos Markdown estándar.
- **Sin Bloqueo de Proveedor:** Puedes cambiar de modelo (Claude 3.7 Sonnet, GPT-4o, Gemini 2.5 Pro) en cualquier momento sin perder tu voz ni tus guiones.
- **Protección de Secretos:** `.gitignore` está configurado por defecto para evitar la subida accidental de archivos `.env`, credenciales o cachés locales.
