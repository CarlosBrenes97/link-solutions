"""Reporte IA Analytics filtrable por fecha para la administración.

Este módulo consulta el Data Warehouse, no modifica la tienda. Su salida es un
JSON que luego podrá consumirse desde una página de Administración. Mientras se
integra la interfaz, se puede demostrar en terminal con:

    python ia\\reportes_ia.py --desde 2025-01-01 --hasta 2025-12-31
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


RAIZ = Path(__file__).resolve().parents[1]


def cargar_env_local(ruta: Path) -> None:
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def validar_rango(desde: str, hasta: str) -> tuple[date, date]:
    inicio = pd.Timestamp(desde).date()
    fin = pd.Timestamp(hasta).date()
    if inicio > fin:
        raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")
    if fin > date.today():
        raise ValueError("La fecha final no puede ser futura.")
    return inicio, fin


def _filas(df: pd.DataFrame) -> list[dict]:
    """Convierte resultados de pandas a JSON simple y redondea números."""
    if df.empty:
        return []
    df = df.where(pd.notnull(df), None).copy()
    for columna in df.select_dtypes(include="number").columns:
        df[columna] = df[columna].round(2)
    return df.to_dict(orient="records")


def crear_reporte(cx, desde: date, hasta: date) -> dict:
    params = {"desde": desde, "hasta": hasta}
    resumen = pd.read_sql(text("""
        SELECT COALESCE(SUM(v.total_linea), 0) AS ingresos,
               COALESCE(SUM(v.cantidad), 0) AS unidades_vendidas,
               COUNT(DISTINCT v.cliente_key) AS clientes_con_compra,
               COUNT(DISTINCT v.pedido_id_nop) AS pedidos
        FROM fact_ventas v JOIN dim_fecha f ON f.fecha_key = v.fecha_key
        WHERE f.fecha BETWEEN :desde AND :hasta
    """), cx, params=params).iloc[0].to_dict()
    productos = pd.read_sql(text("""
        SELECT TOP 5 p.nombre, p.categoria, SUM(v.cantidad) AS unidades,
               SUM(v.total_linea) AS ingresos
        FROM fact_ventas v
        JOIN dim_fecha f ON f.fecha_key = v.fecha_key
        JOIN dim_producto p ON p.producto_key = v.producto_key
        WHERE f.fecha BETWEEN :desde AND :hasta
        GROUP BY p.nombre, p.categoria
        ORDER BY ingresos DESC
    """), cx, params=params)
    baja_rotacion = pd.read_sql(text("""
        SELECT TOP 5 p.nombre, p.categoria, SUM(v.cantidad) AS unidades
        FROM fact_ventas v
        JOIN dim_fecha f ON f.fecha_key = v.fecha_key
        JOIN dim_producto p ON p.producto_key = v.producto_key
        WHERE f.fecha BETWEEN :desde AND :hasta
        GROUP BY p.nombre, p.categoria
        HAVING SUM(v.cantidad) > 0
        ORDER BY unidades ASC, p.nombre ASC
    """), cx, params=params)
    sentimiento = pd.read_sql(text("""
        SELECT COALESCE(c.sentimiento, 'pendiente') AS sentimiento, COUNT(*) AS comentarios
        FROM fact_comentarios c JOIN dim_fecha f ON f.fecha_key = c.fecha_key
        WHERE f.fecha BETWEEN :desde AND :hasta
        GROUP BY c.sentimiento
    """), cx, params=params)
    try:
        demanda = pd.read_sql(text("""
            SELECT TOP 5 p.nombre, p.categoria, d.fecha, d.demanda_prevista
            FROM pred_demanda d JOIN dim_producto p ON p.producto_key = d.producto_key
            WHERE d.fecha > :hasta
            ORDER BY d.demanda_prevista DESC
        """), cx, params={"hasta": hasta})
    except Exception:
        demanda = pd.DataFrame(columns=["nombre", "categoria", "fecha", "demanda_prevista"])
    try:
        ventas_previstas = pd.read_sql(text("""
            SELECT fecha, ventas_previstas, limite_inferior, limite_superior
            FROM pred_ventas
            WHERE producto_key IS NULL AND fecha > :hasta
            ORDER BY fecha
        """), cx, params={"hasta": hasta})
    except Exception:
        ventas_previstas = pd.DataFrame(columns=["fecha", "ventas_previstas", "limite_inferior", "limite_superior"])

    return {
        "periodo": {"desde": str(desde), "hasta": str(hasta)},
        "resumen": {k: (0 if pd.isna(v) else round(float(v), 2)) for k, v in resumen.items()},
        "productos_mayor_ingreso": _filas(productos),
        "productos_baja_rotacion": _filas(baja_rotacion),
        "sentimiento_comentarios": _filas(sentimiento),
        "demanda_esperada": _filas(demanda),
        "ventas_previstas": _filas(ventas_previstas),
    }


def main(desde: str, hasta: str, salida: str | None = None) -> dict:
    inicio, fin = validar_rango(desde, hasta)
    cargar_env_local(RAIZ / ".env")
    if not os.environ.get("SQL_DW"):
        raise RuntimeError("Falta SQL_DW en .env o en las variables de entorno.")
    dw = create_engine(os.environ["SQL_DW"])
    with dw.connect() as cx:
        reporte = crear_reporte(cx, inicio, fin)
    texto = json.dumps(reporte, ensure_ascii=False, indent=2, default=str)
    if salida:
        Path(salida).write_text(texto, encoding="utf-8")
    print(texto)
    return reporte


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un reporte IA Analytics por período.")
    parser.add_argument("--desde", required=True, help="Fecha inicial AAAA-MM-DD")
    parser.add_argument("--hasta", required=True, help="Fecha final AAAA-MM-DD")
    parser.add_argument("--salida", help="Ruta opcional para guardar el JSON")
    args = parser.parse_args()
    main(args.desde, args.hasta, args.salida)
