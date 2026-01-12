# University Telegram Bot

Bot de Telegram para apoyar la asignatura de **Inteligencia Artificial** de la Universidad Gran Mariscal de Ayacucho.

Permite a los estudiantes:

- Consultar dudas sobre el contenido del curso usando un modelo de lenguaje (DeepSeek vía OpenRouter).
- Descargar material del curso (sinóptico y plantillas de evaluación).
- Recibir material recomendado por el docente.
- Mantener conversaciones con contexto (preguntas de seguimiento).

Esta etapa del proyecto también añade **dockerización**, búsqueda web complementaria y **registro analítico de consultas**.

---

## 1. Tecnologías principales

- **Python 3.11**
- **python-telegram-bot 20.7**
- **OpenAI SDK** (usado contra OpenRouter: modelo `deepseek/deepseek-chat-v3.1`)
- **PyPDF2** para procesar el PDF del curso
- **python-dotenv** para variables de entorno
- **Docker** (opcional, para despliegue y ejecución aislada)

---

## 2. Funcionalidades actuales

- **Bot de preguntas y respuestas** sobre el contenido del PDF de la materia.
- **Descarga del sinóptico** directamente desde el bot.
- **Servidor HTTP ligero de health-check** (puerto configurable, por defecto 8000).
- **Soporte híbrido**: prioriza el PDF y, cuando hace falta, usa una búsqueda web como apoyo.
- **Memoria conversacional**: el bot recuerda el contexto reciente de la conversación por chat.
- **Registro de interacciones** para analítica básica.

---

## 3. Mejoras de esta etapa

### 3.1. Menú de recursos descargables (`/recursos`)

Nuevo comando: ` /recursos`

Al ejecutarlo, el bot muestra un menú con botones:

- **📄 Sinóptico de la materia**
- **📝 Plantilla Corte I**
- **📝 Plantilla Corte II**
- **📝 Plantilla Corte III**
- **📚 Material recomendado**

Cada opción envía al usuario:

- Un **PDF** descargado desde una URL configurada en variables de entorno (sinóptico y plantillas), o
- Un **texto** con material recomendado definido por el docente.

Variables implicadas (ver detalle en la sección de entorno):

- `PDF_URL` (sinóptico principal)
- `PDF_URL_CORTE_I`
- `PDF_URL_CORTE_II`
- `PDF_URL_CORTE_III`
- `MATERIAL_RECOMENDADO`

### 3.2. Soporte híbrido con búsqueda web

La generación de respuestas ahora funciona así:

1. Se carga el contenido del PDF del curso (material principal).
2. Para cada pregunta, se hace una **búsqueda web ligera** (por defecto usando DuckDuckGo en formato JSON).
3. Se construye un *system prompt* que:
   - Obliga al modelo a **priorizar siempre** el contenido del PDF.
   - Permite complementar con resultados web **solo si la pregunta está relacionada con la asignatura** y el PDF no es suficiente.
   - Prohíbe salirse del contexto de la materia de Inteligencia Artificial.

Variable implicada:

- `WEB_SEARCH_ENDPOINT` (opcional, por defecto `https://api.duckduckgo.com/`).

### 3.3. Analítica y registro de consultas

Se añadió el módulo `controllers/analytics_logger.py`, que guarda cada interacción en un archivo `JSONL` (una línea por interacción).

Por cada mensaje se registra:

- `timestamp` (UTC)
- `user_id` (real o anonimizado)
- `question` (pregunta del usuario)
- `answer` (respuesta del bot)
- campos reservados `source` y `used_web` para futuras extensiones

Variables implicadas:

- `LOG_FILE_PATH` (por defecto `logs/interactions.log`)
- `ANONYMIZE_LOGS` (`"true"` para anonimizar el `chat.id` con SHA256, `"false"` para guardarlo en claro)

### 3.4. Memoria de contexto conversacional

Antes, cada mensaje se respondía de forma aislada. Ahora:

- Se mantiene un **historial breve** por chat usando `context.chat_data["history"]` (últimas ~10 entradas).
- Ese historial se pasa al modelo junto con la nueva pregunta.
- El usuario puede hacer preguntas de seguimiento del tipo: *"dame más ejemplos de eso"* y el bot mantiene el contexto.

La memoria se mantiene mientras el proceso del bot está vivo; no se persiste aún en base de datos.

---

## 4. Configuración de variables de entorno

El proyecto usa `python-dotenv` (`load_dotenv()`), por lo que se recomienda un archivo de entorno, por ejemplo `env.env` o `.env` en la raíz del proyecto.

Ejemplo (NO uses tus claves reales en el repositorio):

```env
API_TOKEN_Telegram = "TU_TOKEN_DE_TELEGRAM"
API_TOKEN_deepseek = "TU_API_KEY_DEEPSEEK_OPENROUTER"

# PDF principal del curso (sinóptico)
PDF_URL = "https://drive.google.com/uc?export=download&id=ID_DEL_SINOPTICO"

# Plantillas de medición por corte
PDF_URL_CORTE_I = "https://example.com/Plantilla_De_Medicion_De_Corte_I.pdf"
PDF_URL_CORTE_II = "https://example.com/Plantilla_De_Medicion_De_Corte_II.pdf"
PDF_URL_CORTE_III = "https://example.com/Plantilla_De_Medicion_De_Corte_III.pdf"

# Texto libre con material recomendado (libros, vídeos, papers, etc.)
MATERIAL_RECOMENDADO = "Lista de recursos recomendados por el docente"

# Endpoint de búsqueda web (opcional)
WEB_SEARCH_ENDPOINT = "https://api.duckduckgo.com/"

# Registro de analítica
LOG_FILE_PATH = "logs/interactions.log"
ANONYMIZE_LOGS = "true"   # o "false" si no quieres anonimizar

# Puerto para el servidor de health-check HTTP (opcional)
PORT = "8000"
```

> **Importante:** No subas al repositorio tus tokens reales de Telegram ni tus claves de OpenRouter.

---

## 5. Ejecución local (sin Docker)

1. Crear y activar un entorno virtual (opcional pero recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # .venv\Scripts\activate   # Windows PowerShell
   ```

2. Instalar dependencias:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Configurar el archivo de entorno (`.env` o `env.env`) con tus claves y URLs.

4. Ejecutar el bot:

   ```bash
   python main.py
   ```

5. En Telegram, hablar con tu bot y probar:

   - `/start` para recibir bienvenida y sinóptico.
   - `/recursos` para abrir el menú de recursos descargables.
   - Preguntas libres sobre el contenido del curso.

---

## 6. Ejecución con Docker

Este repositorio incluye un `Dockerfile` sencillo basado en `python:3.11-slim`.

### 6.1. Construir la imagen

Desde la raíz del proyecto:

```bash
docker build -t university-telegram-bot .
```

### 6.2. Ejecutar el contenedor usando el archivo de entorno

Asumiendo que tienes un archivo `env.env` en la raíz del proyecto con todas las variables configuradas:

```bash
docker run -d \
  --name university-telegram-bot \
  --env-file .env \
  -p 8000:8000 \
  university-telegram-bot
```

- El bot usará `API_TOKEN_Telegram` y demás variables desde el contenedor.
- El servidor de health-check quedará accesible en `http://localhost:8000`.

### 6.3. Persistir logs fuera del contenedor (opcional)

Para que `logs/interactions.log` no se pierda al borrar el contenedor, monta un volumen:

```bash
docker run -d \
  --name university-telegram-bot \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -p 8000:8000 \
  university-telegram-bot
```

En Windows (PowerShell) puedes usar algo similar a:

```powershell
docker run -d `
  --name university-telegram-bot `
  --env-file .env `
  -v ${PWD}\logs:/app/logs `
  -p 8000:8000 `
  university-telegram-bot
```

---

## 7. Estructura básica del proyecto

```text
.
├── controllers/
│   ├── __init__.py
│   ├── bot_controller.py        # Lógica principal del bot de Telegram
│   └── analytics_logger.py      # Registro de interacciones (analítica)
├── models/
│   └── pdf_handler.py           # Carga y procesamiento del PDF del curso
├── main.py                      # Punto de entrada del bot
├── requirements.txt             # Dependencias de Python
├── Dockerfile                   # Dockerización básica
├── env.env (o .env)             # Variables de entorno (no debe subirse con datos sensibles)
└── README.md                    # Este archivo
```

---

## 8. Próximos pasos posibles

- Persistir el historial de conversación en base de datos para análisis más profundo.
- Añadir panel de visualización de métricas (dashboards) usando los logs.
- Integrar más tipos de recursos descargables (presentaciones, ejercicios, etc.).
