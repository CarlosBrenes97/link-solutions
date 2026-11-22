"""Azure Function: ETL diario y API protegida para IA Analytics."""
import json
import logging
import os
import sys

import azure.functions as func
from sqlalchemy import create_engine

import etl
from ia_pasos import correr_ia  # pronóstico y resumen de comentarios, después del ETL

app = func.FunctionApp()


def _modulo_reportes_ia():
    """Localiza el paquete ia tanto en desarrollo como al publicar la Function."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    for ruta in (os.path.join(aqui, "ia"), os.path.join(aqui, "..", "..", "ia")):
        if os.path.isdir(ruta) and ruta not in sys.path:
            sys.path.insert(0, ruta)
    import reportes_ia
    return reportes_ia


@app.timer_trigger(schedule="0 0 8 * * *",  # 6 campos: seg min hora día mes díaSemana, en UTC. 08:00 UTC = 02:00 CR
                   arg_name="reloj", run_on_startup=False, use_monitor=False)
def etl_diario(reloj: func.TimerRequest) -> None:
    logging.info("Inicia ETL programado")
    etl.main()
    correr_ia()
    logging.info("Termina ETL programado")


# Ejecución manual para la demostración: se llama con la clave de la función
@app.route(route="correr-etl", auth_level=func.AuthLevel.FUNCTION)
def correr_etl(req: func.HttpRequest) -> func.HttpResponse:
    etl.main()
    correr_ia()
    return func.HttpResponse("ETL completado")


@app.route(route="reporte-ia", auth_level=func.AuthLevel.FUNCTION)
def reporte_ia(req: func.HttpRequest) -> func.HttpResponse:
    """Entrega estadísticas y predicciones del período seleccionado en JSON.

    La clave de Function evita que el reporte administrativo quede público.
    La futura página de Administración consume esta ruta; no hay acceso desde la
    tienda pública ni cambios a pedidos, clientes o productos.
    """
    desde = req.params.get("desde")
    hasta = req.params.get("hasta")
    if not desde or not hasta:
        return func.HttpResponse(
            "Debe enviar los parámetros desde y hasta en formato AAAA-MM-DD.",
            status_code=400,
        )
    try:
        reportes = _modulo_reportes_ia()
        inicio, fin = reportes.validar_rango(desde, hasta)
        if not os.environ.get("SQL_DW"):
            return func.HttpResponse("La variable SQL_DW no está configurada.", status_code=500)
        dw = create_engine(os.environ["SQL_DW"])
        with dw.connect() as conexion:
            resultado = reportes.crear_reporte(conexion, inicio, fin)
        return func.HttpResponse(
            json.dumps(resultado, ensure_ascii=False, default=str),
            status_code=200,
            mimetype="application/json",
        )
    except ValueError as error:
        return func.HttpResponse(str(error), status_code=400)
    except Exception:
        logging.exception("No fue posible generar el reporte IA")
        return func.HttpResponse("No fue posible generar el reporte IA.", status_code=500)
