# RICK Multitenant Agent Engine
## Estratega de Marca Personal Autónomo para WhatsApp con Graph & Loop Engineering

> **Versión:** 1.0.0  
> **Estado:** Desplegado en Producción con HTTPS Público  
> **Webhook de WhatsApp:** `https://four-words-rescue.loca.lt/webhook/whatsapp`  
> **Healthcheck:** `https://four-words-rescue.loca.lt/health`  
> **Verify Token (Meta):** `rick_secret_verify_token_2026`  

---

## 🚀 1. Arquitectura y Capacidades de Ingeniería

RICK es un estratega de marca personal multitenant diseñado bajo principios de ingeniería de grafos (**State Graph**) y optimización en bucle cerrado (**Evaluator-Optimizer Loop**):

1. **Mayéutica Creativa (Rick Rubin):**
   - Regla de los 3 niveles de limitación verbal (Nivel 1: Charla 30-60 palabras, Nivel 2: Indagación de trinchera 1 sola pregunta, Nivel 3: Entrega de obra técnica).
   - Extracción de la escena real y la fricción sin teoría abstracta ni saludos vacíos.

2. **Guion Técnico en 3 Bloques Canónicos:**
   - **HOOK:** Texto exacto sin rodeos, Intención psicológica y Dirección de cámara frontal.
   - **DESARROLLO:** Historia real o quiebre de creencia, Intención y Cámara en tono de café.
   - **CIERRE / CTA:** Conclusión contundente o llamado sin clichés de marketing y Pausa de 1 segundo.

3. **Motor de Matriz de 10 Columnas & Doble Radar:**
   - `MatrixRow` valida las 10 columnas (`post_id`, `account_handle`, `views`, `account_median`, `relative_performance`, `hook_text`, `hook_type`, `format`, `emotion`, `duration_seconds`).
   - Identifica patrones ganadores ($R \ge 1.5\times$) combinando los referentes de cabecera (`brand_referents`) y el radar amplio de tendencias del nicho.

4. **Loop de Calidad Cerrado:**
   - **Filtro Anti-Plagio:** Algoritmo de n-gramas contiguos que audita el guion contra referentes (rechazo automático si hay $\ge 5$ palabras idénticas).
   - **Checklist Anti-Slop:** Poda y penaliza clichés corporativos ("en este mundo cambiante", "desata tu potencial", etc.).
   - **Simulador Empírico:** Estima la probabilidad (Alta, Media, Baja) respaldada en $n$ piezas ganadoras del nicho.

5. **Auditoría de Cuenta Propia y Procedural Learnings:**
   - Monitorea los reels del creador contra su mediana personal de views.
   - Genera aprendizajes procesables en Supabase (`procedural_learnings`) que retroalimentan los futuros guiones.
   - Envía reportes semanales limpios directamente a WhatsApp.

---

## 📲 2. Configuración en Meta WhatsApp Business API

Para conectar el motor a tu número oficial de WhatsApp:

1. Ve a [developers.facebook.com](https://developers.facebook.com) > Tu App > **WhatsApp** > **Configuración**.
2. En la sección **Webhook**:
   - **URL de devolución de llamada:** `https://four-words-rescue.loca.lt/webhook/whatsapp`
   - **Identificador de verificación:** `rick_secret_verify_token_2026`
3. Haz clic en **Verificar y guardar**.
4. En **Campos de webhook**, suscríbete al evento `messages`.

---

## 🧪 3. Ejecución de Pruebas y Auditorías

```bash
# Ejecutar la suite completa de tests (39 tests unitarios e integración)
pytest -v tests/

# Auditoría de seguridad de dependencias
pip-audit

# Iniciar servidor local
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```
