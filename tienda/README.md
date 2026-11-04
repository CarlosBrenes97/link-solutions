# Tienda nopCommerce (Carlos)

El código de nopCommerce **no se guarda en este repositorio**: se descarga con el script y queda ignorado por Git
(`tienda/nopCommerce/`). Lo que sí se versiona aquí:

- `setup_tienda.ps1` y `setup_tienda.sh`: descargan nopCommerce en la versión estable que se elija.
- `plugins/`: los plugins propios (por ejemplo `Nop.Plugin.Misc.LinkAnalytics`, HU-14). El script los enlaza a `src/Plugins`.
- Esta carpeta documenta qué se configuró en el panel de administración, porque **esos cambios viven en la base de datos, no en archivos**.

## Descargar nopCommerce
1. Ver las versiones estables disponibles:
   ```bash
   git ls-remote --tags https://github.com/nopSolutions/nopCommerce.git "release-*"
   ```
   No usar la rama `develop`, es la de desarrollo.

   | Versión | SDK de .NET (según su `global.json`) | Comentario |
   |---|---|---|
   | `release-4.90.8` | 9.0 | **Recomendada**: la última de la serie 4.90, con documentación de plugins estable |
   | `release-5.00.0` | 10.0 | Más nueva. Verificar que Azure App Service y Visual Studio la soporten antes de elegirla |

2. Descargar:
   ```powershell
   .\setup_tienda.ps1 -Version release-4.90.8
   ```
   ```bash
   ./setup_tienda.sh release-4.90.8
   ```
3. Abrir `tienda/nopCommerce/src/NopCommerce.sln` en Visual Studio 2022, poner `Nop.Web` como proyecto de inicio y ejecutar.
4. Revisar `tienda/nopCommerce/global.json`: indica qué SDK de .NET se necesita.
5. En el instalador: correo y contraseña de administrador, tu base local (SQL Server Express o LocalDB) y marcar
   **«Create sample data»**.

## Configuración que hay que anotar en `CONFIGURACION.md`
Nombre de la tienda, logo, eslogan, misión y visión (HU-02), usuarios de prueba, dirección pública (cuando se publique) y
cualquier ajuste del panel. Así las compañeras pueden reproducirlo.

## Esquema para Karla
Después de instalar, ejecutar `datos/sql/04_exportar_esquema_tienda.sql` sobre la base de la tienda y guardar el resultado
en `docs/esquema_tienda.csv`.

## Licencia
Leer `tienda/nopCommerce/LICENSE.md` y conservar el crédito «Powered by nopCommerce» del pie de página.
