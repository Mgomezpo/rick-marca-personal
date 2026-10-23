# Architecture Decision Records (ADRs) - RICK Multitenant Agent Engine

Este directorio registra todas las decisiones arquitectónicas significativas tomadas durante el diseño, evolución e implementación del motor **RICK Multitenant Agent Engine**.

Cada registro sigue el estándar de documentación técnica y captura el contexto, alternativas evaluadas, decisión tomada y consecuencias operativas.

---

## 📋 Índice de Decisiones Arquitectónicas

| ADR | Título | Estado | Fecha | Contexto Central |
| :--- | :--- | :--- | :--- | :--- |
| [**ADR-001**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-001-state-graph-architecture.md) | Arquitectura de State Graph para el Motor de RICK | **Accepted** | 2026-10-18 | Elección de grafo determinista con estado inmutable vs cadenas lineales o agentes libres. |
| [**ADR-002**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-002-anti-spam-governor-proactive-loops.md) | Gobernador Anti-Spam y Cadencia de Loops Proactivos | **Accepted** | 2026-10-19 | Control temporal estricto (horas hábiles, ventana 17:00-19:30, 42h) y backoff progresivo. |
| [**ADR-003**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-003-decoupled-radar-ingestion-cache.md) | Inversión del Radar de Mercado e Ingesta Desacoplada | **Accepted** | 2026-10-19 | Ingesta en background con caché $< 50$ms, exclusión a 30 días y rotación de referentes a 7 días. |
| [**ADR-004**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-004-evaluator-optimizer-quality-loop.md) | Bucle Evaluador-Optimizador Anti-Plagio y Anti-Slop | **Accepted** | 2026-10-18 | Loop cerrado con n-gramas ($\ge 5$ palabras idénticas), poda de clichés y simulación empírica. |
| [**ADR-005**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-005-multi-tenant-supabase-isolation.md) | Aislamiento Multi-Tenant y Persistencia de Sesión | **Accepted** | 2026-10-19 | Partición estricta por `user_id` en Supabase con RLS y persistencia multi-turno. |
| [**ADR-006**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-006-wide-fresh-radar-sampling.md) | Muestreo Amplio de Radar y Exclusión Anti-Solapamiento | **Accepted** | 2026-10-19 | Pool de 20 referentes, exclusión de posts a 30 días y rotación de referentes a 7 días. |
| [**ADR-007**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-007-multidimensional-content-architecture.md) | Arquitectura de Contenido Multidimensional: Sagas, Pilares y Planes | **Accepted** | 2026-10-19 | Combinatoria libre y desacoplada de piezas sueltas, pilares, sagas continuas y planes sin DDL destructivo. |
| [**ADR-008**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/ADR-008-apify-niche-discovery-and-conversational-onboarding.md) | Descubrimiento Dinámico de Nicho vía Apify, Ingesta de Referencias y Onboarding en 4 Etapas | **Accepted** | 2026-10-23 | Búsqueda dinámica con Apify, ingesta de reels compartidos en chat, erradicación de jerga bélica ("trinchera") y onboarding en 4 etapas. |

---

## 🔄 Ciclo de Vida de un ADR
```
PROPOSED → ACCEPTED → (SUPERSEDED by ADR-XXX | DEPRECATED)
```
- Los ADRs nunca se eliminan; reflejan la evolución técnica del proyecto.
- Si una decisión cambia, se redacta un nuevo ADR que referencia y reemplaza al anterior.
