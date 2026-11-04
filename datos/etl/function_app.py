"""Azure Function: corre el ETL cada día a las 2:00 a.m. hora de Costa Rica (UTC-6, sin horario de verano)."""
import logging

import azure.functions as func

import etl
from ia_pasos import correr_ia  # pronóstico y resumen de comentarios, después del ETL

app = func.FunctionApp()


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
