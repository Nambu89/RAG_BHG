from typing import Dict, Any, Optional
from datetime import datetime

from ..config.settings import settings

class PromptManager:
    """Gestor centralizado de prompts del sistema"""
    
    def __init__(self):
        self.templates = {
            "system": {
                "default": settings.rag.system_prompt_template,
                "strict": self._get_strict_system_prompt(),
                "creative": self._get_creative_system_prompt(),
                "technical": self._get_technical_system_prompt()
            },
            "user": {
                "default": settings.rag.user_prompt_template,
                "detailed": self._get_detailed_user_prompt(),
                "summary": self._get_summary_user_prompt()
            }
        }
        
    def get_system_prompt(self, context: str, metadata: str, mode: str = "default") -> str:
        """Obtiene el prompt del sistema formateado"""
        template = self.templates["system"].get(mode, self.templates["system"]["default"])
        
        return template.format(
            context=context,
            metadata=metadata,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            hotel_group="Barceló Hotel Group"
        )
        
    def get_user_prompt(self, question: str, mode: str = "default") -> str:
        """Obtiene el prompt del usuario formateado"""
        template = self.templates["user"].get(mode, self.templates["user"]["default"])
        
        return template.format(question=question)
        
    def _get_strict_system_prompt(self) -> str:
        """Prompt estricto para máxima precisión"""
        return """Eres un analista legal de {hotel_group} especializado en contratos.

INSTRUCCIONES CRÍTICAS - DEBES SEGUIRLAS EXACTAMENTE:

1. SOLO usa información de los fragmentos proporcionados
2. NO inventes, supongas o inferencias información no presente
3. Si la información no está disponible, di: "Esta información no se encuentra en los documentos proporcionados"
4. SIEMPRE cita el documento y sección específica
5. Usa lenguaje legal preciso y formal

ESTRUCTURA DE RESPUESTA OBLIGATORIA (JSON):
{{
    "answer": "Tu respuesta basada ÚNICAMENTE en los documentos",
    "confidence": 0.0-1.0 (qué tan seguro estás de la respuesta),
    "sources": [
        {{
            "doc_index": número del documento citado,
            "excerpt": "fragmento exacto del texto citado",
            "section": "sección o cláusula"
        }}
    ],
    "warnings": ["lista de advertencias o limitaciones"]
}}

Contexto de documentos:
{context}

Metadatos:
{metadata}

Fecha actual: {current_date}"""

    def _get_creative_system_prompt(self) -> str:
        """Prompt más flexible para respuestas elaboradas"""
        return """Eres un consultor experto en contratos hoteleros de {hotel_group}.

Tu objetivo es proporcionar respuestas útiles y completas basándote en los documentos disponibles.
Puedes:
- Elaborar y explicar conceptos
- Proporcionar contexto adicional cuando sea relevante
- Hacer conexiones entre diferentes partes de los documentos
- Sugerir interpretaciones cuando haya ambigüedad

PERO SIEMPRE:
- Basa tus respuestas en los documentos proporcionados
- Distingue claramente entre hechos del documento e interpretaciones
- Cita las fuentes

Formato JSON requerido:
{{
    "answer": "respuesta elaborada",
    "confidence": 0.0-1.0,
    "sources": [...],
    "warnings": [...]
}}

Contexto:
{context}

Metadata:
{metadata}"""

    def _get_technical_system_prompt(self) -> str:
        """Prompt para consultas técnicas específicas"""
        return """Eres un experto técnico-legal en contratos de {hotel_group}.

Especialidades:
- Cláusulas financieras y económicas
- Términos operativos hoteleros
- Normativa y cumplimiento
- Plazos y condiciones temporales

Para cada respuesta:
1. Identifica el tipo de consulta técnica
2. Extrae los datos específicos relevantes
3. Proporciona cálculos o interpretaciones técnicas si aplica
4. Mantén precisión absoluta en cifras y fechas

Responde en formato JSON:
{{
    "answer": "respuesta técnica detallada",
    "confidence": 0.0-1.0,
    "sources": [...],
    "warnings": [...],
    "technical_data": {{
        "numbers": [],
        "dates": [],
        "calculations": []
    }}
}}

Documentos:
{context}

Metadata:
{metadata}"""

    def _get_detailed_user_prompt(self) -> str:
        """Prompt de usuario para respuestas detalladas"""
        return """Pregunta: {question}

Por favor proporciona una respuesta DETALLADA que incluya:
1. Respuesta directa a la pregunta
2. Contexto relevante de los contratos
3. Implicaciones o consideraciones importantes
4. Referencias específicas a cláusulas o artículos

Asegúrate de citar todas las fuentes."""

    def _get_summary_user_prompt(self) -> str:
        """Prompt de usuario para respuestas resumidas"""
        return """Pregunta: {question}

Proporciona una respuesta CONCISA y DIRECTA basada en los documentos.
Máximo 2-3 párrafos. Solo los puntos esenciales."""

    def get_validation_prompt(self, answer: str, context: str) -> str:
        """Prompt para validar una respuesta"""
        return f"""Valida si esta respuesta está correctamente basada en el contexto proporcionado:

RESPUESTA A VALIDAR:
{answer}

CONTEXTO ORIGINAL:
{context}

Evalúa:
1. ¿La respuesta se basa fielmente en el contexto?
2. ¿Hay afirmaciones no soportadas por el contexto?
3. ¿Las citas son correctas?

Responde con:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["lista de problemas encontrados"],
    "suggestions": ["mejoras sugeridas"]
}}"""

    def get_query_expansion_prompt(self, query: str) -> str:
        """Prompt para expandir queries"""
        return f"""Expande esta consulta sobre contratos hoteleros para mejorar la búsqueda:

Consulta original: {query}

Genera 3 variaciones que:
1. Use sinónimos legales y términos relacionados
2. Sea más específica o detallada
3. Capture diferentes aspectos de la misma pregunta

Formato:
{{
    "expanded_queries": [
        "variación 1",
        "variación 2", 
        "variación 3"
    ],
    "key_terms": ["términos clave identificados"]
}}"""

    def get_entity_extraction_prompt(self, text: str) -> str:
        """Prompt para extraer entidades de contratos"""
        return f"""Extrae las siguientes entidades del texto contractual:

TEXTO:
{text}

Identifica:
- Partes del contrato (nombres de empresas/personas)
- Fechas y plazos
- Montos y cifras económicas
- Ubicaciones/propiedades
- Tipos de contrato
- Cláusulas importantes

Formato JSON:
{{
    "parties": ["lista de partes"],
    "dates": ["fechas encontradas"],
    "amounts": ["montos con moneda"],
    "locations": ["ubicaciones"],
    "contract_type": "tipo de contrato",
    "key_clauses": ["cláusulas relevantes"]
}}"""

    def get_classification_prompt(self, text: str) -> str:
        """Prompt para clasificar documentos"""
        return f"""Clasifica este fragmento de documento contractual:

TEXTO:
{text[:500]}...

Determina:
1. Tipo de contrato (arrendamiento/gestión/préstamo/servicios/otro)
2. Sector (hotelero/inmobiliario/financiero/otro)
3. Criticidad (alta/media/baja)
4. Estado (vigente/vencido/borrador/indefinido)

Responde en JSON:
{{
    "contract_type": "tipo",
    "sector": "sector",
    "criticality": "nivel",
    "status": "estado",
    "confidence": 0.0-1.0
}}"""