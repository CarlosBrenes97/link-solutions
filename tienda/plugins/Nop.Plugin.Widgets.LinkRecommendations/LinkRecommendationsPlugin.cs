using Nop.Core.Domain.Cms;
using Nop.Services.Cms;
using Nop.Services.Configuration;
using Nop.Services.Plugins;
using Nop.Plugin.Widgets.LinkRecommendations.Components;
using Nop.Web.Framework.Infrastructure;

namespace Nop.Plugin.Widgets.LinkRecommendations;

/// <summary>
/// Widget público para presentar recomendaciones personalizadas.
/// </summary>
public class LinkRecommendationsPlugin : BasePlugin, IWidgetPlugin
{
    private readonly ISettingService _settingService;
    private readonly WidgetSettings _widgetSettings;

    public LinkRecommendationsPlugin(ISettingService settingService, WidgetSettings widgetSettings)
    {
        _settingService = settingService;
        _widgetSettings = widgetSettings;
    }

    public Task<IList<string>> GetWidgetZonesAsync()
    {
        return Task.FromResult<IList<string>>(new List<string>
        {
            PublicWidgetZones.HomepageBeforeProducts
        });
    }

    public Type GetWidgetViewComponent(string widgetZone)
    {
        return typeof(LinkRecommendationsViewComponent);
    }

    public bool HideInWidgetList => false;

    public override async Task InstallAsync()
    {
        if (!_widgetSettings.ActiveWidgetSystemNames.Contains(PluginDescriptor.SystemName))
        {
            _widgetSettings.ActiveWidgetSystemNames.Add(PluginDescriptor.SystemName);
            await _settingService.SaveSettingAsync(_widgetSettings);
        }

        await base.InstallAsync();
    }

    public override async Task UninstallAsync()
    {
        if (_widgetSettings.ActiveWidgetSystemNames.Contains(PluginDescriptor.SystemName))
        {
            _widgetSettings.ActiveWidgetSystemNames.Remove(PluginDescriptor.SystemName);
            await _settingService.SaveSettingAsync(_widgetSettings);
        }

        await base.UninstallAsync();
    }
}
