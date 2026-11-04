"""
Pronóstico de ventas (suavizado exponencial con tendencia amortiguada y estacionalidad, statsmodels).

Lee las ventas mensuales del Data Warehouse, mide el error con los últimos 3 meses (backtest),
reentrena con todo el historial, predice los próximos meses y guarda el resultado en pred_ventas.

Necesita 24+ meses de historia para aprender la estacionalidad anual (27+ para medir el error).
Variable de entorno: SQL_DW (URL de SQLAlchemy del almacén).
"""
import logging
import os

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from statsmodels.tsa.holtwinters import ExponentialSmoothing

log = logging.getLogger("pronostico")

MESES_A_PREDECIR = 6


def ventas_mensuales(cx) -> pd.Series:
    df = pd.read_sql(text(
        """
        SELECT f.anio, f.mes, SUM(v.total_linea) AS ventas
        FROM fact_ventas v JOIN dim_fecha f ON f.fecha_key = v.fecha_key
        GROUP BY f.anio, f.mes
        """), cx)
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes, day=1))
    serie = df.set_index("fecha")["ventas"].astype(float).sort_index().asfreq("MS")
    # el mes en curso suele estar incompleto y sesga el modelo hacia abajo: se descarta
    hoy = pd.Timestamp.today().replace(day=1).normalize()
    if serie.index[-1] >= hoy:
        serie = serie.iloc[:-1]
    return serie.interpolate()


def pronosticar(serie: pd.Series, meses: int = MESES_A_PREDECIR):
    """Devuelve (DataFrame con la predicción, MAPE del backtest en %)."""
    if len(serie) < 24:
        raise ValueError(f"Se necesitan al menos 24 meses de historia y hay {len(serie)}")
    mape = None
    if len(serie) >= 27:  # backtest: 24 meses para entrenar y 3 para comprobar
        entrena, prueba = serie[:-3], serie[-3:]
        modelo = ExponentialSmoothing(entrena, trend="add", damped_trend=True, seasonal="add", seasonal_periods=12).fit()
        mape = float(np.mean(np.abs((prueba - modelo.forecast(3)) / prueba)) * 100)

    final = ExponentialSmoothing(serie, trend="add", damped_trend=True, seasonal="add", seasonal_periods=12).fit()
    pred = final.forecast(meses)
    sd = float(np.std(final.resid))
    salida = pd.DataFrame({
        "fecha": pred.index.date,
        "producto_key": None,
        "ventas_previstas": pred.values.clip(min=0),
        "limite_inferior": (pred.values - 1.96 * sd).clip(min=0),
        "limite_superior": pred.values + 1.96 * sd,
    })
    return salida, mape


def main():
    dw = create_engine(os.environ["SQL_DW"])
    with dw.begin() as cx:
        serie = ventas_mensuales(cx)
        salida, mape = pronosticar(serie)
        cx.execute(text("DELETE FROM pred_ventas WHERE producto_key IS NULL"))
        salida.to_sql("pred_ventas", cx, if_exists="append", index=False)
    log.info("Pronóstico guardado: %d meses. Error del backtest (MAPE): %s", len(salida),
             f"{mape:.1f}%" if mape is not None else "no calculado (faltan meses)")
    return mape


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
