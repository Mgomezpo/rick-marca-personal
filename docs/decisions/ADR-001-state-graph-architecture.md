# ADR-001: Arquitectura de State Graph para el Motor de RICK

## Status
Accepted

## Date
2026-10-18

## Context
El sistema RICK comenzó como un entorno de experimentación monousuario dentro de un entorno de chat con herramientas. Al trasladarlo a un backend multitenant en producción conectado a WhatsApp, se requería una arquitectura que pudiera:
1. Gestionar conversaciones multi-turno con creadores manteniendo contexto e identidad (Rick Rubin).
2. Orquestar diferentes flujos de interacción: charla informal, mayéutica de trinchera (extracción de escena y fricción), auditorías de cuenta y generación de guiones técnicos estructurados.
3. Incorporar bucles de retroalimentación de calidad (loops cerrados de evaluación) sin que el LLM caiga en bucles infinitos o derive sin control.
4. Soportar bifurcaciones tanto reactivas (mensajes entrantes de WhatsApp) como proactivas autónomas (auditorías, chispas de mercado, indagación de inactividad).

## Decision
Implementar el motor central como un **State Graph** tipado e inmutable (`RickGraphEngine` y `GraphState`) inspirado en los principios de LangGraph y sistemas de flujo de estado funcional:
- El estado `GraphState` es un `TypedDict` exhaustivo con modelos Pydantic (`CreatorProfile`, `ScriptDraft`, `ScriptBlock`, `EvaluationResult`, etc.).
- Las transiciones se ejecutan mediante nodos funcionales puros (`rick_strategist_node`, `guionista_node`, `evaluator_node`, `routine_reporter_node`, `governor_node`, `brand_health_node`, `proactive_spark_node`, `trench_inquiry_node`) y enrutadores condicionales (`quality_loop_router`).
- Todas las actualizaciones de estado pasan por la función pura `update_state(state, **kwargs)`.
- El flujo reactivo frente al proactivo se decide en la entrada del grafo mediante el campo `trigger_type`.

## Alternatives Considered

### 1. Cadenas lineales fijas (Sequential Chains / LangChain)
- **Pros:** Fácil de conceptualizar inicialmente.
- **Cons:** Incapaz de manejar ciclos iterativos de optimización (evaluator-optimizer), bifurcaciones condicionales dependientes de la respuesta del usuario ni interrupciones del gobernador proactivo.
- **Rejected:** Muy rígido; no modela la naturaleza interactiva ni la iteración de calidad de un guion.

### 2. Agente Autónomo ReAct no estructurado (ReAct Loop libre)
- **Pros:** Máxima flexibilidad para que el modelo decida herramientas en cualquier momento.
- **Cons:** Comportamiento no determinista, alto consumo de tokens, riesgo de alucinación de llamadas a herramientas, latencia impredecible inaceptable para SLAs de WhatsApp ($< 200$ ms ACK), y dificultad extrema para testing unitario determinista.
- **Rejected:** Inestable y costoso para un producto de producción multitenant.

## Consequences
- **Positivas:**
  - Control granular sobre cada paso del ciclo de vida de la conversación.
  - Testabilidad del 100%: 82 pruebas automatizadas corren en $< 1$ segundo sin llamadas de red obligatorias ni mocks frágiles.
  - Separación clara entre decisiones estratégicas (RICK), generación técnica (Guionista), auditoría (Evaluador) y entrega (WhatsApp Formatter).
- **Compromisos:**
  - Nuevos nodos requieren definir su contrato de tipos en `GraphState`.
