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
                if url.startswith("http://"):
                    url = "https://" + url[len("http://"):]
                return url
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
            titulo_tag = item.select_one("[class*='ui-search-item__title']")
            if not titulo_tag:
                titulo_tag = item.select_one("img[alt]")

            if titulo_tag:
                if titulo_tag.name == "img":
                    titulo = titulo_tag["alt"].strip()
                else:
                    titulo = titulo_tag.text.strip()
            else:
                titulo = "Sin título"

            precio_tag = item.find("span", class_="andes-money-amount__fraction")
            try:
                precio = int(precio_tag.text.replace(".", "")) if precio_tag else None
            except ValueError:
                precio = None

            link_tag = item.find("a", href=True)
            link = link_tag["href"] if link_tag else ""

            img_url = obtener_url_imagen(item)

            if precio is not None and link:
                publicaciones.append({
                    "titulo": titulo,
                    "precio": precio,
                    "link": link,
                    "img_url": img_url
                })

        time.sleep(1)

    driver.quit()
    return publicaciones

def mostrar_top3_en_root(publicaciones, frame_resultados, root):
    for widget in frame_resultados.winfo_children():
        widget.destroy()

    if not publicaciones:
        ttk.Label(frame_resultados, text="No se encontraron resultados.", foreground="red").pack(pady=10)
        return

    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS

    publicaciones_ordenadas = sorted(publicaciones, key=lambda x: x["precio"])
    precios_vistos = set()
    top3 = []

    for pub in publicaciones_ordenadas:
        if pub["precio"] not in precios_vistos:
            top3.append(pub)
            precios_vistos.add(pub["precio"])
        if len(top3) == 3:
            break

    for pub in top3:
        frame = ttk.Frame(frame_resultados, padding=10, relief="ridge")
        frame.pack(fill="x", pady=5)

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
            img_label.grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        title_label = ttk.Label(frame, text=pub["titulo"], wraplength=250, font=("Arial", 10, "bold"))
        title_label.grid(row=0, column=1, sticky="w")

        price_label = ttk.Label(frame, text=f"Precio: ${pub['precio']}", font=("Arial", 10))
        price_label.grid(row=1, column=1, sticky="w")

        btn = ttk.Button(frame, text="Ver en MercadoLibre", command=lambda url=pub["link"]: webbrowser.open(url))
        btn.grid(row=2, column=1, sticky="w", pady=(5, 0))

    root.update_idletasks()
    root.minsize(500, root.winfo_height())

def buscar_y_mostrar(entry, boton, frame_resultados, root):
    producto = entry.get()
    if not producto.strip():
        messagebox.showwarning("Atención", "Por favor ingresá un nombre de producto.")
        return

    boton.config(state="disabled")
    entry.config(state="disabled")

    def tarea():
        publicaciones = buscar_publicaciones(producto)
        mostrar_top3_en_root(publicaciones, frame_resultados, root)
        boton.config(state="normal")
        entry.config(state="normal")

    threading.Thread(target=tarea).start()

def interfaz_principal():
    root = tk.Tk()
    root.title("Buscador de Ofertas - MercadoLibre")
    root.geometry("")
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
