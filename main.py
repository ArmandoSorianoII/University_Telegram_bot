
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
from controllers.bot_controller import BotController

# Cargar variables de entorno
load_dotenv()

def main():
    #Función principal que inicializa y ejecuta el bot
    
    # Obtener token de Telegram
    TG_Bot = os.getenv("API_TOKEN_Telegram")
    
    if not TG_Bot:
        print("❌ Error: API_TOKEN_Telegram no está configurado en las variables de entorno")
        return
    
    # Inicializar controlador
    bot_controller = BotController()
    
    # Cargar PDF al iniciar
    print("🤖 Iniciando bot...")
    if not bot_controller.initialize_pdf():
        print("⚠️ Advertencia: No se pudo cargar el PDF inicialmente")
    
    # Crear aplicación
    application = ApplicationBuilder().token(TG_Bot).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", bot_controller.handle_start_command))
    
    # Registrar handler para mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_controller.handle_text_message))
    
    # Iniciar bot
    print("✅ Bot iniciado. Presiona Ctrl+C para detener.\n")
    application.run_polling()

if __name__ == "__main__":
    main()