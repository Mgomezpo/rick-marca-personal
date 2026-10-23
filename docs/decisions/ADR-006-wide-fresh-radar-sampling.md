# ADR-006: Muestreo Amplio de Radar, Exclusión Anti-Solapamiento y Rotación de Creadores

## Status
Accepted

## Date
2026-10-19

## Context
El sistema de loops proactivos de RICK detonaba chispas de mercado (`market_spark`) basadas en los referentes de cabecera de cada creador. Sin embargo, en un entorno de alta frecuencia existían dos riesgos críticos:
1. **Fatiga de Referentes:** Si un creador cuenta con pocos referentes de cabecera, el motor podía sugerir repetidamente patrones del mismo referente en ventanas cortas de tiempo.
2. **Solapamiento y Repetición de Posts:** Un post viral específico de un referente podía ser seleccionado múltiples veces en distintas semanas, erosionando la frescura percibida por el usuario en WhatsApp.
3. **Escasez de Diversidad Temática:** Los creadores de alto impacto necesitan referencias cruzadas con un grupo más amplio de referentes en su nicho para descubrir ángulos laterales y anomalías de mercado antes de que se vuelvan clichés.

## Decision
Implementar en `src/matrix/radar_ingestion.py` y `src/matrix/wide_radar.py` una política de muestreo amplio y rotación determinística:
1. **Pool Amplio de Referentes (Wide Radar Pool):**
   - El radar ingiere periódicamente un pool ampliado de hasta 20 referentes de la misma vertical o nicho del creador.
   - Aplica un tope máximo de posts analizados por creador (`max_posts_per_creator=5`) para evitar que un único creador con alta frecuencia domine el dataset.
2. **Exclusión Estricta Anti-Solapamiento (30 Días):**
   - Se mantiene un registro persistente de identificadores de posts utilizados (`used_post_ids`).
   - Todo post que haya detonado una chispa para el usuario es excluido automáticamente de futuras selecciones durante 30 días naturales.
3. **Rotación Forzada de Creadores (Cooldown de 7 Días):**
   - Tras seleccionar un referente para una chispa proactiva, dicho referente entra en un período de enfriamiento de 7 días para ese usuario, forzando al algoritmo a rotar hacia otros creadores del radar.
4. **Fallback Local y Rendimiento R >= 2.0x:**
   - La selección prioriza rigurosamente patrones con rendimiento relativo $R \ge 2.0\times$ sobre la mediana del referente. Si el pool fresco no alcanza el umbral, se recurre a patrones históricos validados garantizando que el usuario nunca reciba sugerencias débiles.

## Alternatives Considered

### 1. Muestreo puramente aleatorio entre referentes
- **Pros:** Muy simple de programar.
- **Cons:** Riesgo de seleccionar posts mediocres o repetir el mismo referente dos días seguidos por simple varianza estocástica.
- **Rejected:** Incompatible con el estándar de curaduría de RICK.

### 2. Base de datos relacional pesada para tracking de cada post visualizado
- **Pros:** Soporta consultas complejas SQL.
- **Cons:** Overhead de latencia en la ingesta periódica y bloqueos innecesarios en la caché caliente de $< 50$ms.
- **Rejected:** El tracking en memoria y clave-valor en Supabase es suficiente y ofrece latencia sub-milisegundo.

## Consequences
- **Positivas:**
  - Garantiza frescura total en las chispas proactivas de WhatsApp.
  - Cero repetición de posts durante 30 días y rotación garantizada de creadores cada 7 días.
  - Latencia de consulta en memoria $< 50$ms verificada en pruebas automatizadas.
- **Compromisos:**
  - Requiere mantener al menos 3 a 5 referentes por nicho en el pool ampliado para una rotación saludable.
