# test_contract_types.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.embeddings.vector_store import VectorStore
from src.generation.response_generator import ResponseGenerator

def test_contract_type_search():
    """Prueba la búsqueda de tipos de contratos"""
    
    print("Inicializando sistema...")
    vector_store = VectorStore()
    response_generator = ResponseGenerator()
    
    # Query principal
    query = "¿Qué tipos de contratos tenemos en el sistema?"
    
    print(f"\n🔍 Búsqueda: '{query}'")
    
    # Buscar con más resultados
    search_results = vector_store.hybrid_search(query, top_k=30)
    
    print(f"\n📊 Resultados encontrados: {len(search_results)}")
    
    # Analizar tipos únicos
    contract_types = {}
    for result in search_results:
        doc_type = result.metadata.get('contract_type', 'unknown')
        filename = result.metadata.get('filename', 'unknown')
        
        if doc_type not in contract_types:
            contract_types[doc_type] = set()
        contract_types[doc_type].add(filename)
    
    print("\n📋 Tipos de contratos encontrados:")
    for doc_type, files in sorted(contract_types.items()):
        print(f"\n   {doc_type.upper()}:")
        for file in sorted(files):
            print(f"      - {file}")
    
    # Generar respuesta
    print("\n🤖 Generando respuesta...")
    response = response_generator.generate_response(
        query=query,
        search_results=search_results
    )
    
    print("\n📝 Respuesta generada:")
    print(response['answer'])
    print(f"\n⭐ Confianza: {response['confidence']:.2%}")

if __name__ == "__main__":
    test_contract_type_search()