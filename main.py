from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
from io import BytesIO
import PyPDF2

# Cargar variables de entorno
load_dotenv()

# Obtener tokens
TG_Bot = os.getenv("API_TOKEN_Telegram")
LLM = os.getenv("API_TOKEN_deepseek")
PDF_URL = os.getenv("PDF_URL", "https://drive.google.com/uc?export=download&id=1mP449kYc-8ZfFfbg2PsfYK1lbbc0EhL7")

# Inicializar cliente de DeepSeek
client = OpenAI(
    api_key=LLM,
    base_url="https://openrouter.ai/api/v1"
)

# Variable global para almacenar el contenido del PDF
pdf_content = ""

def cargar_pdf():
    """Carga y procesa el PDF al iniciar el bot"""
    global pdf_content
    
    try:
        print("📄 Cargando contenido del PDF...")
        
        # Descargar el PDF
        response = requests.get(PDF_URL, timeout=30)
        response.raise_for_status()
        
        # Leer el PDF
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extraer texto de todas las páginas
        text_content = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        # Unir todo el contenido
        pdf_content = "\n\n".join(text_content)
        
        print(f"✅ PDF cargado exitosamente: {len(pdf_reader.pages)} páginas, {len(pdf_content)} caracteres")
        
    except Exception as e:
        print(f"❌ Error al cargar el PDF: {e}")
        pdf_content = ""

async def Saludo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Enviar mensaje de bienvenida
    await update.message.reply_text('Bienvenido al bot explicativo de la materia de Inteligencia Artificial')
    
    # Enviar estado de descarga
    await update.message.reply_text('📄 Descargando el material del curso...')
    
    try:
        # Descargar el PDF desde Google Drive
        response = requests.get(PDF_URL, timeout=30)
        response.raise_for_status()
        
        # Crear archivo en memoria
        pdf_file = BytesIO(response.content)
        pdf_file.name = "Psinoptico Inteligencia artificial_2025.pdf"
        
        # Enviar el PDF
        await update.message.reply_document(
            document=pdf_file,
            filename="Psinoptico Inteligencia artificial_2025.pdf",
            caption="📚 Aquí está el material del curso de Inteligencia Artificial"
        )
        
        # Invitar a leer y hacer preguntas
        await update.message.reply_text(
            "📖 Te invito a leer el material y hacer cualquier pregunta sobre el contenido.\n\n"
            "💬 Simplemente escribe tu pregunta y te responderé basándome en el material del curso.\n\n"
            "¡Estoy aquí para ayudarte! 🤖"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al descargar el PDF: {str(e)}")

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde mensajes usando DeepSeek con restricción al contenido del PDF"""
    
    # Verificar que el PDF esté cargado
    if not pdf_content:
        await update.message.reply_text(
            "❌ El material del curso no está disponible. Por favor, contacta al administrador."
        )
        return
    
    # Obtener el mensaje del usuario
    pregunta = update.message.text
    
    # Mostrar que está escribiendo
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    try:
        # Configurar el prompt con instrucciones estrictas
        system_prompt = f"""Eres un asistente educativo especializado en Inteligencia Artificial.

REGLAS ESTRICTAS:
1. SOLO puedes responder preguntas relacionadas con el contenido del material del curso que te proporciono a continuación.
2. Si te preguntan algo que NO está relacionado con el material, debes responder: "Lo siento, solo puedo responder preguntas relacionadas con el material del curso de Inteligencia Artificial. Por favor, haz una pregunta sobre el contenido del documento."
3. NO inventes información que no esté en el material.
4. Si la información no está en el material, indícalo claramente.
5. Responde en español de forma clara y educativa.
6. Puedes explicar, aclarar y profundizar en los temas del material, pero NUNCA salgas del contexto del documento.


MATERIAL DEL CURSO:
{pdf_content}

Recuerda: SOLO responde sobre el contenido de este material."""
        
        # Llamar a DeepSeek con el contexto del PDF
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pregunta}
            ],
            temperature=0.3  # Temperatura baja para respuestas más precisas
        )
        
        # Obtener la respuesta
        respuesta = response.choices[0].message.content
        
        # Enviar respuesta al usuario
        await update.message.reply_text(respuesta)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Cargar el contenido del PDF al iniciar
print("🤖 Iniciando bot...")
cargar_pdf()

# Crear aplicación
application = ApplicationBuilder().token(TG_Bot).build()

# Registrar comandos
application.add_handler(CommandHandler("start", Saludo))

# Registrar handler para mensajes de texto (respuestas con DeepSeek)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

# Iniciar bot
print("✅ Bot iniciado. Presiona Ctrl+C para detener.\n")
application.run_polling(allowed_updates=Update.ALL_TYPES)