"""
ETL de Link Solutions: extrae de las tres fuentes, limpia, y carga el Data Warehouse (esquema en estrella).

Fuentes
  - Ventas de la tienda nopCommerce (base SQL de la tienda)       -> variable SQL_TIENDA (opcional)
  - Ventas históricas (CSV de apoyo, origen = 'historico')         -> ventas_historicas.csv
  - Clientes del CRM simulado                                      -> clientes_crm.csv
  - Comentarios de redes sociales                                  -> comentarios.csv
  - Catálogo de productos                                          -> productos.csv (o la tienda si hay SQL_TIENDA)

Los CSV se leen de Azure Blob Storage si existe BLOB_CONN (contenedor BLOB_CONTENEDOR),
y si no, de la carpeta DATA_DIR (por defecto ../generador/salida). Así se puede probar en local.

Variables de entorno (ver .env.example en la raíz del repo)
  SQL_DW            URL de SQLAlchemy del Data Warehouse. OBLIGATORIA.
  SQL_TIENDA        URL de SQLAlchemy de la base de nopCommerce. Si falta, se omiten las ventas de la tienda.
  BLOB_CONN         Cadena de conexión de la cuenta de almacenamiento. Opcional.
  BLOB_CONTENEDOR   Nombre del contenedor (por defecto 'comentarios').
  DATA_DIR          Carpeta local con los CSV.

El proceso es IDEMPOTENTE: correrlo dos veces seguidas deja las mismas cifras.

IMPORTANTE: las consultas contra nopCommerce (extraer_tienda) usan nombres de tablas y columnas
que hay que VERIFICAR contra la base real de la versión instalada.
"""
import io
import logging
import os
from dataclasses import dataclass

import pandas as pd
from sqlalchemy import bindparam, create_engine, text

log = logging.getLogger("etl")

# Estados de pedido de nopCommerce que NO cuentan como venta. VERIFICAR contra la versión instalada.
# (en las versiones recientes: 40 = Cancelado)
ESTADOS_PEDIDO_EXCLUIDOS = (40,)


# --------------------------------------------------------------------------- configuración
@dataclass
class Config:
    sql_dw: str
    sql_tienda: str | None
    blob_conn: str | None
    blob_contenedor: str
    data_dir: str

    @staticmethod
    def desde_entorno():
        aqui = os.path.dirname(os.path.abspath(__file__))
        return Config(
            sql_dw=os.environ["SQL_DW"],
            sql_tienda=os.environ.get("SQL_TIENDA") or None,
            blob_conn=os.environ.get("BLOB_CONN") or None,
            blob_contenedor=os.environ.get("BLOB_CONTENEDOR", "comentarios"),
            data_dir=os.environ.get("DATA_DIR", os.path.join(aqui, "..", "generador", "salida")),
        )


# --------------------------------------------------------------------------- EXTRAER
def leer_csv(cfg: Config, nombre: str) -> pd.DataFrame:
    if cfg.blob_conn:
        from azure.storage.blob import BlobServiceClient

        bs = BlobServiceClient.from_connection_string(cfg.blob_conn)
        datos = bs.get_blob_client(cfg.blob_contenedor, nombre).download_blob().readall()
        return pd.read_csv(io.BytesIO(datos))
    return pd.read_csv(os.path.join(cfg.data_dir, nombre))


def extraer_tienda(engine) -> pd.DataFrame:
    """Líneas de pedido de nopCommerce. VERIFICAR nombres de tablas y columnas en la base real."""
    q = text(
        """
        SELECT o.Id AS pedido_id, oi.Id AS linea_id, o.CreatedOnUtc AS fecha,
               c.Email AS email, p.Sku AS producto_sku,
               oi.Quantity AS cantidad, oi.UnitPriceExclTax AS precio_unitario
        FROM [Order] o
        JOIN OrderItem oi ON oi.OrderId = o.Id
        JOIN Customer  c  ON c.Id = o.CustomerId
        JOIN Product   p  ON p.Id = oi.ProductId
        WHERE o.Deleted = 0 AND o.OrderStatusId NOT IN :excluidos
        """
    ).bindparams(bindparam("excluidos", expanding=True))
    return pd.read_sql(q, engine, params={"excluidos": list(ESTADOS_PEDIDO_EXCLUIDOS)})


# --------------------------------------------------------------------------- TRANSFORMAR
def clave_fecha(serie) -> pd.Series:
    f = pd.to_datetime(serie)
    return (f.dt.year * 10000 + f.dt.month * 100 + f.dt.day).astype(int)


def limpiar_clientes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df.dropna(subset=["email"]).drop_duplicates("email")
    df["nombre"] = df["nombre"].fillna("Sin nombre").str.strip()
    df["tipo_cliente"] = df["tipo_cliente"].fillna("Individual")
    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"]).dt.date
    return df[["email", "nombre", "tipo_cliente", "provincia", "canal_adquisicion", "fecha_registro"]]

def extraer_productos_tienda(engine) -> pd.DataFrame:
    """Extrae el catálogo de nopCommerce sin duplicar productos."""

    consulta = text("""
        SELECT
            p.Sku AS sku,
            p.Name AS nombre,
            COALESCE(
                MIN(c.Name),
                'Sin categoría'
            ) AS categoria,
            p.Price AS precio
        FROM Product p
        LEFT JOIN Product_Category_Mapping pc
            ON pc.ProductId = p.Id
        LEFT JOIN Category c
            ON c.Id = pc.CategoryId
        WHERE p.Deleted = 0
          AND p.Sku IS NOT NULL
          AND LTRIM(RTRIM(p.Sku)) <> ''
        GROUP BY
            p.Id,
            p.Sku,
            p.Name,
            p.Price
    """)

    with engine.connect() as conexion:
        productos = pd.read_sql(consulta, conexion)

    return limpiar_productos(productos)

def limpiar_productos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sku"] = df["sku"].astype(str).str.strip().str.upper()
    df = df.drop_duplicates("sku")
    return df.rename(columns={"precio": "precio_lista"})[["sku", "nombre", "categoria", "precio_lista"]]


def construir_dim_fecha(desde, hasta) -> pd.DataFrame:
    dias = pd.date_range(desde, hasta, freq="D")
    nombres_mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                   "septiembre", "octubre", "noviembre", "diciembre"]
    nombres_dia = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    return pd.DataFrame({
        "fecha_key": clave_fecha(dias.to_series()).values,
        "fecha": dias.date,
        "anio": dias.year,
        "mes": dias.month,
        "nombre_mes": [nombres_mes[m - 1] for m in dias.month],
        "trimestre": dias.quarter,
        "dia_semana": [nombres_dia[d] for d in dias.day_of_week],
        "es_fin_semana": (dias.day_of_week >= 5).astype(int),
    })


def limpiar_ventas(df: pd.DataFrame, origen: str) -> pd.DataFrame:
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.normalize()
    df["producto_sku"] = df["producto_sku"].astype(str).str.strip().str.upper()
    df = df[df["cantidad"] > 0]
    df["origen"] = origen
    return df


# --------------------------------------------------------------------------- CARGAR
def insertar_nuevos(cx, tabla: str, df: pd.DataFrame, clave: str):
    """Inserta solo las filas cuya clave natural todavía no existe en la tabla."""
    existentes = pd.read_sql(text(f"SELECT {clave} FROM {tabla}"), cx)[clave]
    nuevos = df[~df[clave].isin(existentes)]
    if len(nuevos):
        nuevos.to_sql(tabla, cx, if_exists="append", index=False)
    log.info("%s: %d nuevos de %d", tabla, len(nuevos), len(df))


def cargar(cfg: Config):
    dw = create_engine(cfg.sql_dw)
    tienda = create_engine(cfg.sql_tienda) if cfg.sql_tienda else None

    # ---- extraer
    productos = limpiar_productos(leer_csv(cfg, "productos.csv"))
    clientes = limpiar_clientes(leer_csv(cfg, "clientes_crm.csv"))
    comentarios = leer_csv(cfg, "comentarios.csv")
    historico = leer_csv(cfg, "ventas_historicas.csv")
    historico["email"] = "cliente" + historico["cliente_id"].astype(str) + "@ejemplo.com"
    ventas_hist = limpiar_ventas(historico, "historico")
    ventas_hist = ventas_hist.rename(columns={"pedido_id": "pedido_id_nop"})
    ventas_hist["linea_id_nop"] = range(1, len(ventas_hist) + 1)

    # Integrar el catálogo real de nopCommerce con el catálogo simulado.
    if tienda is not None:
        productos_tienda = extraer_productos_tienda(tienda)

        productos = pd.concat(
            [productos_tienda, productos],
            ignore_index=True
        )

        productos = productos.drop_duplicates(
            subset=["sku"],
            keep="first"
        )

        log.info(
            "Catálogo integrado: %d productos únicos",
            len(productos)
        )

    ventas_tienda = pd.DataFrame()
    if tienda is not None:
        ventas_tienda = limpiar_ventas(extraer_tienda(tienda), "tienda")
        ventas_tienda = ventas_tienda.rename(columns={"pedido_id": "pedido_id_nop", "linea_id": "linea_id_nop"})
        # los clientes que compraron en la tienda y no están en el CRM entran como clientes 'Individual'
        faltan = set(ventas_tienda["email"].str.lower()) - set(clientes["email"])
        if faltan:
            extra = pd.DataFrame({"email": sorted(faltan)})
            extra["nombre"], extra["tipo_cliente"] = "Cliente de la tienda", "Individual"
            extra["provincia"], extra["canal_adquisicion"] = None, "Tienda"
            extra["fecha_registro"] = pd.Timestamp.today().date()
            clientes = pd.concat([clientes, extra], ignore_index=True)
        ventas_tienda["email"] = ventas_tienda["email"].str.strip().str.lower()
    log.info("extraído: %d productos, %d clientes, %d comentarios, %d ventas históricas, %d ventas tienda",
             len(productos), len(clientes), len(comentarios), len(ventas_hist), len(ventas_tienda))

    ventas = pd.concat([ventas_hist, ventas_tienda], ignore_index=True)
    comentarios["fecha"] = pd.to_datetime(comentarios["fecha"]).dt.normalize()
    comentarios["producto_sku"] = comentarios["producto_sku"].astype(str).str.strip().str.upper()
    comentarios["email_cliente"] = comentarios["email_cliente"].astype(str).str.strip().str.lower()

    # ---- cargar (todo en una transacción: o entra todo o no entra nada)
    with dw.begin() as cx:
        # dimensión fecha: cubrir todas las fechas que aparecen
        rango_min = min(ventas["fecha"].min(), comentarios["fecha"].min())
        rango_max = max(ventas["fecha"].max(), comentarios["fecha"].max())
        insertar_nuevos(cx, "dim_fecha", construir_dim_fecha(rango_min, rango_max), "fecha_key")

        # dimensiones
        insertar_nuevos(cx, "dim_producto", productos.rename(columns={"sku": "sku"}), "sku")
        insertar_nuevos(cx, "dim_cliente", clientes, "email")

        dim_prod = pd.read_sql(text("SELECT producto_key, sku, precio_lista FROM dim_producto"), cx)
        dim_cli = pd.read_sql(text("SELECT cliente_key, email FROM dim_cliente"), cx)

        # hechos de ventas: se recargan completos (idempotente)
        hechos = (ventas.merge(dim_prod, left_on="producto_sku", right_on="sku", how="left")
                        .merge(dim_cli, on="email", how="left"))
        sin_producto = hechos["producto_key"].isna().sum()
        sin_cliente = hechos["cliente_key"].isna().sum()
        if sin_producto or sin_cliente:
            log.warning("ventas descartadas: %d sin producto y %d sin cliente conocido", sin_producto, sin_cliente)
            hechos = hechos.dropna(subset=["producto_key", "cliente_key"])
        if "precio_unitario" not in hechos:
            hechos["precio_unitario"] = float("nan")
        hechos["precio_unitario"] = hechos["precio_unitario"].fillna(hechos["precio_lista"])
        hechos["total_linea"] = hechos["cantidad"] * hechos["precio_unitario"]
        hechos["fecha_key"] = clave_fecha(hechos["fecha"])
        hechos = hechos[["pedido_id_nop", "linea_id_nop", "fecha_key", "producto_key", "cliente_key",
                         "cantidad", "precio_unitario", "total_linea", "origen"]]
        hechos[["producto_key", "cliente_key"]] = hechos[["producto_key", "cliente_key"]].astype(int)
        cx.execute(text("DELETE FROM fact_ventas"))
        hechos.to_sql("fact_ventas", cx, if_exists="append", index=False)
        log.info("fact_ventas: %d filas cargadas", len(hechos))

        # comentarios: solo se agregan los nuevos, para no borrar el sentimiento que ya calculó la IA
        com = (comentarios.merge(dim_prod[["producto_key", "sku"]], left_on="producto_sku", right_on="sku", how="left")
                          .merge(dim_cli, left_on="email_cliente", right_on="email", how="left"))
        com = com.dropna(subset=["producto_key"])
        com["fecha_key"] = clave_fecha(com["fecha"])
        com["producto_key"] = com["producto_key"].astype(int)
        com["cliente_key"] = com["cliente_key"].astype("Int64")
        com = com[["comentario_id", "fecha_key", "producto_key", "cliente_key", "red_social", "texto"]]
        insertar_nuevos(cx, "fact_comentarios", com, "comentario_id")

    validar(dw, ventas)


# --------------------------------------------------------------------------- VALIDAR
def validar(dw, ventas_origen: pd.DataFrame):
    with dw.connect() as cx:
        filas = cx.execute(text("SELECT COUNT(*) FROM fact_ventas")).scalar()
        nulos = cx.execute(text(
            "SELECT COUNT(*) FROM fact_ventas WHERE producto_key IS NULL OR cliente_key IS NULL OR fecha_key IS NULL"
        )).scalar()
        dup = cx.execute(text(
            "SELECT COUNT(*) FROM (SELECT email FROM dim_cliente GROUP BY email HAVING COUNT(*) > 1) t"
        )).scalar()
    log.info("validación: fact_ventas=%d (origen=%d), claves nulas=%d, correos repetidos=%d",
             filas, len(ventas_origen), nulos, dup)
    if nulos or dup:
        raise RuntimeError("Validación fallida: hay claves nulas o correos repetidos")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cargar(Config.desde_entorno())
    log.info("ETL terminado")


if __name__ == "__main__":
    main()
