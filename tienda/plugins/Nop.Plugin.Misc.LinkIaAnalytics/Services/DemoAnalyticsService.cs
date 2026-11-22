using Nop.Plugin.Misc.LinkIaAnalytics.Models;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Services;

/// <summary>
/// Datos mock coherentes para demostrar el módulo de IA sin exponer credenciales.
/// La predicción de demanda corresponde al resultado de la red neuronal local.
/// </summary>
public static class DemoAnalyticsService
{
    public static ReporteIaModel CrearReporte(DateTime desde, DateTime hasta)
    {
        // El snapshot base representa 669 días de datos mock ya cargados en el DW.
        var dias = Math.Max(1, (hasta.Date - desde.Date).Days + 1);
        var factor = Math.Clamp(dias / 669m, 0.10m, 1m);

        var reporte = new ReporteIaModel
        {
        Periodo = new PeriodoModel { Desde = desde.ToString("yyyy-MM-dd"), Hasta = hasta.ToString("yyyy-MM-dd") },
        Resumen = new ResumenModel
        {
            Ingresos = Math.Round(878896000m * factor, 0),
            UnidadesVendidas = Math.Round(69464m * factor, 0),
            Clientes = Math.Max(1, (int)Math.Round(300m * factor, 0)),
            Compras = Math.Max(1, (int)Math.Round(17286m * factor, 0))
        },
        ProductosMayorIngreso =
        [
            new() { Nombre = "Bicicleta infantil", Categoria = "Aire libre", Unidades = 1576, Ingresos = 107168000 },
            new() { Nombre = "Casa de muñecas", Categoria = "Muñecos y peluches", Unidades = 1905, Ingresos = 73342500 },
            new() { Nombre = "Patineta", Categoria = "Aire libre", Unidades = 1914, Ingresos = 62205000 },
            new() { Nombre = "Robot a control remoto", Categoria = "Muñecos y peluches", Unidades = 2153, Ingresos = 59207500 },
            new() { Nombre = "Peluche de oso grande", Categoria = "Muñecos y peluches", Unidades = 2122, Ingresos = 45623000 }
        ],
        RotacionBaja =
        [
            new() { Nombre = "Bicicleta infantil", Categoria = "Aire libre", Unidades = 1576 },
            new() { Nombre = "Casa de muñecas", Categoria = "Muñecos y peluches", Unidades = 1905 },
            new() { Nombre = "Patineta", Categoria = "Aire libre", Unidades = 1914 },
            new() { Nombre = "Peluche de oso grande", Categoria = "Muñecos y peluches", Unidades = 2122 },
            new() { Nombre = "Robot a control remoto", Categoria = "Muñecos y peluches", Unidades = 2153 }
        ],
        ComentariosPorSentimiento =
        [
            new() { Sentimiento = "positivo", CantidadComentarios = 246 },
            new() { Sentimiento = "neutral", CantidadComentarios = 61 },
            new() { Sentimiento = "negativo", CantidadComentarios = 39 }
        ],
        PrediccionDemanda =
        [
            new() { Fecha = "2027-05-01", Nombre = "Juego de cartas clásico", Categoria = "Juegos de mesa", DemandaPrevista = 284.03m },
            new() { Fecha = "2027-05-01", Nombre = "Cometa", Categoria = "Aire libre", DemandaPrevista = 267.03m },
            new() { Fecha = "2027-05-01", Nombre = "Pistola de burbujas", Categoria = "Aire libre", DemandaPrevista = 265.18m },
            new() { Fecha = "2027-05-01", Nombre = "Paquete de 20 globos metalizados", Categoria = "Fiestas y disfraces", DemandaPrevista = 240.47m },
            new() { Fecha = "2027-05-01", Nombre = "Tarjeta musical", Categoria = "Regalos y detalles", DemandaPrevista = 236.69m }
        ],
        PrediccionVentas =
        [
            new() { Fecha = "2026-11-01", VentasPrevistas = 32929750.88m },
            new() { Fecha = "2026-12-01", VentasPrevistas = 43981745.25m },
            new() { Fecha = "2027-01-01", VentasPrevistas = 34151665.70m },
            new() { Fecha = "2027-02-01", VentasPrevistas = 36609704.04m },
            new() { Fecha = "2027-03-01", VentasPrevistas = 44407265.61m },
            new() { Fecha = "2027-04-01", VentasPrevistas = 48077977.39m }
        ]
        };

        foreach (var producto in reporte.ProductosMayorIngreso)
        {
            producto.Ingresos = Math.Round(producto.Ingresos * factor, 0);
            producto.Unidades = Math.Max(1, Math.Round(producto.Unidades * factor, 0));
        }
        foreach (var producto in reporte.RotacionBaja)
            producto.Unidades = Math.Max(1, Math.Round(producto.Unidades * factor, 0));
        foreach (var comentario in reporte.ComentariosPorSentimiento)
            comentario.CantidadComentarios = Math.Max(1, (int)Math.Round(comentario.CantidadComentarios * factor, 0));

        return reporte;
    }
}
