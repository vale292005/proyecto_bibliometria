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
    # 1. Vectorización TF-IDF Mejorada
    # Usamos max_features=150 y ngram_range=(1, 2) para capturar palabras sueltas 
    # y combinaciones de dos palabras (ej. "machine learning", "artificial intelligence").
    vectorizer = TfidfVectorizer(max_features=150, stop_words='english', ngram_range=(1, 2))
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
    # Agrupamiento particional estándar (mantenemos los 3 grupos fijos)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels_k = kmeans.fit_predict(matrix)
    score_k = silhouette_score(matrix, labels_k)
    resultados['K-Means'] = {"score": score_k, "labels": labels_k}

    # --- MÉTODO 3: DBSCAN OPTIMIZADO (Para textos) ---
    # Cambiamos la métrica a 'cosine' porque mide el ángulo de los términos y es superior para NLP.
    # Subimos el radio eps a 0.7 para ser más tolerantes y rescatar artículos clasificados como "ruido".
    dbscan = DBSCAN(eps=0.7, min_samples=2, metric='cosine')
    labels_d = dbscan.fit_predict(matrix)
    
    # Manejo de error si DBSCAN no encuentra suficientes grupos o todo es ruido (-1)
    # Exigimos la métrica 'cosine' también en el score para mantener la consistencia matemática
    clusters_unicos = set(labels_d)
    if len(clusters_unicos) > 1 and (len(clusters_unicos) > 2 or -1 not in clusters_unicos):
        score_d = silhouette_score(matrix, labels_d, metric='cosine')
    else:
        score_d = 0.0
        
    resultados['DBSCAN'] = {"score": score_d, "labels": labels_d}

    # Retornamos Z (para el dendrograma), los títulos y el diccionario de IA
    return Z, df['title'].tolist(), resultados