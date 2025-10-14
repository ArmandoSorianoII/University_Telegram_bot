from telegram import Update
from telegram.ext import ContextTypes
from openai import OpenAI
from models.pdf_handler import PDFHandler
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class BotController:
    
    def __init__(self):
        self.pdf_handler = PDFHandler()
        self.client = OpenAI(
            api_key=os.getenv("API_TOKEN_deepseek"),
            base_url="https://openrouter.ai/api/v1"
        )
    
    def initialize_pdf(self) -> bool:
        
        "Inicializa la carga del PDF"
        
        return self.pdf_handler.load_pdf()
    
    def get_pdf_content(self) -> str:
        """
        Obtiene el contenido del PDF
        
        Returns:
            str: Contenido del PDF
        """
        return self.pdf_handler.get_content()
    
    def is_pdf_available(self) -> bool:
        
        #Verifica si el PDF está disponible
        
        return self.pdf_handler.is_pdf_loaded()
    
    def get_pdf_file(self):
        
        #Obtiene el archivo PDF para envío
        
        return self.pdf_handler.get_pdf_file()
    
    async def generate_response(self, question: str) -> str:
        
        #Genera una respuesta usando DeepSeek basada en el contenido del PDF
        
        pdf_content = self.get_pdf_content()
        
        if not pdf_content:
            return "❌ El material del curso no está disponible. Por favor, contacta al administrador."
        
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
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        #Maneja el comando /start
        
        
        # Enviar mensaje de bienvenida
        await update.message.reply_text('Bienvenido al bot explicativo de la materia de Inteligencia Artificial')
        
        # Enviar estado de descarga
        await update.message.reply_text('📄 Descargando el material del curso...')
        
        try:
            # Obtener el archivo PDF
            pdf_file = self.get_pdf_file()
            
            if pdf_file:
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
            else:
                await update.message.reply_text("❌ Error al descargar el PDF. Por favor, intenta más tarde.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error al descargar el PDF: {str(e)}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
  
        #Maneja mensajes de texto del usuario
        
      
        # Verificar que el PDF esté disponible
        if not self.is_pdf_available():
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
            # Generar respuesta usando el controlador
            respuesta = await self.generate_response(pregunta)
            
            # Enviar respuesta al usuario
            await update.message.reply_text(respuesta)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
