import os
import re
import unicodedata
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Cargar variables del entorno desde .env
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")


def quitar_tildes(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return str(texto)


def obtener_especificaciones(producto, api_key):
    query = f"{producto} especificaciones tecnicas"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "hl": "es"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" in results:
        for result in results["organic_results"]:
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            if snippet and link:
                return f"{snippet}\n\n{link}"

        # Si no hay snippet pero sí link, lo mostramos igual
        primer_link = results["organic_results"][0].get("link", "")
        if primer_link:
            return f"No encontré un resumen, pero podés ver más información en: {primer_link}"

    return "No pude encontrar las especificaciones técnicas para ese producto."


def responder_pregunta(pregunta, api_key):
    pregunta_limpia = quitar_tildes(pregunta.lower())
    pregunta_limpia = re.sub(r"[¿?]", "", pregunta_limpia).strip()

    palabras_clave = ["especificaciones", "caracteristicas", "detalles", "ficha tecnica", "specs"]
    if any(palabra in pregunta_limpia for palabra in palabras_clave):
        patron = r"(especificaciones|caracteristicas|detalles|ficha tecnica|specs)"
        producto = re.sub(patron, "", pregunta_limpia).strip()
        if not producto:
            return "Por favor dime el producto sobre el que quieres las especificaciones técnicas."
        return obtener_especificaciones(producto, api_key)

    return ("Podés preguntarme por las especificaciones técnicas de un producto, "
            "por ejemplo: 'Dame las especificaciones del Galaxy S23'.")


# Solo para pruebas desde terminal
if __name__ == "__main__":
    print("Escribe 'salir' para terminar")
    while True:
        entrada = input("🧑‍💻 ")
        if entrada.lower() in ["salir", "exit", "quit"]:
            print("🤖 ¡Hasta luego!")
            break
        respuesta = responder_pregunta(entrada, API_KEY)
        print("🤖", respuesta)
