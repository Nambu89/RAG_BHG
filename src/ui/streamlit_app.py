import streamlit as st
import pandas as pd
from datetime import datetime
import json
import time
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Importar componentes del sistema
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.chunker import SmartChunker
from src.embeddings.vector_store import VectorStore
from src.generation.response_generator import ResponseGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Configuración de la página
st.set_page_config(
    page_title=settings.ui.title,
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #3B82F6;
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    
    .source-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #3B82F6;
    }
    
    .confidence-high { color: #10B981; }
    .confidence-medium { color: #F59E0B; }
    .confidence-low { color: #EF4444; }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'response_generator' not in st.session_state:
    st.session_state.response_generator = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        'queries': 0,
        'avg_confidence': 0,
        'avg_response_time': 0,
        'documents_processed': 0
    }

def main():
    """Función principal de la aplicación"""
    
    # Header
    st.markdown('<h1 class="main-header">🏨 Athenea RAG - Barceló Hotel Group</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6B7280; font-size: 1.2rem;">Sistema Inteligente de Consulta de Contratos</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.barcelo.com/guia-turismo/wp-content/uploads/2019/11/barcelo-hotels-resorts.png", width=200)
        
        st.markdown("### 📊 Panel de Control")
        
        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Consultas", st.session_state.metrics['queries'])
            st.metric("Documentos", st.session_state.metrics['documents_processed'])
        with col2:
            st.metric("Confianza Avg", f"{st.session_state.metrics['avg_confidence']:.2%}")
            st.metric("Tiempo Avg", f"{st.session_state.metrics['avg_response_time']:.2f}s")
        
        st.markdown("---")
        
        # Configuración
        st.markdown("### ⚙️ Configuración")
        
        search_type = st.selectbox(
            "Tipo de búsqueda",
            ["Híbrida (Recomendado)", "Solo Vectorial", "Solo Keywords"],
            help="La búsqueda híbrida combina búsqueda semántica y por palabras clave"
        )
        
        top_k = st.slider(
            "Resultados a recuperar",
            min_value=1,
            max_value=10,
            value=5,
            help="Número de fragmentos relevantes a considerar"
        )
        
        temperature = st.slider(
            "Creatividad del modelo",
            min_value=0.0,
            max_value=1.0,
            value=settings.openai.temperature,
            step=0.1,
            help="0 = Respuestas más conservadoras, 1 = Más creativas"
        )
        
        enable_hyde = st.checkbox(
            "Habilitar HyDE",
            value=settings.search.enable_hyde,
            help="Hypothetical Document Embeddings para mejorar búsqueda"
        )
        
        st.markdown("---")
        
        # Acciones
        st.markdown("### 🛠️ Acciones")
        
        if st.button("🗑️ Limpiar Historial", use_container_width=True):
            st.session_state.chat_history = []
            st.success("Historial limpiado")
            
        if st.button("📥 Exportar Conversación", use_container_width=True):
            export_conversation()
            
    # Área principal
    tabs = st.tabs(["💬 Chat", "📁 Documentos", "📊 Análisis", "ℹ️ Ayuda"])
    
    with tabs[0]:
        chat_interface()
        
    with tabs[1]:
        document_management()
        
    with tabs[2]:
        analytics_dashboard()
        
    with tabs[3]:
        help_section()

def chat_interface():
    """Interfaz de chat principal"""
    
    # Verificar si hay documentos cargados
    if not st.session_state.documents_loaded:
        st.warning("⚠️ No hay documentos cargados. Por favor, ve a la pestaña 'Documentos' para cargar contratos.")
        return
        
    # Inicializar componentes si es necesario
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore()
        
    if st.session_state.response_generator is None:
        st.session_state.response_generator = ResponseGenerator()
        
    # Mostrar historial de chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                # Mostrar respuesta con formato
                display_response(message["content"])
                
    # Input del usuario
    if prompt := st.chat_input("Escribe tu pregunta sobre los contratos..."):
        # Agregar mensaje del usuario
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
            
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Buscando en los documentos..."):
                response = process_query(prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                display_response(response)

def process_query(query: str) -> Dict[str, Any]:
    """Procesa una consulta del usuario"""
    
    start_time = time.time()
    
    try:
        # Configuración de búsqueda
        search_config = st.session_state.get('search_config', {})
        top_k = search_config.get('top_k', 5)
        search_type = search_config.get('search_type', 'hybrid')
        
        # Realizar búsqueda
        if search_type == "Híbrida (Recomendado)":
            search_results = st.session_state.vector_store.hybrid_search(query, top_k)
        elif search_type == "Solo Vectorial":
            search_results = st.session_state.vector_store.search(query, top_k)
        else:  # Solo Keywords
            search_results = st.session_state.vector_store._keyword_search(query, top_k)
            
        # Generar respuesta
        response = st.session_state.response_generator.generate_response(
            query=query,
            search_results=search_results,
            conversation_history=st.session_state.chat_history[-6:]  # Últimos 3 intercambios
        )
        
        # Actualizar métricas
        elapsed_time = time.time() - start_time
        update_metrics(response, elapsed_time)
        
        return response
        
    except Exception as e:
        logger.error(f"Error procesando consulta: {str(e)}")
        return {
            "query": query,
            "answer": "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo.",
            "confidence": 0.0,
            "sources": [],
            "warnings": [str(e)],
            "metadata": {"error": True}
        }

def display_response(response: Dict[str, Any]):
    """Muestra una respuesta con formato"""
    
    # Respuesta principal
    st.markdown(response["answer"])
    
    # Confianza
    confidence = response.get("confidence", 0)
    confidence_color = "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
    st.markdown(f'<p class="confidence-{confidence_color}">Confianza: {confidence:.0%}</p>', unsafe_allow_html=True)
    
    # Advertencias
    warnings = response.get("warnings", [])
    if warnings:
        for warning in warnings:
            st.warning(warning)
            
    # Fuentes
    sources = response.get("sources", [])
    if sources and settings.ui.show_sources:
        with st.expander(f"📚 Fuentes ({len(sources)} documentos)"):
            for i, source in enumerate(sources):
                st.markdown(f'<div class="source-card">', unsafe_allow_html=True)
                st.markdown(f"**Documento:** {source.get('document', 'Desconocido')}")
                st.markdown(f"**Sección:** {source.get('section', 'N/A')}")
                st.markdown(f"**Relevancia:** {source.get('relevance', 0):.2f}")
                if source.get('excerpt'):
                    st.markdown(f"**Extracto:** *{source['excerpt'][:200]}...*")
                st.markdown('</div>', unsafe_allow_html=True)

def document_management():
    """Gestión de documentos"""
    
    st.header("📁 Gestión de Documentos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carga de documentos
        st.subheader("Cargar Documentos")
        
        upload_method = st.radio(
            "Método de carga",
            ["Cargar archivos", "Cargar desde carpeta"]
        )
        
        if upload_method == "Cargar archivos":
            uploaded_files = st.file_uploader(
                "Selecciona los contratos",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt']
            )
            
            if uploaded_files and st.button("📤 Procesar Documentos"):
                process_uploaded_files(uploaded_files)
                
        else:
            folder_path = st.text_input(
                "Ruta de la carpeta",
                value="./data/contracts"
            )
            
            if st.button("📂 Cargar desde Carpeta"):
                process_folder(folder_path)
                
    with col2:
        # Estado actual
        st.subheader("Estado Actual")
        
        if st.session_state.vector_store:
            stats = st.session_state.vector_store.get_stats()
            
            st.info(f"**Documentos indexados:** {stats.get('total_chunks', 0)}")
            st.info(f"**Última actualización:** {stats.get('last_update', 'N/A')}")
            
            if st.button("💾 Guardar Índice"):
                st.session_state.vector_store.save_index()
                st.success("Índice guardado exitosamente")

def process_uploaded_files(files):
    """Procesa archivos subidos"""
    
    with st.spinner("Procesando documentos..."):
        # Guardar archivos temporalmente
        temp_dir = Path("./temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        for file in files:
            file_path = temp_dir / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
                
        # Procesar carpeta temporal
        process_folder(str(temp_dir))
        
        # Limpiar archivos temporales
        for file in temp_dir.glob("*"):
            file.unlink()

def process_folder(folder_path: str):
    """Procesa una carpeta de documentos"""
    
    try:
        # Inicializar componentes
        loader = DocumentLoader()
        chunker = SmartChunker()
        
        # Cargar documentos
        with st.spinner("Cargando documentos..."):
            documents = loader.load_directory(folder_path)
            st.success(f"✅ {len(documents)} documentos cargados")
            
        # Generar chunks
        with st.spinner("Generando chunks..."):
            chunks = chunker.chunk_documents(documents)
            st.success(f"✅ {len(chunks)} chunks generados")
            
        # Crear vector store si no existe
        if st.session_state.vector_store is None:
            st.session_state.vector_store = VectorStore()
            
        # Agregar chunks al vector store
        with st.spinner("Indexando documentos..."):
            result = st.session_state.vector_store.add_chunks(chunks)
            st.success(f"✅ Documentos indexados en {result['time_elapsed']:.2f} segundos")
            
        # Guardar índice
        st.session_state.vector_store.save_index()
        
        # Actualizar estado
        st.session_state.documents_loaded = True
        st.session_state.metrics['documents_processed'] = len(chunks)
        
        # Mostrar resumen
        st.balloons()
        
        with st.expander("📊 Resumen del Procesamiento"):
            # Estadísticas de carga
            st.json(loader.extraction_stats)
            
            # Estadísticas de chunking  
            st.json(chunker.get_chunking_stats())
            
    except Exception as e:
        st.error(f"Error procesando documentos: {str(e)}")
        logger.error(f"Error en process_folder: {str(e)}")

def analytics_dashboard():
    """Dashboard de análisis"""
    
    st.header("📊 Panel de Análisis")
    
    if not st.session_state.chat_history:
        st.info("No hay datos para mostrar. Realiza algunas consultas primero.")
        return
        
    # Extraer datos de las consultas
    queries_data = []
    for i in range(0, len(st.session_state.chat_history), 2):
        if i+1 < len(st.session_state.chat_history):
            user_msg = st.session_state.chat_history[i]
            assistant_msg = st.session_state.chat_history[i+1]
            
            if isinstance(assistant_msg["content"], dict):
                queries_data.append({
                    "query": user_msg["content"],
                    "confidence": assistant_msg["content"].get("confidence", 0),
                    "sources_count": len(assistant_msg["content"].get("sources", [])),
                    "warnings_count": len(assistant_msg["content"].get("warnings", []))
                })
                
    if not queries_data:
        st.info("No hay suficientes datos para el análisis.")
        return
        
    # Convertir a DataFrame
    df = pd.DataFrame(queries_data)
    
    # Visualizaciones
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de confianza
        fig_confidence = px.line(
            df.reset_index(),
            x="index",
            y="confidence",
            title="Evolución de la Confianza",
            labels={"index": "Consulta #", "confidence": "Confianza"}
        )
        fig_confidence.update_traces(mode='lines+markers')
        st.plotly_chart(fig_confidence, use_container_width=True)
        
    with col2:
        # Distribución de fuentes
        fig_sources = px.histogram(
            df,
            x="sources_count",
            title="Distribución de Fuentes por Consulta",
            labels={"sources_count": "Número de Fuentes", "count": "Frecuencia"}
        )
        st.plotly_chart(fig_sources, use_container_width=True)
        
    # Tabla de consultas
    st.subheader("📝 Historial de Consultas")
    st.dataframe(
        df[["query", "confidence", "sources_count", "warnings_count"]],
        use_container_width=True
    )
    
    # Estadísticas generales
    st.subheader("📈 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Confianza Promedio", f"{df['confidence'].mean():.2%}")
    with col2:
        st.metric("Fuentes Promedio", f"{df['sources_count'].mean():.1f}")
    with col3:
        st.metric("Consultas con Advertencias", f"{(df['warnings_count'] > 0).sum()}")
    with col4:
        st.metric("Total Consultas", len(df))

def help_section():
    """Sección de ayuda"""
    
    st.header("ℹ️ Ayuda y Guía de Uso")
    
    with st.expander("🚀 Cómo empezar"):
        st.markdown("""
        1. **Carga de Documentos**: Ve a la pestaña 'Documentos' y carga tus contratos
        2. **Realizar Consultas**: En la pestaña 'Chat', escribe tus preguntas
        3. **Interpretar Resultados**: 
           - **Verde**: Alta confianza (>80%)
           - **Amarillo**: Confianza media (50-80%)
           - **Rojo**: Baja confianza (<50%)
        4. **Ver Fuentes**: Expande la sección de fuentes para ver los documentos citados
        """)
        
    with st.expander("💡 Ejemplos de Consultas"):
        st.markdown("""
        - "¿Cuáles son las obligaciones de información sobre el presupuesto en el contrato X?"
        - "¿En qué contratos tenemos opción de compra?"
        - "Resume las condiciones de los contratos de arrendamiento"
        - "¿Cuáles son los plazos de pago en el contrato de gestión?"
        - "¿Qué penalizaciones existen por incumplimiento?"
        """)
        
    with st.expander("🔧 Configuración Avanzada"):
        st.markdown("""
        - **Búsqueda Híbrida**: Combina búsqueda semántica y por palabras clave (recomendado)
        - **HyDE**: Genera documentos hipotéticos para mejorar la búsqueda
        - **Top-K**: Número de fragmentos a considerar (más = más contexto pero más lento)
        - **Temperatura**: Controla la creatividad del modelo (0 = conservador, 1 = creativo)
        """)
        
    with st.expander("⚠️ Limitaciones"):
        st.markdown("""
        - El sistema solo puede responder basándose en los documentos cargados
        - La calidad de las respuestas depende de la calidad de los documentos
        - Documentos escaneados pueden tener problemas de OCR
        - El sistema no puede interpretar imágenes o gráficos
        """)

def update_metrics(response: Dict[str, Any], elapsed_time: float):
    """Actualiza las métricas del sistema"""
    
    metrics = st.session_state.metrics
    
    # Incrementar contador de consultas
    metrics['queries'] += 1
    
    # Actualizar confianza promedio
    confidence = response.get('confidence', 0)
    if metrics['queries'] == 1:
        metrics['avg_confidence'] = confidence
    else:
        metrics['avg_confidence'] = (
            (metrics['avg_confidence'] * (metrics['queries'] - 1) + confidence) / 
            metrics['queries']
        )
        
    # Actualizar tiempo promedio
    if metrics['queries'] == 1:
        metrics['avg_response_time'] = elapsed_time
    else:
        metrics['avg_response_time'] = (
            (metrics['avg_response_time'] * (metrics['queries'] - 1) + elapsed_time) / 
            metrics['queries']
        )

def export_conversation():
    """Exporta la conversación actual"""
    
    if not st.session_state.chat_history:
        st.warning("No hay conversación para exportar")
        return
        
    # Preparar datos para exportación
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": st.session_state.metrics,
        "conversation": st.session_state.chat_history
    }
    
    # Convertir a JSON
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar JSON",
        data=json_str,
        file_name=f"conversacion_athenea_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# Guardar configuración en session state
def save_config():
    """Guarda la configuración actual"""
    st.session_state.search_config = {
        'search_type': st.session_state.get('search_type', 'hybrid'),
        'top_k': st.session_state.get('top_k', 5),
        'temperature': st.session_state.get('temperature', 0.1),
        'enable_hyde': st.session_state.get('enable_hyde', True)
    }

if __name__ == "__main__":
    main()