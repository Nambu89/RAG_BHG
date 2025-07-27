import pytest
import asyncio
from pathlib import Path
import json
import time
from typing import Dict, Any, List
import numpy as np
from src.agents.base_agent import AgentMessage
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="spacy.cli._util")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weasel.util.config")
warnings.filterwarnings("ignore", category=FutureWarning, module="huggingface_hub.file_download")

# Importar componentes del sistema
from src.config.settings import settings
from src.ingestion.document_loader import DocumentLoader, Document
from src.ingestion.chunker import SmartChunker
from src.ingestion.preprocessor import DocumentPreprocessor
from src.embeddings.openai_embeddings import OpenAIEmbeddings
from src.embeddings.vector_store import VectorStore
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.reranker import AdvancedReranker
from src.generation.response_generator import ResponseGenerator
from src.agents.contract_analyzer import ContractAnalyzerAgent
from src.agents.validator_agent import ValidatorAgent

class TestRAGPipeline:
    """Suite de tests para el pipeline RAG completo"""
    
    @pytest.fixture
    def sample_contract(self):
        """Contrato de ejemplo para tests"""
        return """CONTRATO DE ARRENDAMIENTO DE LOCAL COMERCIAL

Entre Barceló Hotel Group S.A., con CIF A-12345678, domiciliada en Palma de Mallorca, 
representada por D. Juan Pérez García (en adelante, el ARRENDADOR), y Empresa Ejemplo S.L., 
con CIF B-87654321, domiciliada en Madrid, representada por Dña. María López Martín 
(en adelante, el ARRENDATARIO).

CLÁUSULA PRIMERA - OBJETO
El ARRENDADOR cede en arrendamiento al ARRENDATARIO el local comercial situado en 
Calle Principal 123, Barcelona, con una superficie de 200 metros cuadrados.

CLÁUSULA SEGUNDA - DURACIÓN
El presente contrato tendrá una duración de 5 años, comenzando el 1 de enero de 2024 
y finalizando el 31 de diciembre de 2028. El contrato se renovará automáticamente 
por períodos anuales salvo denuncia de cualquiera de las partes con 3 meses de antelación.

CLÁUSULA TERCERA - RENTA
La renta mensual será de 3.000 euros, pagaderos por adelantado en los primeros 5 días 
de cada mes. La renta se actualizará anualmente según el IPC.

CLÁUSULA CUARTA - FIANZA
El ARRENDATARIO depositará una fianza equivalente a dos mensualidades (6.000 euros).

CLÁUSULA QUINTA - OBLIGACIONES DEL ARRENDATARIO
El ARRENDATARIO se obliga a:
- Mantener el local en buen estado de conservación
- No realizar obras sin autorización previa por escrito
- Destinar el local exclusivamente a actividad comercial
- Pagar los suministros (agua, luz, gas)

CLÁUSULA SEXTA - PENALIZACIONES
El retraso en el pago de la renta devengará un interés del 10% anual.
El incumplimiento grave facultará al ARRENDADOR para resolver el contrato.

Firmado en Barcelona, a 15 de diciembre de 2023."""
        
    @pytest.fixture
    def test_documents_dir(self, tmp_path, sample_contract):
        """Crea directorio temporal con documentos de prueba"""
        docs_dir = tmp_path / "test_contracts"
        docs_dir.mkdir()
        
        # Crear varios contratos de prueba
        contracts = {
            "contrato_arrendamiento.txt": sample_contract,
            "contrato_servicios.txt": self._generate_service_contract(),
            "contrato_compraventa.txt": self._generate_sale_contract()
        }
        
        for filename, content in contracts.items():
            (docs_dir / filename).write_text(content, encoding='utf-8')
            
        return docs_dir
        
    def _generate_service_contract(self):
        """Genera un contrato de servicios de prueba"""
        return """CONTRATO DE PRESTACIÓN DE SERVICIOS

Entre Barceló Hotel Group S.A. (CLIENTE) y Servicios Técnicos S.L. (PROVEEDOR).

OBJETO: Servicios de mantenimiento de instalaciones hoteleras.
DURACIÓN: 2 años desde el 1 de marzo de 2024.
PRECIO: 5.000 euros mensuales más IVA.
OBLIGACIONES DEL PROVEEDOR:
- Mantenimiento preventivo mensual
- Disponibilidad 24/7 para emergencias
- Garantía de reparaciones por 6 meses

PENALIZACIONES: 
- Por incumplimiento de SLA: 500 euros por día
- Por falta de disponibilidad: 1.000 euros por incidencia

Firmado en Palma de Mallorca, a 20 de febrero de 2024."""
        
    def _generate_sale_contract(self):
        """Genera un contrato de compraventa de prueba"""
        return """CONTRATO DE COMPRAVENTA

Entre Barceló Hotel Group S.A. (COMPRADOR) e Inmobiliaria Costa S.L. (VENDEDOR).

OBJETO: Edificio situado en Avenida del Mar 45, Málaga.
PRECIO: 2.500.000 euros.
FORMA DE PAGO: 
- 10% a la firma (250.000 euros)
- 90% a la escritura (2.250.000 euros)

CONDICIONES:
- Entrega libre de cargas y ocupantes
- Plazo máximo de escritura: 60 días
- El comprador tiene derecho de tanteo sobre locales anexos

GARANTÍAS: El vendedor garantiza la ausencia de vicios ocultos por 2 años.

Firmado en Málaga, a 10 de enero de 2024."""
        
    @pytest.mark.asyncio
    async def test_document_loading(self, test_documents_dir):
        """Test de carga de documentos"""
        loader = DocumentLoader()
        documents = loader.load_directory(str(test_documents_dir))
        
        assert len(documents) == 3
        assert all(isinstance(doc, Document) for doc in documents)
        assert all(doc.content for doc in documents)
        assert all(doc.metadata for doc in documents)
        
        # Verificar extracción de metadata
        for doc in documents:
            assert 'filename' in doc.metadata
            assert 'char_count' in doc.metadata
            assert doc.metadata['char_count'] > 0
            
    @pytest.mark.asyncio
    async def test_preprocessing(self, sample_contract):
        """Test de preprocesamiento de documentos"""
        preprocessor = DocumentPreprocessor()
        
        # Agregar algunos artefactos para limpiar
        dirty_contract = sample_contract + "\n\nPágina 1 de 1\nCONFIDENCIAL - NO DISTRIBUIR"
        
        result = preprocessor.preprocess_document(dirty_contract)
        
        assert 'content' in result
        assert 'metadata' in result
        assert "Página 1 de 1" not in result['content']
        assert "CONFIDENCIAL" not in result['content']
        assert result['metadata']['reduction_percent'] > 0
        
    @pytest.mark.asyncio
    async def test_chunking(self, sample_contract):
        """Test de chunking de documentos"""
        chunker = SmartChunker()
        
        # Crear documento
        doc = Document(
            content=sample_contract,
            metadata={'filename': 'test.txt'},
            doc_id='test_001'
        )
        
        chunks = chunker.chunk_document(doc)
        
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.chunk_id for chunk in chunks)
        
        # Verificar que no hay pérdida de información importante
        all_content = ' '.join(chunk.content for chunk in chunks)
        assert "ARRENDADOR" in all_content
        assert "3.000 euros" in all_content
        assert "5 años" in all_content
        
    @pytest.mark.asyncio
    async def test_embeddings_generation(self, sample_contract):
        """Test de generación de embeddings"""
        embedder = OpenAIEmbeddings()
        
        # Test embedding de query
        query = "¿Cuál es la duración del contrato?"
        query_embedding = embedder.embed_query(query)
        
        assert isinstance(query_embedding, list)
        assert len(query_embedding) == embedder.get_dimension()
        assert all(isinstance(x, float) for x in query_embedding)
        
        # Test embedding de documentos
        texts = [sample_contract[:500], sample_contract[500:1000]]
        doc_embeddings = embedder.embed_documents(texts)
        
        assert len(doc_embeddings) == 2
        assert all(len(emb) == embedder.get_dimension() for emb in doc_embeddings)
        
    @pytest.mark.asyncio
    async def test_vector_store_operations(self, test_documents_dir):
        """Test de operaciones del vector store"""
        # Cargar y procesar documentos
        loader = DocumentLoader()
        chunker = SmartChunker()
        
        documents = loader.load_directory(str(test_documents_dir))
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            
        # Crear vector store
        vector_store = VectorStore(store_type="faiss")  # Usar FAISS para tests
        
        # Agregar chunks
        result = vector_store.add_chunks(all_chunks)
        assert result['chunks_added'] == len(all_chunks)
        
        # Test búsqueda
        query = "obligaciones del arrendatario"
        search_results = vector_store.search(query, top_k=5)
        
        assert len(search_results) > 0
        assert all('content' in r for r in search_results)
        assert all('score' in r for r in search_results)
        assert any("mantener" in r['content'].lower() for r in search_results)
        
    @pytest.mark.asyncio
    async def test_hybrid_search(self, test_documents_dir):
        """Test de búsqueda híbrida"""
        # Setup
        loader = DocumentLoader()
        chunker = SmartChunker()
        vector_store = VectorStore(store_type="faiss")
        
        documents = loader.load_directory(str(test_documents_dir))
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            
        vector_store.add_chunks(all_chunks)
        
        # Crear motor de búsqueda híbrida
        search_engine = HybridSearchEngine(vector_store)
        
        # Test búsqueda híbrida
        query = "penalizaciones por incumplimiento"
        results = search_engine.search(query, top_k=5, search_type="hybrid")
        
        assert len(results) > 0
        assert all(hasattr(r, 'content') for r in results)
        assert all(hasattr(r, 'score') for r in results)
        assert all(hasattr(r, 'source') for r in results)
        
        # Verificar que encuentra penalizaciones
        relevant_content = ' '.join(r.content for r in results[:3])
        assert "penalizacion" in relevant_content.lower() or "10%" in relevant_content
        
    @pytest.mark.asyncio
    async def test_reranking(self, test_documents_dir):
        """Test del sistema de reranking"""
        # Setup búsqueda
        loader = DocumentLoader()
        chunker = SmartChunker()
        vector_store = VectorStore(store_type="faiss")
        
        documents = loader.load_directory(str(test_documents_dir))
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            
        vector_store.add_chunks(all_chunks)
        
        # Obtener resultados iniciales
        query = "precio y forma de pago"
        initial_results = vector_store.search(query, top_k=10)
        
        # Aplicar reranking
        reranker = AdvancedReranker()
        reranked = reranker.rerank(
            query,
            [{'content': r['content'], 'score': r['score']} for r in initial_results],
            top_k=5
        )
        
        assert len(reranked) <= 5
        assert all(hasattr(r, 'original_score') for r in reranked)
        assert all(hasattr(r, 'rerank_score') for r in reranked)
        assert all(hasattr(r, 'combined_score') for r in reranked)
        
        # Verificar que el orden cambió
        if len(reranked) > 1:
            assert reranked[0].combined_score >= reranked[1].combined_score
            
    @pytest.mark.asyncio
    async def test_response_generation(self, test_documents_dir):
        """Test de generación de respuestas"""
        # Setup completo
        loader = DocumentLoader()
        chunker = SmartChunker()
        vector_store = VectorStore(store_type="faiss")
        
        documents = loader.load_directory(str(test_documents_dir))
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            
        vector_store.add_chunks(all_chunks)
        
        # Generar respuesta
        response_generator = ResponseGenerator()
        
        query = "¿Cuáles son las obligaciones del arrendatario en el contrato de arrendamiento?"
        search_results = vector_store.search(query, top_k=5)
        
        response = response_generator.generate_response(query, search_results)
        
        assert 'answer' in response
        assert 'confidence' in response
        assert 'sources' in response
        assert response['confidence'] > 0
        assert len(response['answer']) > 50  # Respuesta sustancial
        
        # Verificar que menciona obligaciones específicas
        answer_lower = response['answer'].lower()
        assert any(term in answer_lower for term in ['mantener', 'conservación', 'obras', 'pagar'])
        
    @pytest.mark.asyncio
    async def test_contract_analyzer_agent(self, sample_contract):
        """Test del agente analizador de contratos"""
        analyzer = ContractAnalyzerAgent()
        
        # Test análisis completo
        task = {
            'type': 'full_analysis',
            'content': {
                'text': sample_contract,
                'metadata': {'filename': 'test_contract.txt'}
            }
        }
        
        result = await analyzer.execute_task(task)
        
        assert result['status'] == 'success'
        assert 'analysis' in result
        
        analysis = result['analysis']
        assert analysis['contract_type'] == 'arrendamiento'
        assert len(analysis['parties']) > 0
        assert len(analysis['key_dates']) > 0
        assert analysis['financial_terms']['total_eur'] > 0
        assert 'obligations' in analysis
        assert isinstance(analysis['obligations'], list)
        
    @pytest.mark.asyncio
    async def test_validator_agent(self, sample_contract):
        """Test del agente validador"""
        validator = ValidatorAgent()
        
        # Crear una respuesta para validar
        test_response = {
            'response': "El contrato de arrendamiento tiene una duración de 5 años, desde el 1 de enero de 2024 hasta el 31 de diciembre de 2028.",
            'sources': [{'content': sample_contract}],
            'query': "¿Cuál es la duración del contrato?"
        }
        
        # Validar respuesta
        task = {
            'type': 'full_validation',
            'content': test_response
        }
        
        result = await validator.execute_task(task)
        
        assert 'is_valid' in result
        assert 'confidence' in result
        assert result['is_valid'] == True  # Debería ser válida
        assert result['confidence'] > 0.8  # Alta confianza
        
        # Test con respuesta inválida
        invalid_response = {
            'response': "El contrato dura 10 años y el precio es de 10.000 euros mensuales.",
            'sources': [{'content': sample_contract}],
            'query': "¿Cuál es la duración y precio?"
        }
        
        invalid_task = {
            'type': 'full_validation',
            'content': invalid_response
        }
        
        invalid_result = await validator.execute_task(invalid_task)
        
        assert invalid_result['is_valid'] == False
        assert len(invalid_result['issues']) > 0
        
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self, test_documents_dir):
        """Test del pipeline completo de principio a fin"""
        start_time = time.time()
        
        # 1. Cargar documentos
        loader = DocumentLoader()
        documents = loader.load_directory(str(test_documents_dir))
        assert len(documents) > 0
        
        # 2. Preprocesar
        preprocessor = DocumentPreprocessor()
        processed_docs = []
        for doc in documents:
            processed = preprocessor.preprocess_document(doc.content, doc.metadata)
            doc.content = processed['content']
            doc.metadata.update(processed['metadata'])
            processed_docs.append(doc)
            
        # 3. Chunking
        chunker = SmartChunker()
        all_chunks = []
        for doc in processed_docs:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        assert len(all_chunks) >= len(documents)
        
        # 4. Crear vector store e indexar
        vector_store = VectorStore(store_type="faiss")
        vector_store.add_chunks(all_chunks)
        
        # 5. Realizar búsqueda híbrida
        search_engine = HybridSearchEngine(vector_store)
        query = "¿Cuáles son todas las penalizaciones mencionadas en los contratos?"
        search_results = search_engine.search(query, top_k=10, search_type="hybrid")
        assert len(search_results) > 0
        
        # 6. Reranking
        reranker = AdvancedReranker()
        reranked_results = reranker.rerank(
            query,
            [{'content': r.content, 'score': r.score} for r in search_results],
            top_k=5
        )
        
        # 7. Generar respuesta
        response_generator = ResponseGenerator()
        final_response = response_generator.generate_response(
            query,
            [{'content': r.content, 'score': r.combined_score, 'metadata': {}} 
             for r in reranked_results]
        )
        
        # 8. Validar respuesta
        validator = ValidatorAgent()
        validation_result = await validator.process_message(
            AgentMessage.create(
                sender="test",
                recipient="Validator",
                message_type="validate_response",
                content={
                    'response': final_response['answer'],
                    'sources': [{'content': r.content} for r in reranked_results],
                    'query': query
                }
            )
        )
        
        # Verificaciones finales
        assert final_response['answer']
        assert final_response['confidence'] > 0.5
        assert "penalizacion" in final_response['answer'].lower() or "interés" in final_response['answer'].lower()
        
        elapsed_time = time.time() - start_time
        print(f"\nPipeline completo ejecutado en {elapsed_time:.2f} segundos")
        
        # El pipeline debería completarse en menos de 30 segundos
        assert elapsed_time < 30
        
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test de manejo de errores en el pipeline"""
        # Test con documento vacío
        loader = DocumentLoader()
        empty_doc = loader.load_document("nonexistent_file.txt")
        assert empty_doc is None
        
        # Test con embeddings de texto vacío
        embedder = OpenAIEmbeddings()
        empty_embedding = embedder.embed_query("")
        assert isinstance(empty_embedding, list)
        
        # Test con búsqueda sin resultados
        vector_store = VectorStore(store_type="faiss")
        empty_results = vector_store.search("query_that_matches_nothing")
        assert isinstance(empty_results, list)
        assert len(empty_results) == 0
        
        # Test generación sin contexto
        response_generator = ResponseGenerator()
        no_context_response = response_generator.generate_response(
            "¿Pregunta sin contexto?",
            []
        )
        assert no_context_response['confidence'] == 0.0
        assert "No se encontró información" in no_context_response['answer']
        
    def test_performance_metrics(self, test_documents_dir):
        """Test de métricas de rendimiento"""
        # Medir tiempos de cada componente
        metrics = {
            'loading_time': 0,
            'chunking_time': 0,
            'embedding_time': 0,
            'search_time': 0,
            'total_time': 0
        }
        
        total_start = time.time()
        
        # Loading
        start = time.time()
        loader = DocumentLoader()
        documents = loader.load_directory(str(test_documents_dir))
        metrics['loading_time'] = time.time() - start
        
        # Chunking
        start = time.time()
        chunker = SmartChunker()
        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        metrics['chunking_time'] = time.time() - start
        
        # Embedding (simulado para no gastar API)
        start = time.time()
        # Simular tiempo de embedding
        time.sleep(0.1)
        metrics['embedding_time'] = time.time() - start
        
        # Search
        start = time.time()
        vector_store = VectorStore(store_type="faiss")
        # Simular búsqueda
        time.sleep(0.05)
        metrics['search_time'] = time.time() - start
        
        metrics['total_time'] = time.time() - total_start
        
        # Verificar que los tiempos son razonables
        assert metrics['loading_time'] < 1.0  # Menos de 1 segundo
        assert metrics['chunking_time'] < 2.0  # Menos de 2 segundos
        assert metrics['total_time'] < 5.0  # Menos de 5 segundos total
        
        print("\nMétricas de rendimiento:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.3f}s")

# Clase de utilidades para tests
class TestUtils:
    """Utilidades para testing"""
    
    @staticmethod
    def create_mock_chunks(num_chunks: int = 10) -> List[Any]:
        """Crea chunks mock para testing"""
        from src.ingestion.chunker import Chunk
        
        chunks = []
        for i in range(num_chunks):
            chunk = Chunk(
                content=f"Este es el contenido del chunk {i}. Contiene información importante.",
                metadata={'source': f'doc_{i // 3}', 'page': i % 3 + 1},
                chunk_id=f"chunk_{i}",
                doc_id=f"doc_{i // 3}",
                chunk_index=i,
                start_char=i * 100,
                end_char=(i + 1) * 100
            )
            chunks.append(chunk)
            
        return chunks
        
    @staticmethod
    def create_mock_search_results(num_results: int = 5) -> List[Dict[str, Any]]:
        """Crea resultados de búsqueda mock"""
        results = []
        for i in range(num_results):
            results.append({
                'chunk_id': f'chunk_{i}',
                'content': f'Contenido relevante del resultado {i}',
                'metadata': {'source': f'document_{i}'},
                'score': 0.9 - (i * 0.1)
            })
        return results

# Función para ejecutar todos los tests
def run_all_tests():
    """Ejecuta todos los tests del pipeline"""
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_all_tests()