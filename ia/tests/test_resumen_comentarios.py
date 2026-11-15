import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import resumen_comentarios


class ClienteFalso:
    class messages:
        @staticmethod
        def create(**kwargs):
            respuesta = {"sentimientos": ["positivo"], "resumen": "Resumen válido."}
            return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(respuesta))])


def test_analizar_lote_valida_sentimientos_y_resumen():
    resultado = resumen_comentarios.analizar_lote(
        ClienteFalso(), "modelo-prueba", "Producto", ["Muy bueno"]
    )
    assert resultado == {"sentimientos": ["positivo"], "resumen": "Resumen válido."}
