# ADR-002: Gobernador Anti-Spam y Cadencia de Loops Proactivos

## Status
Accepted

## Date
2026-10-19

## Context
A diferencia de un asistente pasivo que solo responde cuando el usuario escribe, RICK incluye capacidades autónomas proactivas (análisis de tendencias de mercado, auditoría de pilares desiertos e indagación socrática tras inactividad del creador).
Sin embargo, enviar mensajes proactivos en WhatsApp presenta riesgos críticos:
1. **Riesgo de bloqueo/spam:** Si un bot envía mensajes a deshoras (madrugada) o con demasiada frecuencia, los usuarios lo bloquean o reportan en WhatsApp, lo cual degrada la reputación del número ante Meta.
2. **Fatiga del creador:** Pings continuos cuando el creador no ha respondido generan fricción y abandono.
3. **Poco valor percibido (baja señal/ruido):** Notificaciones triviales o con patrones de mercado débiles dañan la credibilidad de RICK como mentor de trinchera.

## Decision
Crear el **Anti-Spam Governor** (`src/graph/governor.py`) como compuerta determinista obligatoria antes de cualquier emisión proactiva por WhatsApp:
1. **Bypass del usuario:** Los mensajes iniciados por el usuario (`trigger_type == "user_message"`) jamás son bloqueados por el gobernador.
2. **Ventana Hábil General (Quiet Hours):** Emisiones proactivas regulares (`market_spark`, `brand_health_audit`) solo están permitidas entre las **09:00 y las 19:00 hora local**.
3. **Ventana de Fin de Jornada para Indagación de Trinchera:** La indagación tras inactividad (`trench_inquiry`) solo puede ocurrir entre las **17:00 y las 19:30 hora local**, momento natural de cierre de jornada creativa.
4. **Regla de Inactividad de 42 Horas:** Se exige un mínimo estricto de **42 horas de silencio** del creador antes de que RICK intervenga con una pregunta de trinchera.
5. **Umbral de Calidad SNR:** Confianza mínima del patrón $\ge 0.85$.
6. **Cooldown y Backoff Progresivo:**
   - 0 silencios previos: Cooldown base (24h para chispas/salud, 42h para trinchera).
   - 1 silencio consecutivo: Cooldown extendido a 48 horas.
   - 2 o más silencios consecutivos: Cooldown extendido a 96 horas (respeto total al silencio del creador).

## Alternatives Considered

### 1. Decisiones heurísticas generadas por el propio LLM en cada tick
- **Pros:** Capacidad de razonamiento contextual dinámico.
- **Cons:** Costoso, lento, y propenso a inconsistencias o alucinaciones (un LLM podría justificar enviar un mensaje a las 3:00 AM porque "la idea es muy urgente").
- **Rejected:** Las reglas de entrega y spam deben ser contratos duros y deterministas de ingeniería.

### 2. Cron fijo sin backoff
- **Pros:** Muy simple de programar.
- **Cons:** Bombardearía a usuarios inactivos semanalmente o diariamente sin importar si leen o responden, provocando bloqueos en WhatsApp.
- **Rejected:** Incompatible con la experiencia de mentoría de alta consideración.

## Consequences
- **Positivas:**
  - Protección absoluta contra penalizaciones de spam en Meta WhatsApp Cloud API.
  - El creador siente que RICK respeta su tiempo y solo le habla con señales de altísimo valor.
  - Comportamiento 100% verificable mediante tests unitarios (`tests/test_governor.py`).
- **Compromisos:**
  - Requiere que el backend o el worker pase el contexto temporal (`current_local_hour`, `current_local_minute`, `hours_since_last_ping`, `silence_streak`).
