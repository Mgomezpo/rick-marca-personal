# RICK Multitenant Agent Engine
## Estratega de Marca Personal Autónomo para WhatsApp con Graph & Loop Engineering

[![Tests](https://img.shields.io/badge/tests->95%20passed%20(100%25)-brightgreen.svg)](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/tests)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/pyproject.toml)
[![Architecture](https://img.shields.io/badge/architecture-State%20Graph%20(v1.1.0)-purple.svg)](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/ARQUITECTURA_RICK_MULTITENANT.md)
[![License](https://img.shields.io/badge/security-audited%20(STRIDE)-success.svg)](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/SECURITY.md)

> **Versión Actual:** 1.1.0  
> **Estado:** Desplegado en Producción con Soporte Multi-Tenant  
> **Canal Nativo:** Meta WhatsApp Cloud API (Inbound con ACK $< 200$ ms y Outbound Directo)  
> **Webhook de Producción:** `https://four-words-rescue.loca.lt/webhook/whatsapp`  
> **Healthcheck de Diagnóstico:** `https://four-words-rescue.loca.lt/health`  
> **Verify Token Oficial:** `rick_secret_verify_token_2026`  

---

## ⚡ 1. Resumen y Capacidades de Ingeniería

**RICK** es un estratega de marca personal multitenant diseñado bajo principios de ingeniería de grafos (**State Graph**) y optimización en bucle cerrado (**Evaluator-Optimizer Loop**). Opera como un miembro de equipo interno para creadores de contenido, combinando mayéutica socrática inspirada en Rick Rubin (*The Creative Act*) con rigor técnico editorial.

### 🌟 Capacidades Clave

1. **Mayéutica Creativa & Trinchera (Rick Rubin):**
   - **Regla de los 3 niveles de limitación verbal:**
     - *Nivel 1:* Charla concisa de 30 a 60 palabras, sin clichés corporativos ni teoría vacía.
     - *Nivel 2:* Indagación de trinchera con exactamente 1 sola pregunta para extraer escena real y fricción raíz.
     - *Nivel 3:* Transición directa a entrega técnica de obra sin fricción innecesaria.
2. **Guion Técnico Canónico en 3 Bloques:**
   - **`HOOK`:** Texto exacto sin rodeos, Intención psicológica y Dirección física de cámara.
   - **`DESARROLLO`:** Historia real o quiebre de creencia, Intención empática y Cámara en tono de café.
   - **`CIERRE / CTA`:** Conclusión contundente sin fórmulas gastadas y pausa deliberada de 1 segundo.
3. **Loop de Calidad Cerrado (Anti-Plagio & Anti-Slop):**
   - **Filtro Anti-Plagio Determinista:** Algoritmo de n-gramas que rechaza automáticamente guiones con $\ge 5$ palabras consecutivas idénticas a videos de referencia.
   - **Editor Anti-Slop:** Poda activa y penalización de clichés corporativos de IA.
   - **Simulador Empírico de Retención:** Cálculo de probabilidad (Alta, Media, Baja) basado en $n$ piezas ganadoras del nicho.
4. **4 Loops Proactivos Autónomos:**
   - **`market_spark`:** Alertas ante anomalías virales ($R \ge 1.5\times$) con propuesta de ángulo en tono de equipo.
   - **`brand_health_audit`:** Detección y advertencia de pilares de marca desiertos ($< 15\%$).
   - **`trench_inquiry`:** Pregunta de trinchera vespertina (17:00–19:30) tras $\ge 42$ horas de inactividad creativa.
   - **`routine_reporter`:** Auditoría de cuenta propia, cálculo de mediana personal y aprendizajes procesables (`procedural_learnings`).
5. **Gobernador Anti-Spam y Control de Cadencia:**
   - Reglas estrictas de horas hábiles (09:00 a 19:00), ventana vespertina para trinchera, umbral SNR ($\ge 0.85$) y backoff progresivo (48h y 96h) ante silencios del creador.
6. **Radar de Mercado Desacoplado "Wide & Fresh":**
   - Ingesta en background desde pool de 15 a 25 creadores con acceso a caché en $< 50$ ms.
   - Exclusión de posts usados durante 30 días y rotación de creadores en cooldown de 7 días.
7. **Aislamiento Multi-Tenant y Persistencia:**
   - Aislamiento estricto por `user_id` en Supabase con Row-Level Security (RLS).
   - Persistencia de conversación multi-turno entre webhooks independientes de WhatsApp.
8. **Arquitectura de Contenido Multidimensional (Sagas, Pilares, Planes y Piezas Sueltas):**
   - **Matriz de combinatoria libre:** piezas sueltas de trinchera, pilares estratégicos de marca desacoplados, sagas episódicas continuas y planes.
   - **Ganchos de continuidad y cliffhangers:** ganchos en episodio 2+ que enlazan con la entrega anterior y llamados a la acción con cliffhanger dramático.
   - **Mayéutica creativa de socio en RICK:** detección de historias densas multi-punto y sugerencia amigable (*"¿Hacemos una sola pieza al grano o te parece si armamos una saga de 2 partes?"*).
   - **Persistencia no destructiva:** mapeo a columnas existentes `strategy_tag`, `plan_id` e `idea_fields->series` (JSONB) en `public.pieces` con 100% retrocompatibilidad para las 132 piezas previas y 33 creadores.

---

## 🏗️ 2. Arquitectura del Sistema

```
                      +---------------------------------------+
                      |       Meta WhatsApp Cloud API         |
                      +-------------------+-------------------+
                                          |
                                HTTP POST /webhook/whatsapp
                                          v
                      +---------------------------------------+
                      |       FastAPI Webhook Handler         |
                      |          (ACK < 200ms)                |
                      +-------------------+-------------------+
                                          | BackgroundTasks
                                          v
                      +---------------------------------------+
                      |         RickGraphEngine               |
                      |     (State Graph Orquestador)         |
                      +---------+-------------------+---------+
                                |                   |
               +----------------v---+           +---v----------------+
               |  Flujo Reactivo    |           |  Flujo Proactivo   |
               |  (user_message)    |           |  (market/health)   |
               +--------+-----------+           +---+----------------+
                        |                           |
                        v                           v
               +--------------------+       +--------------------+
               | Rick Rubin Node    |       | Anti-Spam Governor |
               | Guionista (3 Beats)|       |  (Quiet Hours/42h) |
               | Loop Anti-Plagio   |       | 4 Loops Autónomos  |
               +--------+-----------+       +-------+------------+
                        |                           |
                        +-------------+-------------+
                                      |
                                      v
                      +---------------------------------------+
                      |    Outbound WhatsApp Cloud API        |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |   📱 Creador en su WhatsApp          |
                      +---------------------------------------+
```

Para una descripción detallada de todos los componentes, revise el documento completo de arquitectura:  
👉 [**ARQUITECTURA_RICK_MULTITENANT.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/ARQUITECTURA_RICK_MULTITENANT.md)  
👉 [**Registro de Decisiones Arquitectónicas (ADRs)**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/README.md)

---

## 🚀 3. Guía de Inicio Rápido

### Prerrequisitos
- Python 3.11 o superior
- Git

### 1. Clonar e Instalar Dependencias
```bash
# Instalar dependencias del proyecto
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno (`.env`)
Copia la plantilla o crea tu archivo `.env` en la raíz del proyecto:
```env
# Meta WhatsApp Cloud API
WHATSAPP_TOKEN=tu_token_de_acceso_permanente_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_identificador_de_numero_de_telefono
WHATSAPP_VERIFY_TOKEN=rick_secret_verify_token_2026

# Supabase (IrealDemo)
SUPABASE_URL=https://khoikdwablpqiapxkgqx.supabase.co
SUPABASE_KEY=tu_supabase_service_role_key_aqui
```

### 3. Ejecutar el Servidor Local
```bash
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará listo en `http://localhost:8000`:
- **Documentación Interactiva (Swagger):** `http://localhost:8000/docs`
- **Healthcheck:** `http://localhost:8000/health`

---

## 🧪 4. Ejecución de la Suite de Pruebas

Toda la lógica de RICK está cubierta por 82 pruebas automatizadas unitarias y de integración que se ejecutan en menos de 1 segundo:

```bash
# Ejecutar todas las pruebas con reporte detallado
pytest -v tests/

# Auditoría de seguridad de dependencias
pip-audit
```

Resultado verificado:
```text
============================= 82 passed in 0.85s ==============================
```

---

## 📲 5. Configuración en Meta WhatsApp Business API

Para conectar tu instancia en vivo a WhatsApp oficial:

1. Ve a [developers.facebook.com](https://developers.facebook.com) > Tu App > **WhatsApp** > **Configuración**.
2. En la sección **Webhook**:
   - **URL de devolución de llamada:** `https://tu-dominio-publico.com/webhook/whatsapp`
   - **Identificador de verificación:** `rick_secret_verify_token_2026` (o el valor de `WHATSAPP_VERIFY_TOKEN` en tu `.env`)
3. Haz clic en **Verificar y guardar**.
4. En **Campos de webhook**, suscríbete al evento `messages`.

---

## 📚 6. Mapa de Documentación

| Documento | Descripción |
| :--- | :--- |
| [**ARQUITECTURA_RICK_MULTITENANT.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/ARQUITECTURA_RICK_MULTITENANT.md) | Especificación técnica exhaustiva del motor, grafos, nodos y flujos. |
| [**docs/decisions/**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/docs/decisions/README.md) | Architecture Decision Records (ADR-001 a ADR-005) con justificaciones técnicas. |
| [**SECURITY.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/SECURITY.md) | Modelo de amenazas STRIDE, políticas de aislamiento multi-tenant y SLAs. |
| [**CHANGELOG.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/CHANGELOG.md) | Historial cronológico de lanzamientos y adiciones. |
| [**README_WHATSAPP_SETUP.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/README_WHATSAPP_SETUP.md) | Guía detallada paso a paso para la conexión con Meta Cloud API. |
