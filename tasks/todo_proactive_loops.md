# Checklist de Tareas: Loops Proactivos y Radar "Wide & Fresh"
## Seguimiento de Ejecución (Solo iniciar tras aprobación del usuario)

---

### Fase 1: Gobernador y Ventana de Inactividad (`constraint-driven-development`)
- [x] **Task 1.1:** Regla de 42h para `trench_inquiry` en `src/graph/governor.py`.
- [x] **Task 1.2:** Ventana de entrega al final del día (17:00 a 19:30 hora local).
- [x] **Task 1.3:** Tests unitarios en `tests/test_governor.py` validando rechazo antes de las 42h, rechazo antes de las 17:00 y aprobación dentro de la ventana.

### Fase 2: Tono e Identidad de RICK como Miembro de Equipo (`idea-refine`)
- [x] **Task 2.1:** Actualizar `RICK_CANONICAL_SYSTEM_PROMPT` en `src/agents/prompts.py` (lenguaje de complicidad de equipo: "nuestro canal", "revisemos").
- [x] **Task 2.2:** Ajustar los prompts y respuestas de `src/agents/rick.py`, `src/agents/trench.py` y `src/agents/spark.py`.
- [x] **Task 2.3:** Validar en `tests/test_rick_node.py` y `tests/test_conversation_ux.py` el tono de equipo y ausencia de frases de consultor externo.

### Fase 3: Motor de Radar "Wide & Fresh" y Anti-Solapamiento (`api-and-interface-design` + `incremental-implementation`)
- [x] **Task 3.1:** Implementar función `sample_wide_radar` (tope de 3 posts recientes por creador sobre pool de 15–25 cuentas) en `src/matrix/analyzer.py`.
- [x] **Task 3.2:** Implementar memoria de rotación y exclusión de posts ya utilizados (`rotate_creator_patterns`).
- [x] **Task 3.3:** Suite de pruebas en `tests/test_wide_radar.py` validando eliminación de duplicados, recencia y rotación.

### Fase 4: Desacople de Ingesta y Orquestación del Grafo (`graph-engineering` + `ci-cd-and-automation`)
- [ ] **Task 4.1:** Servicio de ingesta desacoplado en background para el radar.
- [ ] **Task 4.2:** Integración con `RickGraphEngine` garantizando consultas a la matriz indexada en $< 50$ms sin scraping en vivo durante la llamada.
- [ ] **Task 4.3:** Endpoint `POST /api/proactive/tick` en `src/api/app.py` preparado para triggers periódicos.
- [ ] **Task 4.4:** Suite completa de pruebas en verde (`pytest -v`).
