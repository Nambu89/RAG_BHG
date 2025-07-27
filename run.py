"""
Script de inicio rápido para BHG RAG
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 11):
        print("Error: Se requiere Python 3.11 o superior")
        print(f"   Tu versión: Python {sys.version}")
        sys.exit(1)
    print("Python version OK")

def check_dependencies():
    """Verifica las dependencias"""
    try:
        import openai
        import streamlit
        import chromadb
        print("Dependencias principales instaladas")
    except ImportError as e:
        print(f"Error: Falta instalar dependencias - {e}")
        print("   Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

def check_env():
    """Verifica las variables de entorno"""
    if not os.path.exists('.env'):
        print("Archivo .env no encontrado")
        if os.path.exists('.env.example'):
            print("   Copiando .env.example a .env...")
            import shutil
            shutil.copy('.env.example', '.env')
            print("  Archivo .env creado")
            print("   IMPORTANTE: Edita .env y agrega tu OPENAI_API_KEY")
            sys.exit(1)
    
    # Verificar API key
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY no configurada en .env")
        sys.exit(1)
    
    print("Variables de entorno OK")

def create_directories():
    """Crea los directorios necesarios"""
    dirs = [
        'data/contracts',
        'data/processed',
        'data/vector_store',
        'logs',
        'temp'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("Directorios creados")

def check_spacy():
    """Verifica el modelo de spaCy"""
    try:
        import spacy
        nlp = spacy.load("es_core_news_sm")
        print("Modelo spaCy instalado")
    except:
        print("Modelo spaCy no instalado (opcional)")
        print("   Para instalarlo: python -m spacy download es_core_news_sm")

def add_sample_contracts():
    """Agrega contratos de ejemplo si no hay ninguno"""
    contracts_dir = Path('data/contracts')
    if not list(contracts_dir.glob('*')):
        print("No hay contratos en data/contracts/")
        print("   Creando contrato de ejemplo...")
        
        sample_contract = """CONTRATO DE ARRENDAMIENTO DE LOCAL COMERCIAL
        
Entre Barceló Hotel Group S.A. (en adelante, el ARRENDADOR) y 
Empresa Ejemplo S.L. (en adelante, el ARRENDATARIO).

CLÁUSULA PRIMERA - OBJETO
El ARRENDADOR cede en arrendamiento al ARRENDATARIO el local comercial 
situado en Calle Principal 123, con una superficie de 200 metros cuadrados.

CLÁUSULA SEGUNDA - DURACIÓN
El presente contrato tendrá una duración de 5 años, comenzando el 1 de enero 
de 2024 y finalizando el 31 de diciembre de 2028.

CLÁUSULA TERCERA - RENTA
La renta mensual será de 3.000 euros, pagaderos por adelantado en los 
primeros 5 días de cada mes.

CLÁUSULA CUARTA - FIANZA
El ARRENDATARIO depositará una fianza equivalente a dos mensualidades.

CLÁUSULA QUINTA - OBLIGACIONES
El ARRENDATARIO se obliga a mantener el local en buen estado y a no realizar 
modificaciones sin autorización previa por escrito del ARRENDADOR.
"""
        
        with open(contracts_dir / 'contrato_ejemplo.txt', 'w', encoding='utf-8') as f:
            f.write(sample_contract)
        
        print("   Contrato de ejemplo creado")

def main():
    """Función principal"""
    print("\nBGH RAG - Sistema de Consulta de Contratos")
    print("=" * 50)
    
    print("\nVerificando requisitos...")
    check_python_version()
    check_dependencies()
    check_env()
    create_directories()
    check_spacy()
    add_sample_contracts()
    
    print("\nTodo listo!")
    print("\nIniciando aplicación...")
    print("=" * 50)
    
    # Ejecutar Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "src/ui/streamlit_app.py",
        "--server.port", "8501",
        "--server.headless", "true"
    ])

if __name__ == "__main__":
    main()