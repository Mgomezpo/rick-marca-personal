# ADR-004: Bucle Evaluador-Optimizador Anti-Plagio y Anti-Slop

## Status
Accepted

## Date
2026-10-18

## Context
La generación de guiones mediante LLMs convencionales sufre de tres problemas endémicos en la creación de contenido para redes sociales:
1. **Slop Corporativo e IA:** Uso automático de clichés ("en este mundo cambiante", "descubre el secreto", "desata tu potencial", "revoluciona tu marca") que restan autenticidad y autoridad al creador.
2. **Riesgo de Plagio Involuntario:** Al alimentar al modelo con videos ganadores de referentes para inspirar ganchos, los LLMs tienden a reproducir frases literales o secuencias completas del texto original.
3. **Falta de Rigor Técnico:** Los guiones convencionales entregan solo "texto para leer en teleprompter", sin dirección de cámara ni intención psicológica de actuación.

## Decision
Implementar un **Evaluator-Optimizer Loop cerrado** (`src/agents/evaluator.py`, `src/graph/edges.py`, `src/agents/guionista.py`):
1. **Estructura Canónica en 3 Bloques:** Todo guion generado se estructura obligatoriamente en tres bloques (`HOOK`, `DESARROLLO`, `CIERRE / CTA`), cada uno conteniendo:
   - `Texto`: Lo que el creador dice en voz alta.
   - `Intención`: La actitud y objetivo psicológico de la toma.
   - `Cámara`: La dirección física de encuadre, mirada y lenguaje corporal.
2. **Filtro Anti-Plagio Determinista de n-gramas:**
   - Algoritmo que tokeniza el borrador del guion y los textos de referencia de benchmark.
   - Si detecta $\ge 5$ palabras contiguas idénticas a cualquier post referente, la pieza es rechazada automáticamente con una penalización y una lista de coincidencias exactas.
3. **Editor Anti-Slop con Lista Negra:**
   - Inspecciona el guion buscando clichés corporativos y frases robóticas predefinidas.
   - Penaliza el puntaje de evaluación e instruye al Guionista sobre qué términos deben eliminarse.
4. **Simulador Empírico de Retención:**
   - Clasifica la probabilidad de éxito de la pieza en Alta, Media o Baja, respaldada por la cantidad de piezas ganadoras análogas identificadas en el nicho.
5. **Enrutador de Bucle Cerrado (`quality_loop_router`):**
   - Si el guion no supera el umbral de aprobación ($score \ge 80$) o falla el filtro anti-plagio, el grafo re-enruta el estado de vuelta al nodo Guionista con las correcciones hasta un máximo de 3 iteraciones antes de la entrega final.

## Alternatives Considered

### 1. Instruir al Guionista en el prompt sin evaluador separado
- **Pros:** Una sola llamada al LLM (menor costo por guion).
- **Cons:** Falla frecuentemente. Los modelos suelen ignorar directivas negativas ("no uses clichés") en prompts largos cuando están concentrados en generar contenido creativo.
- **Rejected:** La evaluación separada e independiente es fundamental para garantizar estándares editoriales profesionales.

### 2. Evaluación subjetiva libre por otro LLM sin reglas de código
- **Pros:** Flexible.
- **Cons:** No garantiza matemáticamente la ausencia de plagio literal (un LLM puede no notar una coincidencia de 6 palabras consecutivas).
- **Rejected:** El filtro de plagio debe ser exacto y determinista en Python, no probabilístico.

## Consequences
- **Positivas:**
  - Guiones 100% libres de plagio literal de los referentes.
  - Supresión activa de lenguaje robótico y corporativo cliché.
  - Entrega enriquecida con dirección técnica de actuación y cámara.
- **Compromisos:**
  - En caso de borradores deficientes, puede requerir hasta 2-3 iteraciones internas de corrección en segundo plano.
