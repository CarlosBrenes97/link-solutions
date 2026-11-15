"""
Sentimiento y resumen de comentarios con un modelo de lenguaje (API de Claude).

Para cada producto con comentarios sin clasificar:
  1. Clasifica cada comentario como positivo, neutro o negativo y lo guarda en fact_comentarios.
  2. Escribe un resumen de 3 oraciones y lo guarda en resumen_comentarios (periodo = mes actual).

Solo procesa comentarios NUEVOS (sentimiento NULL), para no pagar dos veces por lo mismo.

Variables de entorno: SQL_DW, ANTHROPIC_API_KEY, MODELO_LLM (opcional, por defecto claude-haiku-5-5; verificar el vigente).
"""
import json
import logging
import os

import pandas as pd
from sqlalchemy import create_engine, text

log = logging.getLogger("resumen")

LOTE = 40
VALIDOS = {"positivo", "neutro", "negativo"}


def cargar_env_local(ruta: str):
    """Carga variables del .env del repositorio sin imprimir secretos."""
    if not os.path.isfile(ruta):
        return
    with open(ruta, encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def analizar_lote(cliente, modelo: str, producto: str, comentarios: list[str]) -> dict:
    """Devuelve {"sentimientos": [...], "resumen": "..."}. Lanza ValueError si la respuesta no es válida."""
    texto = "\n".join(f"{i}. {c}" for i, c in enumerate(comentarios))
    msg = cliente.messages.create(
        model=modelo,
        max_tokens=1500,
        messages=[{"role": "user", "content": (
            f"Producto: {producto}. Comentarios de clientes numerados:\n{texto}\n\n"
            'Responde SOLO con JSON válido, sin texto extra: {"sentimientos": ["positivo|neutro|negativo", ...], '
            f'"resumen": "tres oraciones en español sobre qué opinan los clientes"}}. '
            f"La lista de sentimientos debe tener exactamente {len(comentarios)} elementos, en el mismo orden."
        )}],
    )
    datos = json.loads(msg.content[0].text)
    sentimientos = [str(s).strip().lower() for s in datos["sentimientos"]]
    if len(sentimientos) != len(comentarios) or not set(sentimientos) <= VALIDOS:
        raise ValueError("Respuesta del modelo con formato inesperado")
    resumen = str(datos["resumen"]).strip()
    if not resumen:
        raise ValueError("Respuesta del modelo sin resumen")
    return {"sentimientos": sentimientos, "resumen": resumen}


def main():
    import anthropic

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cargar_env_local(os.path.join(raiz, ".env"))
    cliente = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    modelo = os.environ.get("MODELO_LLM", "claude-haiku-5-5")
    dw = create_engine(os.environ["SQL_DW"])
    periodo = pd.Timestamp.today().strftime("%Y-%m")

    with dw.begin() as cx:
        pend = pd.read_sql(text(
            """
            SELECT c.comentario_key, c.producto_key, p.nombre, c.texto
            FROM fact_comentarios c JOIN dim_producto p ON p.producto_key = c.producto_key
            WHERE c.sentimiento IS NULL
            """), cx)
        log.info("%d comentarios por clasificar", len(pend))
        clasificados = 0
        for producto_key, grupo in pend.groupby("producto_key"):
            nombre = grupo["nombre"].iloc[0]
            resumenes = []
            for i in range(0, len(grupo), LOTE):
                lote = grupo.iloc[i:i + LOTE]
                try:
                    try:
                        r = analizar_lote(cliente, modelo, nombre, lote["texto"].tolist())
                    except (ValueError, KeyError, json.JSONDecodeError):
                        r = analizar_lote(cliente, modelo, nombre, lote["texto"].tolist())  # un reintento
                except Exception:
                    log.exception("Se omite un lote de %s", nombre)
                    continue
                for key, s in zip(lote["comentario_key"], r["sentimientos"]):
                    cx.execute(text("UPDATE fact_comentarios SET sentimiento = :s WHERE comentario_key = :k"),
                               {"s": s, "k": int(key)})
                clasificados += len(lote)
                resumenes.append(r["resumen"])
            if resumenes:
                cx.execute(text("DELETE FROM resumen_comentarios WHERE producto_key = :p AND periodo = :t"),
                           {"p": int(producto_key), "t": periodo})
                cx.execute(text("INSERT INTO resumen_comentarios (producto_key, periodo, resumen) VALUES (:p, :t, :r)"),
                           {"p": int(producto_key), "t": periodo, "r": " ".join(resumenes)})
        log.info("Comentarios clasificados: %d de %d", clasificados, len(pend))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
