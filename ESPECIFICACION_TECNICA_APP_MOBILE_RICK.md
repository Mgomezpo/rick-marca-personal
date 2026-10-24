# 🗺️ Guía Técnica de Arquitectura y Mapa del Workspace: RICK Multitenant

> **Documento:** Mapa Técnico del Código Fuente, Rutas, Archivos y Persistencia  
> **Propósito:** Guía de referencia técnica exhaustiva para desarrolladores e ingenieros que integren clientes (móvil, web o APIs) con el motor de RICK.  
> **Regla de Documentación:** Cero propuestas de pantallas o UI ficticia. Este documento describe **exclusivamente los archivos, rutas, modelos de datos, endpoints y módulos que existen en este workspace**.  
> **Versión del Motor:** 1.2.0  
> **Ubicación del Workspace:** `c:\Users\mgome\OneDrive\Documents\RICK Multitenant`  

---

## 📑 Tabla de Contenidos

1. [Árbol Completo de Directorios y Archivos del Workspace](#1-árbol-completo-de-directorios-y-archivos-del-workspace)
2. [El Motor de Grafo de Estado (`src/graph/`)](#2-el-motor-de-grafo-de-estado-srcgraph)
3. [Nodos de Agentes Especialistas (`src/agents/`)](#3-nodos-de-agentes-especialistas-srcagents)
4. [Servicios e Ingesta Desacoplada (`src/services/`)](#4-servicios-e-ingesta-desacoplada-srcservices)
5. [Capa de Persistencia y Base de Datos Supabase (`src/db/`)](#5-capa-de-persistencia-y-base-de-datos-supabase-srcdb)
6. [Capa de API Gateway y Webhooks (`src/api/`)](#6-capa-de-api-gateway-y-webhooks-srcapi)
7. [Módulo de Análisis de Mercado y Métricas (`src/matrix/`)](#7-módulo-de-análisis-de-mercado-y-métricas-srcmatrix)
8. [Registro de Decisiones Arquitectónicas (`docs/decisions/`)](#8-registro-de-decisiones-arquitectónicas-docsdecisions)
9. [Configuración, Entorno y Despliegue](#9-configuración-entorno-y-despliegue)
10. [Suite de Pruebas Automatizadas (`tests/`)](#10-suite-de-pruebas-automatizadas-tests)
11. [Contrato de Integración para Nuevos Clientes (App Móvil / Web)](#11-contrato-de-integración-para-nuevos-clientes-app-móvil--web)

---

## 1. Árbol Completo de Directorios y Archivos del Workspace

A continuación se detalla la estructura física del repositorio:

```
c:\Users\mgome\OneDrive\Documents\RICK Multitenant\
├── .env.example                               # Plantilla de variables de entorno (Supabase, OpenAI, Gemini, Apify)
├── .gitignore                                 # Exclusiones de Git
├── .dockerignore                              # Exclusiones de construcción Docker
├── Dockerfile                                 # Configuración de contenedor Linux/Python 3.11 para producción
├── docker-compose.yml                         # Orquestación de contenedor en DigitalOcean/local
├── pyproject.toml                             # Metadatos del proyecto y dependencias de empaquetado
├── requirements.txt                           # Dependencias fijadas (FastAPI, Supabase, OpenAI, Google-GenAI, Pydantic, etc.)
├── vercel.json                                # Configuración de despliegue serverless (si aplica)
├── ARQUITECTURA_RICK_MULTITENANT.md           # Documento de arquitectura general del motor multitenant
├── CHANGELOG.md                               # Historial de cambios y versiones (v1.0.0 a v1.2.0)
├── DEPLOYMENT.md                              # Guía de despliegue en Droplet de DigitalOcean con Docker
├── SECURITY.md                                # Políticas de seguridad y reporte de vulnerabilidades
├── README.md                                  # Manual operativo y bienvenida general
├── README_WHATSAPP_SETUP.md                   # Configuración del canal de producción Meta Cloud API
├── README_TELEGRAM_SETUP.md                   # Configuración del canal de pruebas Telegram
│
├── api/
│   └── index.py                               # Entrypoint serverless minimalista
│
├── docs/
│   └── decisions/                             # Architecture Decision Records (ADRs oficiales)
│       ├── ADR-001-state-graph-architecture.md
│       ├── ADR-002-anti-spam-governor-proactive-loops.md
│       ├── ADR-003-decoupled-radar-ingestion-cache.md
│       ├── ADR-004-evaluator-optimizer-quality-loop.md
│       ├── ADR-005-multi-tenant-supabase-isolation.md
│       ├── ADR-006-wide-fresh-radar-sampling.md
│       ├── ADR-007-multidimensional-content-architecture.md
│       ├── ADR-008-apify-niche-discovery-and-conversational-onboarding.md
│       ├── ADR-009-digitalocean-droplet-docker-deployment-and-telegram-bot.md
│       └── README.md
│
├── scripts/
│   ├── background_sandbox_runner.py           # Runner para pruebas de background y sandbox
│   └── run_25_iterations.py                   # Script de estrés y pruebas de convergencia
│
├── src/                                       # Código fuente principal del motor
│   ├── __init__.py
│   ├── agents/                                # Nodos del grafo (estrategia, guionismo, evaluación)
│   ├── api/                                   # Capa HTTP (FastAPI, webhooks, endpoints)
│   ├── db/                                    # Repositorio y cliente de persistencia Supabase
│   ├── graph/                                 # Orquestador del State Graph, estado inmutable y gobernador
│   ├── matrix/                                # Análisis estadístico de anomalías virales y medianas
│   └── services/                              # Servicios externos (LLM, voz, scraping, runner agnóstico)
│
├── tasks/                                     # Registro histórico de tareas y planes de sprint
└── tests/                                     # 25 suites de pruebas automatizadas (110 tests)
```

---

## 2. El Motor de Grafo de Estado (`src/graph/`)

El flujo cognitivo de RICK se ejecuta como un grafo de estado funcional e inmutable implementado en Python. Los archivos que componen este motor son:

### 2.1 `src/graph/engine.py` (Clase `RickGraphEngine`)
* **Propósito:** Compila y ejecuta el flujo completo de principio a fin recibiendo un `GraphState` inicial y devolviendo el `GraphState` final.
* **Lógica de Ejecución:**
  1. **Bifurcación por `trigger_type`:**
     - Si es distinto de `"user_message"` (ej. `"market_spark"`, `"brand_health_audit"`, `"trench_inquiry"`), pasa primero por el nodo `governor_node`. Si es rechazado por el gobernador, retorna inmediatamente en silencio. Si es aprobado, ejecuta el nodo proactivo correspondiente.
     - Si es `"user_message"` (mensaje de un usuario), ejecuta la **Rama Reactiva**.
  2. **Rama Reactiva:**
     - Ejecuta `rick_strategist_node`.
     - Si la intención clasificada es `"chat"` o `"extract_story"`, retorna la respuesta conversacional.
     - Si es `"view_report"`, ejecuta `routine_reporter_node`.
     - Si es `"generate_script"` o `"evaluate_script"`, entra al **Bucle Evaluador-Optimizador**: ejecuta `guionista_node` $\rightarrow$ `evaluator_node` $\rightarrow$ `quality_loop_router` (hasta que apruebe con score $\ge 8.0$ o complete un máximo de 3 iteraciones).
     - Formatea el resultado final con `format_script_whatsapp`.

### 2.2 `src/graph/state.py` (Esquemas de Dominio Pydantic y TypedDict)
Define los modelos inmutables del sistema:
* **`GraphState(TypedDict)`:** El diccionario de estado global que viaja entre todos los nodos:
  * `user_id`: Identificador único del tenant (`str`).
  * `creator_profile`: Perfil del creador (`CreatorProfile`).
  * `messages`: Historial de conversación (`List[ConversationMessage]`).
  * `current_intent`: Intención clasificada (`str`).
  * `trigger_type`: Tipo de disparo (`"user_message"`, `"market_spark"`, etc.).
  * `story_bank`: Lista de anécdotas reales del creador (`List[StoryReceipt]`).
  * `script_draft`: Borrador de guion técnico generado (`Optional[ScriptDraft]`).
  * `evaluation`: Resultado de auditoría de calidad (`Optional[EvaluationResult]`).
  * `learnings`: Aprendizajes procedimentales de la cuenta (`List[LearningItem]`).
  * `final_response`: Texto final para el usuario (`str`).
* **`ScriptDraft(BaseModel)`:** Modelo canónico del guion técnico estructurado en 3 bloques:
  * `titulo`: Título corto.
  * `formato`: Formato de video (`"Reel"`).
  * `duracion_objetivo`: Duración en segundos (default `45`).
  * `hook`: Bloque inicial (`ScriptBlock`).
  * `desarrollo`: Bloque de anécdota y lección (`ScriptBlock`).
  * `cierre`: Bloque de llamado a la acción (`ScriptBlock`).
  * `pilar`: Pilar estratégico opcional (`Optional[str]`).
  * `series`: Metadatos episódicos opcionales (`Optional[SeriesMetadata]`).
  * `plan_id`: ID del plan de contenido opcional (`Optional[str]`).
  * `visual_hook`: Texto en pantalla para segundo cero (`Optional[str]`).
  * `spoken_hook`: Gancho hablado en segundo cero (`Optional[str]`).
  * `friction_step`: Quiebre o colisión cognitiva (`Optional[str]`).
* **`ScriptBlock(BaseModel)`:** Bloque individual con `texto`, `intencion` psicológica, `camara` (dirección de plano) y `visual_text`.
* **`SeriesMetadata(BaseModel)`:** Metadatos de sagas episódicas (`series_id`, `series_title`, `episode_index`, `total_episodes`, `previous_piece_id`, `next_piece_id`).
* **`StoryReceipt(BaseModel)`:** Anécdota real vivida por el creador (`id`, `summary`, `theme`, `concrete_details`, `punchline`).
* **`CreatorProfile(BaseModel)`:** Perfil del creador (`user_id`, `instagram_handle`, `nicho`, `mediana_views`, `tono_voz`, `referentes`, `story_bank`).
* **`EvaluationResult(BaseModel)`:** Resultado del evaluador (`score` de 0 a 10, `passed`, `feedback`, `plagio_detectado`, `max_palabras_coincidentes`, `simulacion_estimacion`).
* **`update_state(state, **kwargs)`:** Función pura que clona el estado y aplica modificaciones sin efectos secundarios.

### 2.3 `src/graph/governor.py` (Clase `AntiSpamGovernor` y nodo `governor_node`)
* **Propósito:** Evaluar deterministamente si un mensaje proactivo tiene permitido enviarse al creador.
* **Reglas:**
  1. Si `trigger_type == "user_message"`, siempre devuelve `allowed = True` (los mensajes reactivos nunca se bloquean).
  2. **Quiet Hours:** Bloquea envíos si la hora local está fuera del rango **09:00 a 19:00**.
  3. **Ventana de Trinchera:** El trigger `"trench_inquiry"` solo tiene permiso entre **17:00 y 19:30**.
  4. **Umbral de Inactividad:** Requiere que el creador lleve al menos **42 horas en silencio** antes de disparar indagaciones.
  5. **Backoff Progresivo:** Aplica cooldowns progresivos según la racha de mensajes sin responder (24h con 0 silencios, 48h con 1 silencio, 96h con 2+ silencios).

### 2.4 `src/graph/edges.py` (`quality_loop_router`)
* **Propósito:** Determina si el guion pasa a formateo de salida (`"format_output"`) o regresa a reescritura (`"rewrite"`).
* **Condición de Aprobación:** Requiere `evaluation.score >= 8.0` y `plagio_detectado == False`.

### 2.5 `src/graph/formatter.py` (`format_script_whatsapp`)
* **Propósito:** Convierte el objeto `ScriptDraft` y su `EvaluationResult` en un mensaje formateado y limpio para mensajería.

---

## 3. Nodos de Agentes Especialistas (`src/agents/`)

Esta carpeta alberga los nodos que ejecutan el razonamiento estratégico, la generación de contenido y el control de calidad:

* **`src/agents/prompts.py`:**  
  Contiene `RICK_CANONICAL_SYSTEM_PROMPT`. Define la identidad de RICK (Head of Content interno, tono Rick Rubin, prohibición estricta de jerga bélica, prohibición de clichés de IA, principio de memoria viva con historias reales y regla de **máximo una sola pregunta por turno**).
* **`src/agents/rick.py`:**  
  * `classify_intent(user_message, state)`: Clasifica el mensaje del usuario en una de las intenciones soportadas:
    * `cold_onboarding`: Nuevo usuario que necesita onboarding en 4 etapas.
    * `view_report`: Solicitud de métricas, medianas o aprendizajes.
    * `generate_script`: Petición explícita de guion o decisión de formato (pieza única vs saga).
    * `blocked_creator`: Creador bloqueado o en blanco ("sin ideas"); activa Socratic Heavy Lifting.
    * `share_reference_link`: Enlace compartido de Instagram Reel o TikTok para analizar.
    * `meta_question`: Preguntas sobre cómo funciona RICK, comparación con ChatGPT, reseteo, etc.
    * `extract_story`: Relato de una experiencia, error o cliente para extraer historia real.
    * `chat`: Diálogo general o calibración.
  * `rick_strategist_node(state)`: Nodo orquestador. En producción invoca al LLM para responder con mayéutica socrática y heavy lifting si el creador está bloqueado.
* **`src/agents/guionista.py`:**  
  Nodo que redacta el guion en los 3 bloques canónicos (`HOOK`, `DESARROLLO`, `CIERRE`). Soporta tanto piezas sueltas de 45 segundos como sagas episódicas (inyectando cliffhangers hacia el siguiente episodio o enlaces de continuidad retrospectivos).
* **`src/agents/evaluator.py`:**  
  Nodo evaluador que audita el borrador:
  * Ejecuta comparación de n-gramas ($\ge 5$ palabras consecutivas idénticas con el referente) para asegurar **0% de plagio**.
  * Aplica penalizaciones por muletillas y clichés de IA.
  * Asigna un puntaje numérico (0 a 10).
* **`src/agents/routine.py` (`routine_reporter_node`):**  
  Genera el reporte semanal de desempeño de cuenta, calculando la mediana de visualizaciones y extrayendo aprendizajes procedimentales en la base de datos.
* **`src/agents/spark.py` (`proactive_spark_node`):**  
  Toma una anomalía viral del radar ($R \ge 1.5\times$) y genera una propuesta proactiva adaptada a la voz del creador.
* **`src/agents/brand_health.py` (`brand_health_node`):**  
  Audita la distribución temática de los últimos videos del creador y alerta si algún pilar estratégico quedó desierto ($< 15\%$).
* **`src/agents/trench.py` (`trench_inquiry_node`):**  
  Genera una pregunta al final de la tarde para extraer una vivencia real tras 42 horas de inactividad.

---

## 4. Servicios e Ingesta Desacoplada (`src/services/`)

Aloja los clientes externos, orquestadores de inferencia y el runner unificado:

### 4.1 `src/services/session_runner.py` (Punto de Entrada Universal)
* **Función Clave:**  
  ```python
  process_user_turn(
      user_id: str,
      handle: str,
      text: str,
      channel: str = "mobile",
      timestamp: Optional[str] = None,
      repo_override: Optional[SupabaseRepository] = None,
      engine_override: Optional[RickGraphEngine] = None,
  ) -> str
  ```
* **Flujo Operativo:**
  1. Carga el perfil del creador y su banco de anécdotas (`story_bank`) desde Supabase.
  2. Carga los aprendizajes previos (`procedural_learnings`).
  3. Guarda el mensaje del usuario en la tabla `conversations`.
  4. Recupera el historial y lo comprime mediante `compress_conversation_window` (mantiene los últimos 10 mensajes intactos y sintetiza los anteriores en un mensaje de contexto `system`).
  5. Ejecuta el `RickGraphEngine`.
  6. Guarda nuevos aprendizajes generados (`save_learning`).
  7. Guarda el guion generado en `pieces` si se produjo (`save_piece`).
  8. Guarda la respuesta del asistente en `conversations`.
  9. Retorna la respuesta en texto.

### 4.2 `src/services/voice.py` (`VoiceTranscriptionService`)
* **`download_whatsapp_media(media_id)`:** Descarga binarios de notas de voz desde la API de Meta Graph.
* **`transcribe_audio(audio_bytes, mime_type, filename)`:** Transcribe el audio utilizando **OpenAI Whisper-1** con fallback automático a **Google Gemini 2.5 Flash**.

### 4.3 `src/services/llm.py` (`LLMService`)
* Orquestador multi-modelo configurado con `gpt-4o` como primario y Gemini como secundario.
* Implementa generación de texto, llamadas estructuradas Pydantic (`generate_structured`), embeddings y modo de prueba determinista.

### 4.4 `src/services/instagram_scraper.py` (`InstagramScraperService`)
* Ingesta de reels de Instagram mediante el actor de Apify `clockworks~instagram-reels-scraper`:
  * `search_niche_reels(keywords, max_reels=15)`: Búsqueda dinámica de reels virales por palabras clave.
  * `scrape_shared_link(url)`: Extracción de métricas y transcripción de un reel específico pegado en el chat.

### 4.5 `src/services/radar_ingestion.py`
* Ingesta y almacenamiento en memoria del radar de mercado por `user_id`.
* Proporciona consultas en caliente con latencia **$< 50$ ms**.
* Aplica exclusión de piezas usadas durante 30 días (`record_used_post`) y rotación de creadores referentes durante 7 días (`rotate_creator_patterns`).

### 4.6 `src/services/receipt_extractor.py` (`ReceiptExtractorService`)
* Extrae anécdotas y aprendizajes reales del creador (`StoryReceipt`) a partir de sus redes o contenido histórico para poblar la memoria episódica.

### 4.7 `src/services/proactive_worker.py`
* `run_proactive_cycle_for_tenant`: Función ejecutada por workers de fondo o crons para disparar chispas, auditorías o preguntas de reactivación a través del Gobernador.

---

## 5. Capa de Persistencia y Base de Datos Supabase (`src/db/`)

Implementada en [`src/db/repository.py`](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/src/db/repository.py) bajo la clase **`SupabaseRepository`**.

### 5.1 Tablas en PostgreSQL / Supabase
El repositorio se conecta a las siguientes 5 tablas:

| Tabla en Supabase | Columnas Principales | Función y Contenido |
| :--- | :--- | :--- |
| **`user_profiles`** | `user_id` (PK, text), `instagram_handle`, `nicho`, `mediana_views`, `tono_voz`, `referentes` (jsonb). | Configuración, identidad y métricas base del creador. |
| **`conversations`** | `id` (PK, uuid), `user_id` (text), `role` (text: 'user'/'assistant'/'system'), `content` (text), `timestamp` (text), `created_at`. | Historial de mensajes multi-turno entre el creador y RICK. |
| **`pieces`** | `id` (PK, uuid), `user_id` (text), `title` (text), `format` (text), `script` (jsonb), `strategy_tag` (text, pilar), `plan_id` (uuid), `idea_fields` (jsonb: metadatos de sagas), `status` (text: 'draft'/'published'). | Bóveda de guiones técnicos generados con soporte multidimensional. |
| **`episodic_memory`** | `id` (PK, uuid), `user_id` (uuid), `kind` (text: 'story_receipt'), `title` (text), `context_blurb` (text), `content` (jsonb: `{receipt_id, summary, theme, concrete_details, punchline}`). | Memoria viva de anécdotas, proyectos y errores reales del creador. |
| **`procedural_learnings`** | `id` (PK, uuid), `user_id` (text), `statement` (text), `applies_when` (text), `confidence` (numeric), `created_at`. | Reglas y aprendizajes derivados de auditorías de rendimiento. |

### 5.2 Métodos Disponibles en `SupabaseRepository`
* `get_creator_profile(user_id: str) -> Optional[CreatorProfile]`
* `upsert_creator_profile(profile: CreatorProfile) -> None`
* `get_story_bank(user_id: str) -> List[StoryReceipt]`
* `save_story_receipt(user_id: str, receipt: StoryReceipt) -> None`
* `save_message(user_id: str, message: ConversationMessage) -> None`
* `get_conversation(user_id: str, limit: int = 20) -> List[ConversationMessage]`
* `clear_conversation(user_id: str) -> None`
* `save_piece(user_id: str, script: ScriptDraft, status: str = "draft") -> str`
* `get_pieces(user_id: str) -> List[Dict[str, Any]]`
* `get_series_pieces(user_id: str, series_id: str) -> List[Dict[str, Any]]` (ordenados por `episode_index`)
* `get_pillar_pieces(user_id: str, pilar_name: str) -> List[Dict[str, Any]]`
* `save_learning(learning: LearningItem) -> str`
* `get_learnings(user_id: str) -> List[LearningItem]`
* `is_healthy() -> bool`

---

## 6. Capa de API Gateway y Webhooks (`src/api/`)

Implementada en FastAPI con CORS habilitado:

### 6.1 `src/api/app.py`
Expone la aplicación central `FastAPI` y los siguientes endpoints:
* **`GET /health`:** Diagnóstico de salud. Verifica la conectividad con Supabase y el estado de memoria RAM mediante `psutil`. Retorna:
  ```json
  {
    "status": "healthy",
    "service": "rick-multitenant",
    "version": "1.2.0",
    "database": "connected",
    "memory": {"total_mb": 16384.0, "available_mb": 8192.0, "percent_used": 50.0}
  }
  ```
* **`POST /api/proactive/tick`:** Disparo de ciclo proactivo para un tenant (llamado por Cron externo).  
  * Payload: `{"user_id": "...", "trigger_type": "market_spark", "phone_number": "...", "proactive_context": {}}`
  * Evalúa el Gobernador y despacha si está autorizado.

### 6.2 `src/api/webhook.py`
Módulo de integración con Meta WhatsApp Cloud API:
* **`GET /webhook/whatsapp`:** Verificación del token de Meta (`hub.mode`, `hub.challenge`, `hub.verify_token`).
* **`POST /webhook/whatsapp`:** Ingesta de mensajes entrantes. Retorna **ACK HTTP 200 en $< 200$ ms** y deriva el procesamiento a `BackgroundTasks` ejecutando `process_whatsapp_background` $\rightarrow$ `session_runner.process_user_turn`.

---

## 7. Módulo de Análisis de Mercado y Métricas (`src/matrix/`)

Contiene la lógica matemática para identificar anomalías virales y calcular medianas:
* **`src/matrix/metrics.py`:** Calcula medianas de visualizaciones e índices de tracción.
* **`src/matrix/models.py`:** Modelos de datos para publicaciones de Instagram (`PostData`), métricas de cuenta y configuraciones de radar.
* **`src/matrix/analyzer.py`:** Analiza piezas de referentes frente a su mediana. Si el rendimiento relativo $R = \text{vistas} / \text{mediana} \ge 1.5\times$, lo cataloga como **patrón ganador** para alimentar al Guionista y a los Sparks proactivos.

---

## 8. Registro de Decisiones Arquitectónicas (`docs/decisions/`)

Cada decisión técnica está fundamentada en un Architecture Decision Record (ADR):

| ADR | Título | Decisión Técnica Documentada |
| :--- | :--- | :--- |
| **ADR-001** | State Graph Architecture | Adopción de grafo de estado inmutable sobre cadenas lineales o secuencias rígidas. |
| **ADR-002** | Anti-Spam Governor & Loops | Gobernador determinista con Quiet Hours (09:00-19:00), umbral de 42h y backoff progresivo. |
| **ADR-003** | Decoupled Radar & Ingestion | Cero scraping en caliente; ingesta en segundo plano y caché en memoria $< 50$ ms. |
| **ADR-004** | Evaluator-Optimizer Quality Loop | Bucle cerrado de reescritura con filtro de n-gramas anti-plagio ($\ge 5$ palabras) y anti-slop. |
| **ADR-005** | Multi-Tenant Supabase Isolation | Aislamiento estricto por `user_id` en todas las consultas y soporte de fallback en memoria. |
| **ADR-006** | Wide & Fresh Radar Sampling | Pool amplio de 15 a 25 creadores, rotación de 7 días y exclusión de publicaciones por 30 días. |
| **ADR-007** | Multidimensional Content | Desacople de piezas sueltas, sagas episódicas, pilares y planes sin forzar jerarquías. |
| **ADR-008** | Apify Niche Discovery & Onboarding | Búsqueda dinámica con Apify, ingesta de links compartidos y bienvenida en 4 etapas. |
| **ADR-009** | Droplet Docker Deployment & Telegram | Despliegue en contenedor Docker en DigitalOcean Droplet con soporte multicanal. |

---

## 9. Configuración, Entorno y Despliegue

### 9.1 Variables de Entorno (`.env.example`)
* **Supabase:**
  * `SUPABASE_URL`: URL del proyecto Supabase (`https://xxxx.supabase.co`).
  * `SUPABASE_SERVICE_ROLE_KEY`: Clave de servicio para operaciones del backend (bypasea RLS).
  * `SUPABASE_KEY`: Clave anónima o alternativa.
* **Modelos de IA:**
  * `OPENAI_API_KEY`: API Key de OpenAI (para `gpt-4o`, `text-embedding-3-small` y `whisper-1`).
  * `GEMINI_API_KEY`: API Key de Google (para Gemini 2.5 Flash).
* **WhatsApp Cloud API:**
  * `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.
* **Telegram:**
  * `TELEGRAM_BOT_TOKEN`.
* **Radar y Scraping:**
  * `APIFY_API_TOKEN`: Token de Apify para el actor de Instagram Reels.
* **Entorno:**
  * `APP_ENV`: `development` | `production` | `test`.
  * `PORT`: `8000`.

### 9.2 Infraestructura
* **`Dockerfile`:** Construcción ligera basada en `python:3.11-slim`.
* **`docker-compose.yml`:** Levanta el servicio exponiendo el puerto 8000 con reinicio automático.

---

## 10. Suite de Pruebas Automatizadas (`tests/`)

El repositorio cuenta con **110 pruebas automatizadas** que verifican el 100% de la funcionalidad del motor sin depender de llamadas de red de pago (utilizan mocks controlados y fixtures deterministas):

* `test_adversarial_isolation_audit.py`: Valida el aislamiento multi-tenant y la imposibilidad de filtración de datos entre creadores.
* `test_api_webhook.py`: Valida el ACK $< 200$ ms y el challenge de Meta.
* `test_cognitive_reasoning.py`: Valida el razonamiento del estratega y la prevención de trampas de clichés.
* `test_conversation_ux.py`: Valida la mayéutica socrática y la regla de una sola pregunta.
* `test_governor.py`: Valida Quiet Hours, cooldown de 42h y backoff progresivo.
* `test_graph_engine.py`: Valida el flujo completo de `RickGraphEngine`.
* `test_guionista.py` & `test_guionista_sagas.py`: Validan la estructura de 3 bloques y la continuidad de sagas.
* `test_matrix_analyzer.py` & `test_matrix_metrics.py`: Validan la detección de multiplicadores virales $R \ge 1.5\times$.
* `test_multidimensional_state.py`: Valida las 4 dimensiones de contenido desacopladas.
* `test_proactive_graph_engine.py` & `test_proactive_nodes.py`: Validan los loops de sparks, salud y trinchera.
* `test_quality_loop.py`: Valida el bucle evaluador, filtro de n-gramas y poda anti-slop.
* `test_radar_ingestion.py` & `test_wide_radar.py`: Validan la rotación de 7 días y la exclusión de 30 días.
* `test_repository_multidimensional.py`: Valida las consultas de piezas, sagas y pilares en Supabase.
* `test_rick_node.py` & `test_routine_reporter.py`: Validan el comportamiento conversacional y la generación de reportes.

Para correr la suite completa:
```bash
pytest -v
```

---

## 11. Contrato de Integración para Nuevos Clientes (App Móvil / Web)

Cualquier nuevo cliente que consuma este motor (como una aplicación móvil o una interfaz web) debe interactuar a través de las siguientes dos vías:

### Vía A: Invocación del Motor RICK (Canal Conversacional)
Para enviar un mensaje de texto o una nota de voz y recibir la respuesta de RICK:
1. En el backend FastAPI, invocar la función expuesta en [`src/services/session_runner.py`](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/src/services/session_runner.py):
   ```python
   from src.services.session_runner import process_user_turn

   respuesta = process_user_turn(
       user_id="id_del_usuario",
       handle="nombre_o_handle",
       text="texto_del_mensaje",
       channel="mobile",
   )
   ```
2. Si el cliente envía una nota de voz, utilizar [`src/services/voice.py`](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/src/services/voice.py) para transcribir el binario de audio (`transcribe_audio`) antes de pasarlo a `process_user_turn`.

### Vía B: Lectura y Sincronización Directa de Datos (Supabase)
Para consultar datos sin ejecutar el motor de IA (por ejemplo, para listados rápidos o sincronización offline):
1. Conectarse a las tablas de Supabase utilizando la librería cliente de la plataforma (ej. `@supabase/supabase-js`) con la clave pública `anon` y autenticación JWT.
2. Consultar directamente las tablas:
   * `conversations`: Para cargar el historial del chat.
   * `pieces`: Para listar los guiones generados (filtrando por `strategy_tag` para pilares o por `idea_fields->series->series_id` para sagas).
   * `episodic_memory`: Para consultar las anécdotas reales del creador (`kind = 'story_receipt'`).
   * `user_profiles`: Para leer o actualizar los datos del perfil y sus referentes.
