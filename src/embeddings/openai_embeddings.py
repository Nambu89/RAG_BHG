import time
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIEmbeddings:
    """Generador de embeddings usando OpenAI con optimizaciones"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai.api_key)
        self.model = settings.openai.embedding_model
        
        # Configuración según el modelo
        self.model_config = {
            "text-embedding-3-large": {
                "dimension": 3072,
                "max_tokens": 8191,
                "price_per_1k_tokens": 0.00013
            },
            "text-embedding-3-small": {
                "dimension": 1536,
                "max_tokens": 8191,
                "price_per_1k_tokens": 0.00002
            },
            "text-embedding-ada-002": {
                "dimension": 1536,
                "max_tokens": 8191,
                "price_per_1k_tokens": 0.00010
            }
        }
        
        # Obtener configuración del modelo
        self.config = self.model_config.get(self.model, self.model_config["text-embedding-3-large"])
        
        # Tokenizer para contar tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Estadísticas de uso
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "errors": 0
        }
        
        # Cache simple para embeddings
        self.cache = {}
        self.max_cache_size = 1000
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _get_embedding(self, text: str, **kwargs) -> List[float]:
        """Llama a la API de OpenAI para obtener un embedding"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                **kwargs
            )
            
            # Actualizar estadísticas
            self.stats["total_requests"] += 1
            self.stats["total_tokens"] += response.usage.total_tokens
            self.stats["total_cost"] += (response.usage.total_tokens / 1000) * self.config["price_per_1k_tokens"]
            
            return response.data[0].embedding
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error obteniendo embedding: {str(e)}")
            raise
            
    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta"""
        logger.debug(f"Generando embedding para query: {text[:50]}...")
        
        # Verificar cache
        cache_key = f"query_{hash(text)}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]
            
        # Truncar si es necesario
        text = self._truncate_text(text)
        
        # Obtener embedding
        embedding = self._get_embedding(text)
        
        # Guardar en cache
        self._update_cache(cache_key, embedding)
        
        return embedding
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples documentos con batching"""
        logger.info(f"Generando embeddings para {len(texts)} documentos...")
        
        embeddings = []
        batch_size = 100  # OpenAI permite hasta 2048, pero usamos menos por seguridad
        
        # Procesar en batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Verificar cache para cada texto
            batch_to_embed = []
            batch_indices = []
            cached_embeddings = {}
            
            for j, text in enumerate(batch):
                cache_key = f"doc_{hash(text)}"
                if cache_key in self.cache:
                    cached_embeddings[i + j] = self.cache[cache_key]
                    self.stats["cache_hits"] += 1
                else:
                    batch_to_embed.append(self._truncate_text(text))
                    batch_indices.append(i + j)
                    
            # Obtener embeddings para textos no cacheados
            if batch_to_embed:
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch_to_embed
                    )
                    
                    # Actualizar estadísticas
                    self.stats["total_requests"] += 1
                    self.stats["total_tokens"] += response.usage.total_tokens
                    self.stats["total_cost"] += (response.usage.total_tokens / 1000) * self.config["price_per_1k_tokens"]
                    
                    # Procesar respuesta
                    for idx, embedding_data in enumerate(response.data):
                        original_idx = batch_indices[idx]
                        embedding = embedding_data.embedding
                        
                        # Guardar en cache
                        cache_key = f"doc_{hash(texts[original_idx])}"
                        self._update_cache(cache_key, embedding)
                        
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Error en batch {i//batch_size}: {str(e)}")
                    
                    # Procesar individualmente en caso de error
                    for idx, text in zip(batch_indices, batch_to_embed):
                        try:
                            embedding = self._get_embedding(text)
                            cache_key = f"doc_{hash(texts[idx])}"
                            self._update_cache(cache_key, embedding)
                        except:
                            # Usar embedding vacío como fallback
                            embedding = [0.0] * self.config["dimension"]
                            
            # Construir lista final de embeddings
            batch_embeddings = []
            for j in range(len(batch)):
                idx = i + j
                if idx in cached_embeddings:
                    batch_embeddings.append(cached_embeddings[idx])
                else:
                    # Buscar en cache (ya debería estar)
                    cache_key = f"doc_{hash(texts[idx])}"
                    batch_embeddings.append(self.cache.get(cache_key, [0.0] * self.config["dimension"]))
                    
            embeddings.extend(batch_embeddings)
            
            # Pequeña pausa entre batches para evitar rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)
                
        logger.info(f"Embeddings generados. Costo estimado: ${self.stats['total_cost']:.4f}")
        
        return embeddings
        
    def _truncate_text(self, text: str) -> str:
        """Trunca el texto al límite de tokens del modelo"""
        tokens = self.encoding.encode(text)
        
        if len(tokens) > self.config["max_tokens"]:
            logger.warning(f"Texto truncado de {len(tokens)} a {self.config['max_tokens']} tokens")
            tokens = tokens[:self.config["max_tokens"]]
            text = self.encoding.decode(tokens)
            
        return text
        
    def _update_cache(self, key: str, embedding: List[float]):
        """Actualiza el cache con límite de tamaño"""
        if len(self.cache) >= self.max_cache_size:
            # Eliminar el 20% más antiguo (FIFO simplificado)
            keys_to_remove = list(self.cache.keys())[:int(self.max_cache_size * 0.2)]
            for k in keys_to_remove:
                del self.cache[k]
                
        self.cache[key] = embedding
        
    def get_dimension(self) -> int:
        """Retorna la dimensión de los embeddings"""
        return self.config["dimension"]
        
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "model": self.model,
            "dimension": self.config["dimension"]
        }
        
    def estimate_cost(self, num_texts: int, avg_tokens_per_text: int = 500) -> float:
        """Estima el costo de generar embeddings"""
        total_tokens = num_texts * avg_tokens_per_text
        cost = (total_tokens / 1000) * self.config["price_per_1k_tokens"]
        return cost
        
    def create_hyde_embedding(self, query: str, num_hypothetical: int = 3) -> List[float]:
        """
        Implementa HyDE (Hypothetical Document Embeddings)
        Genera documentos hipotéticos que podrían responder la query
        """
        logger.info("Generando HyDE embeddings...")
        
        # Generar documentos hipotéticos usando GPT
        hypothetical_docs = self._generate_hypothetical_documents(query, num_hypothetical)
        
        # Generar embeddings para cada documento
        embeddings = self.embed_documents(hypothetical_docs)
        
        # Promediar los embeddings
        avg_embedding = np.mean(embeddings, axis=0).tolist()
        
        return avg_embedding
        
    def _generate_hypothetical_documents(self, query: str, num_docs: int) -> List[str]:
        """Genera documentos hipotéticos que podrían responder la query"""
        try:
            prompt = f"""Genera {num_docs} fragmentos diferentes de contratos legales que podrían contener la respuesta a esta pregunta:

Pregunta: {query}

Genera fragmentos realistas de contratos del Barceló Hotel Group que incluyan cláusulas, artículos o secciones relevantes.
Cada fragmento debe ser diferente y abordar la pregunta desde distintos ángulos.

Formato de respuesta:
FRAGMENTO 1:
[contenido del fragmento]

FRAGMENTO 2:
[contenido del fragmento]

etc."""

            response = self.client.chat.completions.create(
                model=settings.openai.chat_model,
                messages=[
                    {"role": "system", "content": "Eres un experto en redacción de contratos legales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parsear respuesta
            content = response.choices[0].message.content
            fragments = []
            
            # Extraer fragmentos
            parts = content.split("FRAGMENTO")
            for part in parts[1:]:  # Saltar el primero que está vacío
                fragment = part.split(":", 1)[1].strip() if ":" in part else part.strip()
                if fragment:
                    fragments.append(fragment)
                    
            return fragments[:num_docs]
            
        except Exception as e:
            logger.error(f"Error generando documentos hipotéticos: {str(e)}")
            # Fallback: usar la query original
            return [query]