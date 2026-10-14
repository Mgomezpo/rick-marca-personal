# Spec: RICK Multi-Tenant Agent Engine (Stanley Benchmark)

## Objective
Convert RICK from a fragile prototype with hardcoded context and pseudo-tools into a production-grade, multi-tenant AI Head of Content operating over Telegram (and WhatsApp) backed by Supabase. The benchmark is Stanley (`getstanley.ai`):
1. **Zero Hardcoded Creator Data**: Remove all hardcoded references to Bancolombia, PRGX, or The Insightful Arrow. Every creator starts as a blank slate.
2. **Dynamic Onboarding**: If a user is new (no profile in `user_profiles` or `brand_assets`), RICK greets them as their dedicated Head of Content, requests their socials/handle or a 30s voice note, extracts their niche, common enemy, and voice style, and persists it to Supabase.
3. **Real Tool Calling (Function Calling)**: Replace passive string-injection with real OpenAI tool calling (and Gemini fallback ReAct). The model must genuinely call tools (`guardar_guion_terminado`, `guardar_identidad_creador`, `leer_documento`, `buscar_en_cerebro`, `actualizar_memoria_activa`) during conversation.
4. **Resilient LLM Execution**: Ensure subagents (`hook_writer`, `guionista`, `anti_slop_editor`) have dual OpenAI/Gemini support so API quotas (like Gemini 429) do not break the engine.
5. **Stanley-Level Conversational UX**: Crisp, high-retention responses without corporate Markdown headers (###, ---). Always close with a low-friction question or call to action.

## Tech Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI (Webhooks, Simulation API, Health)
- **Database & Storage**: Supabase Postgres (pgvector 768d, RLS, `auth.users`, `user_profiles`, `brand_assets`, `pieces`, `rick_threads`, `rick_active_memory`)
- **LLM Providers**:
  - Primary: OpenAI (`gpt-4o-mini` / `gpt-4o`) via `openai.OpenAI`
  - Fallback / Multimodal: Google GenAI (`gemini-2.5-flash-lite`, `gemini-3.5-flash`) via `google.genai`
- **Chat Interfaces**: `python-telegram-bot` (Long Polling & Webhook), Meta Cloud API Webhook
- **Testing**: `pytest`, `pytest-asyncio`, `httpx` (FastAPI TestClient)

## Commands
- **Test Suite**: `python -m pytest tests -v`
- **Run Telegram Bot**: `python -m src.services.telegram_bot`
- **Run Local Server**: `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **Simulate Chat**: `POST http://localhost:8000/api/chat-simulation`

## Project Structure
```text
RICK! Guía de Marca Personal/
├── main.py                     # FastAPI application & simulation endpoints
├── SPEC-rick-engine.md         # Specification document (Source of Truth)
├── tasks/
│   ├── plan.md                 # Technical implementation plan
│   └── todo.md                 # Living task checklist
├── src/
│   ├── core/
│   │   ├── config.py           # Environment variables & runtime config
│   │   └── telemetry.py        # Token usage & latency tracking in Supabase
│   ├── db/
│   │   └── supabase.py         # Supabase client, queries, and upsert helpers
│   ├── engine/
│   │   ├── orchestrator.py     # Main RICK loop with real function calling
│   │   ├── tools.py            # Concrete tool schemas and handlers
│   │   ├── vfs.py              # Virtual File System (Supabase per-user + repo canon)
│   │   └── subagents/          # Specialized workers (guionista, hook_writer, anti_slop)
│   ├── services/
│   │   └── telegram_bot.py     # Telegram event handler, voice audio downloader
│   └── api/routers/
│       └── webhook.py          # WhatsApp Meta webhook
└── tests/
    ├── conftest.py             # Pytest setup, test fixtures, LLM mocking
    ├── test_simulation.py      # E2E simulation & webhook tests
    ├── test_subagents.py       # Worker tests
    ├── test_vfs.py             # Virtual File System tests
    └── test_tool_calling.py    # Function calling execution tests
```

## Code Style
- Explicit type hints on all function signatures.
- Clean separation between tool declaration, execution, and model invocation.
- Robust error handling: all external API calls must catch exceptions, log via Python `logging`, and provide graceful fallbacks.
- Zero secrets committed to VCS; loaded via `src.core.config.config`.

## Testing Strategy
1. **Unit Tests (Small & Fast)**:
   - Tool calling serialization and execution in isolation.
   - Anti-slop scanner and rule validation.
   - Virtual File System reading and mock writes.
2. **Integration Tests (Medium)**:
   - Orchestrator multi-turn chat simulation with mocked or live LLM credentials.
   - Dynamic user profile creation and identity persistence.
   - Fast fallback from Gemini to OpenAI when encountering 429 / errors.
3. **Regression Guard**: All 11 existing tests in `tests/` must remain passing.

## Boundaries
- **Always do**: Run `python -m pytest tests` before completing changes. Verify tenant isolation (`user_id` passed to all DB and tool calls). Sanitize HTML/Markdown before sending to Telegram.
- **Ask first**: Altering database schema tables in live Supabase.
- **Never do**: Hardcode any personal identity strings (Bancolombia, etc.) in the orchestrator or prompts. Never execute API calls without timeouts. Never suppress failing assertions in tests.

## Success Criteria
1. `tests/` suite executes via `python -m pytest tests` and achieves **100% passing tests** (zero failures or collection errors).
2. `src/engine/orchestrator.py` contains **zero hardcoded references** to Miguel Gomez, Bancolombia, or PRGX.
3. Real Function Calling: OpenAI calls `tools` parameter and dispatches to Python execution handlers, returning tool outputs to the model.
4. If Gemini hits 429 rate limit in subagents, it gracefully falls back to OpenAI so user flow never breaks.
5. Multi-turn simulation proves that a new user gets onboarded dynamically, can save identity, and can generate and save a script to `pieces`.
