import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)

class UIComponents:
    """Componentes reutilizables para la interfaz de Streamlit"""
    
    @staticmethod
    def render_header():
        """Renderiza el header principal de la aplicación"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #1E3A8A; font-size: 3rem; margin-bottom: 0.5rem;">
                🏨 Athenea RAG
            </h1>
            <p style="color: #64748B; font-size: 1.2rem;">
                Sistema Inteligente de Consulta de Contratos - Barceló Hotel Group
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    @staticmethod
    def render_metrics_cards(metrics: Dict[str, Any]):
        """Renderiza tarjetas de métricas"""
        cols = st.columns(len(metrics))
        
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        
        for idx, (col, (key, value)) in enumerate(zip(cols, metrics.items())):
            with col:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {colors[idx % len(colors)]}, {colors[idx % len(colors)]}CC);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h3 style="margin: 0; font-size: 2rem;">{value}</h3>
                    <p style="margin: 0; opacity: 0.9;">{key}</p>
                </div>
                """, unsafe_allow_html=True)
                
    @staticmethod
    def render_search_box(placeholder: str = "Escribe tu pregunta aquí...") -> str:
        """Renderiza una caja de búsqueda estilizada"""
        st.markdown("""
        <style>
        .search-container {
            background: white;
            border-radius: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 0.5rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        query = st.text_input(
            label="",
            placeholder=placeholder,
            key="search_query",
            label_visibility="collapsed"
        )
        
        return query
        
    @staticmethod
    def render_document_card(
        document: Dict[str, Any],
        show_actions: bool = True
    ):
        """Renderiza una tarjeta de documento"""
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### 📄 {document.get('filename', 'Documento')}")
                
                # Metadata
                metadata = document.get('metadata', {})
                if metadata.get('contract_type'):
                    st.markdown(f"**Tipo:** {metadata['contract_type']}")
                if metadata.get('dates_found'):
                    st.markdown(f"**Fechas:** {', '.join(metadata['dates_found'][:3])}")
                if metadata.get('char_count'):
                    st.markdown(f"**Tamaño:** {metadata['char_count']:,} caracteres")
                    
            with col2:
                if show_actions:
                    if st.button("Ver", key=f"view_{document.get('doc_id')}"):
                        st.session_state['selected_document'] = document
                    if st.button("Eliminar", key=f"delete_{document.get('doc_id')}"):
                        st.session_state['delete_document'] = document
                        
            st.divider()
            
    @staticmethod
    def render_source_card(
        source: Dict[str, Any],
        index: int,
        expanded: bool = False
    ):
        """Renderiza una tarjeta de fuente"""
        relevance = source.get('relevance', 0)
        relevance_color = '#10B981' if relevance > 0.8 else '#F59E0B' if relevance > 0.5 else '#EF4444'
        
        with st.expander(
            f"📖 Fuente {index + 1}: {source.get('document', 'Desconocido')} "
            f"(Relevancia: {relevance:.2f})",
            expanded=expanded
        ):
            # Barra de relevancia
            st.markdown(f"""
            <div style="
                background: #E5E7EB;
                height: 8px;
                border-radius: 4px;
                margin-bottom: 1rem;
            ">
                <div style="
                    background: {relevance_color};
                    width: {relevance * 100}%;
                    height: 100%;
                    border-radius: 4px;
                "></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Metadata
            st.markdown(f"**Sección:** {source.get('section', 'N/A')}")
            if source.get('chunk_id'):
                st.markdown(f"**ID:** `{source['chunk_id']}`")
                
            # Extracto
            if source.get('excerpt'):
                st.markdown("**Extracto:**")
                st.info(source['excerpt'][:500] + "..." if len(source['excerpt']) > 500 else source['excerpt'])
                
    @staticmethod
    def render_confidence_indicator(
        confidence: float,
        show_label: bool = True
    ):
        """Renderiza un indicador de confianza"""
        color = '#10B981' if confidence > 0.8 else '#F59E0B' if confidence > 0.5 else '#EF4444'
        
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            {f'<p style="margin-bottom: 0.5rem;">Confianza en la respuesta:</p>' if show_label else ''}
            <div style="
                background: #E5E7EB;
                height: 24px;
                border-radius: 12px;
                position: relative;
            ">
                <div style="
                    background: {color};
                    width: {confidence * 100}%;
                    height: 100%;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                ">
                    {confidence:.0%}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    @staticmethod
    def render_timeline_chart(events: List[Dict[str, Any]]):
        """Renderiza un gráfico de línea de tiempo"""
        if not events:
            st.info("No hay eventos para mostrar")
            return
            
        # Preparar datos
        df = pd.DataFrame(events)
        
        # Crear figura
        fig = go.Figure()
        
        # Agregar eventos
        for idx, event in enumerate(events):
            fig.add_trace(go.Scatter(
                x=[event['date']],
                y=[idx],
                mode='markers+text',
                marker=dict(size=12, color=event.get('color', '#3B82F6')),
                text=event['title'],
                textposition="top center",
                hovertemplate=f"<b>{event['title']}</b><br>{event.get('description', '')}<br><extra></extra>"
            ))
            
        # Configurar layout
        fig.update_layout(
            title="Línea de Tiempo de Eventos",
            xaxis_title="Fecha",
            yaxis_title="",
            showlegend=False,
            height=400,
            yaxis=dict(showticklabels=False, range=[-1, len(events)])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    @staticmethod
    def render_donut_chart(
        data: Dict[str, float],
        title: str = "Distribución"
    ):
        """Renderiza un gráfico de donut"""
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=.4
        )])
        
        fig.update_layout(
            title=title,
            annotations=[dict(text=f'{sum(data.values())}<br>Total', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    @staticmethod
    def render_heatmap(
        data: pd.DataFrame,
        title: str = "Mapa de Calor"
    ):
        """Renderiza un mapa de calor"""
        fig = px.imshow(
            data,
            labels=dict(x="Columnas", y="Filas", color="Valor"),
            title=title,
            color_continuous_scale="RdYlBu_r"
        )
        
        fig.update_xaxis(side="top")
        st.plotly_chart(fig, use_container_width=True)
        
    @staticmethod
    def render_chat_message(
        message: Dict[str, Any],
        is_user: bool = True
    ):
        """Renderiza un mensaje de chat"""
        alignment = "flex-end" if is_user else "flex-start"
        bg_color = "#E3F2FD" if is_user else "#F5F5F5"
        
        # Escapar el contenido para evitar problemas con HTML
        content = message.get('content', '').replace('<', '&lt;').replace('>', '&gt;')
        timestamp = message.get('timestamp', datetime.now().strftime('%H:%M'))
        
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: {alignment};
            margin: 1rem 0;
        ">
            <div style="
                background: {bg_color};
                padding: 1rem;
                border-radius: 12px;
                max-width: 70%;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ">
                <p style="margin: 0;">{content}</p>
                <small style="opacity: 0.7;">
                    {timestamp}
                </small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    @staticmethod
    def render_loading_animation(text: str = "Procesando..."):
        """Renderiza una animación de carga personalizada"""
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div class="spinner"></div>
            <p style="margin-top: 1rem; color: #64748B;">{text}</p>
        </div>
        
        <style>
        .spinner {{
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3B82F6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        
    @staticmethod
    def render_error_message(
        error: str,
        suggestions: List[str] = None
    ):
        """Renderiza un mensaje de error con sugerencias"""
        st.error(f"⚠️ {error}")
        
        if suggestions:
            st.markdown("**Sugerencias:**")
            for suggestion in suggestions:
                st.markdown(f"• {suggestion}")
                
    @staticmethod
    def render_success_animation():
        """Renderiza una animación de éxito"""
        st.balloons()
        st.success("✅ ¡Operación completada correctamente!")
        
    @staticmethod
    def render_file_upload_zone():
        """Renderiza una zona de carga de archivos estilizada"""
        st.markdown("""
        <style>
        .upload-zone {
            border: 2px dashed #CBD5E1;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            background: #F8FAFC;
            margin: 1rem 0;
        }
        </style>
        
        <div class="upload-zone">
            <p style="color: #64748B; margin: 0;">
                Arrastra tus archivos aquí o haz clic para seleccionar
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Selecciona contratos",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        return uploaded_files
        
    @staticmethod
    def render_progress_steps(
        steps: List[str],
        current_step: int
    ):
        """Renderiza un indicador de progreso por pasos"""
        st.markdown("""
        <style>
        .step-container {
            display: flex;
            justify-content: space-between;
            margin: 2rem 0;
        }
        .step {
            flex: 1;
            text-align: center;
            position: relative;
        }
        .step-number {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .step-completed {
            background: #10B981;
            color: white;
        }
        .step-current {
            background: #3B82F6;
            color: white;
        }
        .step-pending {
            background: #E5E7EB;
            color: #9CA3AF;
        }
        .step-line {
            position: absolute;
            top: 20px;
            left: 50%;
            width: 100%;
            height: 2px;
            background: #E5E7EB;
            z-index: -1;
        }
        .step-line-completed {
            background: #10B981;
        }
        </style>
        """, unsafe_allow_html=True)
        
        html = '<div class="step-container">'
        
        for idx, step in enumerate(steps):
            status = 'completed' if idx < current_step else 'current' if idx == current_step else 'pending'
            
            # Construir línea condicional de forma más clara
            line_html = ''
            if idx < len(steps) - 1:
                line_class = 'step-line-completed' if idx < current_step else ''
                line_html = f'<div class="step-line {line_class}"></div>'
            
            html += f'''
            <div class="step">
                <div class="step-number step-{status}">{idx + 1}</div>
                <p style="margin: 0; font-size: 0.875rem;">{step}</p>
                {line_html}
            </div>
            '''
            
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        
    @staticmethod
    def render_comparison_table(
        data: List[Dict[str, Any]],
        highlight_differences: bool = True
    ):
        """Renderiza una tabla de comparación"""
        if not data:
            st.info("No hay datos para comparar")
            return
            
        df = pd.DataFrame(data)
        
        if highlight_differences and len(data) > 1:
            # Aplicar estilo para destacar diferencias
            def highlight_diff(s):
                if s.nunique() > 1:
                    return ['background-color: #FEF3C7'] * len(s)
                else:
                    return [''] * len(s)
                    
            styled_df = df.style.apply(highlight_diff)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
    @staticmethod
    def render_json_editor(
        data: Dict[str, Any],
        key: str = "json_editor"
    ) -> Dict[str, Any]:
        """Renderiza un editor JSON"""
        json_str = st.text_area(
            "Editor JSON",
            value=json.dumps(data, indent=2, ensure_ascii=False),
            height=300,
            key=key
        )
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            st.error(f"Error en JSON: {str(e)}")
            return data