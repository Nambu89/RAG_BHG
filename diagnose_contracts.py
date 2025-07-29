# diagnose_simple.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from src.config.settings import settings

def diagnose_simple():
    """Diagnóstico simple directo con ChromaDB"""
    
    print("Conectando a ChromaDB...")
    client = chromadb.PersistentClient(path=settings.vector_store.persist_directory)
    
    try:
        collection = client.get_collection(name=settings.vector_store.collection_name)
        
        # Obtener todos los documentos
        print("Obteniendo documentos...")
        results = collection.get(
            include=["documents", "metadatas"]
        )
        
        print(f"\nTotal documentos: {len(results['documents'])}")
        
        # Analizar tipos
        contract_types = {}
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            doc_type = meta.get('contract_type', 'no_detectado')
            filename = meta.get('filename', f'doc_{i}')
            
            if doc_type not in contract_types:
                contract_types[doc_type] = []
            
            contract_types[doc_type].append(filename)
            
            # Buscar menciones específicas
            if 'franquicia' in doc.lower():
                print(f"\n✓ FRANQUICIA encontrada en: {filename}")
                print(f"  Tipo detectado: {doc_type}")
                print(f"  Preview: {doc[:100]}...")
                
            if 'mantenimiento' in doc.lower() and 'servicios' in doc.lower():
                print(f"\n✓ MANTENIMIENTO encontrado en: {filename}")
                print(f"  Tipo detectado: {doc_type}")
                print(f"  Preview: {doc[:100]}...")
        
        print("\n=== RESUMEN DE TIPOS ===")
        for ct, files in contract_types.items():
            print(f"\n{ct}: {len(files)} chunks")
            for f in set(files):
                print(f"  - {f}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_simple()