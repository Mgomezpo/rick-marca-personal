# Changelog
All notable changes to the RICK Multitenant Agent Engine project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-19

### Added
- **Multidimensional Content Architecture (`core-state` & `db-repository`):** Free combinatory matrix allowing Standalone pieces, Brand Pillars, Episodic Sagas, and Plans without forced hierarchies or mandatory classifications.
- **Episodic Series Metadata (`SeriesMetadata`):** Pydantic V2 model in `src/graph/state.py` for saga sequencing (`series_id`, `series_title`, `episode_index`, `total_episodes`, `previous_piece_id`, `next_piece_id`).
- **Narrative Continuity Engine (`script-writer`):** Dynamic continuity hooks in `src/agents/guionista.py` for episodes > 1 linking to previous releases, and dramatic cliffhangers in closing CTA for non-final episodes.
- **Saga Mayeutics in WhatsApp (`rick-strategist`):** Multi-point and dense story detection in `src/agents/rick.py` with peer suggestion of single 45s piece vs 2-part saga (*"¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"*), respecting creator autonomy without imposing.
- **Tenant-Isolated Series & Pillar Queries (`db-repository`):** Implemented `get_series_pieces` and `get_pillar_pieces` in `SupabaseRepository` with strict `user_id` scoping and sorting by `episode_index`.
- **Architectural Documentation (`documentation-and-adrs`):** Registered ADR-006 (Wide Radar Sampling & Anti-Overlap), ADR-007 (Multidimensional Content Architecture), and Section 12 in `ARQUITECTURA_RICK_MULTITENANT.md`.

### Changed
- **Zero Breaking Changes / No Destructive DDL:** Preserved 100% backward compatibility for all 132 historical pieces and 33 active tenants in Supabase, mapping series to native JSONB `idea_fields` and existing columns `strategy_tag` and `plan_id`.

## [1.0.1] - 2026-10-19

### Added
- **Multi-Turn Session Persistence (`db-repository`):** Added `save_message`, `get_conversation`, and `clear_conversation` to `SupabaseRepository` with strict `user_id` multi-tenant isolation, preserving conversation context across distinct incoming WhatsApp webhooks.
- **Outbound WhatsApp Cloud API Dispatcher (`api-webhook`):** Implemented `send_whatsapp_message` to automatically dispatch generated responses back to user WhatsApp accounts via Meta Graph API (`v19.0/{phone_number_id}/messages`).

### Changed
- **Mayeutic Inquiry Decoupling (`rick-strategist`):** Decoupled scene and root-friction detection from rigid turn-count barriers, allowing articulate creators providing both elements to transition directly to script writing without redundant inquiry turns.
- **Dependency & Version Sync:** Synchronized `pyproject.toml` version to `1.0.0` and explicitly declared `psutil>=5.9.0` dependency.

## [1.0.0] - 2026-10-18

### Added
- **Core State Schema (`core-state`):** Inmutable `GraphState` definition, typed data models (`CreatorProfile`, `ScriptDraft`, `ScriptBlock`, `EvaluationResult`, `WinningPattern`, `LearningItem`, `ConversationMessage`), and functional state updater.
- **Matrix Engine (`matrix-engine`):** Exact median calculation discarding invalid entries, relative performance multiplier ($R = \text{views}/\text{median}$), and standard 10-column `MatrixRow` representation.
- **Dual Market Radar (`market-radar`):** Automatic pattern extractor ($R \ge 1.5\times$) aggregating evidence across fixed brand referents (`brand_referents`) and niche discovery, with graceful degradation fallback.
- **RICK Strategist (`rick-strategist`):** Canonical prompt based on Rick Rubin (*The Creative Act*), 3-level verbal limitation matrix, 4-way intent router, and trench mayeutic inquiry (scene & root friction extraction).
- **Technical Script Writer (`script-writer`):** Generation of scripts structured into the 3 canonical blocks (`HOOK`, `DESARROLLO`, `CIERRE / CTA`), each with spoken `Texto`, psychological `Intención`, and physical `Cámara` direction.
- **Evaluator-Optimizer Quality Loop (`evaluator-loop`):** Anti-plagiarism algorithm rejecting $\ge 5$ consecutive matching words from benchmark videos, anti-slop editor penalizing corporate clichés, and empirical probability simulation.
- **Routine Reporter (`routine-reporter`):** Personal account audit service calculating personal median, generating `procedural_learnings` for Supabase, and delivering weekly reports.
- **Conversational Formatter (`channel-whatsapp`):** Mobile-optimized WhatsApp output formatter with zero artificial tables or raw code blocks.
- **Multi-Tenant Supabase Repository (`db-repository`):** Strict `user_id` query scoping and Row-Level Security isolation across profiles, learnings, and pieces.
- **FastAPI WhatsApp Webhook (`api-webhook`):** Meta challenge verification (`GET /webhook/whatsapp`), sub-200ms immediate ACK with `BackgroundTasks` processing (`POST /webhook/whatsapp`), and `/health` system diagnostics.
- **Production Shipping & Containerization (`shipping-and-launch`):** Multi-stage `Dockerfile` with Python 3.11-slim, `.dockerignore`, live HTTPS public deployment, and verified end-to-end smoke testing.
- **Conversational Tuning & UX:** 39 automated unit and integration tests passing with 100% green status, including multi-turn simulation with `@casidonovan` and `@miguel_gomezpo`.
- **Security & Performance Hardening:** Dependency audit via `pip-audit` confirming 0 known vulnerabilities in production dependencies, and STRIDE threat modeling documented in `SECURITY.md`.
