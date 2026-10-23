# Plan de Implementación: Loops Proactivos de RICK Multitenant
## Graph Engineering & Loop Engineering con Agent Skills

> Basado en la especificación [proactive_loops_architecture.md](file:///C:/Users/mgome/.gemini/antigravity-ide/brain/f75ed816-9573-4090-94ff-7cc3b27b2c6d/proactive_loops_architecture.md).

---

## Tareas de Desarrollo (Ciclo TDD: Red -> Green -> Refactor)

### Fase 1: Esquema de Estado y Modelos de Loop Proactivo (`api-and-interface-design`)
- [x] **Task P1**: Extender `src/graph/state.py` con:
  - `TriggerType` enum / literal (`user_message`, `brand_health_audit`, `market_spark`, `trench_inquiry`, `post_mortem`).
  - `BrandHealthReport` (distribución de pilares, detección de voice drift, salud de autoridad).
  - `ProactiveSpark` (referente fuente, R multiplicador, ángulo sugerido para el creador).
  - `GovernorConfig` y `GovernorEvaluation` (cooldown, quiet hours, SNR threshold).
- [x] **Test P1**: `tests/test_proactive_state.py` validando serialización, tipado estricto e inmutabilidad.

### Fase 2: El Gobernador Anti-Spam y Control de Cadencia (`constraint-driven-development`)
- [x] **Task P2**: Implementar `src/graph/governor.py` con:
  - Verificación de cooldown (mínimo 24 horas entre pings no solicitados).
  - Ventana horaria local del creador (por defecto 09:00 a 19:00).
  - Penalización por pings ignorados (exponential backoff).
  - Filtro de umbral SNR ($\ge 0.85$ confianza empírica).
- [x] **Test P2**: `tests/test_governor.py` con casos de rechazo por cooldown, hora nocturna, y aprobación cuando se cumplen todas las condiciones.

### Fase 3: Nodos de Análisis de Marca y Aportes Proactivos (`graph-engineering`)
- [x] **Task P3.1**: Nodo `brand_health_audit_node` en `src/agents/brand_health.py` que audita pilares y genera alertas estratégicas de autoridad.
- [x] **Task P3.2**: Nodo `proactive_spark_node` en `src/agents/spark.py` que toma anomalías de mercado ($R \ge 2.0x$) y redacta un aporte de contenido personalizado sin plagio.
- [x] **Task P3.3**: Nodo `trench_inquiry_node` en `src/agents/trench.py` para reactivar creadores inactivos con preguntas mayéuticas tipo Rubin.
- [x] **Test P3**: `tests/test_proactive_nodes.py` probando cada nodo de forma aislada.

### Fase 4: Enrutamiento y Motor de Compilación del Grafo (`graph-engineering`)
- [x] **Task P4**: Actualizar `src/graph/engine.py` y `src/graph/edges.py`:
  - `proactive_router`: Determina el flujo según `trigger_type` y la aprobación del gobernador.
  - Integración transparente con el formateador de WhatsApp/Telegram.
- [x] **Test P4**: `tests/test_proactive_graph_engine.py` ejecutando los flujos proactivos completos de extremo a extremo.

### Fase 5: Scheduler y Worker de Ejecución Periódica (`ci-cd-and-automation` + `observability`)
- [x] **Task P5**: Implementar `src/services/proactive_worker.py`:
  - Worker que evalúa periódicamente todos los tenants activos (`user_profiles`).
  - Endpoint webhook/cron `POST /api/proactive/tick` para invocar desde `pg_cron` o scheduler externo.
  - Registro de auditoría y telemetría de cada loop ejecutado.
- [x] **Test P5**: `tests/test_proactive_worker.py` con simulación multi-tenant.
