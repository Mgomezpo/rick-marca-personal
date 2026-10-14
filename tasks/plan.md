# Implementation Plan: RICK Engine Overhaul (Stanley Benchmark)

## Overview
Transform RICK from a fragile single-user prototype with hardcoded strings into a production-grade multitenant AI Head of Content with real tool calling, resilient LLM execution (dual OpenAI + Gemini), dynamic creator onboarding, and high-retention conversation formatting.

## Architecture Decisions
1. **Dynamic Tool Calling**: Move tool declarations into a structured module (`src/engine/tools.py`) that outputs valid OpenAI function definitions and executes them deterministically against `DatabaseService` and `VirtualFileSystem`.
2. **Resilient Subagent Architecture**: When Gemini returns 429 RESOURCE_EXHAUSTED, subagents automatically fall back to OpenAI (`gpt-4o-mini`). In test environments, mock or catch rate limits safely.
3. **Clean Multitenant Isolation**: System prompt strictly builds from per-user Supabase records (`brand_assets`, `user_profiles`, `rick_active_memory`, `pieces`). Zero hardcoded creator identity. If no profile exists, RICK enters dynamic onboarding mode.
4. **Conversational UX**: Remove corporate formatting and ensure responses are chunked cleanly for Telegram with strong action-oriented closers.

## Vertical Slices & Task Breakdown

### Phase 1: Resilient Subagents & Test Foundation
- [ ] Task 1.1: Add OpenAI fallback and quota-resilience to `HookWriterSubagent`, `GuionistaSubagent`, and `AntiSlopEditor`.
- [ ] Task 1.2: Add pytest configuration (`conftest.py`) and ensure all 11 baseline tests pass reliably.

### Phase 2: Function Calling Engine
- [ ] Task 2.1: Implement `src/engine/tools.py` with OpenAI JSON schema tool definitions and dispatch map.
- [ ] Task 2.2: Integrate function calling into `RickOrchestrator.process_message()` with multi-step execution (model calls tool -> tool executes -> model summarizes/responds).

### Phase 3: Purge Hardcoding & Dynamic Context Assembly
- [ ] Task 3.1: Clean `orchestrator.py` master prompt — remove all hardcoded references to Bancolombia, PRGX, The Insightful Arrow.
- [ ] Task 3.2: Implement dynamic onboarding flow when user has empty profile in Supabase.

### Phase 4: Verification, E2E Testing & Polish
- [ ] Task 4.1: Write comprehensive tests for tool calling and dynamic onboarding in `tests/test_tool_calling.py`.
- [ ] Task 4.2: Execute full test suite `python -m pytest tests -v` and verify 100% green.
- [ ] Task 4.3: Five-axis code quality review (`code-review-and-quality`).

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Gemini free-tier rate limits (429) | High | Fall back to OpenAI `gpt-4o-mini` immediately on quota error. |
| Tool calling loops indefinitely | Medium | Enforce maximum iteration cap of 3 tool turns per user message. |
| Message formatting breaks in Telegram | Medium | Robust HTML entity escaping and Markdown sanitization in `telegram_bot.py`. |
