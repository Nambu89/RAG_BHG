import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

@dataclass
class OpenAIConfig:
    """Configuración para OpenAI API"""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = "text-embedding-3-large"
    chat_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.1
    max_tokens: int = 2000
    
@dataclass
class ChunkingConfig:
    """Configuración para el chunking de documentos"""
    chunk_size: int = 512
    chunk_overlap: int = 128
    separators: list = None
    
    def __post_init__(self):
        if self.separators is None:
            self.separators = ["\n\n", "\n", ". ", " ", ""]

@dataclass
class VectorStoreConfig:
    """Configuración para el almacén de vectores"""
    type: str = "chromadb"  # chromadb, faiss, qdrant
    collection_name: str = "athenea_contracts"
    embedding_dimension: int = 3072  # text-embedding-3-large
    distance_metric: str = "cosine"
    persist_directory: str = "./data/vector_store"
    
@dataclass
class SearchConfig:
    """Configuración para búsqueda híbrida"""
    top_k_vector: int = 50
    top_k_keyword: int = 50
    top_k_final: int = 20
    similarity_threshold: float = 0.15
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_hyde: bool = True  # Hypothetical Document Embeddings
    
@dataclass
class RAGConfig:
    """Configuración para el pipeline RAG"""
    system_prompt_template: str = """Eres un experto analista legal especializado en contratos del Barceló Hotel Group. 
Tu tarea es responder preguntas sobre contratos basándote ÚNICAMENTE en la información proporcionada.

REGLAS CRÍTICAS:
1. SOLO usa información de los fragmentos proporcionados
2. Si no encuentras la información, di claramente "No encuentro esta información en los documentos proporcionados"
3. SIEMPRE cita el documento fuente y la sección específica
4. Sé preciso con fechas, cifras y cláusulas
5. Si hay ambigüedad, menciona todas las interpretaciones posibles

Contexto de documentos:
{context}

Metadatos de documentos:
{metadata}"""
    
    user_prompt_template: str = """Pregunta: {question}

Por favor, proporciona una respuesta clara y estructurada basada únicamente en los documentos proporcionados."""
    
    enable_validation: bool = True
    confidence_threshold: float = 0.8
    max_context_length: int = 16000
    
@dataclass
class UIConfig:
    """Configuración para la interfaz de usuario"""
    title: str = "Athenea RAG - Barceló Hotel Group"
    theme: str = "dark"
    show_sources: bool = True
    show_confidence: bool = True
    enable_feedback: bool = True
    
@dataclass
class LoggingConfig:
    """Configuración para logging y métricas"""
    log_level: str = "INFO"
    log_file: str = "./logs/athenea.log"
    enable_metrics: bool = True
    metrics_file: str = "./logs/metrics.json"
    track_queries: bool = True
    track_performance: bool = True

class Settings:
    """Configuración global del sistema"""
    def __init__(self):
        self.openai = OpenAIConfig()
        self.chunking = ChunkingConfig()
        self.vector_store = VectorStoreConfig()
        self.search = SearchConfig()
        self.rag = RAGConfig()
        self.ui = UIConfig()
        self.logging = LoggingConfig()
        
        # Validar configuración
        self._validate_config()
        
    def _validate_config(self):
        """Valida que la configuración sea correcta"""
        if not self.openai.api_key:
            raise ValueError("OpenAI API key no configurada. Por favor, configura OPENAI_API_KEY en el archivo .env")
            
        if self.search.similarity_threshold < 0 or self.search.similarity_threshold > 1:
            raise ValueError("similarity_threshold debe estar entre 0 y 1")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return {
            "openai": self.openai.__dict__,
            "chunking": self.chunking.__dict__,
            "vector_store": self.vector_store.__dict__,
            "search": self.search.__dict__,
            "rag": self.rag.__dict__,
            "ui": self.ui.__dict__,
            "logging": self.logging.__dict__
        }

# Instancia global de configuración
settings = Settings()