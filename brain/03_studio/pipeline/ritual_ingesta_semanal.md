# Protocolo Operativo: Ritual Semanal de Ingesta y Deconstrucción de Referentes

---
**Pilar:** brain/03_studio/pipeline/  
**Cadencia:** Semanal (Lunes a primera hora, antes del lote de guiones)  
**Propósito:** Alimentar el estudio con ángulos visuales, ganchos de retención y mecánicas de conversión probadas por creadores que tienen tracción validada en tu nicho.  
---

## 👥 1. El Roster Oficial de Referentes

El estudio monitorea únicamente entre 3 y 6 creadores de alta señal para evitar ruido y optimizar recursos:

| # | Creador | Handle | Territorio Principal | Carpeta en Bóveda |
| :-: | :--- | :--- | :--- | :--- |
| 1 | [Nombre Creador 1] | @handle1 | [Ángulo o fortaleza 1] | brain/03_studio/referentes/creador-1/ |
| 2 | [Nombre Creador 2] | @handle2 | [Ángulo o fortaleza 2] | brain/03_studio/referentes/creador-2/ |
| 3 | [Nombre Creador 3] | @handle3 | [Ángulo o fortaleza 3] | brain/03_studio/referentes/creador-3/ |

---

## ⚙️ 2. Mecánica de Ingesta (Arquitectura Resiliente)

Para garantizar que el ritual **funcione siempre** sin depender de un único punto de falla:

### Canal A: Ingesta Automatizada vía Skill (skills/instagram-scraper/)
* Si tienes configurada tu clave opcional en .env (APIFY_API_TOKEN), puedes pedirle a RICK que raspe las publicaciones recientes de los perfiles de tu roster.

### Canal B: Ingesta Quirúrgica Asistida (Fallback infalible — Cero APIs)
* Si no usas APIs externas, simplemente comparte los enlaces o transcripciones de los vídeos/posts que te llamaron la atención en el chat.
* RICK desglosa el gancho, la retención y la llamada a la acción en segundos.

---

## 🔬 3. Matriz de Extracción (Los 3 Activos Obligatorios)

Por cada pieza destacada de la semana, se extraen estrictamente:

1. **Ángulo Visual y Formato:**
   * ¿Qué se ve en pantalla? Estilo visual, cámara, ritmo de cortes, texto o apoyo visual utilizado.
2. **Ángulo Narrativo & Gancho:**
   * ¿Cuál fue el primer segundo? ¿Qué objeción, mito o problema atacó?
3. **Mecánica de Conversión:**
   * ¿Qué acción pide al usuario? ¿Qué palabra clave en DM o link entrega el recurso?

---

## 📁 4. Entrega y Persistencia

1. **Ficha semanal consolidada:** Guardada en brain/03_studio/referentes/digest_semanal_W[XX].md.
2. **Histórico por creador:** Actualización dentro de la carpeta de cada referente en brain/03_studio/referentes/.
3. **Morfosis a la voz del Creador:** Toda ingesta concluye con **3 Semillas de Producción** traducidas a la voz y stack real del Creador (brain/02_creator/identity/voice_dna.md).
