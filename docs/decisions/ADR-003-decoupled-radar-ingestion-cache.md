# ADR-003: Inversión del Radar de Mercado e Ingesta Desacoplada

## Status
Accepted

## Date
2026-10-19

## Context
El motor de RICK utiliza una **Matriz de 10 Columnas** (`MatrixRow`) para analizar el rendimiento relativo de reels en el nicho ($R = \text{views} / \text{mediana}$) y detectar patrones ganadores ($R \ge 1.5\times$).
En versiones preliminares, el radar intentaba consultar o scrapear cuentas de Instagram o APIs externas sincrónicamente durante el webhook de conversación o en el momento del tick proactivo.
Esto introducía graves problemas:
1. **Violación del SLA de latencia:** Scrapear o llamar APIs externas en vivo toma entre 3 y 15 segundos, haciendo imposible responder en $< 200$ ms o mantener una conversación ágil en WhatsApp.
2. **Fragilidad por rate limits y caídas:** Si la API externa fallaba o aplicaba rate limit, la interacción del usuario se bloqueaba.
3. **Fatiga de referentes:** Sin rotación, el sistema recomendaba repetidamente los mismos 2 o 3 referentes conocidos, perdiendo frescura y diversidad creativa.

## Decision
Implementar la **Inversión de la Ecuación del Radar** y el servicio desacoplado `RadarIngestionService` (`src/services/radar_ingestion.py` y `src/matrix/analyzer.py`):
1. **Ingesta Desacoplada en Segundo Plano:** Las publicaciones de un pool amplio de creadores (15 a 25 referentes por nicho) se ingieren asíncronamente mediante tareas en background o cron jobs.
2. **Caché Indexado Sub-50ms:** La matriz procesada se indexa en memoria/caché por `user_id`. Durante la ejecución de una conversación o tick proactivo, el acceso a los datos toma menos de 50 milisegundos sin llamadas externas en el camino crítico.
3. **Tope de Posts por Creador (`sample_wide_radar`):** Se limita a un máximo de 3 publicaciones ganadoras recientes por referente, evitando que un único creador con un video viral monopolice todas las recomendaciones.
4. **Memoria de Exclusión Anti-Solapamiento (30 días):** Las publicaciones ya utilizadas en guiones generados para el usuario se registran (`record_used_post`) y se excluyen activamente durante 30 días para evitar reciclar el mismo gancho o ángulo.
5. **Rotación de Creadores en Cooldown (7 días):** Si un referente ya inspiró una entrega reciente, se fuerza una rotación (`rotate_creator_patterns`) asignando una penalización temporal de 7 días.

## Alternatives Considered

### 1. Scraping en vivo durante la llamada al webhook
- **Pros:** Datos 100% frescos al milisegundo.
- **Cons:** Latencias de 5 a 20 segundos, rate limits de Instagram/Meta, bloqueos y fallos frecuentes en producción.
- **Rejected:** Inviable para un webhook de WhatsApp en producción.

### 2. Base de datos global sin aislamiento ni rotación
- **Pros:** Una única consulta SQL global.
- **Cons:** Mezcla referentes entre diferentes nichos y usuarios, y carece de control sobre qué piezas ya ha visto o usado cada creador individual.
- **Rejected:** Degrada la calidad y personalización del servicio multitenant.

## Consequences
- **Positivas:**
  - Latencia ultra-baja garantizada ($< 50$ ms para obtener patrones analizados).
  - Variedad y frescura creativa constante mediante la rotación obligatoria de referentes.
  - Cero dependencias bloqueantes durante el procesamiento del webhook de WhatsApp.
- **Compromisos:**
  - Requiere un job periódico de ingesta que mantenga actualizado el pool de publicaciones en el caché de la matriz.
