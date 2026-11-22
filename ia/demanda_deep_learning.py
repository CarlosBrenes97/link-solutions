"""Predicción de demanda por producto con una red neuronal de dos capas.

El modelo usa ventas mensuales del Data Warehouse. Para cada producto aprende
la tendencia temporal y la estacionalidad (mes del año) y estima la demanda de
los próximos meses. Se implementa únicamente con NumPy para que sea fácil de
ejecutar en Azure Functions sin una dependencia pesada de Deep Learning.

Uso local:
    python ia\\demanda_deep_learning.py --meses 6

Variable de entorno requerida: SQL_DW.
"""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect, text


log = logging.getLogger("demanda_dl")
RAIZ = Path(__file__).resolve().parents[1]
MESES_A_PREDECIR = 6


def cargar_env_local(ruta: Path) -> None:
    """Carga .env en desarrollo sin mostrar secretos."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def cargar_demanda_mensual(cx) -> pd.DataFrame:
    """Devuelve una fila por producto y mes, incluyendo meses sin ventas."""
    ventas = pd.read_sql(text("""
        SELECT p.producto_key, p.nombre, p.categoria, f.anio, f.mes,
               SUM(v.cantidad) AS demanda
        FROM fact_ventas v
        INNER JOIN dim_fecha f ON f.fecha_key = v.fecha_key
        INNER JOIN dim_producto p ON p.producto_key = v.producto_key
        GROUP BY p.producto_key, p.nombre, p.categoria, f.anio, f.mes
    """), cx)
    if ventas.empty:
        raise ValueError("No hay ventas en el Data Warehouse para entrenar el modelo.")

    ventas["fecha"] = pd.to_datetime(dict(year=ventas.anio, month=ventas.mes, day=1))
    productos = ventas[["producto_key", "nombre", "categoria"]].drop_duplicates()
    meses = pd.date_range(ventas["fecha"].min(), ventas["fecha"].max(), freq="MS")
    base = (
        productos.assign(_aux=1)
        .merge(pd.DataFrame({"fecha": meses, "_aux": 1}), on="_aux")
        .drop(columns="_aux")
    )
    resultado = base.merge(
        ventas[["producto_key", "fecha", "demanda"]],
        on=["producto_key", "fecha"], how="left"
    )
    resultado["demanda"] = resultado["demanda"].fillna(0.0).astype(float)
    return resultado.sort_values(["producto_key", "fecha"]).reset_index(drop=True)


def crear_caracteristicas(
    datos: pd.DataFrame,
    productos: list[int],
    inicio: pd.Timestamp,
    escala_tiempo: int | None = None,
) -> np.ndarray:
    """Tiempo, estacionalidad y un vector one-hot para cada producto."""
    fecha = pd.to_datetime(datos["fecha"])
    indice_mes = (fecha.dt.year - inicio.year) * 12 + fecha.dt.month - inicio.month
    escala = escala_tiempo or max(int(indice_mes.max()), 1)
    tiempo = (indice_mes.to_numpy(dtype=float) / escala).reshape(-1, 1)
    angulo = 2 * np.pi * fecha.dt.month.to_numpy(dtype=float) / 12.0
    estacionalidad = np.column_stack([np.sin(angulo), np.cos(angulo)])
    posiciones = {producto: i for i, producto in enumerate(productos)}
    one_hot = np.zeros((len(datos), len(productos)), dtype=float)
    one_hot[np.arange(len(datos)), [posiciones[p] for p in datos["producto_key"]]] = 1.0
    return np.column_stack([tiempo, estacionalidad, one_hot])


class RedDemanda:
    """Red neuronal pequeña: entrada -> 32 ReLU -> 16 ReLU -> demanda."""

    def __init__(self, entradas: int, semilla: int = 42):
        rnd = np.random.default_rng(semilla)
        self.w1 = rnd.normal(0, 0.15, (entradas, 32))
        self.b1 = np.zeros((1, 32))
        self.w2 = rnd.normal(0, 0.15, (32, 16))
        self.b2 = np.zeros((1, 16))
        self.w3 = rnd.normal(0, 0.15, (16, 1))
        self.b3 = np.zeros((1, 1))

    def predecir(self, x: np.ndarray) -> np.ndarray:
        h1 = np.maximum(0, x @ self.w1 + self.b1)
        h2 = np.maximum(0, h1 @ self.w2 + self.b2)
        return h2 @ self.w3 + self.b3

    def entrenar(self, x: np.ndarray, y: np.ndarray, epocas: int = 900, tasa: float = 0.02) -> float:
        """Entrena por descenso de gradiente y devuelve el último error medio."""
        n = len(x)
        for _ in range(epocas):
            z1 = x @ self.w1 + self.b1
            h1 = np.maximum(0, z1)
            z2 = h1 @ self.w2 + self.b2
            h2 = np.maximum(0, z2)
            pred = h2 @ self.w3 + self.b3
            error = pred - y

            d_pred = (2.0 / n) * error
            d_w3, d_b3 = h2.T @ d_pred, d_pred.sum(axis=0, keepdims=True)
            d_h2 = d_pred @ self.w3.T
            d_z2 = d_h2 * (z2 > 0)
            d_w2, d_b2 = h1.T @ d_z2, d_z2.sum(axis=0, keepdims=True)
            d_h1 = d_z2 @ self.w2.T
            d_z1 = d_h1 * (z1 > 0)
            d_w1, d_b1 = x.T @ d_z1, d_z1.sum(axis=0, keepdims=True)

            self.w3 -= tasa * d_w3; self.b3 -= tasa * d_b3
            self.w2 -= tasa * d_w2; self.b2 -= tasa * d_b2
            self.w1 -= tasa * d_w1; self.b1 -= tasa * d_b1
        return float(np.mean((self.predecir(x) - y) ** 2))


def predecir_demanda(datos: pd.DataFrame, meses: int = MESES_A_PREDECIR, epocas: int = 900) -> tuple[pd.DataFrame, float]:
    """Entrena la red y devuelve demanda prevista por producto para cada mes futuro."""
    datos = datos.copy()
    productos = sorted(datos["producto_key"].unique().tolist())
    historial = pd.to_datetime(datos["fecha"])
    if historial.nunique() < 24:
        raise ValueError("Se necesitan al menos 24 meses de ventas para predecir demanda.")
    inicio, ultimo = historial.min(), historial.max()
    escala_tiempo = max(
        int(((historial.dt.year - inicio.year) * 12 + historial.dt.month - inicio.month).max()), 1
    )
    x = crear_caracteristicas(datos, productos, inicio, escala_tiempo)
    # log1p estabiliza diferencias grandes entre productos.
    y_original = np.log1p(datos["demanda"].to_numpy(dtype=float)).reshape(-1, 1)
    promedio, desviacion = float(y_original.mean()), float(y_original.std()) or 1.0
    y = (y_original - promedio) / desviacion
    red = RedDemanda(x.shape[1])
    error = red.entrenar(x, y, epocas=epocas)

    fechas = pd.date_range(ultimo + pd.offsets.MonthBegin(1), periods=meses, freq="MS")
    futuro = pd.DataFrame(
        [(producto, fecha) for fecha in fechas for producto in productos],
        columns=["producto_key", "fecha"]
    )
    x_futuro = crear_caracteristicas(futuro, productos, inicio, escala_tiempo)
    escala = red.predecir(x_futuro).ravel() * desviacion + promedio
    futuro["demanda_prevista"] = np.maximum(0, np.expm1(escala))
    futuro["demanda_prevista"] = futuro["demanda_prevista"].round(2)
    return futuro, error


def guardar_predicciones(cx, predicciones: pd.DataFrame) -> None:
    """Crea la tabla si es la primera ejecución y reemplaza el pronóstico vigente."""
    if inspect(cx).has_table("pred_demanda"):
        cx.execute(text("DELETE FROM pred_demanda"))
        predicciones.to_sql("pred_demanda", cx, if_exists="append", index=False)
    else:
        # En una base de desarrollo anterior al script de esquema, pandas crea
        # la tabla la primera vez. En Azure se recomienda aplicar 01_crear_dw.sql.
        predicciones.to_sql("pred_demanda", cx, if_exists="replace", index=False)


def main(meses: int = MESES_A_PREDECIR) -> float:
    cargar_env_local(RAIZ / ".env")
    if not os.environ.get("SQL_DW"):
        raise RuntimeError("Falta SQL_DW en .env o en las variables de entorno.")
    dw = create_engine(os.environ["SQL_DW"])
    with dw.begin() as cx:
        datos = cargar_demanda_mensual(cx)
        predicciones, error = predecir_demanda(datos, meses=meses)
        guardar_predicciones(cx, predicciones)
    log.info("Predicción de demanda guardada: %d filas; error MSE normalizado %.4f", len(predicciones), error)
    return error


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Predice demanda por producto con red neuronal.")
    parser.add_argument("--meses", type=int, default=MESES_A_PREDECIR)
    args = parser.parse_args()
    main(args.meses)
