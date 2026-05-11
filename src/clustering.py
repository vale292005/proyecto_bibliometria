import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt

def generar_clustering_jerarquico(df):
    # 1. Convertir texto a vectores numéricos (TF-IDF)
    # Usamos máximo 50 palabras clave para que el gráfico no sea un caos
    vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
    matrix = vectorizer.fit_transform(df['summary'].astype(str))
    
    # 2. Calcular los "enlaces" (Linkage)
    # Ward minimiza la varianza dentro de los clusters
    Z = linkage(matrix.toarray(), method='ward')
    
    return Z, df['title'].tolist()