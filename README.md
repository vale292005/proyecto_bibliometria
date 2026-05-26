# 📊 Sistema Automatizado de Inteligencia Bibliométrica para IA Generativa

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E.svg)
![Selenium](https://img.shields.io/badge/Selenium-43B02A.svg)

Una plataforma científica end-to-end encargada de automatizar la extracción, el procesamiento de lenguaje natural (NLP) y el clustering inteligente de literatura científica indexada en **EBSCO** y **ScienceDirect** enfocada en Inteligencia Artificial Generativa.

---

## 💡 ¿Qué resuelve este proyecto?
La investigación del estado del arte suele tomar semanas de lectura y clasificación manual. Este software reduce ese tiempo a minutos mediante un ecosistema dividido en tres capas autónomas:
1. **Robótica de Extracción:** Un agente automatizado de Selenium navega, realiza búsquedas complejas y unifica la metadata descargada.
2. **Cerebro Analítico (IA):** Modela el texto de los resúmenes mediante **TF-IDF (con bigramas)** y ejecuta algoritmos de Machine Learning no supervisado para segmentar las tendencias de investigación.
3. **Dashboard Interactivo:** Despliega una interfaz en Streamlit con mapas tridimensionales, nubes de palabras depuradas y exportación de reportes ejecutivos en PDF.

---

## 🛠️ Arquitectura de la Inteligencia Artificial y Algoritmos

El core analítico del proyecto procesa los textos de los resúmenes utilizando la siguiente suite tecnológica:

### 🌟 Procesamiento de Lenguaje Natural (NLP)
* **NLTK (Natural Language Toolkit):** Tokenización y filtrado automático de conectores idiomáticos (*stopwords*) en inglés y español, expandido con un escudo de exclusión para jergas metodológicas (*"study", "research", "paper"*).
* **TF-IDF Vectorizer (Scikit-Learn):** Transforma el texto limpio en matrices matemáticas de pesos vectoriales. Configurado con `ngram_range=(1,2)` para preservar el contexto de palabras compuestas (ej: *"machine learning"*, *"generative ai"*).

### 🤖 Modelos de Clustering (Aprendizaje No Supervisado)
El sistema compara simultáneamente tres enfoques geométricos para clasificar la producción científica:
* **K-Means Clustering:** Segmentación particional que agrupa los textos en un número óptimo ($K=3$) de centros conceptuales latentes.
* **Clustering Jerárquico Aglomerativo (Método Ward):** Construye un árbol filogenético de los abstracts (**Dendrograma**) uniendo los artículos más cercanos de forma orgánica.
* **DBSCAN (Basado en Densidad):** Emplea **Similitud de Coseno** para agrupar documentos por densidad léxica. Clasifica automáticamente los abstracts sumamente aislados o atípicos como **Ruido (`-1`)**, garantizando clústeres puros.

> 📊 **Validación Científica:** La precisión de cada clúster se autoevalúa en tiempo real empleando la métrica matemática de **Silhouette Score**, midiendo el nivel de cohesión interna y separación entre temáticas.

---

## 📁 Estructura del Proyecto

```text
├── data/
│   ├── descargas_ebsco/   # Almacenamiento temporal de archivos .csv y .bib
│   └── processed/         # Dataset consolidado final (unificado.csv)
├── src/
│   ├── scraper.py         # Robot de Selenium optimizado para bases de datos
│   ├── clustering.py      # Pipelines de IA, Vectorización, K-Means y DBSCAN
│   └── visualizer.py      # Motor de gráficos (Plotly, Seaborn) y reportes FPDF
├── app.py                 # Aplicación principal y frontend de Streamlit
├── requirements.txt       # Librerías y dependencias del sistema
└── README.md              # Documentación técnica
