# ADR-007: Arquitectura de Contenido Multidimensional: Sagas, Pilares, Planes y Piezas Sueltas

## Status
Accepted

## Date
2026-10-19

## Context
El sistema RICK atiende a creadores y profesionales que producen contenido para redes sociales (Reels, TikTok, Shorts). Históricamente, muchas herramientas de gestión de contenidos imponen una jerarquía rígida ("todo post debe pertenecer a un pilar, y todo pilar debe pertenecer a un plan de campaña"). 

Esta jerarquía forzada entra en conflicto directo con la realidad del creador en la trinchera:
1. **Piezas Espontáneas y Sueltas:** Muchas de las mejores ideas nacen de una anécdota inmediata (un quiebre con un cliente, una venta fallida esa mañana) que debe redactarse en 45 segundos sin exigir al usuario clasificarla previamente en un pilar o plan.
2. **Pilares de Marca Desacoplados:** Un creador puede tener pilares estratégicos (ej. *Mentalidad*, *Estrategia de Precios*, *Ventas B2B*) para balancear su calendario, pero muchas piezas de un pilar no forman parte de ningún plan o campaña formal.
3. **Sagas y Miniseries Episódicas:** Ciertas lecciones o historias complejas requieren dividirse en múltiples entregas ("Parte 1", "Parte 2"). Estas piezas necesitan continuidad narrativa: el gancho del episodio 2 debe conectar con la entrega anterior (*"Ayer vimos X, hoy el paso 2..."*) y el cierre debe ofrecer un cliffhanger hacia la siguiente entrega. Una saga puede pertenecer a un pilar o ser completamente independiente.
4. **Planes de Contenido y Campañas:** Lotes de contenido o calendarios mensuales con objetivos temporales específicos.
5. **Restricción de No Regresión:** En Supabase existen 132 piezas históricas generadas por 33 creadores activos. La solución debe ser 100% retrocompatible: **cero DDL destructivo (`ALTER`, `DROP`, `RENAME`)**, cero migraciones de datos obligatorias y cero regresiones sobre los tests existentes.

## Decision
Implementar una **Matriz de Combinatoria Libre** donde las cuatro dimensiones de contenido coexisten de manera completamente desacoplada y opcional:

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

### 1. Modelos de Dominio en Pydantic V2 (`src/graph/state.py`):
- Modelo `SeriesMetadata`:
  - `series_id: str`: Identificador de la saga.
  - `series_title: str`: Título temático de la saga.
  - `episode_index: int`: Índice de episodio (1-indexed).
  - `total_episodes: Optional[int]`: Total de episodios previstos (o `None` si es abierta).
  - `previous_piece_id: Optional[str]` y `next_piece_id: Optional[str]`.
- Extensión no destructiva de `ScriptDraft`:
  - `pilar: Optional[str] = None`
  - `series: Optional[SeriesMetadata] = None`
  - `plan_id: Optional[str] = None`
  - Los valores por defecto en `None` garantizan que cualquier instancia previa de `ScriptDraft` continúe funcionando sin mutación de estado ni errores de validación.

### 2. Persistencia y Mapeo en Supabase (`src/db/repository.py`):
- Se aprovecha la estructura nativa existente de `public.pieces`:
  - Columna `strategy_tag` (`text`, nullable): almacena `script.pilar` si existe.
  - Columna `plan_id` (`uuid`, nullable): almacena `script.plan_id` si existe.
  - Columna `idea_fields` (`jsonb`, default `{}`): almacena el bloque episódico `idea_fields["series"] = script.series.model_dump()` cuando `script.series` está presente.
  - Para piezas sueltas (`None`), `strategy_tag` y `plan_id` se guardan como `NULL`/`None` y `idea_fields` queda limpio como `{}`.
- Nuevos métodos de consulta estrictamente aislados por tenant:
  - `get_series_pieces(user_id: str, series_id: str) -> List[Dict[str, Any]]`: recupera episodios filtrados por `user_id` y ordenados por `episode_index`.
  - `get_pillar_pieces(user_id: str, pilar_name: str) -> List[Dict[str, Any]]`: recupera piezas filtradas por `user_id` y `strategy_tag == pilar_name`.
  - Se prohíbe cualquier consulta cross-tenant; el aislamiento multi-tenant se valida a nivel de query builder y repositorio.

### 3. Continuidad Narrativa y Cliffhangers en el Guionista (`src/agents/guionista.py`):
- Si `series is None`: mantiene la estructura autoconclusiva limpia de 3 bloques sin menciones forzadas.
- Si `series.episode_index > 1`: el hook conecta con la entrega previa (*"Ayer vimos la entrega anterior de X. Hoy en la parte Y: ..."*).
- Si `series.episode_index < series.total_episodes`: el cierre / llamado a acción propone un cliffhanger (*"En la parte Y+1 te cuento la solución definitiva..."*).
- Si es el episodio final de la saga: el cierre concluye el arco y llama a guardar la serie completa.

### 4. Orquestación Conversacional Mayéutica en RICK (`src/agents/rick.py`):
- Cuando el usuario comparte una historia densa o con múltiples lecciones (ej. "dos errores", "tres problemas"), RICK detecta el potencial multi-parte y pregunta en tono de socio creativo:
  *"¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"*
- Si el creador elige "una sola pieza", RICK respeta la decisión y genera la pieza autoconclusiva estándar de 45 segundos sin insistir.
- Si el creador elige "saga", RICK estructura la secuencia y genera el primer episodio con los metadatos de serie correspondientes.

## Alternatives Considered

### 1. Jerarquía Relacional Rígida en Base de Datos (Plans -> Pillars -> Sagas -> Pieces)
- **Pros:** Forzaba normalización relacional tradicional en tercera forma normal (3NF).
- **Cons:**
  - Imponía fricción inaceptable al creador por WhatsApp (imposible mandar una idea espontánea sin crear un plan y un pilar previo).
  - Requería migraciones destructivas `ALTER TABLE ... NOT NULL` en `pieces`, rompiendo las 132 piezas existentes.
- **Rejected:** Incompatible con la experiencia conversacional fluida de WhatsApp y con la regla de no regresión.

### 2. Tablas Separadas en PostgreSQL para Sagas (`public.sagas`) y Pilares (`public.pillars`)
- **Pros:** Modelado relacional explícito con claves foráneas (`FOREIGN KEY`).
- **Cons:**
  - Operaciones complejas de DDL en caliente en Supabase.
  - Riesgo de bloqueos de tabla (*table locks*) en producción.
  - Mayor latencia al requerir múltiples joins relacionales para recuperar un guion en el webhook ($< 200$ms SLA).
- **Rejected:** La columna JSONB nativa `idea_fields` de PostgreSQL y las columnas preexistentes `strategy_tag` y `plan_id` ofrecen la misma expresividad sin fricción operativa.

### 3. Dejar las sagas como texto libre sin metadatos estructurados
- **Pros:** No requería tocar modelos de datos.
- **Cons:** Imposible ordenar episodios programáticamente, imposible calcular estadísticas de saga, propenso a alucinaciones del LLM en los números de episodio.
- **Rejected:** La persistencia estructurada es indispensable para la escalabilidad del producto.

## Consequences

- **Positivas:**
  - **Flexibilidad Creativa Absoluta:** Cualquier combinación es válida (pieza suelta, pieza de pilar, saga sin pilar, saga dentro de pilar, pieza dentro de plan, etc.).
  - **100% Retrocompatible:** Las 132 piezas históricas y los 33 creadores continúan operando sin modificaciones.
  - **Aislamiento Multi-Tenant Estricto:** Imposibilidad matemática de mezclar sagas o pilares entre creadores gracias al filtrado obligatorio por `user_id`.
  - **Cero Migraciones Destructivas:** No se requiere ningún `ALTER TABLE` ni comando DDL en Supabase.
  - **Cero Regresiones:** Los 82 tests previos continúan pasando al 100% en verde.
- **Compromisos:**
  - Los clientes frontend o APIs externas deben consultar `idea_fields["series"]` para extraer los metadatos de serie cuando estén presentes.
