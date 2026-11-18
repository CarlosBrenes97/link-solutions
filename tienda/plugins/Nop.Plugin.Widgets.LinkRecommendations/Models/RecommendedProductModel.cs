namespace Nop.Plugin.Widgets.LinkRecommendations.Models;

public class RecommendedProductModel
{
    public string Name { get; init; } = string.Empty;
    public string Sku { get; init; } = string.Empty;
    public string ProductUrl { get; init; } = string.Empty;
    public string Price { get; init; } = string.Empty;
    public int Score { get; init; }
}
