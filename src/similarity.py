import numpy as np
from Levenshtein import distance as lev_dist
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import os

model_ia = SentenceTransformer('all-MiniLM-L6-v2')
# Segundo modelo de IA (más pesado pero muy preciso para semántica)
model_ia_pro = SentenceTransformer('distiluse-base-multilingual-cased-v1')

def similitud_jaccard(texto1,texto2):
    s1 = set(texto1.lower().split())
    s2 = set(texto2.lower().split())
    if not s1 or not s2:return 0.0
    return len(s1.intersection(s2))/len(s1.union(s2))

def similitud_levenshtein(texto1,texto2):
    max_len = max(len(texto1),len(texto2))
    if max_len == 0: return 1.0
    return 1 - (lev_dist(texto1,texto2)/max_len)

def similitud_coseno_tfidf(texto1,texto2):
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([texto1,texto2])
    return cosine_similarity(tfidf[0:1],tfidf[1:2])[0][0]

def distancia_hamming_palabras(texto1,texto2):
    p1,p2 = texto1.lower().split(), texto2.lower().split()
    min_len = min(len(p1),len(p2))
    if min_len == 0: return 0.0 
    coincidencias = sum(1 for i in range(min_len) if p1[i] == p2[i])
    return coincidencias / max(len(p1),len(p2))

def similitud_dice_ngramas(texto1, texto2, n=2):
    """Analiza similitud basada en pares de caracteres (bigramas por defecto)"""
    def get_ngrams(text):
        text = text.lower()
        return set(text[i:i+n] for i in range(len(text)-n+1))
    
    s1, s2 = get_ngrams(texto1), get_ngrams(texto2)
    if not s1 or not s2: return 0.0
    intersection = len(s1.intersection(s2))
    return (2.0 * intersection) / (len(s1) + len(s2))

def similitud_sbert(texto1,texto2):
    embeddings=model_ia.encode([texto1,texto2])
    return cosine_similarity([embeddings[0]],[embeddings[1]])[0][0]

def similitud_ia_pro_multilingue(texto1, texto2):
    """Usa un modelo especializado en múltiples idiomas incluyendo español"""
    embeddings = model_ia_pro.encode([texto1, texto2])
    return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

def similitud_ia_segunda(texto1,texto2):
    return similitud_sbert(texto1,texto2)