# 🏨 BHG RAG - Sistema Inteligente de Consulta de Contratos

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4-green.svg" alt="OpenAI">
  <img src="https://img.shields.io/badge/Streamlit-1.31+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</div>

## 📋 Descripción

Athenea RAG es un sistema avanzado de Retrieval-Augmented Generation (RAG) diseñado específicamente para el Barceló Hotel Group. Permite realizar consultas inteligentes sobre contratos y documentos legales en lenguaje natural, proporcionando respuestas precisas con trazabilidad completa.

### ✨ Características Principales

- 🔍 **Búsqueda Híbrida Avanzada**: Combina búsqueda vectorial semántica con búsqueda por palabras clave
- 🧠 **IA de Última Generación**: Utiliza GPT-4 Turbo y embeddings de OpenAI
- 📚 **Multi-formato**: Soporta PDF, DOCX, TXT, HTML, CSV y Excel
- 🎯 **Alta Precisión**: Sistema de validación y anti-alucinaciones
- 📊 **Análisis en Tiempo Real**: Dashboard con métricas y estadísticas
- 🔒 **Seguro y Confiable**: Diseñado para cumplir con RGPD

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.11 o superior
- Clave API de OpenAI

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/your-org/athenea-rag-mvp.git
cd athenea-rag-mvp
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY
```

5. **Descargar modelo de spaCy (opcional)**
```bash
python -m spacy download es_core_news_sm
```

### Ejecución

```bash
streamlit run src/ui/streamlit_app.py
```

La aplicación estará disponible en `http://localhost:8501`

## 📖 Guía de Uso

### 1. Cargar Documentos

1. Navega a la pestaña "📁 Documentos"
2. Selecciona los contratos (PDF, DOCX, etc.)
3. Haz clic en "Procesar Documentos"

### 2. Realizar Consultas

1. Ve a la pestaña "💬 Chat"
2. Escribe tu pregunta en lenguaje natural
3. El sistema buscará y generará una respuesta basada en los documentos

### 3. Ejemplos de Consultas

- "¿Cuáles son las obligaciones de información sobre el presupuesto?"
- "¿En qué contratos tenemos opción de compra?"
- "Resume las condiciones de los contratos de arrendamiento"
- "¿Qué penalizaciones existen por incumplimiento?"

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   RAG Pipeline   │────▶│    OpenAI API   │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌──────────────┐      ┌──────────────┐
            │ Vector Store │      │   Document   │
            │  (ChromaDB)  │      │    Loader    │
            └──────────────┘      └──────────────┘
```

### Componentes Principales

- **Document Loader**: Carga y procesa múltiples formatos de documentos
- **Smart Chunker**: División inteligente de documentos preservando contexto
- **Vector Store**: Almacenamiento y búsqueda vectorial con ChromaDB/FAISS
- **Response Generator**: Generación de respuestas con validación y citas
- **Streamlit UI**: Interfaz intuitiva y moderna

## 🔧 Configuración Avanzada

### Parámetros de Búsqueda

```python
# En settings.py
search_config = {
    "top_k_vector": 20,      # Resultados de búsqueda vectorial
    "top_k_keyword": 20,     # Resultados de búsqueda por keywords
    "top_k_final": 5,        # Resultados finales tras reranking
    "similarity_threshold": 0.7,  # Umbral de similitud
    "enable_hyde": True      # Hypothetical Document Embeddings
}
```

### Modelos y Embeddings

```python
# Modelos disponibles
EMBEDDING_MODELS = [
    "text-embedding-3-large",   # 3072 dimensiones (recomendado)
    "text-embedding-3-small",   # 1536 dimensiones
    "text-embedding-ada-002"    # 1536 dimensiones (legacy)
]

CHAT_MODELS = [
    "gpt-4-turbo-preview",      # Más capaz (recomendado)
    "gpt-4",                    # Estable
    "gpt-3.5-turbo"            # Más económico
]
```

## 📊 Métricas y Análisis

El sistema registra automáticamente:

- Número de consultas realizadas
- Confianza promedio de las respuestas
- Tiempo de respuesta promedio
- Documentos procesados
- Tasa de error

Accede al dashboard en la pestaña "📊 Análisis" para visualizar las métricas.

## 🐛 Solución de Problemas

### Error: "No module named 'openai'"
```bash
pip install openai --upgrade
```

### Error: "API key not found"
Asegúrate de configurar `OPENAI_API_KEY` en el archivo `.env`

### Documentos no se procesan correctamente
- Verifica que los PDFs no estén protegidos
- Asegúrate de que los archivos no estén corruptos
- Revisa los logs en `./logs/athenea.log`

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Estructura del Proyecto

```
athenea-rag-mvp/
├── src/
│   ├── config/          # Configuración del sistema
│   ├── ingestion/       # Carga y procesamiento de documentos
│   ├── embeddings/      # Generación de embeddings y vector store
│   ├── retrieval/       # Búsqueda y recuperación
│   ├── generation/      # Generación de respuestas
│   ├── ui/              # Interfaz de usuario
│   └── utils/           # Utilidades y logging
├── data/
│   ├── contracts/       # Documentos a procesar
│   ├── processed/       # Documentos procesados
│   └── vector_store/    # Índice vectorial
├── logs/                # Logs del sistema
├── requirements.txt     # Dependencias
├── .env.example        # Ejemplo de configuración
└── README.md           # Este archivo
```

## 🚀 Próximos Pasos (Post-MVP)

- [ ] Integración con Azure AI Search
- [ ] Arquitectura multi-agente completa
- [ ] Integración con SharePoint y Azure AD
- [ ] API REST para integración empresarial
- [ ] Soporte multiidioma mejorado
- [ ] Fine-tuning de modelos específicos

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Equipo

- **Arquitecto IA**: Diseño del sistema RAG
- **Desarrollador**: Implementación y optimización
- **QA**: Pruebas y validación

## 📞 Contacto

Para soporte o consultas sobre el proyecto:
- Email: soporte@athenea-rag.com
- Documentation: [Wiki del Proyecto](https://wiki.athenea-rag.com)

---

<div align="center">
  Fernando Prada - Ingeniero de IA - Consultor Senior - Devoteam Spain
</div>