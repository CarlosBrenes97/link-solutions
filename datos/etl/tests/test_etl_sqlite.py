"""
Prueba del ETL sin Azure ni nopCommerce: usa SQLite como Data Warehouse y los CSV generados.

    cd datos
    python generador/generar_datos.py --salida /tmp/datos_prueba
    DATA_DIR=/tmp/datos_prueba python -m pytest etl/tests -q      (o: python etl/tests/test_etl_sqlite.py)
"""
import os
import sys
import tempfile

import pandas as pd

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
    clientes_sucios = pd.DataFrame([
        {"email": " A@EJEMPLO.COM ", "nombre": "A", "tipo_cliente": None,
         "provincia": "San José", "canal_adquisicion": "Correo", "fecha_registro": "2026-01-01"},
        {"email": "a@ejemplo.com", "nombre": "Duplicado", "tipo_cliente": None,
         "provincia": "San José", "canal_adquisicion": "Correo", "fecha_registro": "fecha inválida"},
        {"email": None, "nombre": "Sin correo", "tipo_cliente": None,
         "provincia": None, "canal_adquisicion": None, "fecha_registro": "2026-01-01"},
    ])
    clientes_limpios = etl.limpiar_clientes(clientes_sucios)
    assert len(clientes_limpios) == 1
    assert clientes_limpios.iloc[0]["email"] == "a@ejemplo.com"

    ventas_sucias = pd.DataFrame([
        {"fecha": "2026-01-01", "producto_sku": "SKU001", "cantidad": 2},
        {"fecha": "fecha inválida", "producto_sku": "SKU001", "cantidad": 1},
        {"fecha": "2026-01-01", "producto_sku": "", "cantidad": 1},
        {"fecha": "2026-01-01", "producto_sku": "SKU001", "cantidad": 0},
    ])
    assert len(etl.limpiar_ventas(ventas_sucias, "prueba")) == 1

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

    # Debe corregir un catálogo existente, no solamente insertar SKU nuevos.
    with eng.begin() as cx:
        cx.execute(text(
            "UPDATE dim_producto SET nombre = 'Nombre viejo', precio_lista = 1 WHERE sku = 'SKU004'"
        ))

    etl.cargar(cfg)
    segunda = contar(eng)
    print(primera)
    assert primera == segunda, "el ETL no es idempotente"
    assert primera["fact_ventas"] > 0 and primera["fact_comentarios"] > 0
    with eng.connect() as cx:
        total = cx.execute(text("SELECT SUM(total_linea) FROM fact_ventas")).scalar()
        producto = cx.execute(text(
            "SELECT nombre, precio_lista FROM dim_producto WHERE sku = 'SKU004'"
        )).one()
    assert total > 0
    assert producto == ("Ajedrez de madera", 14500)


if __name__ == "__main__":
    test_idempotente()
    print("OK")
