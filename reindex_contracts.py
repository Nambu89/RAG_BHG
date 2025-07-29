# reindex_contracts.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import shutil
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.chunker import SmartChunker
from src.embeddings.vector_store import VectorStore

def reindex_all_contracts():
    """Re-indexa todos los contratos con la clasificación correcta"""
    
    print("🗑️  Eliminando índice antiguo...")
    vector_store_path = Path("./data/vector_store")
    if vector_store_path.exists():
        shutil.rmtree(vector_store_path)
        print("   ✓ Índice eliminado")
    
    print("\n📄 Cargando documentos...")
    loader = DocumentLoader()
    documents = loader.load_directory("./data/contracts")  # Ajusta la ruta según tu estructura
    
    print(f"   ✓ {len(documents)} documentos cargados")
    
    # Mostrar tipos detectados
    print("\n📊 Tipos de contratos detectados:")
    for doc in documents:
        doc_type = doc.metadata.get('contract_type', 'unknown')
        filename = doc.metadata.get('filename', 'unknown')
        print(f"   - {filename}: {doc_type}")
    
    print("\n🔨 Generando chunks...")
    chunker = SmartChunker()
    chunks = chunker.chunk_documents(documents)
    print(f"   ✓ {len(chunks)} chunks generados")
    
    print("\n💾 Creando nuevo índice...")
    vector_store = VectorStore()
    result = vector_store.add_chunks(chunks)
    print(f"   ✓ Indexación completada en {result['time_elapsed']:.2f} segundos")
    
    # Guardar el índice
    vector_store.save_index()
    print("\n✅ Re-indexación completada exitosamente!")
    
    # Verificar la indexación
    print("\n🔍 Verificando tipos indexados:")
    import chromadb
    from src.config.settings import settings
    
    client = chromadb.PersistentClient(path=settings.vector_store.persist_directory)
    collection = client.get_collection(name=settings.vector_store.collection_name)
    
    results = collection.get(include=["metadatas"])
    
    types_count = {}
    for meta in results['metadatas']:
        doc_type = meta.get('contract_type', 'unknown')
        types_count[doc_type] = types_count.get(doc_type, 0) + 1
    
    print("\n📈 Resumen final:")
    for doc_type, count in sorted(types_count.items()):
        print(f"   - {doc_type}: {count} chunks")

if __name__ == "__main__":
    reindex_all_contracts()