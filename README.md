# Buscador de Ofertas - MercadoLibre

Este proyecto es una aplicación de escritorio en Python que permite buscar productos en MercadoLibre, mostrar los precios más bajos, comparar historial de precios y guardar favoritos.

---

## Características

- Búsqueda de productos con scraping en MercadoLibre.
- Muestra el top 3 de ofertas con imagen, precio y enlace.
- Guarda historial de precios para ver subidas o bajadas.
- Permite agregar y administrar favoritos.
- Interfaz gráfica con `ttkbootstrap` y `tkinter`.
- Ejecutable standalone para Windows (sin necesidad de instalar Python).

---

## Requisitos

- Windows (probado en Windows 10/11)
- [ChromeDriver](https://sites.google.com/chromium.org/driver/) compatible con tu versión de Google Chrome
- Python 3.11+ (solo si querés correr desde código fuente)

---

## Instalación y uso desde código fuente

1. Clona este repositorio:
   ```bash
   git clone https://github.com/AxelPintos95cs/MLbot
   cd MLbot

2. Instala las dependencias:
    pip install -r requirements.txt

3. Ejecuta la app:
    python mercado_comparison.py


## Creación de ejecutable 

1. Ejecuta el archivo crear_ejecutable.bat con permisos de administrador

2. Se generará una carpeta llamada "dist" y dentro el archivo .exe para utilizar el ejecutable

3. Enjoy!