# [CANAL HISTÓRICO / EXPERIMENTAL] Guía de Pruebas en Telegram

> [!NOTE]
> **Canal Primario de Producción:** El canal de producción oficial y activo de RICK es **Meta WhatsApp Cloud API**.  
> Consulte la guía principal en [**README_WHATSAPP_SETUP.md**](file:///c:/Users/mgome/OneDrive/Documents/RICK%20Multitenant/README_WHATSAPP_SETUP.md).  
> Las instrucciones a continuación corresponden al prototipo mono-usuario exploratorio en la subcarpeta `RICK! Guía de Marca Personal` y se conservan exclusivamente como referencia histórica.

---

### Paso 1: Crear tu Bot en Telegram
1. Abre tu aplicación de **Telegram** (en tu celular o en la PC).
2. Busca el usuario oficial: **`@BotFather`** (tiene la insignia de verificación azul).
3. Escríbele el comando `/newbot`.
4. `@BotFather` te responderá con tu **Token HTTP API**.

---

### Paso 2: Pegar el Token en tu `.env` de prueba
Abre el archivo `.env` en:
`c:\Users\mgome\OneDrive\Documents\RICK Multitenant\RICK! Guía de Marca Personal\.env`

Pega el token en la línea:
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui_sin_comillas
```

---

### Paso 3: Iniciar a RICK en Modo Experimental
Haz doble clic en:
👉 `run_telegram.bat` (en la carpeta `RICK! Guía de Marca Personal`).
