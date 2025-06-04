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
            titulo_tag = item.select_one("h2.ui-search-item__title") or item.select_one("span.ui-search-item__group__element")
            titulo = titulo_tag.text.strip() if titulo_tag else "Sin título"

            precio_tag = item.find("span", class_="andes-money-amount__fraction")
            try:
                precio = int(precio_tag.text.replace(".", "")) if precio_tag else None
            except ValueError:
                precio = None

            link_tag = item.find("a", href=True)
            link = link_tag["href"] if link_tag else ""

            img_url = ""
            img_tag = item.select_one("img.ui-search-result-image__element")
            if img_tag:
                img_url = img_tag.get("data-src") or img_tag.get("src") or ""

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

def mostrar_top3_popup(publicaciones):
    if not publicaciones:
        messagebox.showerror("Sin resultados", "No se encontraron publicaciones.")
        return

    publicaciones_ordenadas = sorted(publicaciones, key=lambda x: x["precio"])
    precios_vistos = set()
    top3 = []

    for pub in publicaciones_ordenadas:
        if pub["precio"] not in precios_vistos:
            top3.append(pub)
            precios_vistos.add(pub["precio"])
        if len(top3) == 3:
            break

    if not top3:
        messagebox.showinfo("Sin resultados", "No se encontraron precios distintos.")
        return

    popup = tk.Toplevel()
    popup.title("Top 3 Ofertas Más Baratas")
    popup.configure(padx=10, pady=10)

    for idx, pub in enumerate(top3):
        frame = ttk.Frame(popup, padding=10, relief="ridge")
        frame.grid(row=idx, column=0, pady=5, sticky="nsew")

        img_data = None
        if pub["img_url"]:
            try:
                r = requests.get(pub["img_url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if r.status_code == 200:
                    img_data = r.content
            except Exception:
                img_data = None

        if img_data:
            image = Image.open(io.BytesIO(img_data))
            image.thumbnail((100, 100), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(image)
            img_label = ttk.Label(frame, image=photo)
            img_label.image = photo
            img_label.grid(row=0, column=0, rowspan=3, padx=5)

        title_label = ttk.Label(frame, text=pub["titulo"], wraplength=250, font=("Arial", 10, "bold"))
        title_label.grid(row=0, column=1, sticky="w")

        price_label = ttk.Label(frame, text=f"Precio: ${pub['precio']}", font=("Arial", 10))
        price_label.grid(row=1, column=1, sticky="w")

        def make_open_link(url):
            return lambda: webbrowser.open(url)

        btn = ttk.Button(frame, text="Ver en MercadoLibre", command=make_open_link(pub["link"]))
        btn.grid(row=2, column=1, sticky="w")

    close_btn = ttk.Button(popup, text="Cerrar", command=popup.destroy)
    close_btn.grid(row=3, column=0, pady=(10, 0))

    popup.resizable(False, False)


def buscar_y_mostrar(entry, boton):
    producto = entry.get()
    if not producto.strip():
        messagebox.showwarning("Atención", "Por favor ingresá un nombre de producto.")
        return

    boton.config(state="disabled")
    entry.config(state="disabled")

    def tarea():
        publicaciones = buscar_publicaciones(producto)
        mostrar_top3_popup(publicaciones)
        boton.config(state="normal")
        entry.config(state="normal")

    threading.Thread(target=tarea).start()

def interfaz_principal():
    root = tk.Tk()
    root.title("Buscador de Ofertas - MercadoLibre")
    root.geometry("400x180")
    root.resizable(False, False)

    ttk.Label(root, text="Nombre del producto:", font=("Arial", 12)).pack(pady=(20, 5))

    entry = ttk.Entry(root, width=40, font=("Arial", 11))
    entry.pack(pady=(0, 10))
    entry.focus()

    boton = ttk.Button(root, text="Buscar", command=lambda: buscar_y_mostrar(entry, boton))
    boton.pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    interfaz_principal()
