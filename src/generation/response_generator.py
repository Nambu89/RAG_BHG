import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from openai import OpenAI

from ..config.settings import settings
from ..utils.logger import get_logger
from .prompts import PromptManager

logger = get_logger(__name__)

class ResponseGenerator:
    """Generador de respuestas usando LLM con validación y control de calidad"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai.api_key)
        self.model = settings.openai.chat_model
        self.prompt_manager = PromptManager()
        
        # Estadísticas
        self.stats = {
            "total_queries": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "avg_confidence": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
        
    def generate_response(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Genera una respuesta basada en los resultados de búsqueda"""
        
        logger.info(f"Generando respuesta para: {query[:50]}...")
        
        start_time = datetime.now()
        
        # Preparar contexto
        context = self._prepare_context(search_results)
        metadata = self._prepare_metadata(search_results)
        
        # Verificar si hay suficiente contexto
        if not context or len(search_results) == 0:
            return self._generate_no_context_response(query)
            
        # Generar respuesta principal
        try:
            # Construir mensajes
            messages = self._build_messages(query, context, metadata, conversation_history)
            
            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
                response_format={"type": "json_object"}  # Forzar respuesta JSON
            )
            
            # Procesar respuesta
            result = self._process_response(response, query, search_results)
            
            # Validar respuesta si está habilitado
            if settings.rag.enable_validation:
                result = self._validate_response(result, context)
                
            # Actualizar estadísticas
            self._update_stats(response, result, success=True)
            
            # Agregar metadatos
            result["metadata"]["response_time"] = (datetime.now() - start_time).total_seconds()
            result["metadata"]["model"] = self.model
            result["metadata"]["search_results_count"] = len(search_results)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            self.stats["failed_responses"] += 1
            
            return self._generate_error_response(query, str(e))
            
    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepara el contexto de los documentos encontrados"""
        context_parts = []
        
        for i, result in enumerate(search_results):
            # Formatear cada resultado
            context_part = f"""
[Documento {i+1}]
Fuente: {result.get('metadata', {}).get('filename', 'Desconocido')}
Sección: {result.get('metadata', {}).get('section', 'N/A')}
Relevancia: {result.get('score', 0):.2f}

Contenido:
{result.get('content', '')}
---"""
            context_parts.append(context_part)
            
        return "\n".join(context_parts)
        
    def _prepare_metadata(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepara metadata de los documentos para referencia"""
        metadata_list = []
        
        for i, result in enumerate(search_results):
            meta = {
                "doc_index": i + 1,
                "filename": result.get('metadata', {}).get('filename'),
                "contract_type": result.get('metadata', {}).get('contract_type'),
                "dates": result.get('metadata', {}).get('dates_found', []),
                "chunk_id": result.get('chunk_id'),
                "score": round(result.get('score', 0), 3)
            }
            metadata_list.append(meta)
            
        return json.dumps(metadata_list, indent=2, ensure_ascii=False)
        
    def _build_messages(
        self,
        query: str,
        context: str,
        metadata: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Construye los mensajes para el LLM"""
        
        # System prompt mejorado con JSON
        system_prompt = f"""Eres un asistente experto en análisis de contratos legales.
    Tu tarea es responder preguntas basándote ÚNICAMENTE en el contexto proporcionado.

    IMPORTANTE: Debes responder SIEMPRE en formato JSON con la siguiente estructura:
    {{
        "answer": "tu respuesta detallada aquí",
        "confidence": 0.95,
        "sources": [
            {{
                "doc_index": 1,
                "excerpt": "texto relevante del documento"
            }}
        ],
        "key_points": ["punto clave 1", "punto clave 2"],
        "warnings": []
    }}

    Contexto disponible:
    {context}

    Metadata de documentos:
    {metadata}

    Reglas:
    1. SIEMPRE responde en formato JSON válido
    2. La respuesta debe estar basada ÚNICAMENTE en el contexto proporcionado
    3. Si no encuentras información relevante, tu answer debe ser "No se encontró información relevante en los documentos disponibles"
    4. confidence debe ser un número entre 0 y 1 que refleje qué tan seguro estás de tu respuesta
    5. sources debe incluir los índices de los documentos que usaste
    6. key_points debe resumir los puntos principales de tu respuesta
    7. warnings debe incluir cualquier advertencia o limitación de tu respuesta
    
    IMPORTANTE para preguntas sobre tipos de contratos:
    - Revisa TODOS los documentos en el contexto
    - Lista TODOS los tipos diferentes que encuentres
    - Los tipos comunes incluyen: arrendamiento, gestión hotelera, franquicia, servicios, mantenimiento, compraventa
    - Si un documento menciona un tipo específico de contrato, inclúyelo en tu respuesta
    """

        messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar historial si existe - CORREGIDO
        if conversation_history:
            for msg in conversation_history[-6:]:  # Últimos 6 mensajes
                # Asegurarse de que el contenido sea string
                content = msg.get('content', '')
                
                # Si el contenido es un diccionario (error anterior), convertir a string
                if isinstance(content, dict):
                    # Intentar extraer el texto de la respuesta
                    if 'answer' in content:
                        content = content['answer']
                    elif 'error' in content:
                        content = f"Error: {content['error']}"
                    else:
                        content = str(content)
                
                # Asegurarse de que sea string
                content = str(content)
                
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": content
                })
        
        # User prompt
        user_prompt = f"Pregunta: {query}\n\nRecuerda responder en formato JSON."
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
        
    def _process_response(
        self,
        response: Any,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Procesa la respuesta del LLM"""
        
        try:
            # Parsear JSON
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Estructura esperada
            result = {
                "query": query,
                "answer": parsed.get("answer", "No se pudo generar una respuesta"),
                "confidence": float(parsed.get("confidence", 0.5)),
                "sources": [],
                "warnings": parsed.get("warnings", []),
                "key_points": parsed.get("key_points", []),
                "metadata": {
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
            
            # Procesar fuentes
            for source in parsed.get("sources", []):
                # Vincular con los resultados de búsqueda
                doc_index = source.get("doc_index", 0) - 1
                if 0 <= doc_index < len(search_results):
                    source_info = {
                        "document": search_results[doc_index].get('metadata', {}).get('filename'),
                        "section": search_results[doc_index].get('metadata', {}).get('section'),
                        "excerpt": source.get("excerpt", ""),
                        "relevance": search_results[doc_index].get('score', 0),
                        "chunk_id": search_results[doc_index].get('chunk_id')
                    }
                    result["sources"].append(source_info)
                    
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON: {str(e)}")
            logger.debug(f"Respuesta recibida: {response.choices[0].message.content}")
            
            # Intentar extraer respuesta como texto plano
            content = response.choices[0].message.content
            
            return {
                "query": query,
                "answer": content,
                "confidence": 0.5,
                "sources": [],
                "key_points": [],
                "warnings": ["La respuesta no se pudo parsear como JSON estructurado"],
                "metadata": {
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
            
    def _validate_response(self, result: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Valida la respuesta generada"""
        
        logger.debug("Validando respuesta...")
        
        # Validación 1: Verificar que la respuesta esté basada en el contexto
        answer_lower = result["answer"].lower()
        context_lower = context.lower()
        
        # Buscar coincidencias significativas
        key_terms = self._extract_key_terms(result["answer"])
        context_coverage = sum(1 for term in key_terms if term in context_lower) / len(key_terms) if key_terms else 0
        
        if context_coverage < 0.3:
            result["warnings"].append("La respuesta podría no estar suficientemente basada en los documentos")
            result["confidence"] *= 0.8
            
        # Validación 2: Verificar confianza mínima
        if result["confidence"] < settings.rag.confidence_threshold:
            result["warnings"].append(f"Confianza baja ({result['confidence']:.2f})")
            
        # Validación 3: Verificar fuentes
        if not result["sources"]:
            result["warnings"].append("No se encontraron fuentes específicas para esta respuesta")
            result["confidence"] *= 0.9
            
        return result
        
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extrae términos clave del texto"""
        import re
        
        # Eliminar palabras comunes
        stopwords = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'por', 'con', 'para', 'es', 'se', 'del', 'al'}
        
        # Extraer palabras significativas
        words = re.findall(r'\b[a-záéíóúñ]+\b', text.lower())
        key_terms = [w for w in words if len(w) > 4 and w not in stopwords]
        
        return key_terms[:10]  # Top 10 términos
        
    def _generate_no_context_response(self, query: str) -> Dict[str, Any]:
        """Genera respuesta cuando no hay contexto disponible"""
        
        return {
            "query": query,
            "answer": "No se encontró información relevante en los documentos disponibles para responder a esta pregunta. Por favor, verifica que la consulta esté relacionada con los contratos del Barceló Hotel Group o reformula tu pregunta con más detalles específicos.",
            "confidence": 0.0,
            "sources": [],
            "key_points": [],
            "warnings": ["No se encontraron documentos relevantes"],
            "metadata": {
                "response_type": "no_context",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    def _generate_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Genera respuesta de error"""
        
        return {
            "query": query,
            "answer": "Se produjo un error al procesar tu consulta. Por favor, intenta nuevamente o contacta al soporte técnico si el problema persiste.",
            "confidence": 0.0,
            "sources": [],
            "key_points": [],
            "warnings": [f"Error del sistema: {error}"],
            "metadata": {
                "response_type": "error",
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    def _update_stats(self, response: Any, result: Dict[str, Any], success: bool):
        """Actualiza estadísticas de uso"""
        
        self.stats["total_queries"] += 1
        
        if success:
            self.stats["successful_responses"] += 1
            
            # Actualizar confianza promedio
            current_avg = self.stats["avg_confidence"]
            n = self.stats["successful_responses"]
            new_confidence = result["confidence"]
            self.stats["avg_confidence"] = ((current_avg * (n - 1)) + new_confidence) / n
            
        else:
            self.stats["failed_responses"] += 1
            
        # Actualizar uso de tokens
        if hasattr(response, 'usage'):
            self.stats["total_tokens"] += response.usage.total_tokens
            
            # Estimar costo (GPT-4 Turbo: $0.01/1K input, $0.03/1K output)
            input_cost = (response.usage.prompt_tokens / 1000) * 0.01
            output_cost = (response.usage.completion_tokens / 1000) * 0.03
            self.stats["total_cost"] += input_cost + output_cost
            
    def generate_summary(self, results: List[Dict[str, Any]], max_results: int = 3) -> str:
        """Genera un resumen de los principales hallazgos"""
        
        prompt = f"""Resume los principales hallazgos de estos documentos contractuales:

{self._prepare_context(results[:max_results])}

Proporciona un resumen ejecutivo de máximo 200 palabras destacando:
1. Tipos de contratos encontrados
2. Partes involucradas
3. Fechas o plazos importantes
4. Cláusulas o términos destacados"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un analista legal experto en resúmenes ejecutivos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generando resumen: {str(e)}")
            return "No se pudo generar el resumen."
            
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del generador"""
        return self.stats