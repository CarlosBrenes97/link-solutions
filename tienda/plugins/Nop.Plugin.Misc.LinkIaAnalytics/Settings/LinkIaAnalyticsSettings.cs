using Nop.Core.Configuration;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Settings;

/// <summary>La conexión se guarda en la configuración de nopCommerce, nunca en Git.</summary>
public class LinkIaAnalyticsSettings : ISettings
{
    public string DataWarehouseConnectionString { get; set; } = string.Empty;
}
