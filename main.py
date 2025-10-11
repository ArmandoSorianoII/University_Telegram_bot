from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from openai import OpenAI
import os

# Cargar variables de entorno
load_dotenv()

# Obtener tokens
TG_Bot = os.getenv("API_TOKEN_Telegram")
LLM = os.getenv("API_TOKEN_deepseek")

# Inicializar cliente de DeepSeek
client = OpenAI(
    api_key=LLM,
    base_url="https://openrouter.ai/api/v1"
)

async def Saludo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bienvenido al bot explicativo de la materia')

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde mensajes usando DeepSeek"""
    
    # Obtener el mensaje del usuario
    pregunta = update.message.text
    
    # Mostrar que está escribiendo
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    try:
        # Llamar a DeepSeek
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1",
            messages=[
                {"role": "user", "content": pregunta}
            ],
            temperature=0.7
        )
        
        # Obtener la respuesta
        respuesta = response.choices[0].message.content
        
        # Enviar respuesta al usuario
        await update.message.reply_text(respuesta)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Crear aplicación
application = ApplicationBuilder().token(TG_Bot).build()

# Registrar comandos
application.add_handler(CommandHandler("start", Saludo))

# Registrar handler para mensajes de texto (respuestas con DeepSeek)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

# Iniciar bot
application.run_polling(allowed_updates=Update.ALL_TYPES)