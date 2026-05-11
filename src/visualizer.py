import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd

def generar_nube_palabras(df):
    # Unimos todos los resúmenes
    texto = " ".join(df['summary'].astype(str).str.lower())
    
    # Definimos palabras que no queremos que salgan (Stopwords)
    stopwords = set(['generative', 'artificial', 'intelligence', 'study', 'research', 'paper', 'results'])
    
    # Crear la nube
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='white',
        stopwords=stopwords,
        colormap='viridis'
    ).generate(texto)
    
    return wordcloud