import re
import unicodedata
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Importaciones opcionales
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    
try:
    from unidecode import unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False

from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PreprocessingConfig:
    """Configuración para el preprocesamiento"""
    remove_extra_whitespace: bool = True
    normalize_unicode: bool = True
    fix_encoding: bool = True
    extract_structure: bool = True
    clean_ocr_artifacts: bool = True
    standardize_quotes: bool = True
    remove_watermarks: bool = True
    detect_language: bool = True
    enable_ner: bool = True  # Añadido para NER

class DocumentPreprocessor:
    """Preprocesador avanzado de documentos legales con soporte multiidioma"""
    
    def __init__(self, config: PreprocessingConfig = None):
        self.config = config or PreprocessingConfig()
        self.nlp_models = {}  # Diccionario para múltiples modelos
        
        # Cargar modelos spaCy si están disponibles
        if SPACY_AVAILABLE:
            self._load_spacy_models()
        else:
            logger.warning("spaCy no está instalado. Algunas funciones estarán limitadas. Instálalo con: pip install spacy")
            
        # Patrones de limpieza (mantener los existentes)
        self.patterns = {
            'watermarks': [
                r'CONFIDENCIAL\s*-?\s*NO\s+DISTRIBUIR',
                r'BORRADOR\s*-?\s*DRAFT',
                r'COPIA\s+NO\s+CONTROLADA',
                r'Página\s+\d+\s+de\s+\d+',
                r'\[WATERMARK\]'
            ],
            'ocr_artifacts': [
                r'[^\x00-\x7F]+',  # Caracteres no ASCII extraños
                r'(?<=[a-z])\s+(?=[a-z])',  # Espacios extra dentro de palabras
                r'(\w)\1{4,}',  # Repeticiones excesivas de caracteres
                r'[|¦]',  # Líneas verticales de tablas mal OCR
            ],
            'legal_sections': [
                r'^(?:ARTÍCULO|CLÁUSULA|SECCIÓN)\s+\w+',
                r'^[IVX]+\.\s+\w+',
                r'^\d+\.\d*\s*\w+',
                r'^[A-Z][A-Z\s]+:$'
            ]
        }
    
    def _load_spacy_models(self):
        """Carga modelos de spaCy para español e inglés"""
        # Modelos españoles
        spanish_models = ['es_core_news_md', 'es_core_news_sm', 'es_core_news_lg']
        for model_name in spanish_models:
            try:
                self.nlp_models['es'] = spacy.load(model_name)
                self.nlp_models['es'].max_length = 2000000  # Aumentar límite
                logger.info(f"Modelo spaCy español cargado: {model_name}")
                break
            except OSError:
                continue
        
        if 'es' not in self.nlp_models:
            logger.warning("Modelo spaCy español no encontrado. Instálalo con: python -m spacy download es_core_news_md")
        
        # Modelos ingleses
        english_models = ['en_core_web_md', 'en_core_web_sm', 'en_core_web_lg']
        for model_name in english_models:
            try:
                self.nlp_models['en'] = spacy.load(model_name)
                self.nlp_models['en'].max_length = 2000000
                logger.info(f"Modelo spaCy inglés cargado: {model_name}")
                break
            except OSError:
                continue
        
        if 'en' not in self.nlp_models:
            logger.warning("Modelo spaCy inglés no encontrado. Instálalo con: python -m spacy download en_core_web_md")
        
        # Compatibilidad con código existente
        self.nlp = self.nlp_models.get('es') or self.nlp_models.get('en')
        
    def preprocess_document(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Preprocesa un documento completo"""
        logger.info("Iniciando preprocesamiento de documento")
        
        original_length = len(content)
        
        # Detectar idioma primero si está habilitado
        language = 'es'  # Default
        if self.config.detect_language:
            language = self._detect_language_improved(content[:2000])
            logger.info(f"Idioma detectado: {language}")
        
        # Pipeline de preprocesamiento (mantener existente)
        if self.config.fix_encoding:
            content = self._fix_encoding_issues(content)
            
        if self.config.normalize_unicode:
            content = self._normalize_unicode(content)
            
        if self.config.clean_ocr_artifacts:
            content = self._clean_ocr_artifacts(content)
            
        if self.config.remove_watermarks:
            content = self._remove_watermarks(content)
            
        if self.config.standardize_quotes:
            content = self._standardize_quotes(content)
            
        if self.config.remove_extra_whitespace:
            content = self._normalize_whitespace(content)
            
        # Extraer estructura si está habilitado
        structure = None
        if self.config.extract_structure:
            structure = self._extract_document_structure(content)
        
        # Extraer entidades si está habilitado
        entities = []
        if self.config.enable_ner and self.nlp_models:
            entities = self._extract_entities(content, language)
            
        # Estadísticas
        stats = {
            'original_length': original_length,
            'processed_length': len(content),
            'reduction_percent': (1 - len(content) / original_length) * 100 if original_length > 0 else 0,
            'structure': structure,
            'language': language,
            'entities': entities,
            'entity_count': len(entities)
        }
        
        logger.info(f"Preprocesamiento completado. Reducción: {stats['reduction_percent']:.1f}%")
        if entities:
            logger.info(f"Entidades extraídas: {stats['entity_count']}")
        
        return {
            'content': content,
            'metadata': {**(metadata or {}), **stats}
        }
    
    def _detect_language_improved(self, text: str) -> str:
        """Detección mejorada de idioma"""
        # Primero intentar con spaCy si hay modelo multiidioma
        if hasattr(self, 'nlp') and self.nlp and hasattr(self.nlp, 'lang_'):
            try:
                doc = self.nlp(text[:1000])
                return doc.lang_
            except:
                pass
        
        # Detección por heurística mejorada
        spanish_words = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'por', 'con', 
            'para', 'los', 'las', 'una', 'su', 'al', 'del', 'se', 'es', 'son',
            'como', 'más', 'pero', 'sus', 'le', 'ya', 'este', 'cuando', 'todo',
            'esta', 'entre', 'nos', 'durante', 'también', 'fue', 'había', 'hasta'
        }
        
        english_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 
            'for', 'it', 'with', 'as', 'you', 'do', 'at', 'this', 'but',
            'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
            'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their'
        }
        
        # Contar palabras
        words = text.lower().split()[:200]
        spanish_count = sum(1 for word in words if word in spanish_words)
        english_count = sum(1 for word in words if word in english_words)
        
        # Decidir idioma
        if spanish_count > english_count * 1.2:
            return 'es'
        elif english_count > spanish_count * 1.2:
            return 'en'
        else:
            # Si no es claro, usar patrones adicionales
            if re.search(r'\b(artículo|cláusula|contrato|acuerdo|partes)\b', text.lower()):
                return 'es'
            elif re.search(r'\b(article|clause|agreement|contract|parties)\b', text.lower()):
                return 'en'
            else:
                return 'es'  # Default español para tu caso
    
    def _extract_entities(self, text: str, language: str = 'es') -> List[Dict[str, Any]]:
        """Extrae entidades nombradas usando el modelo apropiado"""
        if not self.nlp_models:
            return []
        
        # Seleccionar modelo según idioma
        nlp = self.nlp_models.get(language)
        if not nlp and self.nlp_models:
            # Usar cualquier modelo disponible
            nlp = next(iter(self.nlp_models.values()))
        
        if not nlp:
            return []
        
        try:
            # Procesar texto (limitar longitud)
            max_length = min(len(text), 1000000)
            doc = nlp(text[:max_length])
            
            entities = []
            seen = set()  # Para evitar duplicados
            
            # Mapeo de tipos de entidades
            entity_type_map = {
                'PER': 'PERSON',
                'ORG': 'ORGANIZATION', 
                'LOC': 'LOCATION',
                'DATE': 'DATE',
                'TIME': 'TIME',
                'MONEY': 'MONEY',
                'PERCENT': 'PERCENTAGE',
                'MISC': 'MISC'
            }
            
            for ent in doc.ents:
                # Evitar duplicados
                if ent.text.lower() in seen:
                    continue
                seen.add(ent.text.lower())
                
                entity_type = entity_type_map.get(ent.label_, ent.label_)
                
                entities.append({
                    'text': ent.text,
                    'type': entity_type,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'language': language
                })
            
            # Para documentos legales, buscar entidades específicas adicionales
            if language == 'es':
                # Buscar partes del contrato
                parties_pattern = r'(?:entre|ENTRE)\s+([A-Z][^,\n]+?)(?:\s+y\s+|\s+Y\s+)([A-Z][^,\n]+?)(?:\s+\(|,|\s+en\s+adelante)'
                matches = re.finditer(parties_pattern, text)
                for match in matches:
                    if match.group(1).strip():
                        entities.append({
                            'text': match.group(1).strip(),
                            'type': 'PARTY',
                            'start': match.start(1),
                            'end': match.end(1),
                            'language': language
                        })
                    if match.group(2).strip():
                        entities.append({
                            'text': match.group(2).strip(),
                            'type': 'PARTY',
                            'start': match.start(2),
                            'end': match.end(2),
                            'language': language
                        })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extrayendo entidades: {str(e)}")
            return []
    
    # Mantener todos los métodos existentes sin cambios
    def _fix_encoding_issues(self, text: str) -> str:
        """Corrige problemas comunes de encoding"""
        # [Mantener implementación existente]
        replacements = {
            # Vocales minúsculas con tilde
            'Ã¡': 'á', 
            'Ã©': 'é', 
            'Ã­': 'í', 
            'Ã³': 'ó', 
            'Ãº': 'ú',
            # Ñ minúscula
            'Ã±': 'ñ',
            # Vocales mayúsculas con tilde  
            'Ã\x81': 'Á',
            'Ã‰': 'É',
            'Ã\x8d': 'Í', 
            'Ã"': 'Ó',
            'Ãš': 'Ú',
            # Ñ mayúscula - usando código hex
            'Ã\x91': 'Ñ',
            # Comillas tipográficas
            '\u201c': '"',  # Comilla izquierda
            '\u201d': '"',  # Comilla derecha
            '\u2018': "'",  # Comilla simple izquierda
            '\u2019': "'",  # Comilla simple derecha
            # Guiones
            '\u2013': '–',  # En dash
            '\u2014': '—',  # Em dash
            # Otros símbolos
            '\u2026': '...',  # Ellipsis
            '\u2022': '•',    # Bullet
            # Símbolos comunes
            'Â°': '°',
            'Â´': '´',
            'Â¨': '¨',
            # Limpiar caracteres vacíos comunes
            'Ã‚Â': '',
            'Ã‚': '',
            'Â ': ' ',
        }
        
        for bad, good in replacements.items():
            text = text.replace(bad, good)
            
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
        
    def _normalize_unicode(self, text: str) -> str:
        """Normaliza caracteres Unicode"""
        # [Mantener implementación existente]
        text = unicodedata.normalize('NFC', text)
        
        preserved_chars = set('áéíóúñÁÉÍÓÚÑ¡¿')
        
        result = []
        for char in text:
            if char in preserved_chars or char.isascii():
                result.append(char)
            else:
                if UNIDECODE_AVAILABLE:
                    ascii_char = unidecode(char)
                    if ascii_char == char:
                        decomposed = unicodedata.normalize('NFD', char)
                        ascii_char = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
                else:
                    decomposed = unicodedata.normalize('NFD', char)
                    ascii_char = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
                    
                result.append(ascii_char if ascii_char else char)
                
        return ''.join(result)
        
    def _clean_ocr_artifacts(self, text: str) -> str:
        """Limpia artefactos comunes de OCR"""
        # [Mantener implementación existente]
        text = re.sub(r'(?<=[a-záéíóúñ])\s+(?=[a-záéíóúñ])', '', text)
        text = re.sub(r'(\w)\1{4,}', r'\1\1', text)
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        text = re.sub(r'[^\w\s\-\.,:;¡!¿?()[\]{}«»""\'\'áéíóúñÁÉÍÓÚÑ€$%@#&*+=/<>|\\]', ' ', text)
        
        return text
        
    def _remove_watermarks(self, text: str) -> str:
        """Elimina marcas de agua comunes"""
        # [Mantener implementación existente]
        for pattern in self.patterns['watermarks']:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
            
        return text
        
    def _standardize_quotes(self, text: str) -> str:
        """Estandariza comillas y apóstrofes"""
        # Comillas dobles
        text = re.sub(r'[""]', '"', text)  # Comillas tipográficas izquierda y derecha
        text = re.sub(r'[„"]', '"', text)  # Comillas alemanas y otras
        text = re.sub(r'[«»]', '"', text)  # Comillas angulares
        
        # Comillas simples - CORRECCIÓN DEFINITIVA
        # Usar los códigos Unicode directamente
        text = text.replace(''', "'")  # U+2018
        text = text.replace(''', "'")  # U+2019
        text = text.replace('‚', "'")  # U+201A
        text = text.replace('‛', "'")  # U+201B
        
        # Corregir comillas dobles seguidas
        text = re.sub(r'"{2,}', '"', text)
        
        return text
        
    def _normalize_whitespace(self, text: str) -> str:
        """Normaliza espacios en blanco"""
        # [Mantener implementación existente]
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
        
    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Extrae la estructura del documento"""
        # [Mantener implementación existente completa]
        structure = {
            'sections': [],
            'has_toc': False,
            'has_signatures': False,
            'total_articles': 0,
            'total_clauses': 0
        }
        
        toc_patterns = [
            r'ÍNDICE|TABLA\s+DE\s+CONTENIDOS?|SUMARIO|CONTENIDO'
        ]
        for pattern in toc_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                structure['has_toc'] = True
                break
                
        for pattern in self.patterns['legal_sections']:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            structure['sections'].extend(matches)
            
        structure['total_articles'] = len(re.findall(r'ARTÍCULO\s+\d+', text, re.IGNORECASE))
        structure['total_clauses'] = len(re.findall(r'CLÁUSULA\s+\w+', text, re.IGNORECASE))
        
        signature_patterns = [
            r'FIRMA:|FIRMADO:|_+\s*\n\s*\w+',
            r'En\s+prueba\s+de\s+conformidad',
            r'Las\s+partes\s+firman'
        ]
        for pattern in signature_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                structure['has_signatures'] = True
                break
                
        return structure
        
    def _detect_language(self, text: str) -> Optional[str]:
        """Detecta el idioma del documento (mantener por compatibilidad)"""
        return self._detect_language_improved(text)
                
    def batch_preprocess(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocesa múltiples documentos en batch"""
        # [Mantener implementación existente]
        logger.info(f"Preprocesando batch de {len(documents)} documentos")
        
        processed_docs = []
        for doc in documents:
            try:
                processed = self.preprocess_document(
                    doc.get('content', ''),
                    doc.get('metadata', {})
                )
                processed_docs.append(processed)
            except Exception as e:
                logger.error(f"Error preprocesando documento: {str(e)}")
                processed_docs.append(doc)
                
        return processed_docs