from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from openai import OpenAI
from models.pdf_handler import PDFHandler
from controllers.analytics_logger import AnalyticsLogger
import os
import requests
from io import BytesIO
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
        self.analytics_logger = AnalyticsLogger()
    
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
    
    def _get_pdf_from_url_env(self, env_var_name: str, default_filename: str):
        url = os.getenv(env_var_name)
        if not url:
            return None
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            pdf_file = BytesIO(response.content)
            pdf_file.name = default_filename
            return pdf_file
        except Exception:
            return None
    
    def _get_material_recomendado_text(self) -> str:
        text = os.getenv("MATERIAL_RECOMENDADO")
        if text:
            return text
        return "Por ahora no hay material recomendado configurado. Consulta al docente."
    
    def _web_search_snippets(self, question: str) -> str:
        endpoint = os.getenv("WEB_SEARCH_ENDPOINT", "https://api.duckduckgo.com/")
        params = {
            "q": question,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return ""
        snippets = []
        abstract = data.get("AbstractText") or data.get("Abstract")
        if abstract:
            snippets.append(abstract)
        related = data.get("RelatedTopics") or []
        for item in related:
            if isinstance(item, dict):
                text = item.get("Text")
                if text:
                    snippets.append(text)
                topics = item.get("Topics")
                if isinstance(topics, list):
                    for sub in topics:
                        if isinstance(sub, dict):
                            text = sub.get("Text")
                            if text:
                                snippets.append(text)
            if len(snippets) >= 5:
                break
        result = "\n\n".join(snippets)
        if len(result) > 1500:
            result = result[:1500]
        return result
    
    async def generate_response(self, question: str, history=None) -> str:
        
        pdf_content = self.get_pdf_content()
        
        if not pdf_content:
            return "❌ El material del curso no está disponible. Por favor, contacta al administrador."
        
        web_snippets = self._web_search_snippets(question)
        if history is None:
            history = []
        
        try:
            system_prompt = f"""Eres un asistente educativo especializado en Inteligencia Artificial y en apoyar la asignatura correspondiente.

REGLAS ESTRICTAS:
1. Debes responder únicamente a preguntas relacionadas con la asignatura de Inteligencia Artificial. Esto incluye tanto:
   - preguntas que hagan referencia explícita al contenido del material del curso que te proporciono, como
   - preguntas sobre temas de Inteligencia Artificial en general (por ejemplo, nuevos modelos LLM de Google u otras instituciones, tendencias actuales en IA, aplicaciones de redes neuronales, etc.), siempre que estén dentro del ámbito académico de la asignatura.
2. Solo debes rechazar preguntas que sean claramente ajenas a la asignatura de Inteligencia Artificial (por ejemplo, deportes, vida personal del usuario, recetas de cocina, noticias políticas sin relación con IA, etc.). En ese caso, responde: "Lo siento, solo puedo responder preguntas relacionadas con el material del curso de Inteligencia Artificial y con mis funciones dentro de este bot. Por favor, haz una pregunta sobre el contenido del documento o sobre algún tema de Inteligencia Artificial."
3. Debes priorizar siempre el contenido del material del curso. Si una pregunta relacionada con la materia no puede responderse claramente con el material, puedes complementar la respuesta usando la información procedente de la búsqueda web que se te proporciona, manteniéndote siempre en el contexto de la asignatura.
4. Cuando la pregunta sea sobre temas de Inteligencia Artificial de actualidad (por ejemplo, qué modelo LLM lanzó recientemente una empresa), y esa información no esté en el material, utiliza los resultados de la búsqueda web para dar una respuesta sintética, explicando brevemente el modelo y su relación con la temática de la asignatura.
5. Cuando el usuario te pregunte qué puedes hacer, describe de forma breve y clara tus capacidades principales: responder dudas sobre el material de Inteligencia Artificial, enviar recursos del curso (por ejemplo mediante el comando /recursos), sugerir material recomendado y usar búsqueda web como apoyo cuando sea útil.
6. NO inventes información que no esté en el material o en los resultados de la búsqueda web.
7. Si la información no está ni en el material ni en los resultados de la búsqueda web, indícalo claramente.
8. Responde en español de forma clara y educativa.
9. Puedes explicar, aclarar y profundizar en los temas del material, pero NUNCA salgas del contexto del documento ni de los temas propios de la Inteligencia Artificial.
10. Usa el historial de conversación para mantener el contexto y permitir preguntas de seguimiento, pero no cambies de tema fuera de la asignatura ni respondas sobre asuntos totalmente ajenos.


MATERIAL DEL CURSO:
{pdf_content}

RESULTADOS DE BUSQUEDA EN LA WEB (pueden estar vacíos):
{web_snippets}

Recuerda: SOLO respondes sobre el contenido de la asignatura de Inteligencia Artificial: prioriza el material del curso y, cuando sea necesario, complétalo con la información de la búsqueda web siempre que esté relacionada con la asignatura y con tus funciones como asistente educativo."""
            
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            for item in history:
                role = item.get("role")
                content = item.get("content")
                if role and content:
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": question})
            
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3.1",
                messages=messages,
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
    
    async def handle_resources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        keyboard = [
            [InlineKeyboardButton("📄 Sinóptico de la materia", callback_data="resource_sinoptico")],
            [InlineKeyboardButton("📝 Plantilla Corte I", callback_data="resource_corte_i")],
            [InlineKeyboardButton("📝 Plantilla Corte II", callback_data="resource_corte_ii")],
            [InlineKeyboardButton("📝 Plantilla Corte III", callback_data="resource_corte_iii")],
            [InlineKeyboardButton("📚 Material recomendado", callback_data="resource_material")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Selecciona el recurso que deseas recibir:", reply_markup=reply_markup)
    
    async def handle_resources_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = query.data
        if data == "resource_sinoptico":
            pdf_file = self.get_pdf_file()
            if pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename="Psinoptico Inteligencia artificial_2025.pdf",
                    caption="📚 Sinóptico de la materia de Inteligencia Artificial",
                )
            else:
                await query.message.reply_text("❌ No se pudo obtener el sinóptico.")
        elif data == "resource_corte_i":
            pdf_file = self._get_pdf_from_url_env("PDF_URL_CORTE_I", "Plantilla_De_Medicion_De_Corte_I.pdf")
            if pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename="Plantilla_De_Medicion_De_Corte_I.pdf",
                    caption="📝 Plantilla de medición de Corte I",
                )
            else:
                await query.message.reply_text("❌ No se pudo obtener la plantilla de Corte I.")
        elif data == "resource_corte_ii":
            pdf_file = self._get_pdf_from_url_env("PDF_URL_CORTE_II", "Plantilla_De_Medicion_De_Corte_II.pdf")
            if pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename="Plantilla_De_Medicion_De_Corte_II.pdf",
                    caption="📝 Plantilla de medición de Corte II",
                )
            else:
                await query.message.reply_text("❌ No se pudo obtener la plantilla de Corte II.")
        elif data == "resource_corte_iii":
            pdf_file = self._get_pdf_from_url_env("PDF_URL_CORTE_III", "Plantilla_De_Medicion_De_Corte_III.pdf")
            if pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename="Plantilla_De_Medicion_De_Corte_III.pdf",
                    caption="📝 Plantilla de medición de Corte III",
                )
            else:
                await query.message.reply_text("❌ No se pudo obtener la plantilla de Corte III.")
        elif data == "resource_material":
            text = self._get_material_recomendado_text()
            await query.message.reply_text(text)
    
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
        history = context.chat_data.get("history", [])
        
        # Mostrar que está escribiendo
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        
        try:
            # Generar respuesta usando el controlador
            respuesta = await self.generate_response(pregunta, history)
            
            # Enviar respuesta al usuario
            await update.message.reply_text(respuesta)
            
            history.append({"role": "user", "content": pregunta})
            history.append({"role": "assistant", "content": respuesta})
            if len(history) > 10:
                history = history[-10:]
            context.chat_data["history"] = history
            if self.analytics_logger:
                self.analytics_logger.log_interaction(update, pregunta, respuesta)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
