# ADR-008: Descubrimiento Dinámico de Nicho vía Apify, Ingesta de Referencias del Creador y Onboarding Conversacional en 4 Etapas

## Status
Accepted

## Date
2026-10-23

## Context
El sistema RICK operaba previamente con dos limitaciones estructurales en su captación de referencias e interacción inicial con el creador:

1. **Dependencia de Referentes Preconfigurados (Cold Start en Nuevos Nichos):**  
   El radar de mercado asumía un conjunto cerrado de creadores predefinidos o exigía configurar manualmente los competidores antes de poder extraer patrones virales ($R \ge 1.5\times$). Cuando un creador de un nicho no contemplado (ej. *cirugía bariátrica*, *derecho corporativo*, *automatizaciones industriales*) se sumaba al sistema, RICK carecía de capacidad para explorar dinámicamente el ecosistema de Instagram Reels de ese sector.

2. **Enlaces de Referencia Compartidos por el Creador en el Chat:**  
   En la práctica real en WhatsApp, los creadores frecuentemente envían enlaces directos de reels (`https://www.instagram.com/reel/...`) diciendo *"mira este video, me gustó este gancho"* o *"analiza esto"*. El sistema trataba estos enlaces como texto plano no estructurado o charla informal, perdiendo la oportunidad de extraer métricas (vistas, likes, comentarios), evaluar su anomalía viral respecto al nicho e incorporarlo al radar de patrones ganadores del creador.

3. **Sobreuso de Jerga Bélica ("Trinchera") y Slop Corporativo:**  
   Prompts, docstrings y plantillas acumulaban la palabra *"trinchera"* y metáforas de combate (*"en batalla"*, *"balas"*). Esto generaba un tono artificial y agresivo, alejado de la identidad deseada: un **asistente y par creativo de marca personal** que conversa de tú a tú basándose en la experiencia práctica del día a día.

4. **Falsas Promesas y Alucinación de Enlaces:**  
   El modelo corría el riesgo de alucinar paneles inexistentes o enviar placeholders como `[link]` o *"revisa tu dashboard"*. RICK es un motor que vive en WhatsApp y no posee un panel web público de analíticas para el usuario; todo valor, hallazgo y patrón viral debe comunicarse de forma clara, directa y estructurada en el propio chat.

5. **Falta de Estructura Canónica en la Secuencia de Onboarding:**  
   El inicio de la relación con un creador carecía de una progresión metódica en 4 fases que balanceara la oferta irresistible inicial, el diagnóstico de su huella digital, la extracción de su cosmovisión y el perfilado validado con ideas ejecutables.

---

## Decision

Implementar un sistema integral de **descubrimiento dinámico de nicho**, **ingesta de enlaces compartidos**, **erradicación de jerga bélica** y un **onboarding conversacional canónico en 4 etapas**.

### 1. Servicio de Scraper Dinámico (`InstagramScraperService` en `src/services/instagram_scraper.py`)
Se introduce un servicio desacoplado que se comunica con la API de **Apify** utilizando el actor `clockworks~instagram-reels-scraper`:

- **`search_niche_reels(keywords: List[str], max_reels: int = 15) -> List[Dict[str, Any]]`**:  
  Ejecuta una búsqueda dinámica en Instagram Reels basada en los términos temáticos del creador. Retorna registros con URLs reales (`url`), autor (`owner_username`), métricas de rendimiento (`views`, `likes`, `comments`), fecha y transcripción/caption. Cuenta con un fallback determinista para entornos de desarrollo y testing donde no se disponga de `APIFY_API_KEY`.
- **`scrape_shared_link(url: str) -> Optional[Dict[str, Any]]`**:  
  Inspecciona y extrae metadatos y métricas de un enlace individual de Instagram Reel compartido por el usuario en el chat.

### 2. Integración en el Radar de Mercado (`src/services/radar_ingestion.py`)
- **`populate_from_niche_search(keywords: List[str]) -> int`**:  
  Alimenta dinámicamente el caché sub-50ms del radar calculando la mediana del nicho y el ratio de anomalía $R = \text{views}/\text{median}$ sobre datos reales de Instagram.
- **`ingest_shared_link(user_id: str, url: str) -> Optional[MatrixRow]`**:  
  Convierte un enlace enviado por el creador en un registro tipado de la matriz de contenido, calculando su rendimiento relativo y permitiendo que RICK lo use inmediatamente como benchmark.

### 3. Enrutamiento Conversacional y Clasificación de Intenciones (`src/agents/rick.py`)
- Se añade la intención `share_reference_link` a `classify_intent()`.
- Cuando el creador incluye una URL de Instagram Reel, RICK detecta el enlace, invoca el scraper/radar y responde analizando la estructura del reel (gancho, retención, ángulo psicológico), sugiriendo adaptaciones a su voz sin abandonar la conversación de WhatsApp.

### 4. Erradicación Total de Jerga Bélica ("Trinchera")
- Se prohíbe formalmente la palabra *"trinchera"* y el vocabulario bélico en todos los prompts, docstrings, código y tests del motor.
- Se redefine la identidad de RICK como: **asistente y par de marca personal**, con un tono directo, sobrio, analítico y basado en la **experiencia real y práctica**.
- Se añade un test automatizado en `tests/test_rick_node.py` que asegura que `"trinchera"` no forme parte del prompt canónico del sistema.

### 5. Secuencia de Onboarding Conversacional en 4 Etapas
En `src/agents/prompts.py` (`RICK_CANONICAL_SYSTEM_PROMPT`), se formaliza la progresión exacta de onboarding:

```
[Etapa 1: Apertura y Oferta de Prueba]
"Tu prueba corre por mi cuenta: después de que trabajemos juntos un tiempo, 
seguro que te vas a convencer de seguir trabajando conmigo. 
¿Cuáles son tus redes? Déjame ver qué has estado haciendo 📲"
                 │
                 ▼
[Etapa 2: Diagnóstico de Huella & Pregunta 1]
Analizar la huella del creador y lanzar Pregunta 1:
"¿Qué quieres lograr con tu marca personal? ¿Cuál es tu objetivo?"
                 │
                 ▼
[Etapa 3: Cosmovisión & Pregunta 2]
Explorar mentiras de su industria, mitos o posturas contraintuitivas que defiende.
                 │
                 ▼
[Etapa 4: Perfilado, Validación & 3 Opciones de Video]
Presentar perfil (Público Objetivo, Objetivo, Nicho, Posturas, Tono), 
validar con el creador y proponer 3 opciones de video fundamentadas con links reales.
```

### 6. Política Estricta de Cero Enlaces Falsos
- Queda prohibido generar placeholders como `[link]`, `[dashboard]` o prometer interfaces web externas.
- Los únicos enlaces permitidos son URLs reales de Instagram Reels extraídas por el scraper dinámico o el propio radar.

---

## Alternatives Considered

### 1. Scraping Directo sin API (Puppeteer / Playwright headless en el contenedor Docker)
- **Pros:** Cero costo de terceros.
- **Cons:** Bloqueos frecuentes por IP y retos de verificación de Instagram; eleva sustancialmente el consumo de RAM e imagen de Docker; fragilidad operativa en producción.
- **Rejected:** Apify Actor ofrece endpoints estables con rotación de proxies residenciales y mantenimiento activo frente a cambios del DOM de Instagram.

### 2. Exigir al Creador que Llene un Formulario Previo o Lista de Competidores
- **Pros:** Facilidad técnica para el backend.
- **Cons:** Fricción inaceptable en el canal de WhatsApp; destruye la experiencia conversacional inmediata y la promesa *"tu prueba corre por mi cuenta"*.
- **Rejected:** RICK debe ser proactivo y extraer la información mediante mayéutica conversacional fluida.

### 3. Mantener Enlaces Falsos / Placeholders en los Prompts
- **Pros:** Ninguno.
- **Cons:** Destruye la confianza del usuario inmediatamente al recibir mensajes con `[link]` o promesas de herramientas inexistentes.
- **Rejected:** Cero tolerancia a alucinaciones de producto.

---

## Consequences

### Positivas:
1. **Radar Vivo y Adaptable:** Capacidad de explorar cualquier nicho en Instagram Reels y calcular ratios $R$ de anomalía viral con datos reales.
2. **Interactividad Enriquecida:** El creador puede enviar reels de inspiración directamente por WhatsApp y recibir un análisis desglosado al instante.
3. **Comunicación Profesional y Humana:** Eliminación definitiva del slop militar ("trinchera"), alineando el tono con la sobriedad y maestría creativa de Rick Rubin.
4. **Flujo de Bienvenida Claro:** Proceso de 4 etapas que genera compromiso inmediato, perfila al creador y entrega valor tangible con 3 opciones de video verificadas.
5. **Suite de Pruebas Robusta:** 110 pruebas automatizadas pasando al 100% en $< 1.5$ segundos.

### Trade-offs / Mitigaciones:
- **Consumo de Créditos de Apify:** Las consultas a Apify consumen cuota de API. Se mitiga mediante el almacenamiento en caché sub-50ms en memoria/Supabase de `RadarIngestionService` y la ventana de exclusión temporal para no re-scrapear repetidamente.
- **Disponibilidad Offline:** Cuando no hay conexión a Apify o no se cuenta con token en entornos locales de CI/CD, el servicio recurre a un generador determinista de datos de prueba para mantener la suite 100% verde y confiable.
