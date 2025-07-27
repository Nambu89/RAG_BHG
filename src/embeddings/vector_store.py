# src/embeddings/vector_store.py

import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from pathlib import Path

# Importaciones con manejo de errores
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB no disponible. Instalar con: pip install chromadb")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS no disponible. Instalar con: pip install faiss-cpu")

try:
    from sentence_transformers import CrossEncoder
    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False
    print("⚠️ CrossEncoder no disponible. El reranking no funcionará. Instalar con: pip install sentence-transformers")

from ..config.settings import settings
from ..utils.logger import get_logger
from .openai_embeddings import OpenAIEmbeddings

logger = get_logger(__name__)

class VectorStore:
    """Sistema unificado de almacenamiento vectorial con soporte para múltiples backends"""
    
    def __init__(self, store_type: str = None):
        self.config = settings.vector_store
        self.store_type = store_type or self.config.type
        
        # Validar disponibilidad del store seleccionado
        if self.store_type == "chromadb" and not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB no disponible, cambiando a FAISS")
            self.store_type = "faiss"
            
        if self.store_type == "faiss" and not FAISS_AVAILABLE:
            raise ImportError("Ningún backend de vector store disponible. Instala chromadb o faiss-cpu")
        
        # Inicializar embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Inicializar el store específico
        if self.store_type == "chromadb":
            self._init_chromadb()
        elif self.store_type == "faiss":
            self._init_faiss()
        else:
            raise ValueError(f"Tipo de vector store no soportado: {self.store_type}")
            
        # Inicializar reranker para búsqueda híbrida
        self.reranker = None
        if CROSSENCODER_AVAILABLE and settings.search.rerank_model:
            try:
                self.reranker = CrossEncoder(settings.search.rerank_model)
                logger.info(f"Reranker cargado: {settings.search.rerank_model}")
            except Exception as e:
                logger.warning(f"No se pudo cargar el reranker: {e}")
                self.reranker = None
        else:
            logger.warning("Reranking no disponible - usando solo similitud coseno")
            
        # Estadísticas
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "index_size_mb": 0,
            "last_update": None
        }
        
    def _init_chromadb(self):
        """Inicializa ChromaDB como backend"""
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB no está instalado")
            
        logger.info("Inicializando ChromaDB...")
        
        # Crear cliente persistente con la nueva API
        self.chroma_client = chromadb.PersistentClient(
            path=self.config.persist_directory
        )
        
        # Crear o obtener colección
        try:
            self.collection = self.chroma_client.get_collection(
                name=self.config.collection_name
            )
            logger.info(f"Colección existente cargada: {self.config.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )
            logger.info(f"Nueva colección creada: {self.config.collection_name}")
            
    def _init_faiss(self):
        """Inicializa FAISS como backend"""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS no está instalado")
            
        logger.info("Inicializando FAISS...")
        
        self.dimension = self.config.embedding_dimension
        
        # Crear índice FAISS
        # Usar IndexFlatIP para similitud coseno (producto interno)
        self.faiss_index = faiss.IndexFlatIP(self.dimension)
        
        # Para FAISS necesitamos almacenar metadatos por separado
        self.faiss_metadata = []
        self.faiss_documents = []
        
        # Crear directorio si no existe
        Path(self.config.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Intentar cargar índice existente
        index_path = Path(self.config.persist_directory) / "faiss_index.bin"
        metadata_path = Path(self.config.persist_directory) / "faiss_metadata.pkl"
        
        if index_path.exists() and metadata_path.exists():
            try:
                self.faiss_index = faiss.read_index(str(index_path))
                with open(metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.faiss_metadata = data['metadata']
                    self.faiss_documents = data['documents']
                logger.info("Índice FAISS existente cargado")
            except Exception as e:
                logger.warning(f"Error cargando índice FAISS: {str(e)}")
                
    def add_chunks(self, chunks: List[Any]) -> Dict[str, Any]:
        """Agrega chunks al vector store"""
        logger.info(f"Agregando {len(chunks)} chunks al vector store...")
        
        start_time = datetime.now()
        
        # Preparar datos
        texts = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [chunk.chunk_id for chunk in chunks]
        
        # Generar embeddings
        embeddings = self.embeddings.embed_documents(texts)
        
        # Agregar según el backend
        if self.store_type == "chromadb":
            self._add_to_chromadb(texts, embeddings, metadatas, ids)
        elif self.store_type == "faiss":
            self._add_to_faiss(texts, embeddings, metadatas, ids)
            
        # Actualizar estadísticas
        self.stats["total_chunks"] += len(chunks)
        self.stats["last_update"] = datetime.now().isoformat()
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "chunks_added": len(chunks),
            "time_elapsed": elapsed_time,
            "chunks_per_second": len(chunks) / elapsed_time if elapsed_time > 0 else 0
        }
        
        logger.info(f"Chunks agregados correctamente: {result}")
        
        return result
        
    def _add_to_chromadb(self, texts: List[str], embeddings: List[List[float]], 
                        metadatas: List[Dict], ids: List[str]):
        """Agrega datos a ChromaDB"""
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
    def _add_to_faiss(self, texts: List[str], embeddings: List[List[float]], 
                     metadatas: List[Dict], ids: List[str]):
        """Agrega datos a FAISS"""
        # Convertir embeddings a numpy array
        embeddings_np = np.array(embeddings).astype('float32')
        
        # Normalizar para similitud coseno
        faiss.normalize_L2(embeddings_np)
        
        # Agregar al índice
        self.faiss_index.add(embeddings_np)
        
        # Guardar metadata
        for text, metadata, id_ in zip(texts, metadatas, ids):
            self.faiss_documents.append(text)
            self.faiss_metadata.append({
                **metadata,
                "chunk_id": id_
            })
            
    def search(self, query: str, top_k: int = None, filter_dict: Dict = None) -> List[Dict[str, Any]]:
        """Búsqueda vectorial con opciones avanzadas"""
        top_k = top_k or settings.search.top_k_final
        
        logger.info(f"Búsqueda: '{query[:50]}...', top_k={top_k}")
        
        # Generar embedding de la consulta
        query_embedding = self.embeddings.embed_query(query)
        
        # Búsqueda según el backend
        if self.store_type == "chromadb":
            results = self._search_chromadb(query, query_embedding, top_k, filter_dict)
        elif self.store_type == "faiss":
            results = self._search_faiss(query, query_embedding, top_k, filter_dict)
        else:
            results = []
            
        # Reranking si está disponible
        if self.reranker and len(results) > 0:
            results = self._rerank_results(query, results)
            
        # Filtrar por umbral de similitud
        threshold = settings.search.similarity_threshold
        results = [r for r in results if r.get("score", 0) >= threshold]
        
        # Limitar a top_k después del filtrado
        results = results[:top_k]
        
        logger.info(f"Encontrados {len(results)} resultados relevantes")
        
        return results
        
    def _search_chromadb(self, query: str, query_embedding: List[float], 
                        top_k: int, filter_dict: Dict) -> List[Dict[str, Any]]:
        """Búsqueda en ChromaDB"""
        # ChromaDB maneja automáticamente la normalización
        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k * 2, 100),  # Obtener más para el reranking
            "include": ["metadatas", "documents", "distances"]
        }
        
        if filter_dict:
            search_kwargs["where"] = filter_dict
            
        results = self.collection.query(**search_kwargs)
        
        # Formatear resultados
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": 1 - results['distances'][0][i],  # Convertir distancia a similitud
                "rank": i + 1
            })
            
        return formatted_results
        
    def _search_faiss(self, query: str, query_embedding: List[float], 
                     top_k: int, filter_dict: Dict) -> List[Dict[str, Any]]:
        """Búsqueda en FAISS"""
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            logger.warning("Índice FAISS vacío")
            return []
        
        # Normalizar query embedding
        query_vec = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vec)
        
        # Buscar - asegurar que k es válido
        k = min(max(top_k * 2, 1), self.faiss_index.ntotal)
        distances, indices = self.faiss_index.search(query_vec, k)
        
        # Formatear resultados
        formatted_results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS retorna -1 si no hay suficientes resultados
                break
                
            metadata = self.faiss_metadata[idx]
            
            # Aplicar filtros si existen
            if filter_dict:
                match = all(metadata.get(key) == value for key, value in filter_dict.items())
                if not match:
                    continue
                    
            formatted_results.append({
                "chunk_id": metadata.get("chunk_id"),
                "content": self.faiss_documents[idx],
                "metadata": metadata,
                "score": float(dist),  # FAISS con IndexFlatIP retorna similitud directamente
                "rank": i + 1
            })
            
        return formatted_results
        
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reordena los resultados usando un modelo de cross-encoder"""
        if not self.reranker or not results or not CROSSENCODER_AVAILABLE:
            return results
            
        logger.debug(f"Reranking {len(results)} resultados...")
        
        try:
            # Preparar pares query-documento
            pairs = [[query, result["content"]] for result in results]
            
            # Obtener scores del reranker
            rerank_scores = self.reranker.predict(pairs)
            
            # Combinar scores (promedio ponderado)
            for i, result in enumerate(results):
                original_score = result["score"]
                rerank_score = float(rerank_scores[i])
                
                # Promedio ponderado: 70% rerank, 30% original
                combined_score = 0.7 * rerank_score + 0.3 * original_score
                
                result["original_score"] = original_score
                result["rerank_score"] = rerank_score
                result["score"] = combined_score
                
            # Reordenar por score combinado
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Actualizar rankings
            for i, result in enumerate(results):
                result["rank"] = i + 1
                
        except Exception as e:
            logger.error(f"Error en reranking: {e}")
            # Retornar resultados originales si falla el reranking
            
        return results
        
    def hybrid_search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Búsqueda híbrida: vectorial + keyword"""
        top_k = top_k or settings.search.top_k_final
        
        logger.info(f"Búsqueda híbrida: '{query[:50]}...'")
        
        # Búsqueda vectorial
        vector_results = self.search(query, settings.search.top_k_vector)
        
        # Búsqueda por keywords (simulada con búsqueda de términos exactos)
        keyword_results = self._keyword_search(query, settings.search.top_k_keyword)
        
        # Fusión de resultados usando Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            [vector_results, keyword_results],
            k=60  # Parámetro RRF estándar
        )
        
        # Reranking final si está disponible
        if self.reranker and CROSSENCODER_AVAILABLE:
            fused_results = self._rerank_results(query, fused_results)
            
        # Limitar a top_k
        fused_results = fused_results[:top_k]
        
        logger.info(f"Búsqueda híbrida completada: {len(fused_results)} resultados")
        
        return fused_results
        
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Búsqueda básica por keywords"""
        # Tokenizar query
        query_terms = query.lower().split()
        
        results = []
        
        if self.store_type == "chromadb" and CHROMADB_AVAILABLE:
            # ChromaDB no tiene búsqueda de texto nativa, simular con todos los docs
            try:
                all_data = self.collection.get(include=["documents", "metadatas"])
                
                for i, (doc, metadata) in enumerate(zip(all_data["documents"], all_data["metadatas"])):
                    doc_lower = doc.lower()
                    
                    # Contar coincidencias de términos
                    matches = sum(1 for term in query_terms if term in doc_lower)
                    
                    if matches > 0:
                        # Score basado en TF-IDF simplificado
                        score = matches / len(query_terms)
                        
                        results.append({
                            "chunk_id": all_data["ids"][i],
                            "content": doc,
                            "metadata": metadata,
                            "score": score,
                            "match_count": matches
                        })
            except Exception as e:
                logger.error(f"Error en búsqueda keyword ChromaDB: {e}")
                    
        elif self.store_type == "faiss" and FAISS_AVAILABLE:
            # Búsqueda en documentos FAISS
            for i, (doc, metadata) in enumerate(zip(self.faiss_documents, self.faiss_metadata)):
                doc_lower = doc.lower()
                
                matches = sum(1 for term in query_terms if term in doc_lower)
                
                if matches > 0:
                    score = matches / len(query_terms)
                    
                    results.append({
                        "chunk_id": metadata.get("chunk_id"),
                        "content": doc,
                        "metadata": metadata,
                        "score": score,
                        "match_count": matches
                    })
                    
        # Ordenar por score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
        
    def _reciprocal_rank_fusion(self, result_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
        """Implementa Reciprocal Rank Fusion para combinar múltiples rankings"""
        # Diccionario para acumular scores
        fused_scores = {}
        all_results = {}
        
        # Calcular RRF score para cada documento
        for result_list in result_lists:
            for rank, result in enumerate(result_list):
                chunk_id = result["chunk_id"]
                
                # RRF score: 1 / (k + rank)
                rrf_score = 1 / (k + rank + 1)
                
                if chunk_id in fused_scores:
                    fused_scores[chunk_id] += rrf_score
                else:
                    fused_scores[chunk_id] = rrf_score
                    all_results[chunk_id] = result
                    
        # Crear lista de resultados fusionados
        fused_results = []
        for chunk_id, rrf_score in fused_scores.items():
            result = all_results[chunk_id].copy()
            result["rrf_score"] = rrf_score
            result["score"] = rrf_score  # Usar RRF score como score principal
            fused_results.append(result)
            
        # Ordenar por RRF score
        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        
        return fused_results
        
    def save_index(self):
        """Guarda el índice en disco"""
        logger.info("Guardando índice...")
        
        if self.store_type == "chromadb":
            # ChromaDB persiste automáticamente
            pass
            
        elif self.store_type == "faiss":
            # Crear directorio si no existe
            persist_dir = Path(self.config.persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar índice FAISS
            index_path = persist_dir / "faiss_index.bin"
            faiss.write_index(self.faiss_index, str(index_path))
            
            # Guardar metadata
            metadata_path = persist_dir / "faiss_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.faiss_metadata,
                    'documents': self.faiss_documents
                }, f)
                
        # Guardar estadísticas
        stats_path = Path(self.config.persist_directory) / "vector_store_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
            
        logger.info("Índice guardado correctamente")
        
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del vector store"""
        if self.store_type == "chromadb" and hasattr(self, 'collection'):
            # Obtener conteo de ChromaDB
            try:
                count = self.collection.count()
                self.stats["total_chunks"] = count
            except:
                pass
                
        elif self.store_type == "faiss" and hasattr(self, 'faiss_index'):
            self.stats["total_chunks"] = self.faiss_index.ntotal
            
        return self.stats