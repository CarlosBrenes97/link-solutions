# Power BI (Karla)

Guardar aquí el archivo `.pbix` y las capturas. **El `.pbix` no debe contener contraseñas**: usar el usuario de solo lectura.

## Conexión
Obtener datos > Base de datos SQL de Azure > servidor `NOMBRE.database.windows.net`, base `db-dw`, modo **Importar**.

## Modelo
Relaciones de uno a varios desde `dim_fecha`, `dim_producto` y `dim_cliente` hacia `fact_ventas` y `fact_comentarios`.
Marcar `dim_fecha` como tabla de fechas.

## Medidas de inicio
```
Total Ventas    = SUM ( fact_ventas[total_linea] )
Unidades        = SUM ( fact_ventas[cantidad] )
Pedidos         = DISTINCTCOUNT ( fact_ventas[pedido_id_nop] )
Ticket Promedio = DIVIDE ( [Total Ventas], [Pedidos] )
Ventas Mes Anterior = CALCULATE ( [Total Ventas], DATEADD ( dim_fecha[fecha], -1, MONTH ) )
Variación %     = DIVIDE ( [Total Ventas] - [Ventas Mes Anterior], [Ventas Mes Anterior] )
% Positivos     = DIVIDE ( CALCULATE ( COUNTROWS ( fact_comentarios ), fact_comentarios[sentimiento] = "positivo" ),
                           COUNTROWS ( fact_comentarios ) )
```

## Reglas de diseño
Una página por pregunta del negocio, con la pregunta como título. Máximo 5 colores. Ejes con título y unidades.
Elegir el gráfico con la imagen «chart chooser» del curso. Evitar pasteles de más de 4 partes y gráficos 3D.
