using Nop.Core;
using Nop.Core.Domain.Cms;
using Nop.Services.Common;
using Nop.Services.Configuration;
using Nop.Services.Cms;
using Nop.Services.Plugins;
using Nop.Plugin.Misc.LinkIaAnalytics.Components;
using Nop.Web.Framework.Infrastructure;

namespace Nop.Plugin.Misc.LinkIaAnalytics;

/// <summary>Plugin de uso exclusivo para administradores de la tienda.</summary>
public class LinkIaAnalyticsPlugin : BasePlugin, IMiscPlugin, IWidgetPlugin
{
    private readonly IWebHelper _webHelper;
    private readonly ISettingService _settingService;
    private readonly WidgetSettings _widgetSettings;

    public LinkIaAnalyticsPlugin(
        IWebHelper webHelper,
        ISettingService settingService,
        WidgetSettings widgetSettings)
    {
        _webHelper = webHelper;
        _settingService = settingService;
        _widgetSettings = widgetSettings;
    }

    public override string GetConfigurationPageUrl()
        => $"{_webHelper.GetStoreLocation()}{LinkIaAnalyticsDefaults.ConfigureUrl}";

    public Task<IList<string>> GetWidgetZonesAsync()
        => Task.FromResult<IList<string>>(new List<string> { AdminWidgetZones.HeaderAfter });

    public Type GetWidgetViewComponent(string widgetZone)
        => typeof(AdminBrandViewComponent);

    public bool HideInWidgetList => true;

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
