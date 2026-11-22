using Microsoft.AspNetCore.Mvc;
using Nop.Web.Framework.Components;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Components;

/// <summary>Inyecta el estilo de marca del proyecto en las páginas administrativas.</summary>
public sealed class AdminBrandViewComponent : NopViewComponent
{
    public IViewComponentResult Invoke(string widgetZone, object additionalData)
        => View("~/Plugins/Misc.LinkIaAnalytics/Views/Admin/BrandOverride.cshtml");
}
