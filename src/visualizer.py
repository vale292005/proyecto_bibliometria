import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from wordcloud import WordCloud
from fpdf import FPDF
import plotly.express as px

def generar_nube_palabras(df):
    # 1. Unimos y pasamos a minúsculas
    texto = " ".join(df['summary'].astype(str).str.lower())
    
    # 2. Lista extendida de conectores rebeldes (Stopwords)
    stopwords_manual = {
        'of', 'on', 'in', 'it', 'the', 'and', 'for', 'with', 'that', 'this', 'from', 
        'was', 'were', 'been', 'has', 'have', 'had', 'but', 'not', 'are', 'is', 'an', 
        'as', 'at', 'by', 'to', 'or', 'so', 'if', 'be', 'about', 'which', 'who',
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'e', 'ni', 'o', 
        'u', 'pero', 'con', 'sin', 'sobre', 'para', 'por', 'del', 'al', 'que', 'son'
    }
    
    # 3. Filtros académicos que suelen estorbar
    filtros_academicos = {'study', 'research', 'paper', 'results', 'ai', 'intelligence', 'artificial'}
    todas_las_stopwords = stopwords_manual.union(filtros_academicos)

    # 4. LIMPIEZA MANUAL: Eliminamos palabras de 2 o menos letras y stopwords
    palabras = re.findall(r'\b\w{3,}\b', texto)
    texto_limpio = " ".join([w for w in palabras if w not in todas_las_stopwords])

    # 5. Generar la nube con el texto ya filtrado
    wc = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        colormap='viridis',
        max_words=100,
        stopwords=todas_las_stopwords
    ).generate(texto_limpio)
    
    return wc


def generar_mapa_calor_geo(df):
    # 1. Diccionario SUPER EXPANDIDO de detección
    diccionario_paises = {
        'USA': ['usa', 'united states', 'america', 'california', 'new york', 'harvard', 'mit', 'stanford', 'florida', 'texas'],
        'China': ['china', 'beijing', 'shanghai', 'tsinghua', 'zhejiang', 'wuhan'],
        'United Kingdom': ['uk', 'united kingdom', 'london', 'oxford', 'cambridge', 'manchester', 'scotland'],
        'Spain': ['spain', 'españa', 'madrid', 'barcelona', 'valencia', 'sevilla', 'granada'],
        'Colombia': ['colombia', 'bogota', 'medellin', 'cali', 'barranquilla', 'antioquia', 'uniandes'],
        'Mexico': ['mexico', 'méxico', 'unam', 'monterrey', 'guadalajara', 'puebla'],
        'Brazil': ['brazil', 'brasil', 'sao paulo', 'rio de janeiro', 'campinas'],
        'Germany': ['germany', 'deutschland', 'berlin', 'munich', 'hamburg', 'fraunhofer'],
        'France': ['france', 'paris', 'lyon', 'marseille', 'cnrs'],
        'Italy': ['italy', 'italia', 'roma', 'milan', 'napoli'],
        'Canada': ['canada', 'toronto', 'vancouver', 'montreal', 'mcgill'],
        'Australia': ['australia', 'sydney', 'melbourne', 'queensland']
    }

    def buscar_pais(texto):
        if pd.isna(texto): return None
        texto = str(texto).lower()
        for pais, variantes in diccionario_paises.items():
            for variante in variantes:
                if variante in texto:
                    return pais
        return None

    # 2. Aplicar la búsqueda
    df['country'] = df['authors'].astype(str).apply(buscar_pais)
    
    # 3. Rastreo secundario en el summary
    mask_vacio = df['country'].isnull()
    if mask_vacio.any():
        df.loc[mask_vacio, 'country'] = df.loc[mask_vacio, 'summary'].astype(str).apply(buscar_pais)

    # 4. Validar resultados
    conteo = df['country'].value_counts().reset_index()
    conteo.columns = ['País', 'Artículos']

    if conteo.empty:
        return None

    # 5. Crear el Mapa Mundial Interactivo para Streamlit
    fig = px.choropleth(
        conteo,
        locations="País",
        locationmode="country names",
        color="Artículos",
        hover_name="País",
        color_continuous_scale="Viridis",
        title="Distribución Geográfica de la Producción Científica"
    )
    
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    return fig


def _generar_grafico_paises_estatico(df):
    """Función auxiliar interna encargada de generar un gráfico de barras compatible con el PDF"""
    if 'country' not in df.columns or df['country'].isnull().all():
        return None
        
    conteo = df['country'].value_counts().reset_index()
    conteo.columns = ['País', 'Artículos']
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=conteo.head(10), x='Artículos', y='País', palette='viridis', ax=ax)
    ax.set_title("Top Países con Mayor Producción Científica")
    plt.tight_layout()
    return fig


def generar_linea_temporal(df):
    # 1. Limpieza de fechas
    if 'published' in df.columns:
        df['published'] = df['published'].astype(str).str.strip()
        df['year_plot'] = pd.to_datetime(df['published'], errors='coerce').dt.year
        
        # Intento de extracción por expresión regular si falla la conversión estándar
        if df['year_plot'].isnull().all() or (df['year_plot'] == 1970).all():
            df['year_plot'] = df['published'].str.extract(r'(\d{4})').astype(float)
    else:
        df['year_plot'] = 2024

    # 2. Filtrar fechas fantasma o inválidas
    df_temp = df[df['year_plot'].notnull() & (df['year_plot'] > 1900)].copy()

    if df_temp.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No se encontraron fechas válidas en 'published'", ha='center')
        return fig

    # 3. Identificar fuente
    col_revista = 'journal' if 'journal' in df.columns else 'source'
    if col_revista not in df_temp.columns:
        df_temp[col_revista] = 'Fuente Externa'

    # 4. Agrupar y graficar
    try:
        timeline = df_temp.groupby(['year_plot', col_revista]).size().unstack(fill_value=0)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        timeline.plot(kind='line', marker='o', ax=ax)
        
        ax.set_title("Evolución de Publicaciones por Año")
        ax.set_xlabel("Año")
        ax.set_ylabel("Cantidad de Artículos")
        
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        plt.legend(title="Revista/Fuente", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        return fig
    except Exception as e:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"Error en gráfico: {e}", ha='center')
        return fig


def exportar_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- Página 1: Título y Nube ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 20, "Reporte Bibliométrico de IA", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Nube de Palabras Clave", ln=True)
    pdf.ln(5)
    
    # Guardar WordCloud temporalmente
    wc = generar_nube_palabras(df)
    wc.to_file("temp_wc.png")
    pdf.image("temp_wc.png", x=15, y=55, w=180)
    
    # --- Página 2: Geografía (Resuelto con gráfico estático) ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Distribución Geográfica", ln=True)
    pdf.ln(5)
    
    fig_geo_estatico = _generar_grafico_paises_estatico(df)
    if fig_geo_estatico:
        fig_geo_estatico.savefig("temp_geo.png", dpi=300)
        pdf.image("temp_geo.png", x=15, y=35, w=180)
        plt.close(fig_geo_estatico)
    else:
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, "No se encontraron datos geográficos suficientes.", ln=True)
    
    # --- Página 3: Línea Temporal ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Evolución Temporal", ln=True)
    pdf.ln(5)
    
    fig_time = generar_linea_temporal(df)
    fig_time.savefig("temp_time.png", dpi=300)
    pdf.image("temp_time.png", x=15, y=35, w=180)
    plt.close(fig_time)
    
    ruta_pdf = "Reporte_Final_IA.pdf"
    pdf.output(ruta_pdf)
    
    # Limpiar archivos temporales de forma segura
    for f in ["temp_wc.png", "temp_geo.png", "temp_time.png"]:
        if os.path.exists(f): 
            os.remove(f)
        
    return ruta_pdf