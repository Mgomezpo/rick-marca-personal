# Todo List: RICK Multitenant Agent Engine
## Tareas de Implementación Autónoma para `/goal`

> Cada tarea sigue el ciclo TDD (Red -> Green -> Refactor -> Checkpoint).  
> Marcar las casillas `[x]` a medida que se completen.

---

## Fase 0: Control de Versiones y Branching (`git-workflow-and-versioning`)

### Task 0: Inicializar Repositorio Git y Crear Feature Branch
**Description:** Inicializar el repositorio Git en la raíz del proyecto, configurar `.gitignore` para no filtrar credenciales ni entornos virtuales, crear el commit inicial en `main` y abrir la rama de desarrollo `feature/rick-agent-engine`.
**Acceptance criteria:**
- [x] Git inicializado en la raíz del proyecto.
- [x] `.gitignore` protegiendo `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.agents`.
- [x] Rama de trabajo activa `feature/rick-agent-engine`.
- [x] Commit inicial con Conventional Commits: `chore: initial workspace structure and task plan`.
**Verification:**
- [x] `git status` muestra working tree limpio en rama `feature/rick-agent-engine`.
**Dependencies:** None  
**Files likely touched:**
- `.gitignore`  
**Estimated scope:** S (1 archivo)

---

## Fase 1: Cimientos, Entorno y Esquema de Estado (Core State)

### Task 1: Configurar Dependencias del Proyecto y Entorno de Tests
**Description:** Crear `pyproject.toml` con las dependencias requeridas (`fastapi`, `uvicorn`, `pydantic`, `pytest`, `supabase`, `httpx`, `python-dotenv`) y verificar la suite base de pytest.
**Acceptance criteria:**
- [x] `pyproject.toml` creado con dependencias y configuración de `pytest`.
- [x] `tests/__init__.py` y `src/__init__.py` inicializados.
- [x] Entorno ejecuta `pytest tests/` sin fallos.
- [x] Commit atómico: `chore: setup project dependencies and pytest structure`.
**Verification:**
- [x] `pytest tests/` ejecuta con código 0 o sin crash.
**Dependencies:** Task 0  
**Files likely touched:**
- `pyproject.toml`
- `src/__init__.py`
- `tests/__init__.py`  
**Estimated scope:** S (1-2 archivos)

---

### Task 2: Definir el State Schema del Grafo (`core-state`)
**Description:** Diseñar los modelos Pydantic y `TypedDict` que representan el estado inmutable del grafo de RICK (`GraphState`), incluyendo perfil del creador, historial de conversación, contexto de referentes, learnings acumulados, borrador del guion y estado del loop de evaluación.
**Acceptance criteria:**
- [x] `GraphState` definido con tipado estricto en `src/graph/state.py`.
- [x] Modelos de datos para `CreatorProfile`, `ScriptDraft` (Hook, Desarrollo, Cierre con Texto, Intención, Cámara), `EvaluationResult`, `WinningPattern`, `LearningItem`.
- [x] Funciones de serialización y actualización funcional de estado.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_state.py`
**Dependencies:** Task 1  
**Files likely touched:**
- `src/graph/state.py`
- `tests/test_state.py`  
**Estimated scope:** S (2 archivos)

---

## Checkpoint 1: Base de Tipos y Estado Verificada
- [x] `pytest -v tests/test_state.py` en verde.
- [x] Estado inmutable y serializable a JSON.

---

## Fase 2: Motor de la Matriz y Radares de Mercado (`matrix-engine`)

### Task 3: Implementar Cálculo de Medianas y Métricas Relativas
**Description:** Crear el calculador de medianas por cuenta y rendimiento relativo ($R = \text{views} / \text{mediana}$), con soporte tanto para cuentas de referentes como para la cuenta propia del creador.
**Acceptance criteria:**
- [x] Función `calculate_account_median(views_list)` que descarta ceros o nulos y calcula la mediana exacta.
- [x] Función `calculate_relative_performance(views, median)` con clasificaciones automáticas (`> 1.5x` ganador, `< 0.7x` bajo).
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_matrix_metrics.py`
**Dependencies:** Task 2  
**Files likely touched:**
- `src/matrix/metrics.py`
- `tests/test_matrix_metrics.py`  
**Estimated scope:** S (2 archivos)

---

### Task 4: Extractor de Patrones Ganadores y Doble Radar (Cabecera + Discovery)
**Description:** Implementar el extractor de las 10 columnas y el motor de descubrimiento que busca tanto en los referentes de cabecera guardados en Supabase como en el radar amplio del nicho.
**Acceptance criteria:**
- [x] Modelo `MatrixRow` con las 10 columnas validadas.
- [x] Extractor `find_winning_patterns(rows)` que agrupa por tipo de hook + formato + emoción con $R \ge 1.5$.
- [x] Soporte para consulta de referentes fijos (`brand_referents`) y descubrimiento de tendencias.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_matrix_analyzer.py`
**Dependencies:** Task 3  
**Files likely touched:**
- `src/matrix/models.py`
- `src/matrix/analyzer.py`
- `tests/test_matrix_analyzer.py`  
**Estimated scope:** M (3 archivos)

---

## Checkpoint 2: Motor de Matriz Completamente Operativo
- [x] `pytest -v tests/test_matrix_metrics.py tests/test_matrix_analyzer.py` en verde.
- [x] Detección precisa de patrones ganadores con evidencia $\ge 3$ piezas.

---

## Fase 3: RICK Estratega, Guionista Técnico y Loop de Calidad

### Task 5: Nodo RICK de Extracción Creativa y Mayéutica (Tono Rubin)
**Description:** Implementar el orquestador conversacional que hace preguntas simples, aplica la regla de los 3 porqués y extrae anécdotas reales del creador antes de pasar a la fase de guionismo.
**Acceptance criteria:**
- [x] Prompt canónico de RICK enfocado en conversación fluida, preguntas reflexivas y extracción de vivencias.
- [x] Enrutador de intención (`chat`, `extract_story`, `generate_script`, `view_report`).
- [x] Cero sermones de IA o introducciones acartonadas.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_rick_node.py`
**Dependencies:** Task 2  
**Files likely touched:**
- `src/agents/rick.py`
- `src/agents/prompts.py`
- `tests/test_rick_node.py`  
**Estimated scope:** M (3 archivos)

---

### Task 6: Implementar el Nodo Guionista Técnico (Hook, Desarrollo, Cierre)
**Description:** Crear el generador de guiones que monta la historia extraída por RICK sobre la estructura empírica de la matriz, desglosando cada bloque en `Texto` hablado, `Intención` psicológica y dirección de `Cámara`.
**Acceptance criteria:**
- [x] Nodo `guionista_node(state)` con los tres bloques canónicos: `HOOK`, `DESARROLLO`, `CIERRE / CTA`.
- [x] Cada bloque incluye `Texto`, `Intención` y `Cámara`.
- [x] Calibrado a la duración en segundos del patrón ganador.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_guionista.py`
**Dependencies:** Task 4, Task 5  
**Files likely touched:**
- `src/agents/guionista.py`
- `tests/test_guionista.py`  
**Estimated scope:** S (2 archivos)

---

### Task 7: Implementar el Loop de Calidad (Anti-Plagio + Anti-Slop + Simulación)
**Description:** Implementar el bucle evaluador-optimizador que audita el guion en tres filtros: (1) Verificador de similitud (<5 palabras seguidas del referente), (2) Checklist anti-slop, y (3) Simulador de probabilidad respaldado en $n$ piezas.
**Acceptance criteria:**
- [x] Filtro anti-plagio que compara el campo `Texto` contra los videos referentes.
- [x] Nodo `antislop_node(state)` que califica naturalidad, tono y ausencia de frases de gurú.
- [x] Arista condicional: si score $< 8$ o hay plagio detectado, reintenta con feedback (máximo 3 intentos).
- [x] Cálculo de estimación (Alta/Media/Baja) y confianza empírica.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_quality_loop.py`
**Dependencies:** Task 6  
**Files likely touched:**
- `src/agents/evaluator.py`
- `src/graph/edges.py`
- `tests/test_quality_loop.py`  
**Estimated scope:** M (3 archivos)

---

## Checkpoint 3: Loop y Calidad Verificados
- [x] `pytest -v tests/test_guionista.py tests/test_quality_loop.py` en verde.
- [x] Rechazo automático de plagios y clichés; aprobación de guiones auténticos.

---

## Fase 4: Auditoría de Cuenta Propia, Reporte y Canal WhatsApp

### Task 8: Módulo de Auditoría de Cuenta Propia y Aprendizajes (`routine-reporter`)
**Description:** Implementar el servicio que audita las publicaciones del propio creador, mide su rendimiento contra su mediana personal, genera aprendizajes (`procedural_learnings`) y arma el reporte estratégico semanal.
**Acceptance criteria:**
- [x] Función `audit_personal_account(posts, median)` que identifica aciertos y fallos propios.
- [x] Generación automática de `LearningItem` para guardar en base de datos.
- [x] Formateador del reporte semanal conciso para WhatsApp (1-2 veces por semana).
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_routine_reporter.py`
**Dependencies:** Task 3, Task 4  
**Files likely touched:**
- `src/agents/routine.py`
- `tests/test_routine_reporter.py`  
**Estimated scope:** M (2 archivos)

---

### Task 9: Compilación del Grafo y Formateador Conversacional de WhatsApp
**Description:** Unir todos los nodos y aristas en `src/graph/engine.py` y crear el formateador de salida que convierte el guion y los datos en un mensaje de WhatsApp natural, limpio y sin caracteres extraños.
**Acceptance criteria:**
- [x] Grafo compilado ejecutable de inicio a fin.
- [x] Formato de mensaje WhatsApp limpio: Hook, Desarrollo y Cierre legibles, con nota concisa de simulación (sin markdown recargado).
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_graph_engine.py`
**Dependencies:** Task 7, Task 8  
**Files likely touched:**
- `src/graph/engine.py`
- `src/graph/formatter.py`
- `tests/test_graph_engine.py`  
**Estimated scope:** M (3 archivos)

### Task 10: Persistencia Supabase (`IrealDemo`) y Webhook FastAPI
**Description:** Conectar el repositorio de Supabase con aislamiento multitenant por `user_id`, y exponer el endpoint FastAPI `/webhook/whatsapp` con respuesta ACK inmediata (<200ms) y procesamiento en background.
**Acceptance criteria:**
- [x] Repositorio Supabase para perfiles, learnings y piezas.
- [x] Endpoint `POST /webhook/whatsapp` con ACK < 100ms y BackgroundTask.
- [x] Pruebas end-to-end con mocks de red.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_api_webhook.py`
**Dependencies:** Task 9  
**Files likely touched:**
- `src/db/repository.py`
- `src/api/app.py`
- `src/api/webhook.py`
- `tests/test_api_webhook.py`  
**Estimated scope:** M (4 archivos)

---

### Task 11: Simulación Conversacional de Punta a Punta y Tuning de UX
**Description:** Ejecutar una batería de pruebas de conversación multi-turno simulando usuarios reales en WhatsApp usando los perfiles de prueba `@casidonovan` (referente) y `@miguel_gomezpo` (creador). Calibrar la experiencia de usuario (UX) para asegurar que el flujo sea natural, no se trabe, responda con calidez y elegancia, y maneje caídas de scraping con fallbacks robustos.
**Acceptance criteria:**
- [x] Batería de tests multi-turno en `tests/test_conversation_ux.py` cubriendo:
  1. Saludo y mayéutica Rubin (preguntas reflexivas).
  2. Aterrizaje de una anécdota vaga con la regla de los 3 porqués.
  3. Extracción de patrones de `@casidonovan` y ensamblado de guion.
  4. Auditoría de cuenta propia con datos de `@miguel_gomezpo` y reporte de learnings.
- [x] Manejo de contingencias (si Apify/scraping falla o tarda, degradación elegante con datos en caché o mensaje claro).
- [x] Tuning del UX: respuestas limpias, legibles en móvil, cero fricción o formatos rotos.
**Verification:**
- [x] Tests pasan: `pytest -v tests/test_conversation_ux.py`
**Dependencies:** Task 10  
**Files likely touched:**
- `tests/test_conversation_ux.py`
- `src/graph/formatter.py`
- `src/agents/rick.py`  
**Estimated scope:** M (3 archivos)

---

## Checkpoint 4: Sistema Completo y UX de Alta Gama Verificados
- [x] Suite completa en verde: `pytest -v tests/`
- [x] Batería de conversación multi-turno con `@casidonovan` y `@miguel_gomezpo` aprobada.
- [x] Tiempos de respuesta y formateo de WhatsApp verificados al estándar top tier.

---

## Fase 5: Despliegue en Producción y Verificación en Vivo (`shipping-and-launch`)

### Task 12: Containerización y Configuración de Producción
**Description:** Crear el `Dockerfile` optimizado en Python 3.11-slim, scripts de arranque, archivo `.dockerignore` y asegurar que la aplicación pase todas las auditorías de seguridad y variables de entorno antes del despliegue.
**Acceptance criteria:**
- [ ] `Dockerfile` multi-stage ligero creado y probado localmente.
- [ ] Endpoint `GET /health` responde estado del sistema y conectividad Supabase en JSON.
- [ ] Manejo seguro de secretos mediante variables de entorno de producción.
**Verification:**
- [ ] Build local de contenedor o validación de configuración exitosa.
- [ ] `pytest tests/test_api_webhook.py -k test_health` en verde.
**Dependencies:** Task 11  
**Files likely touched:**
- `Dockerfile`
- `.dockerignore`
- `src/api/app.py`  
**Estimated scope:** S (2 archivos)

---

### Task 13: Despliegue en Producción (Cloud Run / HTTPS) y Smoke Test en Vivo
**Description:** Desplegar el contenedor a producción (Cloud Run / servidor cloud con HTTPS), obtener la URL pública de webhook y ejecutar un smoke test enviando un payload real de verificación contra la URL pública en vivo.
**Acceptance criteria:**
- [ ] Servicio desplegado en producción con URL pública segura (`https://...`).
- [ ] Healthcheck `GET /health` devuelve 200 OK en vivo.
- [ ] Smoke test del endpoint webhook responde en menos de 200 ms en vivo.
- [ ] URL documentada y lista para vincular a Meta WhatsApp Business API.
**Verification:**
- [ ] Petición HTTP en vivo a la URL de producción responde 200 OK.
**Dependencies:** Task 12  
**Files likely touched:**
- `deploy.sh` o configuración de despliegue
- `README.md` (con URL pública y guía de conexión a WhatsApp)  
**Estimated scope:** S (2 archivos)

---

## Checkpoint 5: Despliegue en Producción 100% Verificado
- [ ] URL pública HTTPS operativa y respondiendo.
- [ ] Conectividad verificada con Supabase y procesamiento asíncrono activo.
- [ ] RICK en vivo y disponible para recibir mensajes de WhatsApp en producción.

---

## Fase 6: Auditoría Integral de Seguridad, Rendimiento y Release Final

### Task 14: Auditoría de Seguridad y Rendimiento (`security-and-hardening` + `performance-optimization`)
**Description:** Ejecutar auditorías con los subagentes `security-auditor` y `web-performance-auditor`, verificar que no existan secretos expuestos, validar la política RLS en Supabase, auditar vulnerabilidades en dependencias (`pip-audit`) y certificar que la latencia del webhook se mantenga bajo el SLA de 200 ms.
**Acceptance criteria:**
- [ ] Escaneo de dependencias sin vulnerabilidades críticas ni altas.
- [ ] Aislamiento de tenants en Supabase auditado (un usuario jamás ve datos de otro).
- [ ] Latencia del webhook confirmada en $< 200\text{ ms}$.
- [ ] Aprobación de los subagentes `security-auditor` y `code-reviewer`.
**Verification:**
- [ ] Reporte de seguridad limpio y tests de latencia pasando.
**Dependencies:** Task 13  
**Files likely touched:**
- `SECURITY.md`
- `src/api/webhook.py`  
**Estimated scope:** S (2 archivos)

---

### Task 15: Merge a `main`, Tagging Semántico `v1.0.0` y Changelog (`git-workflow-and-versioning`)
**Description:** Finalizar el flujo de trabajo de Git fusionando la rama `feature/rick-agent-engine` en `main`, crear la etiqueta de versión semántica `v1.0.0`, y documentar el `CHANGELOG.md` con todos los componentes entregados.
**Acceptance criteria:**
- [ ] Merge limpio sin conflictos de `feature/rick-agent-engine` a `main`.
- [ ] Git tag `v1.0.0` creado.
- [ ] `CHANGELOG.md` actualizado con el detalle de las capacidades entregadas.
- [ ] Working tree limpio en `main`.
**Verification:**
- [ ] `git branch --show-current` devuelve `main`.
- [ ] `git tag -l` muestra `v1.0.0`.
**Dependencies:** Task 14  
**Files likely touched:**
- `CHANGELOG.md`  
**Estimated scope:** S (1 archivo)

---

## Checkpoint 6: Certificación y Release Final (`v1.0.0`)
- [ ] Repositorio en rama `main` con etiqueta `v1.0.0`.
- [ ] Auditoría de seguridad y rendimiento aprobada.
- [ ] Motor RICK en producción, conectado a WhatsApp y funcionando con calidad máxima.



