-- Usuario de solo lectura sobre la base de nopCommerce (HU: conexión con otros programas).
-- 1) En Azure SQL, el LOGIN se crea conectado a la base master del servidor:
--      CREATE LOGIN etl_lector WITH PASSWORD = '<contraseña larga y única>';
-- 2) Luego, conectado a la base de la tienda:
CREATE USER etl_lector FOR LOGIN etl_lector;
GRANT SELECT ON [dbo].[Order]     TO etl_lector;
GRANT SELECT ON [dbo].[OrderItem] TO etl_lector;
GRANT SELECT ON [dbo].[Customer]  TO etl_lector;
GRANT SELECT ON [dbo].[Product]   TO etl_lector;
-- Verificar los nombres de las tablas en la versión instalada antes de ejecutar.
-- La sintaxis de Azure SQL puede variar: revisar la documentación vigente.
