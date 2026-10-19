# Changelog
All notable changes to the RICK Multitenant Agent Engine project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
