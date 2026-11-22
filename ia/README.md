# Módulo IA Analytics

Este módulo procesa datos mock y de la tienda ya integrados en el Data Warehouse.

## Capacidades

- `recomendaciones.py`: filtrado colaborativo basado en compras similares para personalizar la tienda.
- `pronostico.py`: pronóstico de ventas totales con tendencia y estacionalidad.
- `demanda_deep_learning.py`: red neuronal de dos capas que estima demanda mensual por producto.
- `resumen_comentarios.py`: clasificación y resumen de comentarios con un LLM.
- `reportes_ia.py`: reporte por rango de fechas para la futura pantalla de Administración.

## Probar reportes por fecha

```powershell
python ia\reportes_ia.py --desde 2025-01-01 --hasta 2025-12-31
```

El reporte es de solo lectura: consulta el Data Warehouse y produce un JSON con
ventas, productos destacados, baja rotación, sentimiento y predicciones.

## Flujo diario

La Azure Function ejecuta ETL y luego llama `correr_ia()`. Este flujo actualiza
el pronóstico, la demanda estimada y el análisis de comentarios. La interfaz de
Administración debe consumir el reporte, nunca conectarse directamente a la
base transaccional de la tienda.
