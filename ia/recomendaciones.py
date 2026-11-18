"""HU05: recomendaciones de productos basadas en compras anteriores.

Lee las ventas ya preparadas en el Data Warehouse y calcula recomendaciones
para el correo de un cliente. La tienda puede invocar la misma lógica en el
servidor usando el correo de la persona que haya iniciado sesión.

Uso local:
    python ia\\recomendaciones.py --email maria@example.com

La ejecución es de solo lectura: no modifica ``dw`` ni ``tienda``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


RAIZ = Path(__file__).resolve().parents[1]


def cargar_env_local(ruta: Path) -> None:
    """Carga el archivo .env sin imprimir ninguno de sus secretos."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def leer_ventas_dw(cx) -> pd.DataFrame:
    """Obtiene ventas, clientes y productos desde el Data Warehouse."""
    return pd.read_sql(text("""
        SELECT
            c.email,
            p.sku,
            p.nombre,
            p.categoria,
            p.precio_lista,
            v.cantidad
        FROM fact_ventas AS v
        INNER JOIN dim_cliente AS c ON c.cliente_key = v.cliente_key
        INNER JOIN dim_producto AS p ON p.producto_key = v.producto_key
        WHERE c.email IS NOT NULL
          AND p.sku IS NOT NULL
          AND v.origen = 'tienda'
    """), cx)


def recomendar(ventas: pd.DataFrame, email: str, limite: int = 5) -> pd.DataFrame:
    """Calcula productos recomendados por compras compartidas.

    Se buscan clientes que compartan al menos una compra con la persona y se
    puntúan los otros productos que esas personas han adquirido. Los productos
    ya comprados se excluyen. Si no existe historial, se muestran los productos
    más vendidos como alternativa.
    """
    datos = ventas.copy()
    datos["email"] = datos["email"].astype(str).str.strip().str.lower()
    datos["sku"] = datos["sku"].astype(str).str.strip().str.upper()
    datos["cantidad"] = pd.to_numeric(datos["cantidad"], errors="coerce").fillna(0)
    email = email.strip().lower()

    comprados = set(datos.loc[datos["email"] == email, "sku"])
    if comprados:
        similares = set(datos.loc[
            datos["sku"].isin(comprados) & (datos["email"] != email), "email"
        ])
        candidatas = datos.loc[
            datos["email"].isin(similares) & ~datos["sku"].isin(comprados)
        ].copy()
        motivo = "clientes con compras similares"
    else:
        candidatas = datos.copy()
        motivo = "productos más vendidos (cliente sin historial)"

    # Si alguien ya compró todos los productos de clientes similares, se usa
    # una alternativa popular que tampoco repita productos ya adquiridos.
    if candidatas.empty and comprados:
        candidatas = datos.loc[~datos["sku"].isin(comprados)].copy()
        motivo = "productos más vendidos (sin alternativas nuevas)"

    resultado = (
        candidatas.groupby(["sku", "nombre", "categoria", "precio_lista"], dropna=False,
                            as_index=False)["cantidad"]
        .sum()
        .rename(columns={"cantidad": "puntaje"})
        .sort_values(["puntaje", "sku"], ascending=[False, True])
        .head(limite)
    )
    resultado["motivo"] = motivo
    return resultado[["sku", "nombre", "categoria", "precio_lista", "puntaje", "motivo"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera recomendaciones desde dw (HU05).")
    parser.add_argument("--email", required=True, help="Correo de la cuenta de la tienda.")
    parser.add_argument("--limite", type=int, default=5, help="Máximo de productos recomendados.")
    args = parser.parse_args()

    cargar_env_local(RAIZ / ".env")
    if not os.environ.get("SQL_DW"):
        raise RuntimeError("Falta SQL_DW en el archivo .env o en las variables de entorno.")

    dw = create_engine(os.environ["SQL_DW"])
    with dw.connect() as cx:
        ventas = leer_ventas_dw(cx)
    resultado = recomendar(ventas, args.email, args.limite)

    if resultado.empty:
        print("No hay suficientes compras para generar recomendaciones todavía.")
        return
    print(f"Recomendaciones para {args.email}:")
    print(resultado.to_string(index=False))


if __name__ == "__main__":
    main()
