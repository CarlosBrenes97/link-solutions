# Reparto del trabajo

Cada persona tiene tareas en los tres sprints. Fechas límite: jueves 5, 12 y 19 de noviembre de 2026. Defensa: 23 de noviembre.

## Lista «To Do»

| Sprint | Carlos (CIO) | Karla (CDO) | María José (CAIO) |
|---|---|---|---|
| 1, 5 nov | HU-01 Tienda de prueba, HU-02 Identidad de la empresa | HU-03 Orden de la información, HU-04 Preguntas del negocio | HU-05 Novedad de la plataforma |
| 2, 12 nov | HU-06 Tienda en internet, HU-09 Actualización diaria | HU-07 Información de ejemplo, HU-08 Toda la información junta | HU-10 Ventas esperadas, HU-11 Resumen de comentarios |
| 3, 19 nov | HU-12 Conexión con otros programas | HU-13 Gráficos del negocio | HU-14 Análisis dentro de la tienda, HU-15 Demostración |
| 3, 19 nov | HU-16 Documento de propuesta (los tres) | | |

## Dónde vive el trabajo de cada historia

| Historia | Carpeta |
|---|---|
| HU-01, 02, 06, 12 | `tienda/` y configuración en Azure |
| HU-03, 07, 08 | `datos/sql`, `datos/generador`, `datos/etl` |
| HU-09 | `datos/etl/function_app.py` |
| HU-10, 11 | `ia/` |
| HU-13 | `bi/` |
| HU-14 | `tienda/plugins/` |
| HU-04, 05, 15, 16 | `docs/` |

## Lo que cada uno necesita de los demás
- Karla necesita de Carlos el esquema de la base de la tienda (`datos/sql/04_exportar_esquema_tienda.sql`) y la tienda corriendo.
- María José necesita de Karla el almacén con datos, o los CSV generados mientras tanto.
- Carlos necesita de Karla el ETL terminado para programarlo en Azure.
- Karla necesita de María José las tablas `pred_ventas` y `resumen_comentarios` para graficarlas.
