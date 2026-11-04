"""
Prueba del ETL sin Azure ni nopCommerce: usa SQLite como Data Warehouse y los CSV generados.

    cd datos
    python generador/generar_datos.py --salida /tmp/datos_prueba
    DATA_DIR=/tmp/datos_prueba python -m pytest etl/tests -q      (o: python etl/tests/test_etl_sqlite.py)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text  # noqa: E402

import etl  # noqa: E402

# Mismo modelo que sql/01_crear_dw.sql, simplificado para SQLite
DDL = """
CREATE TABLE dim_fecha (fecha_key INTEGER PRIMARY KEY, fecha DATE, anio INT, mes INT, nombre_mes TEXT,
  trimestre INT, dia_semana TEXT, es_fin_semana INT);
CREATE TABLE dim_producto (producto_key INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, nombre TEXT,
  categoria TEXT, precio_lista REAL);
CREATE TABLE dim_cliente (cliente_key INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, nombre TEXT,
  tipo_cliente TEXT, provincia TEXT, canal_adquisicion TEXT, fecha_registro DATE);
CREATE TABLE fact_ventas (venta_key INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id_nop INT, linea_id_nop INT,
  fecha_key INT, producto_key INT, cliente_key INT, cantidad INT, precio_unitario REAL, total_linea REAL,
  origen TEXT);
CREATE TABLE fact_comentarios (comentario_key INTEGER PRIMARY KEY AUTOINCREMENT, comentario_id TEXT UNIQUE,
  fecha_key INT, producto_key INT, cliente_key INT, red_social TEXT, texto TEXT, sentimiento TEXT,
  puntaje_sentimiento REAL);
"""


def contar(eng):
    with eng.connect() as cx:
        return {t: cx.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                for t in ("dim_fecha", "dim_producto", "dim_cliente", "fact_ventas", "fact_comentarios")}


def test_idempotente():
    carpeta = tempfile.mkdtemp()
    ruta = os.path.join(carpeta, "dw.db")
    eng = create_engine(f"sqlite:///{ruta}")
    with eng.begin() as cx:
        for stmt in DDL.split(";"):
            if stmt.strip():
                cx.execute(text(stmt))
    cfg = etl.Config(sql_dw=f"sqlite:///{ruta}", sql_tienda=None, blob_conn=None, blob_contenedor="x",
                     data_dir=os.environ["DATA_DIR"])
    etl.cargar(cfg)
    primera = contar(eng)
    etl.cargar(cfg)
    segunda = contar(eng)
    print(primera)
    assert primera == segunda, "el ETL no es idempotente"
    assert primera["fact_ventas"] > 0 and primera["fact_comentarios"] > 0
    with eng.connect() as cx:
        total = cx.execute(text("SELECT SUM(total_linea) FROM fact_ventas")).scalar()
    assert total > 0


if __name__ == "__main__":
    test_idempotente()
    print("OK")
