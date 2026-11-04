-- Consultas para comprobar que el almacén responde las preguntas del negocio.
-- Sirven también para validar lo que muestra Power BI.

-- 1. Ventas por mes
SELECT f.anio, f.mes, SUM(v.total_linea) AS ventas
FROM fact_ventas v JOIN dim_fecha f ON f.fecha_key = v.fecha_key
GROUP BY f.anio, f.mes ORDER BY f.anio, f.mes;

-- 2. Los 10 productos que más ingresos generan
SELECT TOP 10 p.nombre, SUM(v.total_linea) AS ingresos
FROM fact_ventas v JOIN dim_producto p ON p.producto_key = v.producto_key
GROUP BY p.nombre ORDER BY ingresos DESC;

-- 3. Ventas por categoría
SELECT p.categoria, SUM(v.total_linea) AS ingresos
FROM fact_ventas v JOIN dim_producto p ON p.producto_key = v.producto_key
GROUP BY p.categoria ORDER BY ingresos DESC;

-- 4. Ventas por tipo de cliente y provincia
SELECT c.tipo_cliente, c.provincia, SUM(v.total_linea) AS ventas, COUNT(DISTINCT v.pedido_id_nop) AS pedidos
FROM fact_ventas v JOIN dim_cliente c ON c.cliente_key = v.cliente_key
GROUP BY c.tipo_cliente, c.provincia ORDER BY ventas DESC;

-- 5. Sentimiento por producto contra sus ventas
SELECT p.nombre,
       SUM(CASE WHEN fc.sentimiento = 'positivo' THEN 1 ELSE 0 END) AS positivos,
       SUM(CASE WHEN fc.sentimiento = 'negativo' THEN 1 ELSE 0 END) AS negativos,
       (SELECT SUM(v.total_linea) FROM fact_ventas v WHERE v.producto_key = p.producto_key) AS ventas
FROM dim_producto p LEFT JOIN fact_comentarios fc ON fc.producto_key = p.producto_key
GROUP BY p.producto_key, p.nombre;

-- 6. Pronóstico de ventas
SELECT fecha, ventas_previstas, limite_inferior, limite_superior
FROM pred_ventas WHERE producto_key IS NULL ORDER BY fecha;

-- Comprobaciones de calidad del ETL
SELECT COUNT(*) AS lineas_de_venta FROM fact_ventas;
SELECT email, COUNT(*) FROM dim_cliente GROUP BY email HAVING COUNT(*) > 1;  -- debe dar 0 filas
