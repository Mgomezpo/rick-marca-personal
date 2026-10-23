# Todo List: Arquitectura de Contenido Multidimensional en RICK
## Tareas de Implementación Desacoplada y Segura (Sagas, Pilares, Planes y Piezas Únicas)

> **Estado:** Completado al 100% y Certificado  
> Cada tarea siguió el ciclo TDD (Red -> Green -> Refactor -> Checkpoint).  
> **Bar de Calidad:** 96 tests pasando en verde (100%). 0 regressions sobre los 82 tests previos. 0 DDL destructivo en Supabase.

---

## Fase 1: Modelos de Dominio y Contratos de Datos (`api-and-interface-design` + `source-driven-development`)

### Task 1.1: Definir Modelos Pydantic V2 para Metadatos de Series y Pilares
**Description:** Extender `src/graph/state.py` con los modelos canónicos `SeriesMetadata` (`series_id`, `series_title`, `episode_index`, `total_episodes`, `previous_piece_id`, `next_piece_id`) y actualizar `ScriptDraft` para incluir opcionalmente `pilar: Optional[str] = None`, `series: Optional[SeriesMetadata] = None` y `plan_id: Optional[str] = None`, preservando compatibilidad 100% con piezas existentes.
**Acceptance criteria:**
- [x] `SeriesMetadata` definido con validación estricta de tipos Pydantic V2 en `src/graph/state.py`.
- [x] `ScriptDraft` acepta campos opcionales `pilar`, `series`, `plan_id` con default `None`.
- [x] Serialización JSON probada sin mutar estados ni romper instancias previas de `ScriptDraft`.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_state.py`
- [x] Tests nuevos: `pytest -v tests/test_multidimensional_state.py`
**Dependencies:** None  
**Files touched:**
- `src/graph/state.py`
- `tests/test_multidimensional_state.py`  
**Estimated scope:** S (2 archivos)

---

## Checkpoint 1: Cimientos de Datos y Contratos Verificados
- [x] Modelos Pydantic V2 serializables a JSON (`.model_dump()`).
- [x] 100% retrocompatible: `ScriptDraft` sin serie ni pilar sigue siendo válido.
- [x] `pytest tests/test_state.py tests/test_multidimensional_state.py` en verde (9/9 tests).

---

## Fase 2: Repositorio Multi-Tenant y Persistencia en Supabase (`security-and-hardening` + `source-driven-development`)

### Task 2.1: Actualizar `save_piece` con Mapeo Multidimensional No Forzado
**Description:** Modificar `save_piece` en `src/db/repository.py` para que cuando un `ScriptDraft` tenga `pilar`, `plan_id` o `series`, estos se almacenen en `strategy_tag`, `plan_id` y dentro del JSONB `idea_fields` de `public.pieces`. Si no se definen, los campos quedan como `NULL` / `None` sin forzar ninguna categoría.
**Acceptance criteria:**
- [x] `save_piece` almacena `strategy_tag` si `script.pilar` está presente.
- [x] `save_piece` almacena `plan_id` si `script.plan_id` está presente.
- [x] `save_piece` guarda el bloque de serie dentro de `idea_fields["series"]` si `script.series` está presente.
- [x] Si es pieza suelta (`None`), guarda el registro limpio sin errores.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_api_webhook.py`
- [x] Tests nuevos: `pytest -v tests/test_repository_multidimensional.py`
**Dependencies:** Task 1.1  
**Files touched:**
- `src/db/repository.py`
- `tests/test_repository_multidimensional.py`  
**Estimated scope:** S (2 archivos)

---

### Task 2.2: Métodos de Consulta Aislados por Tenant para Sagas y Pilares
**Description:** Implementar en `SupabaseRepository` los métodos `get_series_pieces(user_id, series_id)` y `get_pillar_pieces(user_id, pilar_name)` garantizando aislamiento estricto por `user_id` para evitar cualquier fuga de datos entre creadores.
**Acceptance criteria:**
- [x] `get_series_pieces` retorna los episodios ordenados por `episode_index` estrictamente para el `user_id` solicitante.
- [x] `get_pillar_pieces` retorna las piezas del pilar solicitadas bajo `user_id`.
- [x] Ningún usuario puede consultar piezas de series pertenecientes a otro `user_id`.
**Verification:**
- [x] Tests de aislamiento y orden: `pytest -v tests/test_repository_multidimensional.py`
**Dependencies:** Task 2.1  
**Files touched:**
- `src/db/repository.py`
- `tests/test_repository_multidimensional.py`  
**Estimated scope:** S (2 archivos)

---

## Checkpoint 2: Persistencia y Consultas Multi-Tenant Verificadas
- [x] Inserción y lectura de piezas únicas, de pilares y de sagas probada en memoria y con cliente Supabase.
- [x] Cero interferencia con la tabla existente `pieces`.
- [x] Aislamiento RLS por `user_id` 100% verificado.

---

## Fase 3: Motor de Guiones con Continuidad de Sagas (`test-driven-development` + `code-simplification`)

### Task 3.1: Generación de Ganchos de Continuidad y Cliffhangers en `guionista.py`
**Description:** Enriquecer `generate_script_draft` en `src/agents/guionista.py` para que cuando se reciba un `SeriesMetadata` con `episode_index > 1`, el gancho enlace fluidamente con el episodio previo (*"Ayer vimos X, hoy el error #2..."*) y el cierre proponga el *cliffhanger* hacia el siguiente episodio.
**Acceptance criteria:**
- [x] Episodio 1 de saga: Cierre incluye cliffhanger hacia episodio 2.
- [x] Episodio 2+: Hook enlaza explícitamente con la entrega anterior.
- [x] Pieza única (sin serie): Mantiene estructura autoconclusiva limpia tradicional de 3 bloques sin menciones forzadas a otros videos.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_guionista.py`
- [x] Tests nuevos: `pytest -v tests/test_guionista_sagas.py`
**Dependencies:** Task 1.1  
**Files touched:**
- `src/agents/guionista.py`
- `tests/test_guionista_sagas.py`  
**Estimated scope:** S (2 archivos)

---

## Checkpoint 3: Continuidad Narrativa y Calidad de Guion Verificada
- [x] Guiones de saga con continuidad comprobada.
- [x] Guiones únicos mantienen su pegada de 45 segundos sin agregados artificiales.
- [x] Anti-plagio y Anti-slop pasando con score $\ge 8.5$.

---

## Fase 4: Orquestación Conversacional y Mayéutica de RICK (`idea-refine` + `doubt-driven-development`)

### Task 4.1: Propuesta Creativa No Forzada en `rick.py`
**Description:** Actualizar el enrutador conversacional en `src/agents/rick.py` para que cuando una historia o lección sea extensa/densa, RICK sugiera amablemente la opción de dividirla en una miniserie o dejarla en una sola pieza, respetando siempre la decisión del creador.
**Acceptance criteria:**
- [x] RICK detecta historias con múltiples puntos o lecciones densas.
- [x] Pregunta al creador en tono de socio: *"¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"*.
- [x] Si el usuario responde "una sola", genera la pieza única estándar sin insistir.
- [x] Si responde "saga", estructura los episodios con `SeriesMetadata`.
**Verification:**
- [x] Tests conversacionales: `pytest -v tests/test_conversation_ux.py`
- [x] Tests de nodo: `pytest -v tests/test_rick_node.py`
- [x] Tests nuevos de saga UX: `pytest -v tests/test_rick_sagas_ux.py`
**Dependencies:** Tasks 2.2 y 3.1  
**Files touched:**
- `src/agents/rick.py`
- `tests/test_rick_sagas_ux.py`  
**Estimated scope:** M (2 archivos)

---

## Checkpoint 4: Experiencia de Usuario en WhatsApp Verificada End-to-End
- [x] Flujo completo simulado por WhatsApp: creación de pieza única vs. creación de saga de 2 episodios.
- [x] Latencia del webhook confirmada en $< 200\text{ ms}$.
- [x] Todas las piezas persistidas correctamente en el repositorio.

---

## Fase 5: Documentación de Arquitectura y Auditoría de Release (`documentation-and-adrs` + `code-review-and-quality`)

### Task 5.1: Documentar Decisión Arquitectónica (ADR-007)
**Description:** Crear el archivo `docs/decisions/ADR-007-multidimensional-content-architecture.md` siguiendo la plantilla oficial de ADRs, detallando el contexto, requerimientos de combinatoria libre, decisión de persistencia en `pieces` vía JSONB `idea_fields`, alternativas descartadas y consecuencias para agentes y desarrolladores.
**Acceptance criteria:**
- [x] ADR-007 redactado y registrado en `docs/decisions/ADR-007-multidimensional-content-architecture.md`.
- [x] `docs/decisions/README.md` actualizado con el nuevo índice de ADRs (ADR-006 y ADR-007).
**Verification:**
- [x] Archivo ADR-007 existe y cumple la estructura estándar (Contexto, Decisión, Alternativas, Consecuencias).
**Dependencies:** Tasks 1.1 a 4.1  
**Files touched:**
- `docs/decisions/ADR-007-multidimensional-content-architecture.md`
- `docs/decisions/ADR-006-wide-fresh-radar-sampling.md`
- `docs/decisions/README.md`  
**Estimated scope:** S (3 archivos)

---

### Task 5.2: Actualizar Documento Maestro de Arquitectura (`ARQUITECTURA_RICK_MULTITENANT.md`)
**Description:** Incorporar la sección 12 en `ARQUITECTURA_RICK_MULTITENANT.md` documentando en profundidad la Arquitectura de Contenido Multidimensional: el diagrama de relaciones libres entre Sagas, Pilares, Planes y Piezas Únicas, la especificación de campos en `public.pieces` y el flujo conversacional de mayéutica para sugerir formatos sin imponerlos.
**Acceptance criteria:**
- [x] `ARQUITECTURA_RICK_MULTITENANT.md` enriquecido con la nueva sección 12 y diagrama Mermaid.
- [x] Explicación técnica de la retrocompatibilidad con las 132 piezas previas.
- [x] Índice y referencias actualizadas.
**Verification:**
- [x] Revisión de sintaxis Markdown y diagrama Mermaid sin errores de renderizado.
**Dependencies:** Task 5.1  
**Files touched:**
- `ARQUITECTURA_RICK_MULTITENANT.md`  
**Estimated scope:** S (1 archivo)

---

### Task 5.3: Actualizar README.md, CHANGELOG.md y Documentación de Apoyo
**Description:** Actualizar el `README.md` principal y `CHANGELOG.md` documentando las nuevas capacidades liberadas en la versión `v1.1.0` (Sagas, Pilares desacoplados, Ganchos de continuidad).
**Acceptance criteria:**
- [x] `README.md` documenta la capacidad de sagas y pilares y versionado v1.1.0.
- [x] `CHANGELOG.md` documenta el release `v1.1.0`.
- [x] `pyproject.toml` sincronizado a `1.1.0`.
**Verification:**
- [x] Documentación sincronizada con el estado real del repositorio.
**Dependencies:** Task 5.2  
**Files touched:**
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`  
**Estimated scope:** S (3 archivos)

---

### Task 5.4: Suite Completa de Tests (>95 tests) y Certificación de Calidad
**Description:** Ejecutar la suite completa de pruebas unitarias e integración asegurando cero regresiones sobre los 82 tests previos, auditar código con `code-reviewer` y verificar la definición de terminado.
**Acceptance criteria:**
- [x] Suite completa de tests ejecutada: 96 tests pasando al 100% en verde.
- [x] Cero regresiones en tests preexistentes (82/82 + 14 tests nuevos = 96/96).
- [x] Certificación de calidad multi-eje aprobada.
**Verification:**
- [x] `pytest -v` pasa al 100% con código de salida 0.
**Dependencies:** Tasks 5.1 a 5.3  
**Files touched:**
- `tests/`  
**Estimated scope:** S (1 archivo)

---

## Checkpoint Final: Aprobación y Certificación de Calidad
- [x] 0 regresiones (todos los tests previos pasan).
- [x] 0 alteraciones destructivas en Supabase (100% compatible con las 132 piezas existentes).
- [x] Documentación maestra (`ARQUITECTURA_RICK_MULTITENANT.md`, `ADR-007` y `README.md`) completa y de alto estándar técnico.
- [x] Sistema multidimensional 100% operativo y certificado.
