import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import io
import requests
import webbrowser
import threading
import time
import sqlite3
from datetime import datetime

DB_NAME = "precios.db"

# --- Base de datos ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS historial_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            titulo TEXT,
            precio INTEGER,
            fecha TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_precio(product_id, titulo, precio):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT precio FROM historial_precios
        WHERE product_id = ?
        ORDER BY fecha DESC LIMIT 1
    """, (product_id,))
    row = c.fetchone()

    if not row or row[0] != precio:
        c.execute("""
            INSERT INTO historial_precios (product_id, titulo, precio, fecha)
            VALUES (?, ?, ?, ?)
        """, (product_id, titulo, precio, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return row[0] if row else None

# --- Scraper ---
def obtener_url_imagen(item):
    img_tag = item.find("img")
    if not img_tag:
        return ""
    for attr in ["data-src", "data-lazy-src", "data-srcset", "src"]:
        url = img_tag.get(attr)
        if url and url.strip():
            if attr == "data-srcset":
                url = url.split(",")[0].split(" ")[0]
            if "pixel" not in url.lower() and "blank" not in url.lower():
                return url.replace("http://", "https://")
    return ""

def extraer_id_desde_url(url):
    partes = url.split("-")
    for parte in partes:
        if parte.startswith("MLA"):
            return parte.split("#")[0]
    return ""

def buscar_publicaciones(consulta, max_paginas=5):
    consulta = consulta.replace(" ", "-")
    publicaciones = []

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)

    for pagina in range(1, max_paginas + 1):
        url = f"https://listado.mercadolibre.com.ar/{consulta}_Desde_{(pagina - 1) * 50 + 1}"
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-layout__item"))
            )
        except Exception:
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("li.ui-search-layout__item")

        for item in items:
            titulo_tag = item.select_one("[class*='ui-search-item__title']") or item.select_one("img[alt]")
            titulo = titulo_tag["alt"].strip() if titulo_tag.name == "img" else titulo_tag.text.strip()

            precio_tag = item.find("span", class_="andes-money-amount__fraction")
            try:
                precio = int(precio_tag.text.replace(".", "")) if precio_tag else None
            except ValueError:
                precio = None

            link_tag = item.find("a", href=True)
            link = link_tag["href"] if link_tag else ""
            product_id = extraer_id_desde_url(link)
            img_url = obtener_url_imagen(item)

            if precio is not None and link:
                publicaciones.append({
                    "titulo": titulo,
                    "precio": precio,
                    "link": link,
                    "img_url": img_url,
                    "product_id": product_id
                })
        time.sleep(1)
    driver.quit()
    return publicaciones

def filtrar_por_palabras_clave(publicaciones, consulta):
    palabras = consulta.lower().split()
    filtradas = []
    for pub in publicaciones:
        titulo = pub["titulo"].lower()
        if all(palabra in titulo for palabra in palabras):
            filtradas.append(pub)
    return filtradas


def mostrar_top3_en_root(publicaciones, frame_resultados, root):
    for widget in frame_resultados.winfo_children():
        widget.destroy()

    if not publicaciones:
        ttk.Label(frame_resultados, text="No se encontraron resultados.", foreground="red").pack(pady=10)
        root.geometry("500x150")
        return

    root.geometry("500x600")

    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS

    publicaciones_ordenadas = sorted(publicaciones, key=lambda x: x["precio"])
    vistos = set()
    top3 = []
    for pub in publicaciones_ordenadas:
        if pub["precio"] not in vistos:
            top3.append(pub)
            vistos.add(pub["precio"])
        if len(top3) == 3:
            break

    for pub in top3:
        frame = ttk.Frame(frame_resultados, padding=10, relief="ridge")
        frame.pack(fill="x", pady=5)

        # Imagen
        img_data = None
        if pub["img_url"]:
            try:
                r = requests.get(pub["img_url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if r.status_code == 200:
                    img_data = r.content
            except Exception:
                pass

        if img_data:
            image = Image.open(io.BytesIO(img_data))
            image.thumbnail((100, 100), resample_filter)
            photo = ImageTk.PhotoImage(image)
            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.grid(row=0, column=0, rowspan=4, padx=5, pady=5)

        # Título y precio
        ttk.Label(frame, text=pub["titulo"], wraplength=250, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text=f"Precio actual: ${pub['precio']}", font=("Arial", 10)).grid(row=1, column=1, sticky="w")

        precio_anterior = guardar_precio(pub["product_id"], pub["titulo"], pub["precio"])
        comparacion = "🆕 Nuevo"
        if precio_anterior is not None:
            if pub['precio'] < precio_anterior:
                comparacion = f"🔻 Bajó (Antes: ${precio_anterior})"
            elif pub['precio'] > precio_anterior:
                comparacion = f"🔺 Subió (Antes: ${precio_anterior})"
            else:
                comparacion = "➖ Igual que antes"
        ttk.Label(frame, text=comparacion, font=("Arial", 9, "italic"), foreground="gray").grid(row=2, column=1, sticky="w")

        ttk.Button(frame, text="Ver en MercadoLibre", command=lambda url=pub["link"]: webbrowser.open(url)).grid(row=3, column=1, sticky="w", pady=(5, 0))

def buscar_y_mostrar(entry, boton, frame_resultados, root):
    producto = entry.get().strip()
    if not producto:
        messagebox.showwarning("Atención", "Por favor ingresá un nombre de producto.")
        return
    boton.config(state="disabled")
    entry.config(state="disabled")

    def tarea():
        publicaciones = buscar_publicaciones(producto)
        publicaciones_filtradas = filtrar_por_palabras_clave(publicaciones, producto)
        mostrar_top3_en_root(publicaciones_filtradas, frame_resultados, root)
        boton.config(state="normal")
        entry.config(state="normal")


    threading.Thread(target=tarea).start()

def interfaz_principal():
    init_db()
    root = tk.Tk()
    root.title("Buscador de Ofertas - MercadoLibre")
    root.geometry("500x150")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use('clam')

    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Nombre del producto:", font=("Arial", 12)).pack(pady=(0, 5))
    entry = ttk.Entry(main_frame, width=40, font=("Arial", 11))
    entry.pack(pady=(0, 10))
    entry.focus()

    frame_resultados = ttk.Frame(main_frame)
    frame_resultados.pack(fill="both", expand=True, pady=(10, 0))

    boton = ttk.Button(main_frame, text="Buscar", command=lambda: buscar_y_mostrar(entry, boton, frame_resultados, root))
    boton.pack(pady=(0, 10))

    root.bind('<Return>', lambda event: buscar_y_mostrar(entry, boton, frame_resultados, root))
    root.mainloop()

if __name__ == "__main__":
    interfaz_principal()