using Microsoft.AspNetCore.Mvc;
using Nop.Plugin.Misc.LinkIaAnalytics.Models;
using Nop.Plugin.Misc.LinkIaAnalytics.Services;
using Nop.Services.Messages;
using Nop.Services.Security;
using Nop.Web.Framework;
using Nop.Web.Framework.Controllers;
using Nop.Web.Framework.Mvc.Filters;

namespace Nop.Plugin.Misc.LinkIaAnalytics.Controllers;

[AutoValidateAntiforgeryToken]
[AuthorizeAdmin]
[Area(AreaNames.ADMIN)]
public class LinkIaAnalyticsController : BasePluginController
{
    private readonly INotificationService _notificationService;

    public LinkIaAnalyticsController(INotificationService notificationService)
    {
        _notificationService = notificationService;
    }

    public virtual IActionResult Dashboard(string? desde, string? hasta)
    {
        var hoy = DateTime.UtcNow.Date;
        var desdeSeguro = DateTime.TryParse(desde, out var inicio) ? inicio.Date : hoy.AddMonths(-12);
        var hastaSeguro = DateTime.TryParse(hasta, out var fin) ? fin.Date : hoy;
        var model = new DashboardModel
        {
            Desde = desdeSeguro.ToString("yyyy-MM-dd"),
            Hasta = hastaSeguro.ToString("yyyy-MM-dd"),
            ApiConfigurada = true
        };

        if (desdeSeguro > hastaSeguro || hastaSeguro > hoy)
        {
            model.Error = "Seleccione un periodo válido que no incluya fechas futuras.";
            return View("~/Plugins/Misc.LinkIaAnalytics/Views/Admin/Dashboard.cshtml", model);
        }

        model.Reporte = DemoAnalyticsService.CrearReporte(desdeSeguro, hastaSeguro);
        model.Mensaje = $"Reporte generado para el período {model.Desde} a {model.Hasta}.";

        return View("~/Plugins/Misc.LinkIaAnalytics/Views/Admin/Dashboard.cshtml", model);
    }

    public virtual IActionResult Configure()
    {
        return View("~/Plugins/Misc.LinkIaAnalytics/Views/Admin/Configure.cshtml", new ConfigureModel());
    }

    [HttpPost]
    public virtual IActionResult Configure(ConfigureModel model)
    {
        if (!ModelState.IsValid)
            return View("~/Plugins/Misc.LinkIaAnalytics/Views/Admin/Configure.cshtml", model);

        _notificationService.SuccessNotification("El módulo usa datos mock de demostración y no requiere credenciales.");
        return RedirectToAction(nameof(Configure));
    }
}
