import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
# import spacy
from collections import Counter
import json


try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Chunk:
    """Representa un fragmento de documento"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    
    def __post_init__(self):
        # Agregar información adicional
        self.metadata["chunk_id"] = self.chunk_id
        self.metadata["chunk_index"] = self.chunk_index
        self.metadata["char_count"] = len(self.content)
        self.metadata["word_count"] = len(self.content.split())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el chunk a diccionario"""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char
        }

class SmartChunker:
    """Sistema avanzado de chunking con múltiples estrategias"""
    
    def __init__(self):
        self.config = settings.chunking
        
        # Inicializar tokenizer para contar tokens con precisión
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # # Cargar modelo spaCy para análisis lingüístico (opcional)
        # try:
        #     self.nlp = spacy.load("es_core_news_sm")
        #     logger.info("Modelo spaCy cargado para chunking inteligente")
        # except:
        #     self.nlp = None
        #     logger.warning("Modelo spaCy no disponible, usando chunking básico")

        # Cargar modelo spaCy para análisis lingüístico (opcional)
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("es_core_news_sm")
                logger.info("Modelo spaCy cargado para chunking inteligente")
            except:
                self.nlp = None
                logger.warning("Modelo spaCy no disponible, usando chunking básico")
        else:
            self.nlp = None
            logger.warning("spaCy no está instalado. El chunking inteligente no funcionará.")
            
        # Inicializar splitter de LangChain como base
        self.base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
            length_function=self._token_length
        )
        
        # Estadísticas
        self.stats = {
            "total_chunks": 0,
            "avg_chunk_size": 0,
            "min_chunk_size": float('inf'),
            "max_chunk_size": 0
        }
        
    def chunk_documents(self, documents: List[Any]) -> List[Chunk]:
        """Procesa una lista de documentos y genera chunks"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
            
        # Actualizar estadísticas
        if all_chunks:
            sizes = [len(chunk.content) for chunk in all_chunks]
            self.stats["total_chunks"] = len(all_chunks)
            self.stats["avg_chunk_size"] = sum(sizes) / len(sizes)
            self.stats["min_chunk_size"] = min(sizes)
            self.stats["max_chunk_size"] = max(sizes)
            
        logger.info(f"Generados {len(all_chunks)} chunks total")
        logger.info(f"Estadísticas: {self.stats}")
        
        return all_chunks
        
    def chunk_document(self, document: Any) -> List[Chunk]:
        """Genera chunks para un documento individual"""
        content = document.content
        base_metadata = document.metadata.copy()
        
        # Detectar estructura del documento
        doc_structure = self._analyze_document_structure(content)
        
        # Elegir estrategia de chunking basada en la estructura
        if doc_structure["has_sections"]:
            chunks = self._semantic_chunking(content, doc_structure)
        else:
            chunks = self._sliding_window_chunking(content)
            
        # Convertir a objetos Chunk
        chunk_objects = []
        for i, (chunk_content, start_char, end_char) in enumerate(chunks):
            # Generar ID único para el chunk
            chunk_id = self._generate_chunk_id(document.doc_id, i, chunk_content)
            
            # Preparar metadata del chunk
            chunk_metadata = base_metadata.copy()
            
            # Limpiar metadata para ChromaDB - convertir listas y valores problemáticos
            for key, value in list(chunk_metadata.items()):
                if isinstance(value, list):
                    chunk_metadata[key] = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, dict):
                    chunk_metadata[key] = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    chunk_metadata[key] = ""
            
            # Agregar nueva metadata (también serializada si es necesario)
            chunk_metadata.update({
                "chunk_method": "semantic" if doc_structure["has_sections"] else "sliding_window",
                "section": self._extract_section_title(content, start_char) or "",
                "keywords": json.dumps(self._extract_keywords(chunk_content), ensure_ascii=False),
                "entities": json.dumps(self._extract_entities(chunk_content) if self.nlp else [], ensure_ascii=False)
            })
            
            chunk_obj = Chunk(
                content=chunk_content,
                metadata=chunk_metadata,
                chunk_id=chunk_id,
                doc_id=document.doc_id,
                chunk_index=i,
                start_char=start_char,
                end_char=end_char
            )
            
            chunk_objects.append(chunk_obj)
            
        logger.info(f"Documento {document.doc_id} dividido en {len(chunk_objects)} chunks")
        
        return chunk_objects
        
    def _semantic_chunking(self, content: str, structure: Dict) -> List[Tuple[str, int, int]]:
        """Chunking basado en la estructura semántica del documento"""
        chunks = []
        
        # Identificar secciones principales
        sections = self._split_by_sections(content, structure["section_markers"])
        
        for section_content, section_start in sections:
            # Si la sección es muy grande, subdividir
            if self._token_length(section_content) > self.config.chunk_size:
                # Subdividir por párrafos o subsecciones
                sub_chunks = self._split_large_section(section_content, section_start)
                chunks.extend(sub_chunks)
            else:
                chunks.append((section_content, section_start, section_start + len(section_content)))
                
        return chunks
        
    def _sliding_window_chunking(self, content: str) -> List[Tuple[str, int, int]]:
        """Chunking con ventana deslizante (método tradicional mejorado)"""
        # Usar el splitter base pero con ajustes
        text_chunks = self.base_splitter.split_text(content)
        
        chunks = []
        current_pos = 0
        
        for chunk_text in text_chunks:
            start_pos = content.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
                
            end_pos = start_pos + len(chunk_text)
            chunks.append((chunk_text, start_pos, end_pos))
            current_pos = start_pos + len(chunk_text) - self.config.chunk_overlap
            
        return chunks
        
    def _split_large_section(self, section: str, base_offset: int) -> List[Tuple[str, int, int]]:
        """Divide una sección grande en chunks más pequeños"""
        # Intentar dividir por párrafos primero
        paragraphs = section.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        current_start = base_offset
        
        for para in paragraphs:
            para_length = self._token_length(para)
            
            if current_length + para_length > self.config.chunk_size and current_chunk:
                # Guardar chunk actual
                chunk_content = '\n\n'.join(current_chunk)
                chunks.append((
                    chunk_content,
                    current_start,
                    current_start + len(chunk_content)
                ))
                
                # Iniciar nuevo chunk con overlap
                if self.config.chunk_overlap > 0 and current_chunk:
                    # Incluir último párrafo del chunk anterior como overlap
                    current_chunk = [current_chunk[-1]]
                    current_length = self._token_length(current_chunk[0])
                    current_start = current_start + len(chunk_content) - len(current_chunk[0])
                else:
                    current_chunk = []
                    current_length = 0
                    current_start = current_start + len(chunk_content) + 2  # +2 for \n\n
                    
            current_chunk.append(para)
            current_length += para_length
            
        # Agregar último chunk si existe
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append((
                chunk_content,
                current_start,
                current_start + len(chunk_content)
            ))
            
        return chunks
        
    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analiza la estructura del documento"""
        structure = {
            "has_sections": False,
            "section_markers": [],
            "has_numbered_sections": False,
            "has_articles": False,
            "predominant_structure": "plain"
        }
        
        # Buscar marcadores de sección
        section_patterns = [
            (r'^[IVX]+\.\s+\w+', 'roman_numerals'),  # I. INTRODUCCIÓN
            (r'^\d+\.\s+\w+', 'numbered'),  # 1. Introducción
            (r'^ARTÍCULO\s+\d+', 'articles'),  # ARTÍCULO 1
            (r'^CLÁUSULA\s+\w+', 'clauses'),  # CLÁUSULA PRIMERA
            (r'^[A-Z][A-Z\s]+:$', 'uppercase_headers'),  # DEFINICIONES:
            (r'^#{1,3}\s+\w+', 'markdown')  # # Título
        ]
        
        for pattern, pattern_type in section_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if len(matches) > 2:  # Al menos 3 secciones
                structure["has_sections"] = True
                structure["section_markers"].extend(matches)
                structure["predominant_structure"] = pattern_type
                
                if pattern_type == "numbered":
                    structure["has_numbered_sections"] = True
                elif pattern_type == "articles":
                    structure["has_articles"] = True
                    
        return structure
        
    def _split_by_sections(self, content: str, markers: List[str]) -> List[Tuple[str, int]]:
        """Divide el contenido por marcadores de sección"""
        if not markers:
            return [(content, 0)]
            
        sections = []
        
        # Crear patrón regex para encontrar todos los marcadores
        pattern = '|'.join(re.escape(marker) for marker in markers)
        
        # Encontrar todas las posiciones de los marcadores
        positions = []
        for match in re.finditer(pattern, content):
            positions.append((match.start(), match.group()))
            
        # Dividir el contenido
        for i, (pos, marker) in enumerate(positions):
            if i < len(positions) - 1:
                next_pos = positions[i + 1][0]
                section_content = content[pos:next_pos].strip()
            else:
                section_content = content[pos:].strip()
                
            if section_content:
                sections.append((section_content, pos))
                
        return sections
        
    def _extract_section_title(self, content: str, position: int) -> Optional[str]:
        """Extrae el título de la sección actual"""
        # Buscar hacia atrás desde la posición para encontrar el título
        section_before = content[:position]
        lines = section_before.split('\n')
        
        # Buscar la última línea no vacía que parezca un título
        for line in reversed(lines[-5:]):  # Revisar últimas 5 líneas
            line = line.strip()
            if line and (
                line.isupper() or 
                re.match(r'^[IVX]+\.\s+', line) or
                re.match(r'^\d+\.\s+', line) or
                re.match(r'^ARTÍCULO\s+\d+', line)
            ):
                return line
                
        return None
        
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extrae palabras clave del texto"""
        # Palabras a ignorar (stopwords en español)
        stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
            'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar',
            'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o',
            'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'si', 'me',
            'ya', 'ver', 'porque', 'dar', 'cuando', 'muy', 'sin', 'vez',
            'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo',
            'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así',
            'primero', 'desde', 'grande', 'eso', 'ni', 'nos', 'llegar',
            'pasar', 'tiempo', 'después', 'poner', 'parte', 'vida', 'quedar',
            'siempre', 'creer', 'hablar', 'llevar', 'dejar', 'nada', 'cada',
            'seguir', 'menos', 'nuevo', 'encontrar'
        }
        
        # Tokenizar y filtrar
        words = re.findall(r'\b[a-záéíóúñ]+\b', text.lower())
        words = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Contar frecuencias
        word_freq = Counter(words)
        
        # Obtener top N
        keywords = [word for word, freq in word_freq.most_common(top_n)]
        
        return keywords
        
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extrae entidades nombradas usando spaCy"""
        if not self.nlp:
            return []
            
        try:
            doc = self.nlp(text[:1000])  # Limitar a primeros 1000 chars por velocidad
            
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                
            return entities[:10]  # Limitar a 10 entidades
            
        except Exception as e:
            logger.warning(f"Error extrayendo entidades: {str(e)}")
            return []
            
    def _token_length(self, text: str) -> int:
        """Cuenta tokens usando el tokenizer de OpenAI"""
        return len(self.encoding.encode(text))
        
    def _generate_chunk_id(self, doc_id: str, index: int, content: str) -> str:
        """Genera un ID único para el chunk"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
        return f"{doc_id}_chunk_{index}_{content_hash}"
        
    def get_chunking_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del proceso de chunking"""
        return self.stats