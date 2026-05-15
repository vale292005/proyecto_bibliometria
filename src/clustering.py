import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import linkage
import matplotlib.pyplot as plt

def generar_analisis_clusters(df):
    """
    Genera tres modelos de clustering (Jerárquico, K-Means, DBSCAN) 
    y calcula su asertividad mediante el Silhouette Score.
    """
    # 1. Vectorización TF-IDF de los resúmenes
    # Usamos un máximo de 100 términos para balancear precisión y velocidad
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    matrix = vectorizer.fit_transform(df['summary'].astype(str)).toarray()
    
    resultados = {}

    # --- MÉTODO 1: Jerárquico (Ward) ---
    # Calculamos la matriz de enlace para el dendrograma
    Z = linkage(matrix, method='ward')
    
    # Para calcular la asertividad, simulamos una división en 3 grupos
    from scipy.cluster.hierarchy import fcluster
    labels_h = fcluster(Z, t=3, criterion='maxclust')
    score_h = silhouette_score(matrix, labels_h)
    resultados['Jerárquico'] = {"score": score_h, "labels": labels_h}

    # --- MÉTODO 2: K-Means ---
    # Agrupamiento particional estándar
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels_k = kmeans.fit_predict(matrix)
    score_k = silhouette_score(matrix, labels_k)
    resultados['K-Means'] = {"score": score_k, "labels": labels_k}

    # --- MÉTODO 3: DBSCAN ---
    # Agrupamiento basado en densidad
    dbscan = DBSCAN(eps=0.5, min_samples=2)
    labels_d = dbscan.fit_predict(matrix)
    
    # Manejo de error si DBSCAN no encuentra suficientes grupos para la métrica
    if len(set(labels_d)) > 1:
        score_d = silhouette_score(matrix, labels_d)
    else:
        score_d = 0.0
    resultados['DBSCAN'] = {"score": score_d, "labels": labels_d}

    # Retornamos Z (para el dendrograma), los títulos y el diccionario de IA
    return Z, df['title'].tolist(), resultados