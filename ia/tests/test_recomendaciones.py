import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recomendaciones import recomendar


def test_recomienda_el_producto_del_cliente_similar_no_comprado():
    ventas = pd.DataFrame([
        {"email": "maria@example.com", "sku": "COMUN", "nombre": "Juego común", "categoria": "Juegos", "precio_lista": 100, "cantidad": 1},
        {"email": "maria@example.com", "sku": "BICI", "nombre": "Bicicleta", "categoria": "Aire libre", "precio_lista": 200, "cantidad": 1},
        {"email": "andrea@example.com", "sku": "COMUN", "nombre": "Juego común", "categoria": "Juegos", "precio_lista": 100, "cantidad": 1},
        {"email": "andrea@example.com", "sku": "AJEDREZ", "nombre": "Ajedrez", "categoria": "Juegos", "precio_lista": 150, "cantidad": 1},
    ])

    resultado = recomendar(ventas, "maria@example.com")

    assert resultado["sku"].tolist() == ["AJEDREZ"]
    assert resultado.iloc[0]["motivo"] == "clientes con compras similares"


def test_cliente_sin_historial_recibe_productos_populares():
    ventas = pd.DataFrame([
        {"email": "ana@example.com", "sku": "A", "nombre": "A", "categoria": "Juegos", "precio_lista": 100, "cantidad": 1},
        {"email": "bea@example.com", "sku": "A", "nombre": "A", "categoria": "Juegos", "precio_lista": 100, "cantidad": 3},
        {"email": "bea@example.com", "sku": "B", "nombre": "B", "categoria": "Juegos", "precio_lista": 100, "cantidad": 1},
    ])

    resultado = recomendar(ventas, "nuevo@example.com", limite=2)

    assert resultado["sku"].tolist() == ["A", "B"]
    assert "sin historial" in resultado.iloc[0]["motivo"]
