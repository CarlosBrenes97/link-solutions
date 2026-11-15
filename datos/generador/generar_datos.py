"""
Generador de datos de ejemplo para Link Solutions (todo es ficticio).

Crea tres archivos CSV en la carpeta de salida:
  - productos.csv           catálogo de 25 productos (para cargar en nopCommerce)
  - clientes_crm.csv        clientes del CRM simulado
  - ventas_historicas.csv   pedidos de los últimos 24+ meses con tendencia y estacionalidad
  - comentarios.csv         comentarios de redes sociales ligados a productos y clientes

Uso:
    pip install -r requirements.txt
    python generar_datos.py                 # escribe en ./salida
    python generar_datos.py --salida ../../datos_tmp --semilla 7

Los datos son reproducibles: la misma semilla produce los mismos archivos.
"""
import argparse
import os

import numpy as np
import pandas as pd
from faker import Faker

PROVINCIAS = ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"]
CANALES = ["Redes sociales", "Búsqueda en internet", "Recomendación", "Correo"]
REDES = ["Facebook", "Instagram", "X", "TikTok"]

# Catálogo canónico de la tienda (sku, nombre, categoría, precio en colones,
# probabilidad de comentario positivo). Los SKU y nombres deben coincidir con
# los productos importados en nopCommerce y con dim_producto del DW.
CATALOGO = [
    ("SKU001", "Juego de mesa familiar", "Juegos de mesa", 18500, 0.75),
    ("SKU002", "Rompecabezas de 1000 piezas", "Juegos de mesa", 9500, 0.70),
    ("SKU003", "Juego de cartas clásico", "Juegos de mesa", 3800, 0.68),
    ("SKU004", "Ajedrez de madera", "Juegos de mesa", 14500, 0.72),
    ("SKU005", "Dominó de colores", "Juegos de mesa", 6200, 0.67),
    ("SKU006", "Set de bloques de construcción", "Didácticos y construcción", 14000, 0.78),
    ("SKU007", "Set de ciencia para niños", "Didácticos y construcción", 17500, 0.76),
    ("SKU008", "Pizarra magnética infantil", "Didácticos y construcción", 11500, 0.70),
    ("SKU009", "Rompecabezas de madera para bebés", "Didácticos y construcción", 7800, 0.65),
    ("SKU010", "Peluche de oso grande", "Muñecos y peluches", 21500, 0.82),
    ("SKU011", "Muñeca con accesorios", "Muñecos y peluches", 16500, 0.75),
    ("SKU012", "Figura de acción articulada", "Muñecos y peluches", 9800, 0.68),
    ("SKU013", "Casa de muñecas", "Muñecos y peluches", 38500, 0.73),
    ("SKU014", "Robot a control remoto", "Muñecos y peluches", 27500, 0.62),
    ("SKU015", "Pelota deportiva", "Aire libre", 6500, 0.70),
    ("SKU016", "Bicicleta infantil", "Aire libre", 68000, 0.74),
    ("SKU017", "Patineta", "Aire libre", 32500, 0.65),
    ("SKU018", "Pistola de burbujas", "Aire libre", 4500, 0.80),
    ("SKU019", "Cometa", "Aire libre", 3200, 0.66),
    ("SKU020", "Caja de regalo sorpresa", "Regalos y detalles", 15500, 0.72),
    ("SKU021", "Tarjeta musical", "Regalos y detalles", 3500, 0.78),
    ("SKU022", "Set de papel de regalo", "Regalos y detalles", 4200, 0.70),
    ("SKU023", "Disfraz infantil de superhéroe", "Fiestas y disfraces", 12500, 0.75),
    ("SKU024", "Paquete de 20 globos metalizados", "Fiestas y disfraces", 4800, 0.68),
    ("SKU025", "Piñata tradicional", "Fiestas y disfraces", 9500, 0.71),
]

POSITIVOS = [
    "Excelente {p}, llegó rapidísimo y funciona de maravilla.",
    "Muy contento con mi {p}, la calidad está buenísima por el precio.",
    "El {p} superó mis expectativas, lo recomiendo a todos.",
    "Pura vida el {p}, ya lo estoy usando todos los días.",
    "Buen producto, el {p} vale cada colón.",
    "La atención fue muy buena y el {p} llegó bien empacado.",
    "Segunda vez que compro y el {p} no me ha fallado.",
]
NEUTROS = [
    "El {p} cumple, nada especial pero hace lo que tiene que hacer.",
    "Llegó el {p}, todavía lo estoy probando.",
    "El {p} está bien, esperaba un poco más por el precio.",
    "Normal el {p}, ni bueno ni malo.",
    "Recibí el {p} a tiempo, falta ver cómo dura.",
]
NEGATIVOS = [
    "Muy decepcionado con el {p}, a la semana dejó de funcionar.",
    "El {p} llegó con defectos y el cambio fue un trámite largo.",
    "No recomiendo el {p}, la calidad es mala para lo que cuesta.",
    "Mala experiencia, el {p} no es lo que mostraban en la foto.",
    "El {p} se calienta y falla seguido, una pérdida de plata.",
    "Tardó demasiado en llegar y el {p} venía con la caja golpeada.",
]


def generar_productos():
    return pd.DataFrame(
        [{"sku": s, "nombre": n, "categoria": c, "precio": p} for s, n, c, p, _ in CATALOGO]
    )


def generar_clientes(rng, fk, n=300, inicio="2024-07-01"):
    return pd.DataFrame({
        "cliente_id": range(1, n + 1),
        "nombre": [fk.name() for _ in range(n)],
        "email": [f"cliente{i}@ejemplo.com" for i in range(1, n + 1)],
        "tipo_cliente": rng.choice(["Individual", "Empresa"], n, p=[0.75, 0.25]),
        "provincia": rng.choice(PROVINCIAS, n),
        "canal_adquisicion": rng.choice(CANALES, n),
        "fecha_registro": pd.to_datetime(inicio) + pd.to_timedelta(rng.integers(0, 850, n), unit="D"),
    })


def generar_ventas(rng, clientes, fin="2026-10-31", inicio="2024-07-01"):
    """Tendencia suave + ciclo anual + pico en diciembre. Son 28 meses completos: el
    pronóstico necesita 24 para aprender la estacionalidad más 3 para medir su error."""
    dias = pd.date_range(inicio, fin, freq="D")
    base = 14 + 0.02 * np.arange(len(dias))
    est = 1 + 0.35 * np.sin(2 * np.pi * (dias.dayofyear - 80) / 365)
    est = est * np.where(dias.month == 12, 1.6, 1.0)
    n_pedidos = rng.poisson(base * est)
    # los productos baratos se venden más seguido que los caros
    precios = np.array([p for _, _, _, p, _ in CATALOGO], dtype=float)
    pesos = 1 / precios ** 0.3
    pesos = pesos / pesos.sum()
    skus = [s for s, *_ in CATALOGO]
    filas, pedido = [], 1
    for d, n in zip(dias, n_pedidos):
        for _ in range(int(n)):
            cliente = int(rng.integers(1, len(clientes) + 1))
            for _ in range(int(rng.integers(1, 4))):  # 1 a 3 líneas por pedido
                filas.append({
                    "pedido_id": pedido,
                    "fecha": d.date().isoformat(),
                    "cliente_id": cliente,
                    "producto_sku": str(rng.choice(skus, p=pesos)),
                    "cantidad": int(rng.integers(1, 4)),
                })
            pedido += 1
    return pd.DataFrame(filas)


def generar_comentarios(rng, clientes, ventas, n=400):
    """Cada comentario sale de una compra real, así el sentimiento se puede comparar con las ventas."""
    prob_pos = {s: pp for s, _, _, _, pp in CATALOGO}
    nombre = {s: nom.lower() for s, nom, _, _, _ in CATALOGO}
    muestra = ventas.sample(n=min(n, len(ventas)), random_state=int(rng.integers(0, 10**6)))
    filas = []
    for i, (_, v) in enumerate(muestra.iterrows(), start=1):
        pp = prob_pos[v.producto_sku]
        r = rng.random()
        if r < pp:
            plantilla = rng.choice(POSITIVOS)
        elif r < pp + (1 - pp) * 0.35:
            plantilla = rng.choice(NEUTROS)
        else:
            plantilla = rng.choice(NEGATIVOS)
        fecha = pd.to_datetime(v.fecha) + pd.Timedelta(days=int(rng.integers(2, 20)))
        filas.append({
            "comentario_id": f"C{i:04d}",
            "fecha": fecha.date().isoformat(),
            "producto_sku": v.producto_sku,
            "email_cliente": f"cliente{int(v.cliente_id)}@ejemplo.com",
            "red_social": str(rng.choice(REDES)),
            "texto": plantilla.format(p=nombre[v.producto_sku]),
        })
    return pd.DataFrame(filas).sort_values("fecha")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=os.path.join(os.path.dirname(__file__), "salida"))
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()

    os.makedirs(a.salida, exist_ok=True)
    rng = np.random.default_rng(a.semilla)
    fk = Faker("es_ES")
    Faker.seed(a.semilla)

    productos = generar_productos()
    clientes = generar_clientes(rng, fk)
    ventas = generar_ventas(rng, clientes)
    comentarios = generar_comentarios(rng, clientes, ventas)

    for nombre, df in [("productos", productos), ("clientes_crm", clientes),
                       ("ventas_historicas", ventas), ("comentarios", comentarios)]:
        ruta = os.path.join(a.salida, f"{nombre}.csv")
        df.to_csv(ruta, index=False, encoding="utf-8")
        print(f"{ruta}: {len(df)} filas")


if __name__ == "__main__":
    main()
