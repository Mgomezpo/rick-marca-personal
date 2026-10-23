# Master Plan: Arquitectura de Contenido Multidimensional en RICK
## Gestión Flexible y Desacoplada: Piezas Únicas, Pilares de Marca, Sagas y Planes

> **Estado:** Listo para Revisión del Usuario (No Proceder hasta Aprobación Explícita)  
> **Fecha:** 19 de Octubre, 2026  
> **Skills Aplicadas:** `using-agent-skills`, `planning-and-task-breakdown`, `source-driven-development`, `constraint-driven-development`, `security-and-hardening`, `test-driven-development`, `documentation-and-adrs`, `code-review-and-quality`.  
> **Regla de Oro:** **NO ROMPER NADA**. 100% retrocompatible con los 33 usuarios activos y las 132 piezas existentes en Supabase. Zero regressions sobre los 82 tests unitarios actuales.

---

## 1. Visión y Justificación Arquitectónica

El usuario determinó que el contenido no debe estar atrapado en una jerarquía rígida ("todo dentro de un plan" o "todo forzado a un pilar"). El sistema debe ser un **habilitador creativo multidimensional**:

```
                              ┌──────────────────────────────────┐
                              │     Dimensiones de Contenido     │
                              └────────────────┬─────────────────┘
                                               │
             ┌──────────────────┬──────────────┴─────┬─────────────────┐
             ▼                  ▼                    ▼                 ▼
     [1. Standalone]      [2. Pilar]           [3. Saga]         [4. Plan]
     Pieza única y        Asociada a un        Secuencia de      Campaña o lote
     espontánea de        pilar estratégico    episodios con     calendarizado
     trinchera sin        de marca para        gancho continuo   con objetivo
     clasificación        balance y voz        y cliffhanger     temporal
             │                  │                    │                 │
             └──────────────────┴──────────────┬─────┴─────────────────┘
                                               ▼
                              ┌──────────────────────────────────┐
                              │  Matriz de Combinatoria Libre    │
                              │  (Cualquier combinación válida)  │
                              └──────────────────────────────────┘
```

---

## 2. Source-Driven Development: Detección y Verificación de Fuentes Oficiales

### Stack Tecnológico Detectado (`pyproject.toml`):
* **Python:** `>= 3.11`
* **Pydantic:** `>= 2.8.0` (Sintaxis Pydantic V2: `BaseModel`, `Field`, `model_dump()`, validadores con `@field_validator`)
* **Supabase Python Client:** `>= 2.30.0` (PostgREST query builder con filtros `.eq()`, `.is_()`, `.contains()`)
* **FastAPI:** `>= 0.115.0`
* **PostgreSQL Engine:** Supabase PostgreSQL con JSONB nativo (`idea_fields`), RLS habilitado y columnas `strategy_tag` y `plan_id` ya presentes en `public.pieces`.

### Verificación de Fuentes Oficiales:
1. **Pydantic v2 Models (`pydantic>=2.8.0`):**
   * *Fuente:* https://docs.pydantic.dev/latest/concepts/models/
   * *Patrón Verificado:* Campos opcionales tipados con `Optional[T] = None`, exportación canónica mediante `.model_dump(exclude_none=True)` o `.model_dump()` sin mutación de estado.
2. **Supabase / PostgREST JSONB Filter & Upsert (`supabase>=2.30.0`):**
   * *Fuente:* https://supabase.com/docs/reference/python/insert y https://supabase.com/docs/reference/python/select
   * *Patrón Verificado:* Consultas seguras mediante query builder `table("pieces").select("*").eq("user_id", user_id)` parametrizadas para evitar cualquier inyección SQL. Filtros sobre JSONB mediante operadores PostgREST nativos.
3. **PostgreSQL JSONB Compatibility:**
   * *Fuente:* https://www.postgresql.org/docs/current/datatype-json.html
   * *Patrón Verificado:* Uso de la columna existente `idea_fields` de tipo `jsonb` con valor por defecto `{}`. No requiere migraciones destructivas `ALTER TABLE` ni bloqueos de esquema en caliente.

---

## 3. Matriz de Seguridad y Reglas de No Regresión (`security-and-hardening` + `constraint-driven-development`)

1. **Aislamiento Multi-Tenant Estricto:**
   * Toda consulta y guardado exige el `user_id` del tenant autenticado.
   * Si una pieza referencia una `series_id` o `plan_id`, el backend verifica que dicho plan o serie pertenezca estrictamente al mismo `user_id`. Prohibido vincular piezas a planes de otros creadores.
2. **Zero Breaking Changes en Base de Datos:**
   * La tabla `public.pieces` ya contiene:
     - `plan_id`: `uuid` (nullable)
     - `strategy_tag`: `text` (nullable)
     - `idea_fields`: `jsonb` (not null, default `{}`)
   * **Cero comandos DDL destructivos (`DROP`, `ALTER TYPE`, `RENAME`).** Todas las 132 piezas existentes siguen siendo 100% legibles sin migración de datos.
3. **Mantenimiento del Bar de Calidad (82/82 tests):**
   * Cualquier cambio debe mantener la suite completa de `pytest tests/` en verde.
   * La latencia del webhook de WhatsApp debe mantenerse $< 200\text{ ms}$ (procesamiento asíncrono en background tasks).

---

## 4. Desglose Vertical de Fases y Tareas (`planning-and-task-breakdown`)

El plan se divide en 4 fases verticales, con checkpoints de verificación intermedios:

### Fase 1: Modelos de Dominio y Contratos de Datos (Pydantic V2)
* **Objetivo:** Definir los metadatos de serie, pilar y plan sin romper los modelos existentes `ScriptDraft` y `GraphState`.
* **Archivos:** `src/graph/state.py`, `tests/test_state.py`.
* **Skill aplicada:** `api-and-interface-design`, `test-driven-development`.

### Fase 2: Repositorio Multi-Tenant y Consultas de Sagas en Supabase
* **Objetivo:** Actualizar `SupabaseRepository` para mapear `strategy_tag`, `plan_id` y `series_info` en `idea_fields`, además de proveer métodos de lectura para listar episodios de una saga y piezas por pilar.
* **Archivos:** `src/db/repository.py`, `tests/test_supabase_repository.py`.
* **Skill aplicada:** `source-driven-development`, `security-and-hardening`.

### Fase 3: Motor de Guiones: Ganchos de Continuidad y Sagas (Guionista Node)
* **Objetivo:** Dotar a `generate_script_draft` de la capacidad de generar ganchos de continuidad cuando se redacta un episodio secuencial ("Ayer te conté X... hoy vemos el paso 2") y cliffhangers de cierre, manteniendo la pieza única autoconclusiva por defecto.
* **Archivos:** `src/agents/guionista.py`, `tests/test_guionista.py`.
* **Skill aplicada:** `test-driven-development`, `code-simplification`.

### Fase 4: Orquestación Conversacional y Mayéutica de RICK
* **Objetivo:** RICK detecta cuándo una idea tiene potencial de saga o pilar, y ofrece amablemente las opciones al creador ("¿pieza única de 45s o miniserie de 2 partes?") sin forzarlo.
* **Archivos:** `src/agents/rick.py`, `tests/test_rick_node.py`, `tests/test_conversation_ux.py`.
* **Skill aplicada:** `idea-refine`, `doubt-driven-development`.

### Fase 5: Documentación de Arquitectura de Primera Clase y Registro de ADRs
* **Objetivo:** Aplicar con máximo rigor la skill `documentation-and-adrs` para documentar el *por qué* y no solo el *qué*, garantizando que la arquitectura completa del repositorio se mantenga actualizada y de nivel senior.
* **Entregables de Documentación:**
  1. `docs/decisions/ADR-007-multidimensional-content-architecture.md`: Contexto, requerimientos de no-bloqueo, decisión de combinatoria libre, alternativas evaluadas (jerarquía forzada en base de datos vs. desacople JSONB) y consecuencias operativas.
  2. `ARQUITECTURA_RICK_MULTITENANT.md`: Actualización exhaustiva del documento maestro de arquitectura, incorporando la sección 12 dedicada a la *Matriz de Contenido Multidimensional*, el diagrama Mermaid de interconexión (Sagas/Pilares/Planes), y el mapa de persistencia en `public.pieces`.
  3. `docs/decisions/README.md` y `README.md`: Indexación de ADR-007 y actualización del índice arquitectónico.
  4. Comentarios inline de trinchera: Documentar el *why* y los *gotchas* (ej. por qué `idea_fields` usa defaults no destructivos y cómo se previene fuga multi-tenant).
* **Archivos:** `docs/decisions/ADR-007-multidimensional-content-architecture.md`, `ARQUITECTURA_RICK_MULTITENANT.md`, `docs/decisions/README.md`, `README.md`, `CHANGELOG.md`.
* **Skill aplicada:** `documentation-and-adrs`, `code-review-and-quality`.

---

## 5. Matriz de Riesgos y Mitigaciones

| Riesgo Identificado | Impacto | Mitigación Arquitectónica |
| :--- | :---: | :--- |
| **Incompatibilidad con las 132 piezas existentes** | Alto | Campos de serie y pilar son completamente opcionales (`None`). Si `idea_fields` no tiene llave `series`, se trata como pieza única. |
| **Complejidad excesiva para el creador en WhatsApp** | Medio | RICK nunca envía formularios técnicos ni opciones confusas; habla como socio creativo con lenguaje limpio y coloquial. |
| **Cross-tenant data leak al buscar series** | Crítico | Todos los métodos en `repository.py` aplican `.eq("user_id", user_id)` y validan que el `series_id` solicitado pertenezca al usuario que lo invoca. |
| **Regresión en tests existentes** | Alto | Ejecución continua de `pytest tests/` en cada checkpoint tras cada tarea. |
