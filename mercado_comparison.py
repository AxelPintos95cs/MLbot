from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import io
import requests
import webbrowser

def buscar_publicaciones(consulta, limite=20):
    consulta = consulta.replace(" ", "-")
    url = f"https://listado.mercadolibre.com.ar/{consulta}"

    options = Options()
    options.add_argument("--headless=new")  # Modo headless para no mostrar ventana
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        # Esperar a que carguen los items (nuevo selector para MercadoLibre)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-layout__item"))
        )
    except Exception as e:
        print("Timeout esperando resultados:", e)
        driver.quit()
        return []

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    publicaciones = []

    items = soup.select("li.ui-search-layout__item")[:limite]

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



    return publicaciones

def encontrar_mas_barato(publicaciones):
    if not publicaciones:
        return None
    return min(publicaciones, key=lambda x: x["precio"])

def mostrar_popup(pub):
    if pub is None:
        messagebox.showerror("Sin resultados", "No se encontraron publicaciones.")
        return

    root = tk.Tk()
    root.title("Oferta más barata encontrada")
    root.configure(padx=10, pady=10)

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
        image.thumbnail((200, 200), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)
        img_label = ttk.Label(root, image=photo)
        img_label.image = photo
        img_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

    title_label = ttk.Label(root, text=pub["titulo"], wraplength=300, font=("Arial", 11, "bold"))
    title_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

    price_label = ttk.Label(root, text=f"Precio: ${pub['precio']}", font=("Arial", 10))
    price_label.grid(row=2, column=0, sticky="w")

    def abrir_link():
        webbrowser.open(pub["link"])

    btn = ttk.Button(root, text="Ver en MercadoLibre", command=abrir_link)
    btn.grid(row=2, column=1, padx=(10, 0))

    close_btn = ttk.Button(root, text="Cerrar", command=root.destroy)
    close_btn.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    root.resizable(False, False)
    root.mainloop()

def main():
    producto = input("Ingresá el nombre del producto que querés buscar: ")
    publicaciones = buscar_publicaciones(producto, limite=20)

    if not publicaciones:
        print("No se encontraron resultados.")
        return

    mas_barato = encontrar_mas_barato(publicaciones)
    mostrar_popup(mas_barato)

if __name__ == "__main__":
    main()
