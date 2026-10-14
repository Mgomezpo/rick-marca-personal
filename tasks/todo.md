# Task List: RICK Multi-Tenant Engine Overhaul

## Phase 1: Resilient Subagents & Test Foundation
- [x] Task 1.1: Add OpenAI fallback and quota-resilience to `HookWriterSubagent`, `GuionistaSubagent`, and `AntiSlopEditor`.
  - Acceptance: When Gemini hits 429 quota or fails, subagents cleanly call OpenAI (`config.OPENAI_MODEL`) and return structured results.
  - Verify: `test_hook_writer_subagent` passes even under Gemini rate limits.
  - Files: `src/engine/subagents/hook_writer.py`, `src/engine/subagents/anti_slop_editor.py`, `src/engine/subagents/guionista.py`.
- [x] Task 1.2: Add pytest configuration (`conftest.py` / root path handling).
  - Acceptance: Running `python -m pytest tests` discovers tests properly and executes without import errors.
  - Verify: `python -m pytest tests` runs without collection errors.
  - Files: `tests/conftest.py`.

## Checkpoint 1: Foundation
- [x] All baseline tests pass: `python -m pytest tests` (11/11 passing).

## Phase 2: Function Calling Engine
- [x] Task 2.1: Create `src/engine/tools.py` with OpenAI tool schemas and execution handler.
  - Acceptance: Tools (`leer_documento`, `listar_cerebro`, `buscar_en_cerebro`, `guardar_guion_terminado`, `guardar_identidad_creador`, `actualizar_memoria_activa`) defined in OpenAI JSON schema format with deterministic executor.
  - Verify: Unit test invoking tool executor directly with mock inputs.
  - Files: `src/engine/tools.py`.
- [x] Task 2.2: Implement Tool Calling execution loop in `RickOrchestrator.process_message()`.
  - Acceptance: When OpenAI or Gemini generates `tool_calls`, the orchestrator executes each tool, feeds the output back into conversation messages, and produces final response. Max 3 tool iterations.
  - Verify: Integration test showing orchestrator calling `guardar_identidad_creador` or `guardar_guion_terminado`.
  - Files: `src/engine/orchestrator.py`.

## Checkpoint 2: Tool Calling
- [x] Orchestrator successfully calls functions and stores data in Supabase.

## Phase 3: Purge Hardcoding & Dynamic Onboarding
- [x] Task 3.1: Remove hardcoded Bancolombia/PRGX/The Insightful Arrow from `orchestrator.py`.
  - Acceptance: Master system prompt has zero references to Miguel Gomez, Bancolombia, or PRGX.
  - Verify: Grep search confirms zero hardcoded strings.
  - Files: `src/engine/orchestrator.py`.
- [x] Task 3.2: Implement dynamic onboarding flow.
  - Acceptance: If user profile in Supabase is empty, RICK welcomes the creator as Head of Content, asks for their handle or 30s voice note, and guides them smoothly.
  - Verify: Simulated chat with a new phone number initiates dynamic onboarding without hallucinating previous clients.
  - Files: `src/engine/orchestrator.py`.

## Checkpoint 3: Dynamic Multitenancy
- [x] New user gets clean onboarding with zero identity bleed.

## Phase 4: Verification & Five-Axis Review
- [x] Task 4.1: Write `tests/test_tool_calling.py` covering tool calling, multi-turn tool handling, and onboarding.
  - Verify: All tests pass.
  - Files: `tests/test_tool_calling.py`.
- [x] Task 4.2: Run full test suite `python -m pytest tests -v`.
  - Verify: 100% tests pass (20/20 passing).
- [x] Task 4.3: Five-axis code quality audit (`code-review-and-quality`).
  - Verify: Document findings and ensure high code health across correctness, readability, architecture, security, and performance.
- [x] Task 4.4: Hardening Onboarding, Scraper Fallback & Anti-Hallucination Tool Calling (Stanley Caliber)
  - Acceptance: Fixed `openai` library missing in Docker; added `redactar_guion_formato_oficial` and `consultar_posts_instagram`; Stanley 2-step async onboarding with background footprint research; deployed to droplet 68.183.30.218.
  - Verify: Container `rick-telegram-bot` rebuilt and active in production.

## Phase 5: Competitive Benchmarking (Telethon UserBot Auditor)
- [ ] Task 5.1: Credenciales y Setup de Telethon
  - Acceptance: Obtener `api_id` y `api_hash` desde my.telegram.org y configurar archivo de entorno `.env.benchmarking` o sección en `.env`.
  - Archivos: `.env`, `tools/competitor_auditor.py`.
- [ ] Task 5.2: Motor de Auditoría y Diálogo Autónomo
  - Acceptance: Script en Telethon que inicia sesión con cuenta de usuario, contacta al bot competidor (`@username`), ejecuta protocolo de conversación (onboarding, solicitud de guiones, manejo de objeciones) y captura respuestas + latencias.
  - Archivos: `tools/competitor_auditor.py`.
- [ ] Task 5.3: Evaluador de Benchmarking y Comparativa vs RICK
  - Acceptance: Generar reporte automatizado en markdown (`benchmarks/competitor_analysis_<bot>.md`) comparando: tiempos de respuesta, profundidad de frameworks narrativos, fricción de onboarding, tono y detección de debilidades competitivas para adoptar en RICK.
  - Archivos: `benchmarks/competitor_analysis.md`.

## Phase 6: Official Instagram Graph API (Meta OAuth & Dashboard Integration)
- [ ] Task 6.1: Meta App Setup & OAuth Flow para Creadores
  - Acceptance: Cuando el dashboard/environment web de RICK esté montado, permitir al creador conectar su cuenta profesional de Instagram vía Facebook Login / Meta App.
  - Archivos: `src/services/instagram_graph.py`, `src/api/oauth.py`.
- [ ] Task 6.2: Sincronización de Métricas Oficiales de Instagram
  - Acceptance: Consulta directa y sin límites de insights oficiales (alcance, retención de video, guardados, comentarios de reels) sin depender de scrapers externos.
  - Archivos: `src/services/instagram_graph.py`, Supabase `creator_insights`.
