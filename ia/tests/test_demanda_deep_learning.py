import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demanda_deep_learning import predecir_demanda


def test_red_neuronal_genera_demanda_no_negativa_por_producto():
    fechas = pd.date_range("2024-01-01", periods=24, freq="MS")
    filas = []
    for producto in (1, 2):
        for i, fecha in enumerate(fechas):
            filas.append({
                "producto_key": producto,
                "nombre": f"Producto {producto}",
                "categoria": "Prueba",
                "fecha": fecha,
                "demanda": 10 + producto + (i % 12),
            })
    salida, error = predecir_demanda(pd.DataFrame(filas), meses=3, epocas=30)
    assert len(salida) == 6
    assert set(salida["producto_key"]) == {1, 2}
    assert (salida["demanda_prevista"] >= 0).all()
    assert np.isfinite(error)
