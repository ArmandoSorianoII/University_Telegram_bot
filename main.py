from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, Application

from dotenv import load_dotenv
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from controllers.bot_controller import BotController

# Cargar variables de entorno
load_dotenv()

async def post_init(application: Application):
    """
    Configura los comandos del bot en el menú de Telegram
    """
    await application.bot.set_my_commands([
        BotCommand("start", "Iniciar el bot"),
        BotCommand("recursos", "Ver recursos disponibles")
    ])

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
    application = ApplicationBuilder().token(TG_Bot).post_init(post_init).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler("start", bot_controller.handle_start_command))
    application.add_handler(CommandHandler("recursos", bot_controller.handle_resources_command))
    
    # Registrar handler para mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_controller.handle_text_message))
    application.add_handler(CallbackQueryHandler(bot_controller.handle_resources_callback))
    
    # Iniciar bot
    # Levantar un servidor HTTP ligero para que Render detecte un puerto abierto (health check)
    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK")

        # Evitar logs por cada request
        def log_message(self, format, *args):
            return

    def _start_health_server():
        try:
            port = int(os.environ.get("PORT", "8000"))
        except Exception:
            port = 8000
        server = HTTPServer(("0.0.0.0", port), _HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🔌 Health server listening on port {port}")

    _start_health_server()
    print("✅ Bot iniciado. Presiona Ctrl+C para detener.\n")
    application.run_polling()

if __name__ == "__main__":
    main()