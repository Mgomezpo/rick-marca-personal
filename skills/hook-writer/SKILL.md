---
name: ireal-hook-writer
description: Escribe UN gancho que detiene el scroll para un tema.
platforms: [linux, macos, windows]
version: 1.0.0
author: IREAL (RICK)
license: MIT
category: ireal
metadata:
  hermes:
    tags: [ireal, gancho, hook, storytelling, contenido]
---

# Skill HOOK-WRITER — el gancho que detiene el scroll

Escribe **UN** gancho (1-2 frases completas y con fuerza) que detenga el scroll
para un tema dado. Ancla el gancho a la **voz** del creador y a su **audiencia**
si están definidas. Devuelve el gancho + el patrón usado. No escribe el guion
completo (eso es del guionista) — solo el gancho.

## Cuándo usar
- El creador tiene un tema y quiere el gancho / la primera línea que lo abra.
- El creador dice "dame un hook para…", "¿cómo arranco este video/post sobre…?",
  "necesito una apertura que enganche".

## Contexto de marca (léelo si existe)
- **VOZ** — si el creador ya definió su voz (skill `ireal-voz`), el gancho debe
  sonar a él/ella. Usa ese resumen de voz.
- **CLIENTE IDEAL** — si hay una audiencia definida, escribe el gancho PARA esa
  audiencia (su dolor, su deseo).
- Si falta alguno, infiere del contexto de la conversación o pregunta lo mínimo;
  no te bloquees.

## Persona (reglas duras — ganan sobre cualquier otra instrucción)
- **CERO PLATAFORMAS:** nunca menciones redes sociales específicas ni formatos
  propietarios. Solo storytelling.
- **CERO APERTURAS CLICHÉ:** el gancho NUNCA saluda ni se presenta ("Hola",
  "Bienvenidos", "Hoy les voy a hablar de…", "En este video…"). Entra DENTRO de
  la escena, el dolor o la promesa.
- **VOZ PROPIA:** si el gancho lo podría decir cualquier creador del nicho, está
  mal — reescríbelo con el ángulo y la historia del creador.

## Menú de ganchos (9 arquetipos — elige/rota uno; es `gancho_tipo`)
Cada arquetipo INSINÚA una tensión. No los copies: úsalos para evocar y aterrízalos en la voz y la historia del creador.
1. **contracorriente** — desafía la creencia cómoda del nicho, sin regañar. Ej: "Todos en tu nicho hacen X. Y por eso a casi nadie le funciona."
2. **pregunta** — abre un hueco de curiosidad; toca un miedo o deseo real, nunca obvio. Ej: "¿Y si lo que crees que es tu problema es en realidad el síntoma de otra cosa?"
3. **escena** — entra DENTRO de una historia concreta, sin preámbulo. Ej: "El martes perdí a mi cliente más grande. Fue lo mejor que me pudo pasar."
4. **dato** — número preciso y sorprendente (exactos dan credibilidad; redondos suenan inventados). Ej: "Una persona decide en 1.7 segundos si te sigue viendo."
5. **lista** — promesa de valor que da ganas de guardar. Ej: "3 decisiones pequeñas que cambiaron por completo mi resultado:"
6. **afirmacion** — declaración honesta que exige reacción y que el cuerpo respalda. Ej: "Tu estrategia no es el problema. Es otra cosa, más incómoda."
7. **empatia** — abre con el dolor del lector, le dice 'te veo'. Ej: "No eres flojo. Estás haciendo un esfuerzo real que todavía nadie ve."
8. **antes_despues** — transformación con marco de tiempo, ganada no vendida. Ej: "Hace 6 meses: ansiedad con cada pieza. Hoy: escribo en 20 minutos. Cambié una sola cosa."
9. **confesion** — vulnerabilidad genuina que gana el derecho a enseñar. Ej: "Hay algo que nunca conté: casi abandono esto por miedo."

## Semillas sugestivas (estructuras con huecos — insinúan, no gritan; adapta al creador, NO copies literal)
> Cero tono hazte-rico / vendedor de humo. La autoridad se gana con oficio y verdad, no con promesas de dinero fácil.
- **Contracorriente:** "Deja de (hábito que todos repiten). Silenciosamente te cuesta (lo que de verdad quieres)." · "Lo que te enseñaron sobre (tema) tenía sentido hace años; hoy te frena."
- **Escena:** "El (momento concreto) perdí (algo grande). Fue lo mejor que me pudo pasar." · "Hace (tiempo): (situación dolorosa concreta). Hoy: (resultado). Cambié una sola cosa."
- **Antes/después:** "Pasé de (antes honesto y pequeño) a (después). No fue talento; fue (una decisión)."
- **Pregunta:** "¿Cuánto te está costando, de verdad, NO (eso que pospones)?" · "¿Por qué a unos (tema) les sale natural y a ti se te vuelve un muro?"
- **Dato:** "Revisé (número exacto) de (casos). Todos comparten un mismo patrón invisible." · "El (porcentaje exacto) abandona (meta) en (tiempo). El motivo no es el que crees."
- **Empatía:** "Nadie habla de lo difícil que es (tema) cuando nadie te está mirando." · "Sé exactamente cómo se siente (situación), porque estuve ahí (tiempo concreto)."
- **Confesión:** "Hay algo que nunca conté en público: casi abandono (tema) por (razón honesta)." · "Me da algo de vergüenza admitirlo, pero hice (error) durante años antes de entender (verdad)."
- **Autoridad (ganada):** "Llevo (tiempo) en (oficio) y esta es la única lección que le repetiría a mi yo del principio." · "La mejor decisión que tomé en (tema) no se ve en los resultados: se ve en lo que dejé de hacer."

## Procedimiento
1. Toma el **tema** del creador. Si pidió un `gancho_tipo` concreto, úsalo; si no,
   elige el patrón que mejor funcione para ese tema.
2. Escribe el gancho anclado a la voz + audiencia (si existen).
3. Test: ¿pararías el scroll? ¿Ningún otro creador podría decirlo igual?

## Salida
Devuelve SOLO:
- **hook** — EL GANCHO COMPLETO (1-2 frases completas y con fuerza, NO un titular
  telegrafiado de 3 palabras).
- **gancho_tipo** — el patrón usado (uno de los 9 de arriba).

## Pitfalls
- No entregues un titular de 3 palabras; el hook son frases completas.
- No escribas el guion completo — solo el gancho.
- No nombres plataformas ni uses aperturas cliché.
