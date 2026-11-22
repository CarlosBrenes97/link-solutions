using System.Text.Json.Serialization;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Models;

public class DashboardModel
{
    public string Desde { get; set; } = string.Empty;
    public string Hasta { get; set; } = string.Empty;
    public bool ApiConfigurada { get; set; }
    public string Error { get; set; } = string.Empty;
    public string Mensaje { get; set; } = string.Empty;
    public ReporteIaModel? Reporte { get; set; }
}

public class ConfigureModel
{
    public string DataWarehouseConnectionString { get; set; } = string.Empty;
    public bool IsConfigured { get; set; }
}

public class ReporteIaModel
{
    [JsonPropertyName("periodo")] public PeriodoModel Periodo { get; set; } = new();
    [JsonPropertyName("resumen")] public ResumenModel Resumen { get; set; } = new();
    [JsonPropertyName("productos_mayor_ingreso")] public List<ProductoIngresoModel> ProductosMayorIngreso { get; set; } = [];
    [JsonPropertyName("rotacion_baja")] public List<ProductoIngresoModel> RotacionBaja { get; set; } = [];
    [JsonPropertyName("comentarios_por_sentimiento")] public List<SentimientoModel> ComentariosPorSentimiento { get; set; } = [];
    [JsonPropertyName("prediccion_demanda")] public List<DemandaModel> PrediccionDemanda { get; set; } = [];
    [JsonPropertyName("prediccion_ventas")] public List<VentaPrevistaModel> PrediccionVentas { get; set; } = [];
}

public class PeriodoModel
{
    [JsonPropertyName("desde")] public string Desde { get; set; } = string.Empty;
    [JsonPropertyName("hasta")] public string Hasta { get; set; } = string.Empty;
}

public class ResumenModel
{
    [JsonPropertyName("ingresos")] public decimal Ingresos { get; set; }
    [JsonPropertyName("unidades_vendidas")] public decimal UnidadesVendidas { get; set; }
    [JsonPropertyName("clientes")] public int Clientes { get; set; }
    [JsonPropertyName("compras")] public int Compras { get; set; }
}

public class ProductoIngresoModel
{
    [JsonPropertyName("nombre")] public string Nombre { get; set; } = string.Empty;
    [JsonPropertyName("categoria")] public string Categoria { get; set; } = string.Empty;
    [JsonPropertyName("ingresos")] public decimal Ingresos { get; set; }
    [JsonPropertyName("unidades")] public decimal Unidades { get; set; }
}

public class SentimientoModel
{
    [JsonPropertyName("sentimiento")] public string Sentimiento { get; set; } = string.Empty;
    [JsonPropertyName("cantidad_comentarios")] public int CantidadComentarios { get; set; }
}

public class DemandaModel
{
    [JsonPropertyName("fecha")] public string Fecha { get; set; } = string.Empty;
    [JsonPropertyName("nombre")] public string Nombre { get; set; } = string.Empty;
    [JsonPropertyName("categoria")] public string Categoria { get; set; } = string.Empty;
    [JsonPropertyName("demanda_prevista")] public decimal DemandaPrevista { get; set; }
}

public class VentaPrevistaModel
{
    [JsonPropertyName("fecha")] public string Fecha { get; set; } = string.Empty;
    [JsonPropertyName("ventas_previstas")] public decimal VentasPrevistas { get; set; }
}
