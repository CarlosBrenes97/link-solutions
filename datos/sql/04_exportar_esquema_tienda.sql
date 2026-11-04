-- Lista las tablas y columnas de la base de nopCommerce (para que Karla vea la estructura real).
-- Ejecutar sobre la base de la tienda y guardar el resultado como CSV en docs/esquema_tienda.csv
SELECT t.name AS tabla, c.name AS columna, ty.name AS tipo, c.max_length, c.is_nullable
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE t.name IN ('Order', 'OrderItem', 'Customer', 'Product', 'Category', 'Product_Category_Mapping', 'Address')
ORDER BY t.name, c.column_id;
