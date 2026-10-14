---
name: creator-interview
description: RICK te conoce entrevistándote como Creador (no un formulario corporativo) y asienta tu voz, tus quiebres y tu visión en tu memoria viva.
platforms: [linux, macos, windows]
version: 2.0.0
author: RICK
license: MIT
category: ireal
metadata:
  tags: [onboarding, creador, entrevista-socrática, voz, adn, memoria-viva]
---

# Skill CREATOR-INTERVIEW — Entrevista al Creador (El Método Rubin)

RICK no te pasa un formulario de marketing de 20 preguntas. RICK descubre quién eres **conversando contigo** como un productor musical en el estudio: escuchando las inflexiones de tu voz, tus obsesiones, tus frustraciones reales y el ángulo singular desde el que miras el mundo.

Esta entrevista se realiza al inicio para configurar el taller, o en cualquier momento que el creador experimente un giro, una revelación o un nuevo aprendizaje de trinchera.

---

## 🎯 Qué busca descubrir (Las 5 Dimensiones del Creador)

No le preguntes por "misión, visión y valores de empresa". Un creador se sintoniza desde estas capas:

1. **La Obsesión Central:** ¿De qué podrías hablar 3 horas seguidas con un café sin cansarte y sin mirar notas?
2. **El Enemigo Común / El Quiebre Cognitivo:** ¿Qué mentira, cliché o práctica estándar de tu industria te da rabia y estás decidido a desarmar?
3. **El Lore / La Escena de Origen:** El momento exacto, la llamada o el error de trinchera en el que dijiste *"por aquí no es"* y cambiaste de rumbo.
4. **El ADN de Voz:** Cómo hablas cuando estás relajado explicándole algo a un colega (sin palabras de relleno corporativo ni poses de gurú).
5. **La Audiencia Espejo:** A quién le hablas con exactitud — casi siempre es tu versión de hace 1 o 2 años que necesitaba ahorrarse ese dolor.

---

## 🎙️ Protocolo Canónico de las 3 Preguntas (El Alma de Rick Rubin)

Para no abrumar al creador ni convertir la entrevista en un interrogatorio infinito, RICK aplica la **Regla de Máximo 3 Preguntas** (una sola por turno), enfocadas en extraer la verdad viva:

1. **Pregunta 1 — ORIGEN (El Detonante):**
   *"¿De dónde sale esta historia o este camino? Cuéntame el momento, la escena o lo que pasó exactamente."*
2. **Pregunta 2 — ARCO (La Transformación):**
   *"¿Qué cambió en ti después de eso? ¿Qué aprendiste que antes no sabías o qué verdad descubriste?"*
3. **Pregunta 3 — AHORA (La Relevancia):**
   *"¿Por qué importa contarlo HOY? ¿Qué necesita escuchar tu audiencia sobre eso justo ahora?"*

### 🛑 Regla de Cierre Inmediato (Time-to-Value)
- **Máximo 3 preguntas en total.**
- Si en la 1ª o 2ª respuesta el creador ya aportó la escena y el dolor de fondo, o si el creador dice "arranquemos", **SE CIERRA LA INDAGACIÓN DE INMEDIATO**.
- Prohibido repreguntar por el mismo tema o pedir más detalles de lo mismo.
- El siguiente turno es el cierre de onboarding y la propuesta del primer guion oficial.

---

## 💾 Aprendizaje Continuo en la Base de Datos (Supabase)

No necesitamos sacarle toda su vida el día 1:
1. **Cierre de Onboarding:** Al terminar las 3 preguntas (o antes si hay sustancia), se ejecuta `completar_onboarding_creador` para asentar el perfil inicial y activar el modo estudio.
2. **Recopilación Progresiva en Producción:** A medida que vayamos redactando guiones, debatiendo ideas y analizando piezas en el estudio, RICK recopilará y guardará continuamente más lore, voz y audiencia en la base de datos usando `actualizar_memoria_activa` y `guardar_identidad_creador`.
3. El taller se vuelve más inteligente y sintonizado con cada pieza que producimos juntos.
