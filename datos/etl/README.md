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

## Verificar antes de usar con nopCommerce real
`extraer_tienda()` usa las tablas `[Order]`, `OrderItem`, `Customer` y `Product` y las columnas `Deleted`, `OrderStatusId`,
`UnitPriceExclTax`, `CreatedOnUtc`, `Sku`. Comparar con la base real (ver `datos/sql/04_exportar_esquema_tienda.sql`) y
ajustar la lista `ESTADOS_PEDIDO_EXCLUIDOS`.

## Despliegue
1. Crear la Function App (Python, plan de consumo).
2. Configuración > variables: `SQL_DW`, `SQL_TIENDA`, `BLOB_CONN`, `BLOB_CONTENEDOR`, `ANTHROPIC_API_KEY`.
3. `./publicar.sh nombre-de-la-app`.
4. Probar desde el portal (Code + Test) y revisar los registros.
5. En Linux sin controlador ODBC 18 disponible, cambiar a `pymssql` (cambia la URL a `mssql+pymssql://...`).
