import sqlite3

FAV_DB = "favoritos.db"

def init_favoritos_db():
    conn = sqlite3.connect(FAV_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (
            product_id TEXT PRIMARY KEY,
            titulo TEXT,
            precio INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def agregar_a_favoritos(pub):
    product_id = pub["product_id"].strip()
    print("AGREGANDO A FAVORITOS:", product_id, pub["titulo"], pub["precio"])
    conn = sqlite3.connect(FAV_DB, timeout=10)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO favoritos (product_id, titulo, precio)
            VALUES (?, ?, ?)
        """, (product_id, pub["titulo"], pub["precio"]))
        conn.commit()
    except sqlite3.IntegrityError:
        print("El producto ya está en favoritos, no se agrega de nuevo.")
    finally:
        conn.close()

def obtener_favoritos():
    conn = sqlite3.connect(FAV_DB)
    c = conn.cursor()
    c.execute("SELECT product_id, titulo, precio FROM favoritos ORDER BY titulo")
    resultados = c.fetchall()
    conn.close()
    return resultados

def eliminar_favorito(product_id):
    conn = sqlite3.connect(FAV_DB)
    c = conn.cursor()
    c.execute("DELETE FROM favoritos WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
