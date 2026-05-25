import os
import re
import time
import shutil
import glob
import pandas as pd
import bibtexparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
CARPETA_DESCARGAS = os.path.abspath("data/descargas_ebsco")
CARPETA_PROCESADO = os.path.abspath("data/processed")
CSV_SALIDA        = os.path.join(CARPETA_PROCESADO, "unificado.csv")
ESPERA_DESCARGA   = 60

# Columnas que EBSCO incluye en su CSV exportado
# (los nombres reales pueden variar; el script los detecta automáticamente)
COLUMNAS_RESUMEN  = ["AB", "Abstract", "Resumen", "abstract", "resumen", "AB "]
COLUMNAS_TITULO   = ["TI", "Title", "Título", "title", "TI "]
COLUMNAS_AUTORES  = ["AU", "Author", "Autores", "author", "AU "]
COLUMNAS_ANIO     = ["PY", "Year", "Año", "year", "PY "]
COLUMNAS_DOI      = ["DOI", "doi", "Do"]

def bibtex_to_dataframe(ruta_bib):
    try:
        with open(ruta_bib,encoding='utf-8') as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
        df = pd.DataFrame(bib_database.entries)

        mapping = {
            'title': 'title',
            'author': 'authors',
            'abstract': 'summary',
            'year': 'published',
            'doi': 'url'
        }

        df_out = pd.DataFrame()
        df_out = pd.DataFrame()
        df_out['title'] = df['title'] if 'title' in df.columns else pd.Series()
        df_out['authors'] = df['author'] if 'author' in df.columns else "Sin autor"
        df_out['summary'] = df['abstract'] if 'abstract' in df.columns else "Sin resumen"
        df_out['published'] = df['year'] if 'year' in df.columns else "2024"
        df_out['url'] = df['doi'].apply(lambda d: f"https://doi.org/{d}" if pd.notnull(d) else "")

        return df_out
    except Exception as e:
       print(f"   ⚠️ Error procesando BibTeX: {e}")
       return pd.DataFrame()
    
def clic_boton_exportar(driver):
    selectores = [
        (By.CSS_SELECTOR, "button[data-auto='export-all-link']"), # Por el nombre que me diste
        (By.CLASS_NAME, "export-all-link-text"), 
        (By.XPATH, "//span[contains(text(), 'Export')]"),
        (By.XPATH, "//button[.//span[contains(text(), 'Export')]]")
    ]
    el = encontrar_elemento(driver, selectores, timeout=10)
    if el:
        try:
            clic_js(driver, el)
            print("   ✅ Botón 'Export' pulsado.")
            return True
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
    return False

def manejar_modal_export(driver):
    print("   ⏳ Esperando modal de exportación...")
    time.sleep(2)
    
    # Según tu captura, el modal tiene opciones como "Export citation to BibTeX"
    selectores_bibtex = [
        (By.XPATH, "//button[contains(text(), 'BibTeX')]"),
        (By.XPATH, "//span[contains(text(), 'BibTeX')]"),
        (By.PARTIAL_LINK_TEXT, "BibTeX")
    ]
    
    el = encontrar_elemento(driver, selectores_bibtex, timeout=8)
    if el:
        try:
            clic_js(driver, el)
            print("   ✅ Opción BibTeX seleccionada.")
            return True
        except Exception as e:
            print(f"   ⚠️ Error al seleccionar formato: {e}")
    return False

def configurar_driver(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    prefs = {
        "download.default_directory":                                carpeta,
        "download.prompt_for_download":                              False,
        "download.directory_upgrade":                                True,
        "plugins.always_open_pdf_externally":                        True,
        "profile.default_content_settings.popups":                   0,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "safebrowsing.enabled":                                      True,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )


def esperar_descarga(carpeta, antes, timeout=ESPERA_DESCARGA):
    fin = time.time() + timeout
    while time.time() < fin:
        ahora  = {f for f in os.listdir(carpeta)
                  if not f.endswith(".crdownload") and not f.endswith(".tmp")}
        nuevos = ahora - antes
        if nuevos:
            return os.path.join(carpeta, sorted(nuevos)[-1])
        time.sleep(0.8)
    return None


def clic_js(driver, elemento):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elemento)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", elemento)


def encontrar_elemento(driver, selectores, timeout=8):
    for by, sel in selectores:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
            return el
        except Exception:
            continue
    return None


def diagnosticar(driver):
    elementos = driver.find_elements(By.CSS_SELECTOR, "[data-auto]")
    vistos = set()
    print("\n  🔍 data-auto disponibles:")
    for el in elementos:
        val = el.get_attribute("data-auto")
        tag = el.tag_name
        if val and val not in vistos:
            vistos.add(val)
            print(f"     <{tag}> data-auto='{val}'")
    print()


# ══════════════════════════════════════════════════════════
# PASOS DE SELECCIÓN Y DESCARGA
# ══════════════════════════════════════════════════════════

def seleccionar_todos(driver):
    selectores = [
        (By.CSS_SELECTOR, "input[data-auto='bulk-record-checkbox']"),  # ✅ confirmado
        (By.CSS_SELECTOR, "input[aria-label*='Seleccionar todos']"),
        (By.CSS_SELECTOR, "input[aria-label*='Select all']"),
        (By.XPATH,        "//input[@type='checkbox' and contains(@aria-label,'Seleccionar todos')]"),
    ]
    el = encontrar_elemento(driver, selectores, timeout=8)
    if el:
        try:
            if not el.is_selected():
                clic_js(driver, el)
                time.sleep(1.2)
            print("   ✅ Checkbox 'Seleccionar todos' marcado.")
            return True
        except Exception as e:
            print(f"   ⚠️  Error checkbox: {e}")
    else:
        print("   ❌ Checkbox no encontrado.")
    return False


def clic_boton_descargar(driver):
    selectores = [
        (By.CSS_SELECTOR, ".export-all-link-text"), 
        (By.XPATH, "//span[contains(text(), 'Export')]"),
        (By.CSS_SELECTOR, "button[data-auto='toolbar-download-button']"),
        (By.CSS_SELECTOR, "button[data-auto='download-button']"),
        (By.CSS_SELECTOR, "button[data-auto='bulk-download']"),
        (By.CSS_SELECTOR, "button[data-auto='download']"),
        (By.CSS_SELECTOR, "button[data-auto='toolbar-download']"),
        (By.CSS_SELECTOR, "button[aria-label='Descargar']"),
        (By.CSS_SELECTOR, "button[aria-label='Download']"),
        (By.CSS_SELECTOR, "button[aria-label*='escargar']"),
        (By.XPATH,        "//button[normalize-space(.)='Descargar']"),
        (By.XPATH,        "//button[normalize-space(.)='Download']"),
        (By.XPATH,        "//button[.//*[local-name()='title' and contains(text(),'escargar')]]"),
        (By.XPATH,        "(//div[contains(@class,'toolbar') or contains(@class,'bulk')]//button)[2]"),
    ]
    el = encontrar_elemento(driver, selectores, timeout=6)
    if el:
        try:
            clic_js(driver, el)
            print("   ✅ Botón Descargar pulsado.")
            return True
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
    else:
        print("   ❌ Botón Descargar no encontrado.")
        diagnosticar(driver)
    return False


def manejar_modal_csv(driver):
    """
    En el modal de EBSCO selecciona formato CSV.
    En el modal de ScienceDirect selecciona BibTeX (que dispara la descarga directa).
    """
    print("   ⏳ Esperando modal...")
    time.sleep(3)

    # Esperar modal
    for sel in ["[role='dialog']", ".modal", "[class*='modal']", ".modal-content"]:
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            print("   ✅ Modal detectado.")
            break
        except Exception:
            continue

    # ── Seleccionar formato ─────────────────
    selectores_csv = [
        # Prioridad ScienceDirect: el data-aa-button es el ID más seguro de tu HTML
        (By.CSS_SELECTOR, "button[data-aa-button='srp-export-multi-bibtex']"),
        (By.XPATH, "//span[contains(text(), 'BibTeX')]"),
        # Selectores EBSCO originales
        (By.CSS_SELECTOR, "input[type='radio'][value='Csv']"),
        (By.CSS_SELECTOR, "input[type='radio'][value='CSV']"),
        (By.XPATH, "//label[normalize-space(text())='CSV']/preceding-sibling::input"),
        (By.XPATH, "(//input[@type='radio'])[3]"),
    ]

    csv_marcado = False
    for by, sel in selectores_csv:
        try:
            elemento = driver.find_element(by, sel)
            
            # --- CAMBIO CLAVE PARA SCIENCEDIRECT ---
            # Si es un botón (ScienceDirect), el clic inicia la descarga solo.
            if elemento.tag_name == "button" or "button" in elemento.get_attribute("class"):
                clic_js(driver, elemento)
                print("   📊 ScienceDirect: Botón BibTeX pulsado. Descarga iniciada.")
                return True # Salimos aquí porque no hay botón "Confirmar" después
            
            # --- LÓGICA ORIGINAL EBSCO ---
            if elemento.tag_name == "input":
                if not elemento.is_selected():
                    clic_js(driver, elemento)
                print("   📊 Formato CSV seleccionado.")
                csv_marcado = True
                break # Rompemos el bucle para ir abajo al botón de confirmar
        except Exception:
            continue

    # Fallback original si no se marcó nada (EBSCO)
    if not csv_marcado:
        print("   ⚠️  No se pudo seleccionar automáticamente; buscando radios de EBSCO.")
        for by, sel in [(By.XPATH, "(//input[@type='radio'])[1]"), (By.CSS_SELECTOR, "input[type='radio'][value='Pdf']")]:
            try:
                radio = driver.find_element(by, sel)
                if not radio.is_selected(): clic_js(driver, radio)
                break
            except: continue

    time.sleep(0.5)

    # ── Botón "Descargar" (Solo para EBSCO) ─────────────────
    selectores_boton = [
        (By.CSS_SELECTOR, "button[data-auto='confirm-download']"),
        (By.CSS_SELECTOR, "button[data-auto='modal-download']"),
        (By.XPATH, "//button[normalize-space(text())='Descargar']"),
        (By.XPATH, "//button[normalize-space(text())='Download']"),
        (By.XPATH, "(//*[@role='dialog']//button)[last()]"),
    ]
    el = encontrar_elemento(driver, selectores_boton, timeout=6)
    if el:
        try:
            clic_js(driver, el)
            print("   ✅ Confirmado en modal de EBSCO.")
            return True
        except Exception as e:
            print(f"   ⚠️  Error al confirmar: {e}")
    
    return csv_marcado


# ══════════════════════════════════════════════════════════
# PROCESAR CSV DESCARGADO DE EBSCO → unificado.csv
# ══════════════════════════════════════════════════════════

def primera_col(df, candidatas):
    """Devuelve el nombre de la primera columna que exista en el DataFrame."""
    for c in candidatas:
        if c in df.columns:
            return c
    return None


def procesar_csv_ebsco(ruta_csv):
    """
    Lee el CSV exportado por EBSCO y lo normaliza al formato
    usado por app.py: title, authors, summary, published, url, archivo
    """
    # EBSCO puede exportar con distintas codificaciones
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(ruta_csv, encoding=enc, dtype=str)
            break
        except Exception:
            df = None

    if df is None or df.empty:
        print(f"   ⚠️  No se pudo leer {ruta_csv}")
        return pd.DataFrame()

    print(f"   📋 Columnas en CSV EBSCO: {list(df.columns)}")

    col_titulo   = primera_col(df, COLUMNAS_TITULO)
    col_autores  = primera_col(df, COLUMNAS_AUTORES)
    col_resumen  = primera_col(df, COLUMNAS_RESUMEN)
    col_anio     = primera_col(df, COLUMNAS_ANIO)
    col_doi      = primera_col(df, COLUMNAS_DOI)

    def limpiar(col):
        if col and col in df.columns:
            return df[col].fillna("").astype(str).str.strip()
        return pd.Series([""] * len(df))

    df_out = pd.DataFrame({
        "title":     limpiar(col_titulo),
        "authors":   limpiar(col_autores),
        "summary":   limpiar(col_resumen),   # ← abstract completo
        "published": limpiar(col_anio),
        "url":       limpiar(col_doi).apply(
                         lambda d: f"https://doi.org/{d}" if d else ""
                     ),
        "archivo":   ruta_csv,
    })

    # Filtrar filas sin título
    df_out = df_out[df_out["title"].str.len() > 5]

    # Reemplazar "Resumen no disponible" por el resumen real
    df_out["summary"] = df_out["summary"].apply(
        lambda s: s if len(s) > 20 else "Sin resumen en exportación"
    )

    print(f"   ✅ {len(df_out)} registros con resumen extraídos del CSV.")
    return df_out


# ══════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════

def procesar_archivos():
    """Retorna siempre (total: int, repetidos: int)."""
    os.makedirs(CARPETA_PROCESADO, exist_ok=True)
    os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

    driver = configurar_driver(CARPETA_DESCARGAS)
    frames = []   # DataFrames de cada página

    try:
        driver.get("https://library.uniquindio.edu.co/databases")

        print("\n" + "═" * 55)
        print("  DESCARGA MASIVA EBSCO — con resúmenes completos")
        print("═" * 55)
        print("""
INSTRUCCIONES:
  1. En la ventana de Chrome que se abrió, inicia sesión con tus credenciales.
  2. Una vez que pases el login institucional y veas la base de datos abierta, vuelve aquí.
  3. Presiona ENTER. El script buscará el término de IA automáticamente.
""")
        input(">>> PRESIONA [ENTER] CUANDO HAYAS INICIADO SESIÓN <<<\n")

        print("Detectando página y comenzando proceso...")
        time.sleep(3)

        url_actual = driver.current_url.lower()
        termino_busqueda = "generative artificial intelligence"

        if "sciencedirect" in url_actual or "elsevier" in url_actual:
            print("  🚀 Modo ScienceDirect activado.")
            selectores_caja = [
                (By.CSS_SELECTOR, "input[name='qs']"),
                (By.ID,"qs")
            ]
            selectores_buscar = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CLASS_NAME, "search-submit-button")
            ]

            caja = encontrar_elemento(driver, selectores_caja, timeout=10)
            if caja:
                caja.clear()
                caja.send_keys(termino_busqueda)
                btn = encontrar_elemento(driver, selectores_buscar, timeout=5)
                if btn:
                    clic_js(driver, btn)
                    print("  ✅ Búsqueda iniciada en ScienceDirect.")
                    time.sleep(5)
                else:
                    print("  ⚠️  No se encontró botón de búsqueda en ScienceDirect.")
        elif "ebsco" in url_actual:
            print("  🚀 Modo EBSCO activado. Asegúrate de haber hecho tu búsqueda.")

            selectores_caja = [
                (By.ID, "search-input"),
                (By.CSS_SELECTOR, "input#search-input"),
                (By.CSS_SELECTOR, "input.eb-search-autocomplete__input"),
                (By.CSS_SELECTOR, "input[data-auto='search-input-box']"),
                (By.CSS_SELECTOR, "input[aria-label='Búsqueda']")
            ]
            selectores_buscar = [
                (By.CSS_SELECTOR, "button.search-components__search-button"),
                (By.CSS_SELECTOR, "button[aria-label='Buscar']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "button[data-auto='search-submit-button']")
            ]

            caja = encontrar_elemento(driver, selectores_caja, timeout=10)
            if caja:
                caja.clear()
                caja.send_keys(termino_busqueda)
                btn = encontrar_elemento(driver, selectores_buscar, timeout=5)
                if btn:
                    clic_js(driver, btn)
                    print("  ✅ Búsqueda iniciada en EBSCO.")
                    time.sleep(5)
                else:
                    print("  ⚠️  No se encontró botón de búsqueda en EBSCO.")
            else:
                print("  ⚠️  No se encontró caja de búsqueda en EBSCO.")
                print("  Por favor, escribe la búsqueda manualmente en el navegador y continúa.")
                input("  >>> Presiona ENTER cuando los resultados estén cargados <<<")


        pagina_actual = 1

        while True:
            print(f"\n{'─'*50}")
            print(f"  📄 PÁGINA {pagina_actual}")
            print(f"{'─'*50}")

            antes = set(os.listdir(CARPETA_DESCARGAS))

            # 1. Seleccionar todos
            print("\n  [1/3] Seleccionando todos los resultados...")
            if not seleccionar_todos(driver):
                print("  ⚠️  Marca manualmente y presiona ENTER.")
                input("  >>> ENTER <<<\n")

            time.sleep(1)

            # 2. Abrir modal
            print("  [2/3] Abriendo modal de descarga...")
            if not clic_boton_descargar(driver):
                print("  ⚠️  Haz clic en el ícono ⬇ en Chrome y presiona ENTER.")
                input("  >>> ENTER <<<\n")

            # 3. Seleccionar CSV y confirmar
            print("  [3/3] Seleccionando CSV y confirmando...")
            manejar_modal_csv(driver)

            # 4. Esperar archivo CSV
            print(f"\n  ⏳ Esperando archivo (máx {ESPERA_DESCARGA}s)...")
            ruta = esperar_descarga(CARPETA_DESCARGAS, antes)

            if ruta:
                nombre  = f"pagina_{pagina_actual:03d}_{os.path.basename(ruta)}"
                destino = os.path.join(CARPETA_DESCARGAS, nombre)
                try:
                    shutil.move(ruta, destino)
                    ruta = destino
                    print(f"  ✅ Archivo: {nombre}")
                except Exception as e:
                    print(f"  ⚠️  Renombrado fallido: {e}")

                # 5. Procesar CSV descargado
                if ruta.lower().endswith(".csv"):
                    df_pag = procesar_csv_ebsco(ruta)
                    if not df_pag.empty:
                        frames.append(df_pag)
                elif ruta.lower().endswith(".bib"):
                    df_pag = bibtex_to_dataframe(ruta)
                    if not df_pag.empty:
                        frames.append(df_pag)
                else:
                    print(f"  ℹ️  Archivo descargado no es CSV ({os.path.basename(ruta)}). "
                          f"Asegúrate de seleccionar CSV en el modal.")
            else:
                print("  ⚠️  No llegó ningún archivo.")

            # 6. ¿Siguiente página?
            siguiente = None
            for sel in [
                "a[data-auto='next-page']",
                "button[data-auto='next-page']",
                "a[aria-label='Siguiente página']",
                "a[aria-label='Next page']",
            ]:
                try:
                    siguiente = driver.find_element(By.CSS_SELECTOR, sel)
                    break
                except Exception:
                    continue

            if siguiente:
                resp = input(
                    f"\n  ¿Continuar con página {pagina_actual + 1}? [S/n]: "
                ).strip().lower()
                if resp in ("", "s", "si", "sí", "y", "yes"):
                    try:
                        driver.execute_script("arguments[0].click();", siguiente)
                        time.sleep(2.5)
                        pagina_actual += 1
                        continue
                    except Exception:
                        print("  ⚠️  No se pudo ir a la siguiente página.")
            else:
                print("  ℹ️  No se detectó botón 'Siguiente'.")

            resp2 = input("\n  ¿Procesar más páginas manualmente? [s/N]: ").strip().lower()
            if resp2 in ("s", "si", "sí", "y", "yes"):
                print("  Navega a la siguiente página en Chrome y presiona ENTER.")
                input("  >>> ENTER <<<\n")
                pagina_actual += 1
            else:
                break

    except Exception as e:
        print(f"\n🔴 Error general: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # ── Unir todos los DataFrames y guardar ─────────────────────────────────
    if not frames:
        # Intentar procesar CSVs que ya estén en la carpeta (por si se descargaron pero no se procesaron)
        csvs_existentes = glob.glob(os.path.join(CARPETA_DESCARGAS, "*.csv"))
        if csvs_existentes:
            print(f"\n  ℹ️  Procesando {len(csvs_existentes)} CSV(s) existentes en la carpeta...")
            for c in sorted(csvs_existentes):
                df_pag = procesar_csv_ebsco(c)
                if not df_pag.empty:
                    frames.append(df_pag)

    if not frames:
        print("\n❌ No se procesaron artículos.")
        return 0, 0

    df_total    = pd.concat(frames, ignore_index=True)
    total       = len(df_total)
    df_dedup    = df_total.drop_duplicates(subset=["title"])
    repetidos   = total - len(df_dedup)

    df_dedup.to_csv(CSV_SALIDA, index=False, encoding="utf-8-sig")

    print(f"\n{'═'*55}")
    print(f"  ✨ PROCESO FINALIZADO")
    print(f"  📊 {total} artículos | {repetidos} duplicados eliminados")
    print(f"  📝 Resúmenes incluidos: "
          f"{(df_dedup['summary'].str.len() > 20).sum()} de {len(df_dedup)}")
    print(f"  📁 CSVs: {CARPETA_DESCARGAS}")
    print(f"  📊 Unificado: {CSV_SALIDA}")
    print(f"{'═'*55}\n")

    return total, repetidos


if __name__ == "__main__":
    procesar_archivos()