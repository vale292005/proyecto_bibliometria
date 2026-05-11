import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def procesar_archivos(busqueda="generative artificial intelligence"):
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    datos = []

    try:
        driver.get("https://library.uniquindio.edu.co/databases")
        print("\n" + "🚀"*10 + " INSTRUCCIONES " + "🚀"*10)
        print("1. Busca tu tema en EBSCO.")
        print("2. Asegúrate de que los resultados carguen en pantalla.")
        print("3. Presiona ENTER aquí.")
        input(">>> ESPERANDO ACCIÓN EN CHROME...")

        # Capturamos los bloques de resultados completos
        # EBSCO organiza cada resultado en una etiqueta 'article' o div con clase específica
        resultados = driver.find_elements(By.CSS_SELECTOR, "div.result-list-item, article, [data-automation='search-result']")

        for res in resultados:
            try:
                # Extraemos el título (suele ser el enlace h3)
                titulo_el = res.find_element(By.TAG_NAME, "h3")
                titulo = titulo_el.text.strip()

                # Extraemos la línea de metadatos (donde están autores y año)
                # Intentamos capturar el texto que sigue al título
                metadatos = res.text.replace(titulo, "").strip()
                
                # Buscamos un año de 4 dígitos (ej: 2023, 2024, 2026) en el texto
                import re
                anio_match = re.search(r'\b(20\d{2})\b', metadatos)
                anio = anio_match.group(1) if anio_match else "2026"

                if len(titulo) > 30:
                    datos.append({
                        "title": titulo,
                        "authors": "EBSCO Source",
                        "summary": titulo[:50] + "...",
                        "published": anio,
                        "url": driver.current_url
                    })
            except:
                continue

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    if not datos:
        return 0, 0

    df = pd.DataFrame(datos)
    os.makedirs('data/processed', exist_ok=True)
    df.drop_duplicates(subset=['title']).to_csv('data/processed/unificado.csv', index=False, encoding='utf-8-sig')
    return len(df), 0