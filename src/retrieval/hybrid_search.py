import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re
from collections import Counter
import math

from ..utils.logger import get_logger
from ..config.settings import settings
from ..embeddings.openai_embeddings import OpenAIEmbeddings

logger = get_logger(__name__)

@dataclass
class SearchResult:
    """Resultado de búsqueda unificado"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    rank: int
    source: str  # 'vector', 'keyword', 'hybrid'
    match_details: Dict[str, Any] = None

class HybridSearchEngine:
    """Motor de búsqueda híbrida avanzado"""
    
    def __init__(self, vector_store, embeddings_model=None):
        self.vector_store = vector_store
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.config = settings.search  # Agregar configuración
        
        # Parámetros BM25
        self.bm25_k1 = 1.2
        self.bm25_b = 0.75
        self.avg_doc_length = 100.0  # Valor por defecto para evitar división por cero
        self.total_docs = 0
        self.idf_cache = {}  # Cache para IDF
        
        # Cache para búsquedas recientes
        self.search_cache = {}
        self.cache_size = 100
        
        logger.info("Motor de búsqueda híbrida inicializado")
        
    def search(
        self,
        query: str,
        top_k: int = None,
        search_type: str = "hybrid",
        filters: Dict[str, Any] = None,
        boost_keywords: List[str] = None
    ) -> List[SearchResult]:
        """
        Realiza búsqueda según el tipo especificado
        
        Args:
            query: Consulta del usuario
            top_k: Número de resultados a retornar
            search_type: 'vector', 'keyword', o 'hybrid'
            filters: Filtros adicionales
            boost_keywords: Palabras clave para dar más peso
        """
        top_k = top_k or self.config.top_k_final
        
        logger.info(f"Búsqueda {search_type}: '{query[:50]}...'")
        
        if search_type == "vector":
            return self._vector_search(query, top_k, filters)
        elif search_type == "keyword":
            return self._keyword_search(query, top_k, filters, boost_keywords)
        elif search_type == "hybrid":
            return self._hybrid_search(query, top_k, filters, boost_keywords)
        else:
            raise ValueError(f"Tipo de búsqueda no válido: {search_type}")
            
    def _vector_search(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """Búsqueda puramente vectorial"""
        if not self.vector_store:
            logger.error("Vector store no configurado")
            return []
            
        # Obtener resultados del vector store
        raw_results = self.vector_store.search(query, top_k * 2, filters)
        
        # Convertir a SearchResult
        results = []
        for i, result in enumerate(raw_results[:top_k]):
            search_result = SearchResult(
                chunk_id=result['chunk_id'],
                content=result['content'],
                metadata=result.get('metadata', {}),
                score=result['score'],
                rank=i + 1,
                source='vector',
                match_details={'vector_score': result['score']}
            )
            results.append(search_result)
            
        return results
        
    def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None,
        boost_keywords: List[str] = None
    ) -> List[SearchResult]:
        """Búsqueda por palabras clave usando BM25"""
        if not self.vector_store:
            return []
            
        # Obtener todos los documentos (esto es ineficiente para grandes colecciones)
        # En producción, usar un índice invertido real
        all_docs = self._get_all_documents(filters)
        
        if not all_docs:
            return []
            
        # Actualizar estadísticas de documentos
        self._update_doc_stats(all_docs)
            
        # Tokenizar query
        query_tokens = self._tokenize(query.lower())
        if boost_keywords:
            query_tokens.extend([kw.lower() for kw in boost_keywords])
            
        # Calcular scores BM25
        scores = []
        for doc in all_docs:
            score = self._calculate_bm25_score(query_tokens, doc)
            if score > 0:
                scores.append((doc, score))
                
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Convertir a SearchResult
        results = []
        for i, (doc, score) in enumerate(scores[:top_k]):
            search_result = SearchResult(
                chunk_id=doc['chunk_id'],
                content=doc['content'],
                metadata=doc.get('metadata', {}),
                score=score,
                rank=i + 1,
                source='keyword',
                match_details={
                    'bm25_score': score,
                    'matched_terms': self._get_matched_terms(query_tokens, doc['content'])
                }
            )
            results.append(search_result)
            
        return results
        
    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None,
        boost_keywords: List[str] = None
    ) -> List[SearchResult]:
        """Búsqueda híbrida con fusión de resultados"""
        
        # Obtener resultados de ambos métodos
        vector_results = self._vector_search(
            query,
            self.config.top_k_vector,
            filters
        )
        
        keyword_results = self._keyword_search(
            query,
            self.config.top_k_keyword,
            filters,
            boost_keywords
        )
        
        # Fusionar resultados
        fused_results = self._fuse_results(
            [vector_results, keyword_results],
            weights=[0.6, 0.4]  # Dar más peso a búsqueda vectorial
        )
        
        # Aplicar reranking si está disponible
        if hasattr(self.vector_store, 'reranker') and self.vector_store.reranker:
            fused_results = self._rerank_results(query, fused_results)
            
        return fused_results[:top_k]
        
    def _fuse_results(
        self,
        result_lists: List[List[SearchResult]],
        weights: List[float] = None,
        fusion_method: str = "rrf"
    ) -> List[SearchResult]:
        """
        Fusiona múltiples listas de resultados
        
        Args:
            result_lists: Lista de listas de resultados
            weights: Pesos para cada lista (solo para weighted fusion)
            fusion_method: 'rrf' o 'weighted'
        """
        if fusion_method == "rrf":
            return self._reciprocal_rank_fusion(result_lists)
        elif fusion_method == "weighted":
            return self._weighted_fusion(result_lists, weights)
        else:
            raise ValueError(f"Método de fusión no válido: {fusion_method}")
            
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[SearchResult]],
        k: int = 60
    ) -> List[SearchResult]:
        """Implementa Reciprocal Rank Fusion"""
        fused_scores = {}
        all_results = {}
        
        for result_list in result_lists:
            for result in result_list:
                chunk_id = result.chunk_id
                
                # RRF score
                rrf_score = 1 / (k + result.rank)
                
                if chunk_id in fused_scores:
                    fused_scores[chunk_id] += rrf_score
                else:
                    fused_scores[chunk_id] = rrf_score
                    all_results[chunk_id] = result
                    
        # Crear lista fusionada
        fused_results = []
        for chunk_id, rrf_score in sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            result = all_results[chunk_id]
            result.score = rrf_score
            result.source = 'hybrid'
            result.rank = len(fused_results) + 1
            fused_results.append(result)
            
        return fused_results
        
    def _weighted_fusion(
        self,
        result_lists: List[List[SearchResult]],
        weights: List[float] = None
    ) -> List[SearchResult]:
        """Fusión ponderada de resultados"""
        if not weights:
            weights = [1.0 / len(result_lists)] * len(result_lists)
            
        # Normalizar scores en cada lista
        normalized_lists = []
        for result_list in result_lists:
            if not result_list:
                normalized_lists.append([])
                continue
                
            max_score = max(r.score for r in result_list)
            min_score = min(r.score for r in result_list)
            range_score = max_score - min_score
            
            if range_score > 0:
                normalized = [
                    SearchResult(
                        chunk_id=r.chunk_id,
                        content=r.content,
                        metadata=r.metadata,
                        score=(r.score - min_score) / range_score,
                        rank=r.rank,
                        source=r.source,
                        match_details=r.match_details
                    )
                    for r in result_list
                ]
            else:
                normalized = result_list
                
            normalized_lists.append(normalized)
            
        # Combinar con pesos
        combined_scores = {}
        all_results = {}
        
        for i, (result_list, weight) in enumerate(zip(normalized_lists, weights)):
            for result in result_list:
                chunk_id = result.chunk_id
                weighted_score = result.score * weight
                
                if chunk_id in combined_scores:
                    combined_scores[chunk_id] += weighted_score
                else:
                    combined_scores[chunk_id] = weighted_score
                    all_results[chunk_id] = result
                    
        # Crear lista final
        fused_results = []
        for chunk_id, score in sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            result = all_results[chunk_id]
            result.score = score
            result.source = 'hybrid'
            result.rank = len(fused_results) + 1
            fused_results.append(result)
            
        return fused_results
        
    def _calculate_bm25_score(
        self,
        query_tokens: List[str],
        document: Dict[str, Any]
    ) -> float:
        """Calcula score BM25 para un documento"""
        doc_content = document['content'].lower()
        doc_tokens = self._tokenize(doc_content)
        
        # Longitud del documento
        doc_length = len(doc_tokens)
        
        # Evitar división por cero
        if self.avg_doc_length == 0:
            self.avg_doc_length = max(doc_length, 100.0)
        
        # Frecuencias de términos
        term_freqs = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in term_freqs:
                continue
            
            # Frecuencia del término
            tf = term_freqs[term]
            
            # IDF (simplificado - en producción usar índice invertido)
            idf = self._get_idf(term)
            
            # BM25 formula
            numerator = idf * tf * (self.bm25_k1 + 1)
            denominator = tf + self.bm25_k1 * (
                1 - self.bm25_b + self.bm25_b * (doc_length / self.avg_doc_length)
            )
            
            if denominator > 0:
                score += numerator / denominator
        
        return score
        
    def _get_idf(self, term: str) -> float:
        """Calcula IDF para un término (simplificado)"""
        if term in self.idf_cache:
            return self.idf_cache[term]
            
        # En producción, esto vendría de un índice invertido
        # Aquí usamos un valor por defecto
        if self.total_docs > 0:
            idf = math.log((self.total_docs + 1) / 2)  # Asumimos que aparece en la mitad
        else:
            idf = 2.0  # Valor por defecto
            
        self.idf_cache[term] = idf
        
        return idf
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto para búsqueda"""
        # Eliminar puntuación y dividir
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        
        # Eliminar stopwords básicas
        stopwords = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'por', 'con',
            'para', 'es', 'se', 'del', 'al', 'los', 'las', 'una', 'su'
        }
        
        return [t for t in tokens if t and t not in stopwords]
        
    def _get_matched_terms(
        self,
        query_tokens: List[str],
        content: str
    ) -> List[str]:
        """Obtiene términos que coinciden en el contenido"""
        content_lower = content.lower()
        matched = []
        
        for term in query_tokens:
            if term in content_lower:
                matched.append(term)
                
        return matched
        
    def _update_doc_stats(self, docs: List[Dict[str, Any]]):
        """Actualiza estadísticas de documentos para BM25"""
        self.total_docs = len(docs)
        
        if self.total_docs > 0:
            total_length = sum(len(self._tokenize(d['content'])) for d in docs)
            self.avg_doc_length = total_length / self.total_docs
        else:
            self.avg_doc_length = 100.0  # Valor por defecto
        
    def _get_all_documents(
        self,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los documentos del vector store"""
        # Esta es una implementación simplificada
        # En producción, usar un índice invertido real
        
        if not self.vector_store:
            return []
            
        # Para ChromaDB
        if hasattr(self.vector_store, 'collection'):
            try:
                results = self.vector_store.collection.get(
                    where=filters,
                    include=['documents', 'metadatas']
                )
                
                docs = []
                for i, (doc, meta) in enumerate(
                    zip(results.get('documents', []), results.get('metadatas', []))
                ):
                    docs.append({
                        'chunk_id': results['ids'][i] if 'ids' in results else str(i),
                        'content': doc,
                        'metadata': meta or {}
                    })
                    
                return docs
                
            except Exception as e:
                logger.error(f"Error obteniendo documentos: {str(e)}")
                return []
                
        # Para FAISS
        elif hasattr(self.vector_store, 'faiss_documents'):
            docs = []
            for i, (doc, meta) in enumerate(
                zip(
                    self.vector_store.faiss_documents,
                    self.vector_store.faiss_metadata
                )
            ):
                if filters:
                    # Aplicar filtros
                    match = all(
                        meta.get(k) == v for k, v in filters.items()
                    )
                    if not match:
                        continue
                        
                docs.append({
                    'chunk_id': meta.get('chunk_id', str(i)),
                    'content': doc,
                    'metadata': meta
                })
                
            return docs
            
        return []
        
    def _rerank_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Reordena resultados usando el reranker del vector store"""
        if not results:
            return results
            
        # Convertir a formato esperado por el reranker
        docs_for_rerank = [
            {
                'chunk_id': r.chunk_id,
                'content': r.content,
                'metadata': r.metadata,
                'score': r.score
            }
            for r in results
        ]
        
        # Rerank
        reranked = self.vector_store._rerank_results(query, docs_for_rerank)
        
        # Convertir de vuelta a SearchResult
        reranked_results = []
        for i, doc in enumerate(reranked):
            result = SearchResult(
                chunk_id=doc['chunk_id'],
                content=doc['content'],
                metadata=doc['metadata'],
                score=doc['score'],
                rank=i + 1,
                source='hybrid-reranked',
                match_details={
                    'original_score': doc.get('original_score'),
                    'rerank_score': doc.get('rerank_score')
                }
            )
            reranked_results.append(result)
            
        return reranked_results