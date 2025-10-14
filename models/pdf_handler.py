import requests
from io import BytesIO
import PyPDF2
from typing import Optional
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class PDFHandler:
    """Modelo para manejar la carga y procesamiento de PDFs"""
    
    def __init__(self):
        self.content = ""
        self.is_loaded = False
        self.pdf_url = os.getenv("PDF_URL")
    
    def load_pdf(self) -> bool:
        """
        Carga y procesa el PDF desde la URL configurada
        
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario
        """
        try:
            print("📄 Cargando contenido del PDF...")
            
            # Descargar el PDF
            response = requests.get(self.pdf_url, timeout=30)
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
            self.content = "\n\n".join(text_content)
            self.is_loaded = True
            
            print(f"✅ PDF cargado exitosamente: {len(pdf_reader.pages)} páginas, {len(self.content)} caracteres")
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar el PDF: {e}")
            self.content = ""
            self.is_loaded = False
            return False
    
    def get_content(self) -> str:
        """
        Obtiene el contenido del PDF
        
      
        str: Contenido del PDF o string vacío si no está cargado
        """
        return self.content if self.is_loaded else ""
    
    def is_pdf_loaded(self) -> bool:
        
        "Verifica si el PDF está cargado"

        return self.is_loaded
    
    def get_pdf_file(self) -> Optional[BytesIO]:
        """
        Obtiene el archivo PDF como BytesIO para envío
        
        Returns:
            BytesIO: Archivo PDF en memoria o None si hay error
        """
        try:
            response = requests.get(self.pdf_url, timeout=30)
            response.raise_for_status()
            
            pdf_file = BytesIO(response.content)
            pdf_file.name = "Psinoptico Inteligencia artificial_2025.pdf"
            return pdf_file
            
        except Exception as e:
            print(f"❌ Error al obtener archivo PDF: {e}")
            return None
