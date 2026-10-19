# 🤖 Guía Rápida: Probar a RICK en Telegram (en 1 minuto)

Telegram es la forma **más rápida y cómoda** de probar a RICK desde tu celular sin lidiar con los procesos de Meta ni configurar webhooks o dominios públicos. Funciona en **modo Long Polling directo**.

---

### Paso 1: Crear tu Bot en Telegram (30 segundos)

1. Abre tu aplicación de **Telegram** (en tu celular o en la PC).
2. Busca el usuario oficial: **`@BotFather`** (tiene la insignia de verificación azul).
3. Escríbele el comando:
   ```text
   /newbot
   ```
4. Te pedirá:
   - **Nombre para tu bot:** Ej: `RICK Creative Mentor`
   - **Username único (debe terminar en bot):** Ej: `rick_mentor_creativo_bot`
5. `@BotFather` te responderá con tu **Token HTTP API** (se ve algo como `7891234567:AAFnK_...`).
6. **Copia ese token.**

---

### Paso 2: Pegar el Token en tu `.env`

Abre el archivo `.env` en:
`c:\Users\mgome\OneDrive\Documents\RICK Multitenant\RICK! Guía de Marca Personal\.env`

Pega el token en la línea:
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui_sin_comillas
```
Guarda el archivo.

---

### Paso 3: Iniciar a RICK

Haz doble clic en el archivo:
👉 **`run_telegram.bat`** (en la carpeta `RICK! Guía de Marca Personal`)

Verás en la pantalla:
```text
=======================================================
  🤖 Iniciando RICK en Telegram (Modo Long Polling)
=======================================================
✅ RICK está escuchando mensajes en Telegram. ¡Escríbele a tu bot!
```

---

### Paso 4: ¡Chatea o mándale audios a RICK!

1. Busca tu bot en Telegram con el username que creaste.
2. Dale a **Iniciar** (`/start`).
3. RICK te responderá con su personalidad de Rick Rubin y arrancará la entrevista de voz inicial.
4. **Prueba enviarle una nota de voz:** RICK la descargará, la transcribirá con Gemini y te responderá como si la hubieras escrito.
5. Pídele un guion: verás cómo consulta los frameworks de su cerebro y te genera el guion en 5 actos por beats.
