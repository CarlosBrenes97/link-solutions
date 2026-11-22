using Nop.Services.Events;
using Nop.Services.Plugins;
using Nop.Web.Framework.Events;
using Nop.Web.Framework.Menu;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Services;

/// <summary>Agrega la entrada IA Analytics debajo de Informes.</summary>
public class EventConsumer : IConsumer<AdminMenuCreatedEvent>
{
    private readonly IPluginManager<IPlugin> _pluginManager;

    public EventConsumer(IPluginManager<IPlugin> pluginManager) => _pluginManager = pluginManager;

    public async Task HandleEventAsync(AdminMenuCreatedEvent eventMessage)
    {
        var plugin = await _pluginManager.LoadPluginBySystemNameAsync(LinkIaAnalyticsDefaults.SystemName);
        if (plugin is null)
            return;

        var reports = eventMessage.RootMenuItem.GetItemBySystemName("Reports");
        if (reports is null || reports.ChildNodes.Any(item => item.SystemName == LinkIaAnalyticsDefaults.SystemName))
            return;

        reports.ChildNodes.Add(new AdminMenuItem
        {
            SystemName = LinkIaAnalyticsDefaults.SystemName,
            Title = "IA Analytics",
            Url = eventMessage.GetMenuItemUrl("LinkIaAnalytics", "Dashboard"),
            IconClass = "far fa-chart-bar",
            Visible = true
        });
    }
}
