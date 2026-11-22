"""Pasos de IA que se ejecutan después del ETL. Si fallan, el ETL ya quedó cargado."""
import logging
import os
import sys

log = logging.getLogger("ia")


def correr_ia():
    # En local, ia/ está en la raíz del repo. Al publicar la función, publicar.sh la copia a datos/etl/ia
    aqui = os.path.dirname(os.path.abspath(__file__))
    for ruta in (os.path.join(aqui, "ia"), os.path.join(aqui, "..", "..", "ia")):
        if os.path.isdir(ruta):
            sys.path.insert(0, ruta)
    try:
        import pronostico
        pronostico.main()
    except Exception:
        log.exception("Falló el pronóstico de ventas")
    try:
        import demanda_deep_learning
        demanda_deep_learning.main()
    except Exception:
        # El reporte de BI continúa disponible aunque el modelo no pueda entrenar.
        log.exception("Falló la predicción de demanda con red neuronal")
    try:
        import resumen_comentarios
        resumen_comentarios.main()
    except Exception:
        log.exception("Falló el resumen de comentarios")
