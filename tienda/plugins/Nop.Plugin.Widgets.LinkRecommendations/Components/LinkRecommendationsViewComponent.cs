using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Nop.Core;
using Nop.Plugin.Widgets.LinkRecommendations.Models;
using Nop.Services.Catalog;
using Nop.Services.Customers;
using Nop.Services.Directory;
using Nop.Services.Orders;
using Nop.Services.Seo;
using Nop.Web.Framework.Components;

namespace Nop.Plugin.Widgets.LinkRecommendations.Components;

/// <summary>
/// Compara las compras del cliente actual con las de otros clientes.
/// Un producto recibe un punto por cada cliente similar que también lo compró.
/// </summary>
public class LinkRecommendationsViewComponent : NopViewComponent
{
    private readonly ICustomerService _customerService;
    private readonly IOrderService _orderService;
    private readonly IPriceFormatter _priceFormatter;
    private readonly IProductService _productService;
    private readonly IUrlRecordService _urlRecordService;
    private readonly IWorkContext _workContext;
    private readonly ILogger<LinkRecommendationsViewComponent> _logger;

    public LinkRecommendationsViewComponent(
        ICustomerService customerService,
        IOrderService orderService,
        IPriceFormatter priceFormatter,
        IProductService productService,
        IUrlRecordService urlRecordService,
        IWorkContext workContext,
        ILogger<LinkRecommendationsViewComponent> logger)
    {
        _customerService = customerService;
        _orderService = orderService;
        _priceFormatter = priceFormatter;
        _productService = productService;
        _urlRecordService = urlRecordService;
        _workContext = workContext;
        _logger = logger;
    }

    public async Task<IViewComponentResult> InvokeAsync(string widgetZone, object additionalData)
    {
        try
        {
        var customer = await _workContext.GetCurrentCustomerAsync();
        if (await _customerService.IsGuestAsync(customer))
            return Content(string.Empty);

        var myOrders = await _orderService.SearchOrdersAsync(customerId: customer.Id, pageSize: 200);
        var purchasedProductIds = new HashSet<int>();

        foreach (var order in myOrders)
        {
            foreach (var item in await _orderService.GetOrderItemsAsync(order.Id))
                purchasedProductIds.Add(item.ProductId);
        }

        if (!purchasedProductIds.Any())
            return Content(string.Empty);

        // En una versión productiva con gran volumen esto se reemplaza por una tabla
        // precalculada por el ETL/servicio de IA. Para el demo usa los pedidos de la tienda.
        var allOrders = await _orderService.SearchOrdersAsync(pageSize: 200);
        var productsByCustomer = new Dictionary<int, HashSet<int>>();

        foreach (var order in allOrders.Where(order => order.CustomerId != customer.Id))
        {
            if (!productsByCustomer.TryGetValue(order.CustomerId, out var productIds))
            {
                productIds = [];
                productsByCustomer[order.CustomerId] = productIds;
            }

            foreach (var item in await _orderService.GetOrderItemsAsync(order.Id))
                productIds.Add(item.ProductId);
        }

        var scores = new Dictionary<int, int>();
        foreach (var otherCustomerProducts in productsByCustomer.Values)
        {
            if (!otherCustomerProducts.Overlaps(purchasedProductIds))
                continue;

            foreach (var productId in otherCustomerProducts.Except(purchasedProductIds))
                scores[productId] = scores.GetValueOrDefault(productId) + 1;
        }

        if (!scores.Any())
            return Content(string.Empty);

        var candidateIds = scores
            .OrderByDescending(score => score.Value)
            .ThenBy(score => score.Key)
            .Take(3)
            .Select(score => score.Key)
            .ToArray();

        var candidates = await _productService.GetProductsByIdsAsync(candidateIds);
        var model = new List<RecommendedProductModel>();

        foreach (var product in candidates
                     .Where(product => product.Published && !product.Deleted)
                     .OrderByDescending(product => scores[product.Id]))
        {
            var seName = await _urlRecordService.GetSeNameAsync(product);
            model.Add(new RecommendedProductModel
            {
                Name = product.Name,
                Sku = product.Sku,
                ProductUrl = Url.RouteUrl("Product", new { SeName = seName }) ?? $"/{seName}",
                Price = await _priceFormatter.FormatPriceAsync(product.Price),
                Score = scores[product.Id]
            });
        }

        return model.Any()
            ? View("~/Plugins/Widgets.LinkRecommendations/Views/PublicInfo.cshtml", model)
            : Content(string.Empty);
        }
        catch (Exception exception)
        {
            _logger.LogError(exception, "No fue posible preparar las recomendaciones del cliente.");
            return Content(string.Empty);
        }
    }
}
