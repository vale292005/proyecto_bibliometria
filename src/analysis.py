import pandas as pd
from collections import Counter
import re

def analizar_conceptos_y_categorias(df):
    # 1. Categorización
    palabras_edu = ['education', 'learning', 'teaching', 'student', 'university', 'academic', 'classroom', 'pedagogy', 'teacher']
    pattern = '|'.join(palabras_edu)
    
    # Creamos la columna de educación
    df['is_education'] = df['summary'].str.lower().str.contains(pattern, na=False)
    
    # 2. Análisis de Frecuencia
    texto_completo = " ".join(df['summary'].astype(str).str.lower())
    # Filtramos palabras de más de 5 letras para evitar conectores (the, and, with...)
    palabras = re.findall(r'\b\w{6,}\b', texto_completo)
    
    # Contamos las 10 más comunes
    frecuencia = Counter(palabras).most_common(10)
    
    return df, frecuencia