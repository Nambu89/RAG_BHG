from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime
import json
from difflib import SequenceMatcher

from .base_agent import BaseAgent, AgentMessage
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ValidatorAgent(BaseAgent):
    """Agente especializado en validación y control de calidad"""
    
    def __init__(self):
        super().__init__(
            name="Validator",
            description="Agente de validación y control de calidad anti-alucinaciones",
            capabilities=[
                "Validar respuestas contra documentos fuente",
                "Detectar alucinaciones e información inventada",
                "Verificar consistencia de datos",
                "Validar citas y referencias",
                "Calcular confianza de respuestas",
                "Detectar contradicciones"
            ]
        )
        
        # Umbrales de validación - AJUSTADOS PARA SER MENOS ESTRICTOS
        self.thresholds = {
            'min_similarity': 0.5,  # Reducido de 0.7
            'min_confidence': 0.5,  # Reducido de 0.6
            'max_hallucination_score': 0.5,  # Aumentado de 0.3
            'min_source_coverage': 0.3  # Reducido de 0.5
        }
        
        # Patrones de validación
        self.validation_patterns = {
            'unsupported_claims': [
                r'(?:según|de acuerdo con|como indica)\s+(?:el documento|la fuente)',
                r'(?:establece|menciona|señala)\s+que',
                r'(?:específicamente|claramente|expresamente)\s+(?:dice|indica)'
            ],
            'hedging_language': [
                r'(?:posiblemente|probablemente|quizás|tal vez)',
                r'(?:podría|debería|sería)',
                r'(?:parece que|aparentemente|supuestamente)',
                r'(?:en general|normalmente|típicamente)'
            ],
            'absolute_claims': [
                r'(?:siempre|nunca|todos|ninguno)',
                r'(?:definitivamente|absolutamente|sin duda)',
                r'(?:debe|tiene que|es obligatorio)'
            ]
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Procesa mensajes de validación"""
        logger.info(f"Validator procesando mensaje de {message.sender}")
        
        try:
            if message.message_type == "validate_response":
                result = await self._validate_response(message.content)
                
            elif message.message_type == "check_consistency":
                result = await self._check_consistency(message.content)
                
            elif message.message_type == "validate_sources":
                result = await self._validate_sources(message.content)
                
            elif message.message_type == "detect_hallucinations":
                result = await self._detect_hallucinations(message.content)
                
            else:
                result = {
                    "error": f"Tipo de mensaje no soportado: {message.message_type}"
                }
                
            return AgentMessage.create(
                sender=self.name,
                recipient=message.sender,
                message_type=f"{message.message_type}_response",
                content=result
            )
            
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            return AgentMessage.create(
                sender=self.name,
                recipient=message.sender,
                message_type="error",
                content={"error": str(e)}
            )
            
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tareas de validación"""
        task_type = task.get('type')
        
        if task_type == 'full_validation':
            return await self._full_validation(task['content'])
            
        elif task_type == 'fact_checking':
            return await self._fact_check(task['content'])
            
        elif task_type == 'cross_reference':
            return await self._cross_reference_validation(task['content'])
            
        else:
            return {"error": f"Tipo de tarea no soportada: {task_type}"}
            
    async def _full_validation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una validación completa - MÉTODO QUE FALTABA"""
        try:
            # Extraer componentes
            response = content.get('response', '')
            sources = content.get('sources', [])
            query = content.get('query', '')
            
            # Realizar validación completa usando el método existente
            validation_result = await self._validate_response(content)
            
            # Añadir análisis adicionales
            additional_checks = {
                'factual_accuracy': self._check_factual_accuracy(response, sources),
                'logical_consistency': self._check_logical_consistency(response),
                'source_attribution': self._check_source_attribution(response, sources),
                'completeness': self._check_response_completeness(response, query)
            }
            
            # Combinar resultados
            full_validation = {
                **validation_result,
                'additional_checks': additional_checks,
                'overall_score': self._calculate_overall_validation_score(validation_result, additional_checks)
            }
            
            # Generar reporte detallado
            full_validation['detailed_report'] = self._generate_detailed_validation_report(full_validation)
            
            return full_validation
            
        except Exception as e:
            logger.error(f"Error en validación completa: {str(e)}")
            return {
                'is_valid': False,
                'error': f'Error durante la validación: {str(e)}',
                'confidence': 0.0
            }
    
    def _check_factual_accuracy(self, response: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica la precisión factual de la respuesta"""
        facts_found = self._extract_facts_from_response(response)
        verified_facts = 0
        unverified_facts = []
        
        for fact in facts_found:
            if self._is_fact_in_sources(fact, sources):
                verified_facts += 1
            else:
                unverified_facts.append(fact)
        
        accuracy_score = verified_facts / len(facts_found) if facts_found else 1.0
        
        return {
            'accuracy_score': accuracy_score,
            'verified_facts': verified_facts,
            'unverified_facts': unverified_facts,
            'total_facts': len(facts_found)
        }
    
    def _extract_facts_from_response(self, response: str) -> List[str]:
        """Extrae hechos verificables de la respuesta"""
        facts = []
        
        # Patrones para identificar afirmaciones factuales
        fact_patterns = [
            r'(?:es|son|fue|fueron)\s+([^,\.]+)',
            r'(?:tiene|tienen|tuvo|tuvieron)\s+([^,\.]+)',
            r'(?:costa|cuesta)\s+([^,\.]+)',
            r'(?:mide|miden)\s+([^,\.]+)',
            r'(?:dura|duran)\s+([^,\.]+)'
        ]
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                fact = match.group(0).strip()
                if len(fact) > 15:  # Filtrar hechos muy cortos
                    facts.append(fact)
        
        return facts
    
    def _is_fact_in_sources(self, fact: str, sources: List[Dict[str, Any]]) -> bool:
        """Verifica si un hecho está en las fuentes"""
        fact_lower = fact.lower()
        
        for source in sources:
            source_content = source.get('content', '').lower()
            if self._calculate_similarity(fact_lower, source_content) > 0.8:
                return True
            
            # Verificar componentes clave del hecho
            key_components = [word for word in fact_lower.split() if len(word) > 4]
            if len(key_components) >= 2:
                matches = sum(1 for comp in key_components if comp in source_content)
                if matches >= len(key_components) * 0.7:
                    return True
        
        return False
    
    def _check_logical_consistency(self, response: str) -> Dict[str, Any]:
        """Verifica la consistencia lógica de la respuesta"""
        inconsistencies = []
        
        # Verificar contradicciones
        contradictions = self._detect_contradictions(response)
        inconsistencies.extend(contradictions)
        
        # Verificar secuencia temporal
        temporal_issues = self._check_temporal_consistency(response)
        inconsistencies.extend(temporal_issues)
        
        # Verificar coherencia numérica
        numerical_issues = self._check_numerical_consistency(response)
        inconsistencies.extend(numerical_issues)
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies,
            'consistency_score': max(0, 1 - (len(inconsistencies) * 0.2))
        }
    
    def _check_numerical_consistency(self, text: str) -> List[str]:
        """Verifica consistencia en valores numéricos"""
        issues = []
        
        # Extraer todos los números
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
        
        # Buscar sumas o totales
        sum_pattern = r'(?:total|suma|en total)\s*:?\s*(\d+(?:\.\d+)?)'
        sum_matches = re.finditer(sum_pattern, text, re.IGNORECASE)
        
        for match in sum_matches:
            stated_total = float(match.group(1))
            # Verificar si hay números antes que deberían sumar al total
            preceding_text = text[:match.start()]
            preceding_numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', preceding_text[-200:])
            
            if len(preceding_numbers) >= 2:
                calculated_sum = sum(float(n) for n in preceding_numbers[-5:])  # Últimos 5 números
                if abs(calculated_sum - stated_total) > 0.01 and calculated_sum < stated_total * 2:
                    issues.append(f"Posible inconsistencia numérica: suma declarada {stated_total} vs calculada {calculated_sum}")
        
        return issues
    
    def _check_source_attribution(self, response: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica la atribución correcta a las fuentes"""
        attribution_patterns = [
            r'según (?:el documento|la fuente)(?:\s+(\d+))?',
            r'como (?:indica|señala|menciona) (?:el documento|la fuente)(?:\s+(\d+))?',
            r'\[(\d+)\]',
            r'\((?:doc|documento)\s*(\d+)\)'
        ]
        
        attributions_found = []
        unverified_attributions = []
        
        for pattern in attribution_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                doc_ref = match.group(1) if len(match.groups()) > 0 and match.group(1) else None
                attribution = {
                    'text': match.group(0),
                    'doc_ref': doc_ref,
                    'position': match.start()
                }
                attributions_found.append(attribution)
                
                # Verificar si la atribución es correcta
                if doc_ref:
                    try:
                        doc_index = int(doc_ref) - 1
                        if doc_index < 0 or doc_index >= len(sources):
                            unverified_attributions.append(attribution)
                    except:
                        unverified_attributions.append(attribution)
        
        return {
            'total_attributions': len(attributions_found),
            'unverified_attributions': len(unverified_attributions),
            'attribution_quality': 1 - (len(unverified_attributions) / len(attributions_found)) if attributions_found else 1.0
        }
    
    def _check_response_completeness(self, response: str, query: str) -> Dict[str, Any]:
        """Verifica si la respuesta es completa respecto a la pregunta"""
        # Extraer elementos clave de la pregunta
        question_keywords = self._extract_question_keywords(query)
        
        # Verificar cuántos elementos se abordan en la respuesta
        addressed_keywords = []
        missing_keywords = []
        
        response_lower = response.lower()
        for keyword in question_keywords:
            if keyword.lower() in response_lower:
                addressed_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        completeness_score = len(addressed_keywords) / len(question_keywords) if question_keywords else 1.0
        
        return {
            'completeness_score': completeness_score,
            'addressed_elements': addressed_keywords,
            'missing_elements': missing_keywords,
            'is_complete': completeness_score >= 0.7
        }
    
    def _extract_question_keywords(self, query: str) -> List[str]:
        """Extrae palabras clave importantes de la pregunta"""
        # Eliminar palabras comunes
        stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'de', 'en', 'que', 'es', 'por', 'para', 'con', 'a'}
        
        # Extraer palabras significativas
        words = query.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Añadir entidades nombradas si se detectan
        entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', query)
        keywords.extend(entities)
        
        return list(set(keywords))
    
    def _calculate_overall_validation_score(self, base_validation: Dict[str, Any], additional_checks: Dict[str, Any]) -> float:
        """Calcula un score general de validación"""
        scores = []
        
        # Score base de validación
        if 'confidence' in base_validation:
            scores.append(base_validation['confidence'])
        
        # Scores adicionales
        if 'factual_accuracy' in additional_checks:
            scores.append(additional_checks['factual_accuracy']['accuracy_score'])
        
        if 'logical_consistency' in additional_checks:
            scores.append(additional_checks['logical_consistency']['consistency_score'])
        
        if 'source_attribution' in additional_checks:
            scores.append(additional_checks['source_attribution']['attribution_quality'])
        
        if 'completeness' in additional_checks:
            scores.append(additional_checks['completeness']['completeness_score'])
        
        # Promedio ponderado
        if scores:
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Pesos para cada score
            weighted_sum = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
            total_weight = sum(weights[:len(scores)])
            return round(weighted_sum / total_weight, 3)
        
        return 0.5
    
    def _generate_detailed_validation_report(self, validation_data: Dict[str, Any]) -> str:
        """Genera un reporte detallado de validación"""
        report_parts = []
        
        # Estado general
        if validation_data.get('is_valid'):
            report_parts.append("✓ VALIDACIÓN EXITOSA")
        else:
            report_parts.append("✗ VALIDACIÓN CON PROBLEMAS")
        
        # Score general
        overall_score = validation_data.get('overall_score', 0)
        report_parts.append(f"Score General: {overall_score:.1%}")
        
        # Problemas principales
        if validation_data.get('issues'):
            report_parts.append(f"\nProblemas Detectados ({len(validation_data['issues'])})")
            for issue in validation_data['issues'][:3]:
                report_parts.append(f"  • {issue}")
        
        # Checks adicionales
        if 'additional_checks' in validation_data:
            checks = validation_data['additional_checks']
            
            if 'factual_accuracy' in checks:
                acc = checks['factual_accuracy']
                report_parts.append(f"\nPrecisión Factual: {acc['accuracy_score']:.1%}")
                if acc['unverified_facts']:
                    report_parts.append(f"  - {len(acc['unverified_facts'])} hechos sin verificar")
            
            if 'completeness' in checks:
                comp = checks['completeness']
                report_parts.append(f"\nCompletitud: {comp['completeness_score']:.1%}")
                if comp['missing_elements']:
                    report_parts.append(f"  - Elementos faltantes: {', '.join(comp['missing_elements'][:3])}")
        
        return "\n".join(report_parts)
            
    async def _validate_response(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Valida una respuesta completa"""
        response = content.get('response', '')
        sources = content.get('sources', [])
        query = content.get('query', '')
        
        validation_results = {
            'is_valid': True,
            'confidence': 1.0,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 1. Validar cobertura de fuentes
        source_validation = self._validate_source_coverage(response, sources)
        validation_results['source_coverage'] = source_validation['coverage']
        
        if source_validation['coverage'] < self.thresholds['min_source_coverage']:
            validation_results['issues'].append(
                f"Baja cobertura de fuentes: {source_validation['coverage']:.1%}"
            )
            validation_results['is_valid'] = False
            
        # 2. Detectar alucinaciones
        hallucination_check = self._check_for_hallucinations(response, sources)
        validation_results['hallucination_score'] = hallucination_check['score']
        
        if hallucination_check['score'] > self.thresholds['max_hallucination_score']:
            validation_results['issues'].extend(hallucination_check['detected'])
            validation_results['is_valid'] = False
            
        # 3. Validar consistencia
        consistency_check = self._check_response_consistency(response, query)
        if not consistency_check['is_consistent']:
            validation_results['warnings'].extend(consistency_check['inconsistencies'])
            
        # 4. Validar citas
        citation_validation = self._validate_citations(response, sources)
        if citation_validation['invalid_citations']:
            validation_results['issues'].extend(citation_validation['invalid_citations'])
            
        # 5. Calcular confianza final
        validation_results['confidence'] = self._calculate_confidence(validation_results)
        
        # 6. Generar sugerencias
        if validation_results['issues'] or validation_results['warnings']:
            validation_results['suggestions'] = self._generate_improvement_suggestions(
                validation_results,
                response,
                sources
            )
            
        # Actualizar métricas
        self.update_metrics('tasks_completed', 1)
        if not validation_results['is_valid']:
            self.update_metrics('validations_failed', 1)
            
        return validation_results
        
    def _validate_source_coverage(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Valida qué porcentaje de la respuesta está cubierto por fuentes"""
        if not sources:
            return {'coverage': 0.0, 'uncovered_claims': [response]}
            
        response_sentences = self._split_into_sentences(response)
        covered_sentences = 0
        uncovered_claims = []
        
        for sentence in response_sentences:
            sentence_covered = False
            
            for source in sources:
                source_content = source.get('content', '')
                
                # Verificar si la información clave está en la fuente
                # Extraer números, fechas y términos clave
                key_info = re.findall(r'\b(?:\d+\s*años?|\d{1,2}.*?202\d|enero|diciembre)\b', sentence, re.IGNORECASE)
                
                if key_info:
                    # Verificar que la información clave esté en la fuente
                    key_info_found = all(info.lower() in source_content.lower() for info in key_info)
                    if key_info_found:
                        sentence_covered = True
                        break
                else:
                    # Para oraciones sin información específica, usar similitud
                    similarity = self._calculate_similarity(sentence, source_content)
                    if similarity > self.thresholds['min_similarity']:
                        sentence_covered = True
                        break
                        
            if sentence_covered:
                covered_sentences += 1
            else:
                uncovered_claims.append(sentence)
                
        coverage = covered_sentences / len(response_sentences) if response_sentences else 0
        
        return {
            'coverage': coverage,
            'covered_sentences': covered_sentences,
            'total_sentences': len(response_sentences),
            'uncovered_claims': uncovered_claims
        }
        
    def _check_for_hallucinations(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detecta posibles alucinaciones en la respuesta"""
        hallucinations = []
        
        # 1. Buscar afirmaciones no soportadas
        unsupported = self._find_unsupported_claims(response, sources)
        hallucinations.extend(unsupported)
        
        # 2. Detectar información específica no presente en fuentes
        specific_info = self._extract_specific_information(response)
        for info in specific_info:
            if not self._is_info_in_sources(info, sources):
                hallucinations.append(f"Información no verificada: {info}")
                
        # 3. Detectar lenguaje especulativo excesivo
        speculative = self._detect_speculative_language(response)
        if speculative['count'] > 2:
            hallucinations.append(
                f"Lenguaje especulativo excesivo: {speculative['count']} instancias"
            )
            
        # Calcular score de alucinación
        response_length = len(response.split())
        hallucination_score = len(hallucinations) / max(response_length / 100, 1)
        
        return {
            'score': min(hallucination_score, 1.0),
            'detected': hallucinations,
            'severity': 'high' if hallucination_score > 0.5 else 'medium' if hallucination_score > 0.2 else 'low'
        }
        
    def _find_unsupported_claims(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Encuentra afirmaciones no soportadas por las fuentes"""
        unsupported = []
        
        # Buscar patrones de afirmaciones
        for pattern in self.validation_patterns['unsupported_claims']:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            
            for match in matches:
                # Extraer la oración completa
                start = response.rfind('.', 0, match.start()) + 1
                end = response.find('.', match.end())
                if end == -1:
                    end = len(response)
                    
                claim = response[start:end].strip()
                
                # Verificar si está en fuentes
                if not self._is_claim_supported(claim, sources):
                    unsupported.append(f"Afirmación no soportada: {claim[:100]}...")
                    
        return unsupported
        
    def _extract_specific_information(self, response: str) -> List[str]:
        """Extrae información específica como números, fechas, nombres"""
        specific_info = []
        
        # Números y cantidades
        numbers = re.findall(r'\b\d+(?:\.\d+)?(?:\s*(?:%|euros?|€|\$|días?|meses?|años?))\b', response)
        specific_info.extend(numbers)
        
        # Fechas
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', response)
        specific_info.extend(dates)
        
        # Nombres propios (simplificado)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', response)
        specific_info.extend([n for n in proper_nouns if len(n) > 3])
        
        return specific_info
        
    def _is_info_in_sources(
        self,
        info: str,
        sources: List[Dict[str, Any]]
    ) -> bool:
        """Verifica si una información específica está en las fuentes"""
        for source in sources:
            if info.lower() in source.get('content', '').lower():
                return True
        return False
        
    def _is_claim_supported(
        self,
        claim: str,
        sources: List[Dict[str, Any]]
    ) -> bool:
        """Verifica si una afirmación está soportada por las fuentes"""
        claim_lower = claim.lower()
        
        # Eliminar stopwords para comparación
        important_words = [
            w for w in claim_lower.split()
            if len(w) > 3 and w not in {'para', 'sobre', 'entre', 'desde', 'hasta'}
        ]
        
        if len(important_words) < 2:
            return True  # Muy genérico para validar
            
        for source in sources:
            source_content = source.get('content', '').lower()
            matches = sum(1 for word in important_words if word in source_content)
            
            if matches >= len(important_words) * 0.6:  # 60% de coincidencia
                return True
                
        return False
        
    def _detect_speculative_language(self, response: str) -> Dict[str, Any]:
        """Detecta lenguaje especulativo o hedging"""
        instances = []
        
        for pattern in self.validation_patterns['hedging_language']:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                instances.append({
                    'text': match.group(0),
                    'position': match.start()
                })
                
        return {
            'count': len(instances),
            'instances': instances[:5]  # Primeras 5 instancias
        }
        
    def _check_response_consistency(
        self,
        response: str,
        query: str
    ) -> Dict[str, Any]:
        """Verifica la consistencia de la respuesta con la consulta"""
        inconsistencies = []
        
        # 1. Verificar que la respuesta aborde la pregunta
        query_keywords = set(query.lower().split())
        response_keywords = set(response.lower().split())
        
        keyword_overlap = len(query_keywords & response_keywords) / len(query_keywords)
        if keyword_overlap < 0.3:
            inconsistencies.append("La respuesta parece no abordar directamente la consulta")
            
        # 2. Detectar contradicciones internas
        contradictions = self._detect_contradictions(response)
        inconsistencies.extend(contradictions)
        
        # 3. Verificar coherencia temporal
        temporal_issues = self._check_temporal_consistency(response)
        inconsistencies.extend(temporal_issues)
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies
        }
        
    def _detect_contradictions(self, text: str) -> List[str]:
        """Detecta posibles contradicciones en el texto"""
        contradictions = []
        sentences = self._split_into_sentences(text)
        
        # Buscar patrones contradictorios
        contradiction_patterns = [
            (r'no\s+\w+', r'sí\s+\w+'),
            (r'nunca', r'siempre'),
            (r'ninguno', r'todos'),
            (r'prohibido', r'permitido'),
            (r'debe', r'no debe')
        ]
        
        for i, sent1 in enumerate(sentences):
            for j, sent2 in enumerate(sentences[i+1:], i+1):
                for neg_pattern, pos_pattern in contradiction_patterns:
                    if (re.search(neg_pattern, sent1, re.IGNORECASE) and 
                        re.search(pos_pattern, sent2, re.IGNORECASE)):
                        contradictions.append(
                            f"Posible contradicción entre: '{sent1[:50]}...' y '{sent2[:50]}...'"
                        )
                        
        return contradictions
        
    def _check_temporal_consistency(self, text: str) -> List[str]:
        """Verifica consistencia temporal"""
        issues = []
        
        # Extraer todas las fechas
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
        dates = []
        
        for match in re.finditer(date_pattern, text):
            try:
                day, month, year = match.groups()
                if len(year) == 2:
                    year = '20' + year
                dates.append({
                    'date': datetime(int(year), int(month), int(day)),
                    'text': match.group(0),
                    'position': match.start()
                })
            except:
                continue
                
        # Verificar orden cronológico si hay contexto
        if len(dates) > 1:
            for i in range(1, len(dates)):
                # Buscar palabras clave entre fechas
                text_between = text[dates[i-1]['position']:dates[i]['position']]
                
                if 'después' in text_between or 'posteriormente' in text_between:
                    if dates[i]['date'] < dates[i-1]['date']:
                        issues.append(
                            f"Inconsistencia temporal: {dates[i]['text']} no es posterior a {dates[i-1]['text']}"
                        )
                        
        return issues
        
    def _validate_citations(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Valida que las citas sean correctas"""
        invalid_citations = []
        valid_citations = 0
        
        # Buscar patrones de citas
        citation_patterns = [
            r'\[(\d+)\]',  # [1]
            r'\((?:doc|documento)\s*(\d+)\)',  # (doc 1)
            r'según\s+(?:el\s+)?documento\s+(\d+)',  # según documento 1
            r'<cite[^>]*>([^<]+)</cite>'  # <cite>...</cite>
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            
            for match in matches:
                citation_ref = match.group(1)
                
                # Verificar si la referencia es válida
                try:
                    ref_num = int(citation_ref) if citation_ref.isdigit() else -1
                    if ref_num < 1 or ref_num > len(sources):
                        invalid_citations.append(
                            f"Referencia inválida: {match.group(0)} (no existe documento {ref_num})"
                        )
                    else:
                        valid_citations += 1
                except:
                    invalid_citations.append(
                        f"Formato de cita inválido: {match.group(0)}"
                    )
                    
        return {
            'valid_citations': valid_citations,
            'invalid_citations': invalid_citations,
            'total_citations': valid_citations + len(invalid_citations)
        }
        
    def _calculate_confidence(self, validation_results: Dict[str, Any]) -> float:
        """Calcula la confianza final basada en los resultados de validación"""
        base_confidence = 1.0
        
        # Penalizaciones
        penalties = {
            'issues': 0.2 * len(validation_results.get('issues', [])),
            'warnings': 0.1 * len(validation_results.get('warnings', [])),
            'low_coverage': 0.3 if validation_results.get('source_coverage', 0) < 0.5 else 0,
            'hallucinations': validation_results.get('hallucination_score', 0) * 0.5
        }
        
        # Aplicar penalizaciones
        total_penalty = sum(penalties.values())
        confidence = max(0, base_confidence - total_penalty)
        
        # Ajustar por cobertura de fuentes
        source_coverage = validation_results.get('source_coverage', 0)
        confidence *= (0.5 + 0.5 * source_coverage)  # 50% base + 50% por cobertura
        
        return round(confidence, 3)
        
    def _generate_improvement_suggestions(
        self,
        validation_results: Dict[str, Any],
        response: str,
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Genera sugerencias para mejorar la respuesta"""
        suggestions = []
        
        # Basado en issues encontrados
        if validation_results.get('source_coverage', 0) < 0.7:
            suggestions.append(
                "Aumentar las referencias a los documentos fuente para mejorar la cobertura"
            )
            
        if validation_results.get('hallucination_score', 0) > 0.2:
            suggestions.append(
                "Eliminar afirmaciones no verificables y basarse más en el contenido exacto de las fuentes"
            )
            
        if 'invalid_citations' in validation_results and validation_results['invalid_citations']:
            suggestions.append(
                "Corregir las referencias a documentos para que coincidan con las fuentes disponibles"
            )
            
        # Sugerencias específicas basadas en patrones
        speculative = self._detect_speculative_language(response)
        if speculative['count'] > 3:
            suggestions.append(
                "Reducir el lenguaje especulativo y usar afirmaciones más directas basadas en las fuentes"
            )
            
        # Sugerencias de estructura
        if len(response) < 100:
            suggestions.append(
                "Expandir la respuesta con más detalles de los documentos fuente"
            )
        elif len(response) > 1000:
            suggestions.append(
                "Considerar resumir la respuesta manteniendo solo la información más relevante"
            )
            
        return suggestions[:5]  # Máximo 5 sugerencias
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones"""
        # Patrón mejorado para español
        sentence_endings = r'[.!?]+'
        sentences = re.split(sentence_endings, text)
        
        # Limpiar y filtrar
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return sentences
        
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos - VERSIÓN MEJORADA"""
        # Normalizar textos
        text1_lower = text1.lower().strip()
        text2_lower = text2.lower().strip()
        
        # Para textos cortos, verificar si uno contiene al otro
        if len(text1_lower) < 100 or len(text2_lower) < 100:
            # Extraer información clave (números, fechas)
            key_info1 = re.findall(r'\b(?:\d+\s*años?|\d{4}|enero|diciembre)\b', text1_lower)
            key_info2 = re.findall(r'\b(?:\d+\s*años?|\d{4}|enero|diciembre)\b', text2_lower)
            
            # Si la información clave coincide, considerar similar
            if key_info1 and key_info2:
                common_info = set(key_info1) & set(key_info2)
                if common_info:
                    return 0.9  # Alta similitud si la información clave coincide
        
        # Usar SequenceMatcher para similitud general
        similarity = SequenceMatcher(None, text1_lower, text2_lower).ratio()
        
        # Si uno contiene al otro, aumentar la similitud
        if text1_lower in text2_lower or text2_lower in text1_lower:
            similarity = max(similarity, 0.8)
        
        return similarity
        
    async def _detect_hallucinations(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Método específico para detectar alucinaciones"""
        response = content.get('response', '')
        sources = content.get('sources', [])
        
        hallucination_analysis = {
            'detected_hallucinations': [],
            'risk_level': 'low',
            'confidence_in_detection': 0.9,
            'recommendations': []
        }
        
        # Análisis profundo de alucinaciones
        # 1. Entidades no mencionadas
        entities = self._extract_entities(response)
        for entity in entities:
            if not self._is_entity_in_sources(entity, sources):
                hallucination_analysis['detected_hallucinations'].append({
                    'type': 'unsupported_entity',
                    'content': entity,
                    'severity': 'medium'
                })
                
        # 2. Relaciones causales no soportadas
        causal_claims = self._extract_causal_claims(response)
        for claim in causal_claims:
            if not self._is_causal_claim_supported(claim, sources):
                hallucination_analysis['detected_hallucinations'].append({
                    'type': 'unsupported_causation',
                    'content': claim,
                    'severity': 'high'
                })
                
        # 3. Cuantificaciones no verificables
        quantifications = self._extract_quantifications(response)
        for quant in quantifications:
            if not self._is_quantification_supported(quant, sources):
                hallucination_analysis['detected_hallucinations'].append({
                    'type': 'unsupported_quantification',
                    'content': quant,
                    'severity': 'medium'
                })
                
        # Determinar nivel de riesgo
        hallucination_count = len(hallucination_analysis['detected_hallucinations'])
        if hallucination_count == 0:
            hallucination_analysis['risk_level'] = 'low'
        elif hallucination_count <= 2:
            hallucination_analysis['risk_level'] = 'medium'
        else:
            hallucination_analysis['risk_level'] = 'high'
            
        # Recomendaciones
        if hallucination_count > 0:
            hallucination_analysis['recommendations'].append(
                "Revisar y eliminar las afirmaciones no soportadas por las fuentes"
            )
            if hallucination_analysis['risk_level'] == 'high':
                hallucination_analysis['recommendations'].append(
                    "Considerar reescribir la respuesta basándose más estrictamente en las fuentes"
                )
                
        return hallucination_analysis
        
    def _extract_entities(self, text: str) -> List[str]:
        """Extrae entidades nombradas del texto"""
        entities = []
        
        # Patrones para entidades
        patterns = [
            r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b',  # Nombres propios
            r'\b\d{4}\b',  # Años
            r'\b\d+(?:\.\d+)?%\b',  # Porcentajes
            r'(?:Sr\.|Sra\.|Dr\.|Dra\.)\s+[A-Z][a-zA-Z]+'  # Títulos + nombres
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            entities.extend([match.group(0) for match in matches])
            
        return list(set(entities))
        
    def _is_entity_in_sources(self, entity: str, sources: List[Dict[str, Any]]) -> bool:
        """Verifica si una entidad está mencionada en las fuentes"""
        entity_lower = entity.lower()
        
        for source in sources:
            if entity_lower in source.get('content', '').lower():
                return True
                
        # Verificar variaciones (e.g., "Juan Pérez" -> "J. Pérez")
        if ' ' in entity:
            parts = entity.split()
            if len(parts) == 2:
                abbreviated = f"{parts[0][0]}. {parts[1]}"
                for source in sources:
                    if abbreviated.lower() in source.get('content', '').lower():
                        return True
                        
        return False
        
    def _extract_causal_claims(self, text: str) -> List[str]:
        """Extrae afirmaciones causales del texto"""
        causal_patterns = [
            r'(?:debido a|por causa de|como resultado de|por)\s+([^,\.]+)',
            r'(?:causa|provoca|resulta en|lleva a)\s+([^,\.]+)',
            r'(?:por lo tanto|en consecuencia|así que)\s+([^,\.]+)'
        ]
        
        claims = []
        for pattern in causal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extraer contexto completo
                start = text.rfind('.', 0, match.start()) + 1
                end = text.find('.', match.end())
                if end == -1:
                    end = len(text)
                claims.append(text[start:end].strip())
                
        return claims
        
    def _is_causal_claim_supported(self, claim: str, sources: List[Dict[str, Any]]) -> bool:
        """Verifica si una afirmación causal está soportada"""
        # Extraer elementos clave de la relación causal
        key_elements = [word for word in claim.split() if len(word) > 4]
        
        if len(key_elements) < 2:
            return True  # Muy vago para validar
            
        # Buscar en fuentes
        for source in sources:
            source_content = source.get('content', '')
            
            # Verificar si los elementos clave están cercanos en la fuente
            all_present = all(elem.lower() in source_content.lower() for elem in key_elements)
            
            if all_present:
                # Verificar proximidad (simplificado)
                positions = [source_content.lower().find(elem.lower()) for elem in key_elements]
                max_distance = max(positions) - min(positions)
                
                if max_distance < 200:  # Dentro de ~200 caracteres
                    return True
                    
        return False
        
    def _extract_quantifications(self, text: str) -> List[str]:
        """Extrae cuantificaciones del texto"""
        patterns = [
            r'\b\d+(?:\.\d+)?(?:\s*(?:%|por ciento|euros?|€|\$|días?|meses?|años?))\b',
            r'(?:todos|ninguno|la mayoría|algunos|muchos|pocos)\s+(?:de\s+)?(?:los|las)\s+\w+',
            r'(?:más de|menos de|aproximadamente|cerca de)\s+\d+'
        ]
        
        quantifications = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            quantifications.extend([match.group(0) for match in matches])
            
        return quantifications
        
    def _is_quantification_supported(self, quant: str, sources: List[Dict[str, Any]]) -> bool:
        """Verifica si una cuantificación está soportada por las fuentes"""
        # Para números exactos, buscar coincidencia exacta
        if re.match(r'\d+(?:\.\d+)?', quant):
            for source in sources:
                if quant in source.get('content', ''):
                    return True
            return False
            
        # Para cuantificadores vagos, ser más permisivo
        vague_quantifiers = ['algunos', 'muchos', 'pocos', 'la mayoría']
        if any(q in quant.lower() for q in vague_quantifiers):
            return True  # Difícil de validar precisamente
            
        # Buscar en fuentes
        return any(quant.lower() in source.get('content', '').lower() for source in sources)
        
    async def _check_consistency(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica consistencia entre múltiples respuestas o documentos"""
        items = content.get('items', [])
        
        if len(items) < 2:
            return {
                'is_consistent': True,
                'message': 'Se requieren al menos 2 elementos para verificar consistencia'
            }
            
        consistency_report = {
            'is_consistent': True,
            'inconsistencies': [],
            'common_elements': [],
            'confidence': 1.0
        }
        
        # Comparar pares de elementos
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                comparison = self._compare_items(items[i], items[j])
                
                if comparison['inconsistencies']:
                    consistency_report['is_consistent'] = False
                    consistency_report['inconsistencies'].extend(comparison['inconsistencies'])
                    
                consistency_report['common_elements'].extend(comparison['common_elements'])
                
        # Eliminar duplicados
        consistency_report['inconsistencies'] = list(set(consistency_report['inconsistencies']))
        consistency_report['common_elements'] = list(set(consistency_report['common_elements']))
        
        # Calcular confianza
        if consistency_report['inconsistencies']:
            consistency_report['confidence'] = max(
                0.3,
                1.0 - (len(consistency_report['inconsistencies']) * 0.1)
            )
            
        return consistency_report
        
    def _compare_items(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> Dict[str, Any]:
        """Compara dos elementos para encontrar inconsistencias"""
        comparison = {
            'inconsistencies': [],
            'common_elements': []
        }
        
        # Comparar contenido textual
        text1 = item1.get('content', '')
        text2 = item2.get('content', '')
        
        # Extraer y comparar hechos clave
        facts1 = self._extract_key_facts(text1)
        facts2 = self._extract_key_facts(text2)
        
        # Encontrar contradicciones
        for fact1 in facts1:
            for fact2 in facts2:
                if self._are_facts_contradictory(fact1, fact2):
                    comparison['inconsistencies'].append(
                        f"Contradicción: '{fact1}' vs '{fact2}'"
                    )
                elif self._are_facts_similar(fact1, fact2):
                    comparison['common_elements'].append(fact1)
                    
        return comparison
        
    def _extract_key_facts(self, text: str) -> List[str]:
        """Extrae hechos clave del texto"""
        facts = []
        
        # Patrones para hechos
        fact_patterns = [
            r'(?:es|son|está|están)\s+([^,\.]+)',
            r'(?:tiene|tienen)\s+([^,\.]+)',
            r'(?:debe|deben)\s+([^,\.]+)',
            r'(?:el|la|los|las)\s+(\w+)\s+(?:es|son)\s+([^,\.]+)'
        ]
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                fact = match.group(0).strip()
                if len(fact) > 15:  # Filtrar hechos muy cortos
                    facts.append(fact)
                    
        return facts[:20]  # Limitar a 20 hechos
        
    def _are_facts_contradictory(self, fact1: str, fact2: str) -> bool:
        """Determina si dos hechos son contradictorios"""
        # Simplificado: buscar negaciones opuestas
        if ('no' in fact1 and 'no' not in fact2) or ('no' in fact2 and 'no' not in fact1):
            # Verificar si hablan del mismo tema
            common_words = set(fact1.lower().split()) & set(fact2.lower().split())
            if len(common_words) > 3:
                return True
                
        # Buscar antónimos comunes
        antonyms = [
            ('permitido', 'prohibido'),
            ('obligatorio', 'opcional'),
            ('siempre', 'nunca'),
            ('todos', 'ninguno')
        ]
        
        for word1, word2 in antonyms:
            if (word1 in fact1.lower() and word2 in fact2.lower()) or \
               (word2 in fact1.lower() and word1 in fact2.lower()):
                return True
                
        return False
        
    def _are_facts_similar(self, fact1: str, fact2: str) -> bool:
        """Determina si dos hechos son similares"""
        return self._calculate_similarity(fact1, fact2) > 0.8
        
    async def _validate_sources(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Valida las fuentes proporcionadas"""
        sources = content.get('sources', [])
        
        validation = {
            'total_sources': len(sources),
            'valid_sources': 0,
            'invalid_sources': [],
            'duplicate_sources': [],
            'source_quality': {}
        }
        
        seen_content = {}
        
        for i, source in enumerate(sources):
            # Verificar estructura básica
            if not isinstance(source, dict) or 'content' not in source:
                validation['invalid_sources'].append(f"Fuente {i+1}: estructura inválida")
                continue
                
            content_hash = hash(source.get('content', ''))
            
            # Verificar duplicados
            if content_hash in seen_content:
                validation['duplicate_sources'].append(
                    f"Fuente {i+1} duplica fuente {seen_content[content_hash]}"
                )
            else:
                seen_content[content_hash] = i + 1
                validation['valid_sources'] += 1
                
            # Evaluar calidad de la fuente
            quality = self._evaluate_source_quality(source)
            validation['source_quality'][f'source_{i+1}'] = quality
            
        return validation
        
    def _evaluate_source_quality(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la calidad de una fuente"""
        content = source.get('content', '')
        
        quality = {
            'length': len(content),
            'has_metadata': bool(source.get('metadata')),
            'relevance_indicators': 0,
            'quality_score': 0
        }
        
        # Indicadores de relevancia para contratos
        relevance_keywords = [
            'contrato', 'acuerdo', 'cláusula', 'obligación', 'derecho',
            'parte', 'firma', 'vigencia', 'plazo', 'pago'
        ]
        
        content_lower = content.lower()
        quality['relevance_indicators'] = sum(
            1 for kw in relevance_keywords if kw in content_lower
        )
        
        # Calcular score de calidad
        scores = []
        if quality['length'] > 100:
            scores.append(1.0)
        elif quality['length'] > 50:
            scores.append(0.5)
        else:
            scores.append(0.2)
            
        if quality['has_metadata']:
            scores.append(1.0)
            
        if quality['relevance_indicators'] > 3:
            scores.append(1.0)
        elif quality['relevance_indicators'] > 1:
            scores.append(0.5)
            
        quality['quality_score'] = sum(scores) / len(scores) if scores else 0
        
        return quality
        
    async def _fact_check(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza verificación de hechos"""
        claims = content.get('claims', [])
        sources = content.get('sources', [])
        
        fact_check_results = {
            'total_claims': len(claims),
            'verified_claims': [],
            'unverified_claims': [],
            'partially_verified_claims': []
        }
        
        for claim in claims:
            verification = self._verify_single_claim(claim, sources)
            
            if verification['status'] == 'verified':
                fact_check_results['verified_claims'].append(verification)
            elif verification['status'] == 'partial':
                fact_check_results['partially_verified_claims'].append(verification)
            else:
                fact_check_results['unverified_claims'].append(verification)
                
        return fact_check_results
        
    def _verify_single_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica una afirmación individual"""
        verification = {
            'claim': claim,
            'status': 'unverified',
            'supporting_sources': [],
            'confidence': 0.0
        }
        
        for i, source in enumerate(sources):
            if self._is_claim_supported(claim, [source]):
                verification['supporting_sources'].append(i + 1)
                
        if len(verification['supporting_sources']) >= 2:
            verification['status'] = 'verified'
            verification['confidence'] = 1.0
        elif len(verification['supporting_sources']) == 1:
            verification['status'] = 'partial'
            verification['confidence'] = 0.7
        else:
            verification['confidence'] = 0.0
            
        return verification
        
    async def _cross_reference_validation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Validación cruzada entre múltiples fuentes"""
        sources = content.get('sources', [])
        claims = content.get('claims', [])
        
        cross_reference_results = {
            'consistency_matrix': {},
            'conflicting_information': [],
            'corroborated_information': [],
            'unique_information': []
        }
        
        # Construir matriz de consistencia entre fuentes
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                consistency = self._check_source_consistency(sources[i], sources[j])
                cross_reference_results['consistency_matrix'][f"{i+1}_vs_{j+1}"] = consistency
                
        # Verificar información conflictiva
        for claim in claims:
            support_count = 0
            conflict_count = 0
            
            for source in sources:
                if self._is_claim_supported(claim, [source]):
                    support_count += 1
                elif self._is_claim_contradicted(claim, source):
                    conflict_count += 1
                    
            if conflict_count > 0:
                cross_reference_results['conflicting_information'].append({
                    'claim': claim,
                    'support_count': support_count,
                    'conflict_count': conflict_count
                })
            elif support_count > 1:
                cross_reference_results['corroborated_information'].append({
                    'claim': claim,
                    'support_count': support_count
                })
            elif support_count == 1:
                cross_reference_results['unique_information'].append({
                    'claim': claim,
                    'source': 'single source'
                })
                
        return cross_reference_results
        
    def _check_source_consistency(self, source1: Dict[str, Any], source2: Dict[str, Any]) -> float:
        """Verifica consistencia entre dos fuentes"""
        content1 = source1.get('content', '')
        content2 = source2.get('content', '')
        
        # Extraer hechos clave de cada fuente
        facts1 = self._extract_key_facts(content1)
        facts2 = self._extract_key_facts(content2)
        
        # Contar hechos contradictorios
        contradictions = 0
        for f1 in facts1:
            for f2 in facts2:
                if self._are_facts_contradictory(f1, f2):
                    contradictions += 1
                    
        # Calcular score de consistencia
        total_facts = len(facts1) + len(facts2)
        if total_facts == 0:
            return 1.0
            
        consistency_score = 1.0 - (contradictions * 2 / total_facts)
        return max(0, consistency_score)
        
    def _is_claim_contradicted(self, claim: str, source: Dict[str, Any]) -> bool:
        """Verifica si una afirmación es contradicha por una fuente"""
        source_content = source.get('content', '')
        
        # Buscar negaciones de la afirmación
        if 'no' in claim.lower():
            positive_claim = claim.replace('no ', '').replace('No ', '')
            if positive_claim.lower() in source_content.lower():
                return True
        else:
            negative_claim = 'no ' + claim.lower()
            if negative_claim in source_content.lower():
                return True
                
        return False
        
    def validate_input(self, input_data: Any) -> bool:
        """Valida la entrada del validador"""
        if isinstance(input_data, dict):
            return 'response' in input_data or 'items' in input_data
        return False
        
    def format_output(self, output_data: Any) -> Any:
        """Formatea la salida de validación"""
        if isinstance(output_data, dict) and 'is_valid' in output_data:
            # Formato user-friendly
            formatted = {
                'estado': 'VÁLIDO' if output_data['is_valid'] else 'REQUIERE REVISIÓN',
                'confianza': f"{output_data.get('confidence', 0) * 100:.1f}%",
                'problemas_detectados': len(output_data.get('issues', [])),
                'advertencias': len(output_data.get('warnings', [])),
                'resumen': self._generate_validation_summary(output_data)
            }
            
            if output_data.get('suggestions'):
                formatted['recomendaciones'] = output_data['suggestions']
                
            return formatted
            
        return output_data
        
    def _generate_validation_summary(self, validation_data: Dict[str, Any]) -> str:
        """Genera un resumen de la validación"""
        if validation_data.get('is_valid'):
            return "La respuesta ha sido validada correctamente y está correctamente soportada por las fuentes."
        else:
            issues = len(validation_data.get('issues', []))
            warnings = len(validation_data.get('warnings', []))
            return f"Se detectaron {issues} problemas y {warnings} advertencias. Se recomienda revisar la respuesta."