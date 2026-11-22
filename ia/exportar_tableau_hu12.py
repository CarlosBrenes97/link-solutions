"""Exporta datos agregados y seguros para el tablero Tableau de HU12.

El archivo resultante no incluye correos, nombres de clientes, pedidos ni
credenciales. Reúne las ventas mensuales históricas del Data Warehouse y las
seis predicciones generadas por ``ia/pronostico.py``.

Uso desde la raíz del proyecto::

    python ia\\exportar_tableau_hu12.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "reportes" / "tableau" / "hu12_pronostico_ventas.csv"


def cargar_env_local(ruta: Path) -> None:
    """Carga .env sin mostrar ningún secreto en pantalla."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def leer_datos(cx) -> pd.DataFrame:
    historico = pd.read_sql(text("""
        SELECT
            DATEFROMPARTS(f.anio, f.mes, 1) AS fecha,
            CAST(SUM(v.total_linea) AS DECIMAL(18, 2)) AS ventas_reales
        FROM fact_ventas AS v
        INNER JOIN dim_fecha AS f ON f.fecha_key = v.fecha_key
        GROUP BY f.anio, f.mes
    """), cx)

    pronostico = pd.read_sql(text("""
        SELECT
            fecha,
            ventas_previstas,
            limite_inferior,
            limite_superior
        FROM pred_ventas
        WHERE producto_key IS NULL
    """), cx)

    historico["fecha"] = pd.to_datetime(historico["fecha"])
    pronostico["fecha"] = pd.to_datetime(pronostico["fecha"])
    datos = historico.merge(pronostico, on="fecha", how="outer").sort_values("fecha")
    datos["periodo"] = datos["ventas_reales"].notna().map(
        {True: "Histórico", False: "Pronóstico"}
    )
    return datos[[
        "fecha", "periodo", "ventas_reales", "ventas_previstas",
        "limite_inferior", "limite_superior",
    ]]


def leer_datos_mock() -> pd.DataFrame:
    """Genera el extracto desde los CSV ficticios reproducibles del proyecto.

    Sirve para demostrar HU12 si Azure SQL está temporalmente inaccesible.
    No incluye información de clientes y reutiliza el mismo modelo de pronóstico.
    """
    ventas = pd.read_csv(RAIZ / "datos" / "generador" / "salida" / "ventas_historicas.csv")
    productos = pd.read_csv(RAIZ / "datos" / "generador" / "salida" / "productos.csv")
    ventas["fecha"] = pd.to_datetime(ventas["fecha"])
    ventas = ventas.merge(
        productos[["sku", "precio"]], left_on="producto_sku", right_on="sku", how="left"
    )
    ventas["total_linea"] = ventas["cantidad"] * ventas["precio"]
    serie = (
        ventas.groupby(ventas["fecha"].dt.to_period("M"))["total_linea"]
        .sum()
        .sort_index()
    )
    serie.index = serie.index.to_timestamp()

    from pronostico import pronosticar

    prediccion, _ = pronosticar(serie)
    historico = pd.DataFrame({"fecha": serie.index, "ventas_reales": serie.values})
    prediccion["fecha"] = pd.to_datetime(prediccion["fecha"])
    datos = historico.merge(prediccion, on="fecha", how="outer").sort_values("fecha")
    datos["periodo"] = datos["ventas_reales"].notna().map(
        {True: "Histórico", False: "Pronóstico"}
    )
    return datos[[
        "fecha", "periodo", "ventas_reales", "ventas_previstas",
        "limite_inferior", "limite_superior",
    ]]


def main() -> Path:
    parser = argparse.ArgumentParser(description="Exporta el CSV de Tableau para HU12.")
    parser.add_argument(
        "--fuente", choices=("dw", "mock"), default="dw",
        help="dw usa Azure; mock usa los 28 meses ficticios reproducibles.",
    )
    args = parser.parse_args()

    if args.fuente == "mock":
        datos = leer_datos_mock()
    else:
        cargar_env_local(RAIZ / ".env")
        if not os.environ.get("SQL_DW"):
            raise RuntimeError("Falta SQL_DW en el archivo .env o en las variables de entorno.")
        engine = create_engine(os.environ["SQL_DW"])
        with engine.connect() as cx:
            datos = leer_datos(cx)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(SALIDA, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    print(f"Exportación HU12 creada: {SALIDA}")
    print(f"Filas: {len(datos)}. Fuente: {args.fuente}. Datos personales incluidos: no.")
    return SALIDA


if __name__ == "__main__":
    main()
