import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import torch
from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger(__name__)

@dataclass
class RerankResult:
    """Resultado de reranking"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    original_score: float
    rerank_score: float
    combined_score: float
    original_rank: int
    new_rank: int

class AdvancedReranker:
    """Sistema avanzado de reranking con múltiples estrategias"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.search.rerank_model
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Cargar modelo
        self._load_model()
        
        # Configuración
        self.batch_size = 32
        self.max_length = 512
        self.combine_method = 'weighted'  # 'weighted', 'multiply', 'rrf'
        self.weight_original = 0.3
        self.weight_rerank = 0.7
        
        # Cache para optimización
        self.cache = {}
        self.max_cache_size = 1000
        
    def _load_model(self):
        """Carga el modelo de reranking"""
        try:
            self.model = CrossEncoder(self.model_name, device=self.device)
            logger.info(f"Modelo de reranking cargado: {self.model_name}")
        except Exception as e:
            logger.error(f"Error cargando modelo de reranking: {str(e)}")
            logger.warning("Usando reranker por defecto")
            
            # Fallback a un modelo más ligero
            try:
                self.model = CrossEncoder(
                    'cross-encoder/ms-marco-MiniLM-L-6-v2',
                    device=self.device
                )
            except:
                self.model = None
                logger.error("No se pudo cargar ningún modelo de reranking")
                
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = None,
        return_all: bool = False,
        use_cache: bool = True
    ) -> List[RerankResult]:
        """
        Reordena documentos según relevancia
        
        Args:
            query: Consulta del usuario
            documents: Lista de documentos con 'content' y 'score'
            top_k: Número de documentos a retornar
            return_all: Si retornar todos los documentos reordenados
            use_cache: Si usar cache para optimización
        """
        if not self.model or not documents:
            return self._fallback_rerank(query, documents, top_k)
            
        logger.info(f"Reranking {len(documents)} documentos")
        
        # Preparar pares query-documento
        pairs = []
        cached_scores = {}
        uncached_indices = []
        
        for i, doc in enumerate(documents):
            if use_cache:
                cache_key = self._get_cache_key(query, doc['content'])
                if cache_key in self.cache:
                    cached_scores[i] = self.cache[cache_key]
                    continue
                    
            pairs.append([query, doc['content'][:self.max_length * 2]])
            uncached_indices.append(i)
            
        # Calcular scores para documentos no cacheados
        if pairs:
            try:
                # Procesar en batches
                all_scores = []
                for i in range(0, len(pairs), self.batch_size):
                    batch = pairs[i:i + self.batch_size]
                    batch_scores = self.model.predict(batch)
                    all_scores.extend(batch_scores)
                    
                # Asignar scores a índices originales
                for idx, score in zip(uncached_indices, all_scores):
                    doc = documents[idx]
                    if use_cache:
                        cache_key = self._get_cache_key(query, doc['content'])
                        self._update_cache(cache_key, float(score))
                        
            except Exception as e:
                logger.error(f"Error en reranking: {str(e)}")
                return self._fallback_rerank(query, documents, top_k)
                
        # Crear resultados de reranking
        rerank_results = []
        for i, doc in enumerate(documents):
            if i in cached_scores:
                rerank_score = cached_scores[i]
            else:
                idx_in_scores = uncached_indices.index(i)
                rerank_score = float(all_scores[idx_in_scores])
                
            # Combinar scores
            original_score = doc.get('score', 0.0)
            combined_score = self._combine_scores(original_score, rerank_score)
            
            result = RerankResult(
                chunk_id=doc.get('chunk_id', str(i)),
                content=doc['content'],
                metadata=doc.get('metadata', {}),
                original_score=original_score,
                rerank_score=rerank_score,
                combined_score=combined_score,
                original_rank=i + 1,
                new_rank=0  # Se asignará después
            )
            rerank_results.append(result)
            
        # Ordenar por score combinado
        rerank_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Asignar nuevos rankings
        for i, result in enumerate(rerank_results):
            result.new_rank = i + 1
            
        # Aplicar top_k si es necesario
        if top_k and not return_all:
            rerank_results = rerank_results[:top_k]
            
        logger.info(f"Reranking completado. Top resultado: score={rerank_results[0].combined_score:.3f}")
        
        return rerank_results
        
    async def async_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[RerankResult]:
        """Versión asíncrona del reranking para mejor rendimiento"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            result = await loop.run_in_executor(
                executor,
                self.rerank,
                query,
                documents,
                top_k
            )
            
        return result
        
    def batch_rerank(
        self,
        queries: List[str],
        document_lists: List[List[Dict[str, Any]]],
        top_k: int = None
    ) -> List[List[RerankResult]]:
        """Rerank múltiples queries en batch"""
        results = []
        
        for query, docs in zip(queries, document_lists):
            reranked = self.rerank(query, docs, top_k)
            results.append(reranked)
            
        return results
        
    def _combine_scores(
        self,
        original_score: float,
        rerank_score: float
    ) -> float:
        """Combina score original y de reranking"""
        if self.combine_method == 'weighted':
            return (
                self.weight_original * original_score +
                self.weight_rerank * rerank_score
            )
        elif self.combine_method == 'multiply':
            return original_score * rerank_score
        elif self.combine_method == 'rrf':
            # Reciprocal Rank Fusion simplificado
            k = 60
            return 1 / (k + 1/original_score) + 1 / (k + 1/rerank_score)
        else:
            return rerank_score
            
    def _fallback_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[RerankResult]:
        """Reranking de respaldo cuando no hay modelo"""
        logger.warning("Usando reranking de respaldo (sin modelo)")
        
        query_terms = set(query.lower().split())
        
        results = []
        for i, doc in enumerate(documents):
            # Score simple basado en coincidencia de términos
            content_lower = doc['content'].lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            
            # Boost para coincidencias exactas de frases
            if query.lower() in content_lower:
                matches *= 2
                
            rerank_score = matches / len(query_terms) if query_terms else 0
            
            result = RerankResult(
                chunk_id=doc.get('chunk_id', str(i)),
                content=doc['content'],
                metadata=doc.get('metadata', {}),
                original_score=doc.get('score', 0.0),
                rerank_score=rerank_score,
                combined_score=self._combine_scores(
                    doc.get('score', 0.0),
                    rerank_score
                ),
                original_rank=i + 1,
                new_rank=0
            )
            results.append(result)
            
        # Ordenar y asignar rankings
        results.sort(key=lambda x: x.combined_score, reverse=True)
        for i, result in enumerate(results):
            result.new_rank = i + 1
            
        if top_k:
            results = results[:top_k]
            
        return results
        
    def _get_cache_key(self, query: str, content: str) -> str:
        """Genera clave de cache"""
        # Usar solo los primeros 100 caracteres para la clave
        content_preview = content[:100]
        return f"{hash(query)}_{hash(content_preview)}"
        
    def _update_cache(self, key: str, score: float):
        """Actualiza cache con límite de tamaño"""
        if len(self.cache) >= self.max_cache_size:
            # Eliminar 20% más antiguo (FIFO)
            keys_to_remove = list(self.cache.keys())[:int(self.max_cache_size * 0.2)]
            for k in keys_to_remove:
                del self.cache[k]
                
        self.cache[key] = score
        
    def get_feature_scores(
        self,
        query: str,
        document: str
    ) -> Dict[str, float]:
        """
        Calcula scores de características adicionales
        Útil para análisis y debugging
        """
        features = {}
        
        # Longitud normalizada
        features['length_ratio'] = len(document) / 1000  # Normalizar a ~1 para 1000 chars
        
        # Densidad de términos de query
        query_terms = set(query.lower().split())
        doc_terms = set(document.lower().split())
        features['term_overlap'] = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
        
        # Posición de primera coincidencia
        first_match = float('inf')
        for term in query_terms:
            pos = document.lower().find(term)
            if pos != -1 and pos < first_match:
                first_match = pos
        features['first_match_position'] = 1 / (first_match + 1) if first_match != float('inf') else 0
        
        # Coincidencia de frase exacta
        features['exact_match'] = 1.0 if query.lower() in document.lower() else 0.0
        
        return features
        
    def explain_reranking(
        self,
        query: str,
        document: Dict[str, Any],
        rerank_result: RerankResult
    ) -> Dict[str, Any]:
        """Explica por qué un documento fue reordenado"""
        explanation = {
            'query': query,
            'chunk_id': rerank_result.chunk_id,
            'original_rank': rerank_result.original_rank,
            'new_rank': rerank_result.new_rank,
            'rank_change': rerank_result.original_rank - rerank_result.new_rank,
            'scores': {
                'original': rerank_result.original_score,
                'rerank': rerank_result.rerank_score,
                'combined': rerank_result.combined_score
            },
            'features': self.get_feature_scores(query, document['content']),
            'combine_method': self.combine_method,
            'weights': {
                'original': self.weight_original,
                'rerank': self.weight_rerank
            }
        }
        
        # Análisis de mejora/empeoramiento
        if explanation['rank_change'] > 0:
            explanation['assessment'] = f"Mejoró {explanation['rank_change']} posiciones"
        elif explanation['rank_change'] < 0:
            explanation['assessment'] = f"Empeoró {-explanation['rank_change']} posiciones"
        else:
            explanation['assessment'] = "Mantuvo su posición"
            
        return explanation
        
    def optimize_weights(
        self,
        validation_data: List[Tuple[str, List[Dict[str, Any]], List[int]]]
    ) -> Dict[str, float]:
        """
        Optimiza los pesos de combinación usando datos de validación
        
        Args:
            validation_data: Lista de (query, documents, relevant_indices)
        """
        best_weights = {
            'original': self.weight_original,
            'rerank': self.weight_rerank
        }
        best_score = 0
        
        # Grid search simple
        for w_original in np.arange(0, 1.1, 0.1):
            w_rerank = 1 - w_original
            
            self.weight_original = w_original
            self.weight_rerank = w_rerank
            
            total_score = 0
            for query, docs, relevant_indices in validation_data:
                reranked = self.rerank(query, docs)
                
                # Calcular precisión@k
                top_k_ids = [r.chunk_id for r in reranked[:len(relevant_indices)]]
                relevant_found = sum(
                    1 for i in relevant_indices
                    if docs[i].get('chunk_id') in top_k_ids
                )
                precision = relevant_found / len(relevant_indices)
                total_score += precision
                
            avg_score = total_score / len(validation_data)
            
            if avg_score > best_score:
                best_score = avg_score
                best_weights = {
                    'original': w_original,
                    'rerank': w_rerank
                }
                
        # Restaurar mejores pesos
        self.weight_original = best_weights['original']
        self.weight_rerank = best_weights['rerank']
        
        logger.info(f"Pesos optimizados: {best_weights}, Score: {best_score:.3f}")
        
        return best_weights