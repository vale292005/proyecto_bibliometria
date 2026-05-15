import streamlit as st
from src.scraper import procesar_archivos
import os
import pandas as pd
import matplotlib.pyplot as plt
from src.similarity import (similitud_coseno_tfidf,similitud_sbert,similitud_levenshtein,similitud_jaccard)

st.set_page_config(page_title="Analizador Bibliométrico IA", layout="wide")

st.title("📊 Herramienta de Análisis Bibliométrico")
st.sidebar.title("Navegación")

menu = st.sidebar.radio(
    "Seleccione un Requerimiento:",
    ["Inicio", "Req 1: Descarga y Unificación", "Req 2: Similitud Textual", 
     "Req 3: Análisis de Categorías", "Req 4: Clustering Jerárquico", "Req 5: Visualización"]
)

if menu == "Inicio":
    st.write("Bienvenido al sistema de análisis sobre **IA Generativa**.")
    st.info("Utilice el menú de la izquierda para navegar por las fases del proyecto.")

elif menu == "Req 1: Descarga y Unificación":
    st.header("Automatización de Datos")
    st.write("Este módulo descarga datos de ArXiv sobre *Generative AI* y unifica los registros.")
    
    if st.button("Ejecutar Automatización"):
        with st.spinner("Buscando en las bases de datos..."):
            total, repetidos = procesar_archivos()
            
            st.success("¡Proceso completado!")
            
            col1, col2 = st.columns(2)
            col1.metric("Registros Únicos", total)
            col2.metric("Registros Repetidos eliminados", repetidos)
            
            st.info("Los archivos `unificado.csv` y `repetidos.csv` han sido generados en `data/processed/`.")
            
            # Mostrar una vista previa del resultado
            import pandas as pd
            df = pd.read_csv('data/processed/unificado.csv')
            st.dataframe(df.head())
            
elif menu == "Req 2: Similitud Textual":
    st.header("🔍 Análisis de Similitud Textual")
    st.write("Compare el abstract de dos artículos usando algoritmos clásicos, estadísticos y de IA avanzada.")
    
    if os.path.exists('data/processed/unificado.csv'):
        df = pd.read_csv('data/processed/unificado.csv')
        
        # Selector de artículos
        titulos = df['title'].tolist()
        seleccion = st.multiselect("Seleccione exactamente 2 artículos para comparar:", options=titulos, max_selections=2)
        
        if len(seleccion) == 2:
            # Extraer abstracts
            abs1 = df[df['title'] == seleccion[0]]['summary'].values[0]
            abs2 = df[df['title'] == seleccion[1]]['summary'].values[0]
            
            # Actualizamos las importaciones con los nuevos algoritmos
            from src.similarity import (similitud_jaccard, similitud_levenshtein, 
                                      similitud_coseno_tfidf, similitud_sbert,
                                      similitud_dice_ngramas, similitud_ia_segunda)
            
            st.subheader("Resultados de Similitud")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📚 Clásicos y N-Gramas")
                st.write(f"**Jaccard:** {similitud_jaccard(abs1, abs2):.4f}")
                st.write(f"**Levenshtein:** {similitud_levenshtein(abs1, abs2):.4f}")
                st.write(f"**Dice (N-Gramas):** {similitud_dice_ngramas(abs1, abs2):.4f}")
                st.write(f"**Coseno TF-IDF:** {similitud_coseno_tfidf(abs1, abs2):.4f}")
            
            with col2:
                st.markdown("### 🤖 Inteligencia Artificial")
                st.write(f"**SBERT (MiniLM):** {similitud_sbert(abs1, abs2):.4f}")
                st.write(f"**DistilBERT (Pro Multilingüe):** {similitud_ia_segunda(abs1, abs2):.4f}")
                
                # Cálculo de promedio de IA para una métrica final
                promedio_ia = (similitud_sbert(abs1, abs2) + similitud_ia_segunda(abs1, abs2)) / 2
                st.metric("Similitud Semántica Promedio", f"{promedio_ia:.4f}")
            
            with st.expander("Ver contenido de los abstracts"):
                st.info(f"**Doc 1:** {abs1}")
                st.warning(f"**Doc 2:** {abs2}")
    else:
        st.error("Por favor, ejecute primero el Requerimiento 1.")
        
elif menu == "Req 3: Análisis de Categorías":
    st.header("📊 Análisis de Conceptos y Categorías")
    
    ruta = 'data/processed/unificado.csv'
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        
        from src.analysis import analizar_conceptos_y_categorias
        
        # Procesar los datos
        df_procesado, top_palabras = analizar_conceptos_y_categorias(df)
        
        # --- Visualización 1: Gráfico de Barras ---
        st.subheader("Top 10 Conceptos más frecuentes")
        df_freq = pd.DataFrame(top_palabras, columns=['Concepto', 'Repeticiones'])
        st.bar_chart(df_freq.set_index('Concepto'))
        
        # --- Visualización 2: Categorización ---
        st.subheader("Distribución por Categoría")
        conteo_edu = df_procesado['is_education'].value_counts()
        
        # Renombrar para que se vea bonito
        conteo_edu.index = ['Educación' if x else 'Otros Temas (IA General)' for x in conteo_edu.index]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("Conteo de artículos:")
            st.write(conteo_edu)
        with col2:
            # Gráfico de pastel (pie chart) simple de Streamlit
            st.info(f"El {conteo_edu.get('Educación', 0) / len(df) * 100:.1f}% de los artículos son del área educativa.")

        # --- Tabla de resultados ---
        with st.expander("Ver artículos clasificados como Educación"):
            st.dataframe(df_procesado[df_procesado['is_education'] == True][['title', 'authors']])
            
    else:
        st.error("⚠️ No hay datos. Por favor, ejecuta primero el Requerimiento 1.")
        



elif menu == "Req 4: Clustering Jerárquico":
    st.header("🧬 Laboratorio de Clustering de IA")
    
    ruta = 'data/processed/unificado.csv'
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        from src.clustering import generar_analisis_clusters
        Z, titulos, resultados = generar_analisis_clusters(df)

        # Creamos 3 pestañas para que se vea un análisis por cada uno
        tab1, tab2, tab3 = st.tabs(["🌳 Jerárquico", "🎯 K-Means", "📊 Comparativa"])

        with tab1:
            st.subheader("Dendrograma de Similitud")
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            from scipy.cluster.hierarchy import dendrogram
            dendrogram(Z, labels=[t[:30] for t in titulos], orientation='left', ax=ax1)
            st.pyplot(fig1)
            st.info(f"Asertividad: {((resultados['Jerárquico']['score'] + 1) / 2 * 100):.1f}%")

        with tab2:
            st.subheader("Distribución de Grupos K-Means")
            # Como no podemos ver 100 dimensiones, mostramos cuántos artículos hay por grupo
            conteo_k = pd.Series(resultados['K-Means']['labels']).value_counts()
            st.bar_chart(conteo_k)
            st.write("Esta gráfica de barras muestra el tamaño de los 3 grupos detectados.")
            st.info(f"Asertividad: {((resultados['K-Means']['score'] + 1) / 2 * 100):.1f}%")

        with tab3:
            st.subheader("Tabla de Asertividad Comparada")
            # Aquí pones la tabla que compara los tres
            df_comp = pd.DataFrame({
                "Artículo": titulos,
                "K-Means": resultados['K-Means']['labels'],
                "DBSCAN": resultados['DBSCAN']['labels']
            })
            st.dataframe(df_comp)
    else:
        st.error("Primero ejecuta el Requerimiento 1.")
        



elif menu == "Req 5: Visualización":
    st.header("📈 Dashboard de Resultados Bibliométricos")
    
    ruta = 'data/processed/unificado.csv'
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        
        # --- FILA 1: Métricas rápidas ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Artículos Procesados", len(df))
        col2.metric("Autores Únicos", df['authors'].nunique())
        col3.metric("Palabras clave detectadas", "+50")
        
        # --- FILA 2: Nube de Palabras ---
        st.subheader("☁️ Nube de Conceptos (WordCloud)")
        from src.visualizer import generar_nube_palabras
        
        wc = generar_nube_palabras(df)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        
        # --- FILA 3: Buscador Dinámico ---
        st.subheader("🔍 Buscador de Artículos")
        busqueda = st.text_input("Filtrar por palabra clave (ej. 'ethics', 'student', 'transform'):")
        
        if busqueda:
            resultado = df[df['summary'].str.contains(busqueda, case=False, na=False)]
            st.write(f"Se encontraron {len(resultado)} artículos:")
            st.dataframe(resultado[['title', 'authors', 'url']])
        else:
            st.write("Mostrando todos los registros:")
            st.dataframe(df[['title', 'authors', 'url']])
            
    else:
        st.error("Primero ejecuta el Requerimiento 1 para tener datos que visualizar.")