using System;
using System.Linq;
using LegacyOrders.Models;

namespace LegacyOrders.Services
{
    public interface IDiscountRuleEngine
    {
        decimal CalculateDiscount(Order order, Customer customer);
    }

    public class DiscountRuleEngine : IDiscountRuleEngine
    {
        private const decimal MaxDiscountPercentageCap = 0.25m; // Cap total discount at 25%
        private const decimal VipSubtotalThreshold = 500.00m;
        private const decimal VipDiscountRate = 0.15m;
        private const int BulkQuantityThreshold = 50;
        private const decimal BulkDiscountRate = 0.10m;

        public decimal CalculateDiscount(Order order, Customer customer)
        {
            if (order == null) throw new ArgumentNullException(nameof(order));
            if (customer == null) throw new ArgumentNullException(nameof(customer));

            decimal discount = 0.0m;

            // RULE-001: VIP Customer Tier Discount
            // VIP customers with order subtotal >= $500 get a 15% discount on subtotal
            if (customer.Tier == CustomerTier.VIP && order.Subtotal >= VipSubtotalThreshold)
            {
                discount += order.Subtotal * VipDiscountRate;
            }
            else if (customer.Tier == CustomerTier.Gold && order.Subtotal >= 300.00m)
            {
                // Gold tier gets 8% discount if subtotal >= $300
                discount += order.Subtotal * 0.08m;
            }

            // RULE-002: Bulk Order Volume Discount
            // Orders with total quantity > 50 non-promotional units receive an additional 10% discount on those items
            int eligibleBulkUnits = order.Items.Where(i => !i.IsPromotional).Sum(i => i.Quantity);
            if (eligibleBulkUnits > BulkQuantityThreshold)
            {
                decimal nonPromoSubtotal = order.Items.Where(i => !i.IsPromotional).Sum(i => i.Quantity * i.UnitPrice);
                discount += nonPromoSubtotal * BulkDiscountRate;
            }

            // RULE-003: Promotional Code Validation
            // Promo code 'HOLIDAY2024' provides flat $25 discount on orders over $100
            if (!string.IsNullOrWhiteSpace(order.PromoCode))
            {
                if (order.PromoCode.Equals("HOLIDAY2024", StringComparison.OrdinalIgnoreCase) && order.Subtotal >= 100.00m)
                {
                    discount += 25.00m;
                }
            }

            // RULE-004: Maximum Discount Safety Cap
            // Total discount cannot exceed 25% of the original subtotal
            decimal maxAllowedDiscount = order.Subtotal * MaxDiscountPercentageCap;
            if (discount > maxAllowedDiscount)
            {
                discount = maxAllowedDiscount;
            }

            return Math.Round(discount, 2);
        }
    }
}
