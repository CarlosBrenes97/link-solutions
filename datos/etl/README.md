# ETL y automatización diaria

- `etl.py`: extrae, limpia y carga el Data Warehouse. Idempotente.
- `ia_pasos.py`: corre el pronóstico y el resumen de comentarios después del ETL.
- `function_app.py`: Azure Function con disparador de temporizador (2:00 a.m. Costa Rica = `0 0 8 * * *` en UTC) y un punto de entrada manual.
- `tests/test_etl_sqlite.py`: prueba sin Azure.
- `publicar.sh`: publica la función (requiere Azure Functions Core Tools).

## Ejecutar en local contra una base real
```bash
export SQL_DW="mssql+pyodbc://..."      # ver .env.example en la raíz
python etl.py
```

Al ejecutarse desde el repositorio, `etl.py` carga automáticamente las variables del archivo `.env` de la raíz.
Nunca se imprimen ni se versionan sus valores. Si se usa una contraseña con caracteres especiales en una URL,
codificarla para URL antes de guardarla en `.env`.

## Verificar antes de usar con nopCommerce real
`extraer_tienda()` usa las tablas `[Order]`, `OrderItem`, `Customer` y `Product` y las columnas `Deleted`, `OrderStatusId`,
`UnitPriceExclTax`, `CreatedOnUtc`, `Sku`. Comparar con la base real (ver `datos/sql/04_exportar_esquema_tienda.sql`) y
ajustar la lista `ESTADOS_PEDIDO_EXCLUIDOS`.

El catálogo de la tienda es la fuente maestra cuando se configura `SQL_TIENDA`: por cada SKU, el ETL actualiza en
`dim_producto` el nombre, la categoría y el precio, además de insertar productos nuevos. Los productos obsoletos no se
eliminan automáticamente porque podrían tener hechos históricos. Si se limpia una base de demostración de nopCommerce,
recrear el DW con `datos/sql/01_crear_dw.sql` antes de ejecutar el ETL evita conservar productos demo.

El catálogo ficticio versionado en `datos/generador/generar_datos.py` debe conservar los mismos SKU y nombres que la
tienda. Después de cambiarlo, regenerar los CSV antes de probar el ETL.

Orden recomendado para una tienda de demostración:

1. Probar la importación con 2 o 3 categorías y productos.
2. Cambiar la moneda de nopCommerce a CRC.
3. Eliminar productos y categorías demo, si no existen pedidos que deban conservarse.
4. Importar categorías y luego productos.
5. Exportar el catálogo y verificar los 25 SKU.
6. Recrear el DW y ejecutar el ETL.

## Despliegue
1. Crear la Function App (Python, plan de consumo).
2. Configuración > variables: `SQL_DW`, `SQL_TIENDA`, `BLOB_CONN`, `BLOB_CONTENEDOR`, `ANTHROPIC_API_KEY`.
3. `./publicar.sh nombre-de-la-app`.
4. Probar desde el portal (Code + Test) y revisar los registros.
5. En Linux sin controlador ODBC 18 disponible, cambiar a `pymssql` (cambia la URL a `mssql+pymssql://...`).
