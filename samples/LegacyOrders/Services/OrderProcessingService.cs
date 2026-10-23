using System;
using System.Threading.Tasks;
using LegacyOrders.Data;
using LegacyOrders.Models;

namespace LegacyOrders.Services
{
    public interface IOrderProcessingService
    {
        Task<Order> ProcessNewOrderAsync(Order order);
        Task<bool> CancelOrderAsync(Guid orderId, string reason, string userRole);
    }

    public class OrderProcessingService : IOrderProcessingService
    {
        private const decimal MinimumOrderAmount = 10.00m;
        private readonly IOrderRepository _repository;
        private readonly IDiscountRuleEngine _discountEngine;
        private readonly IPaymentGatewayService _paymentGateway;

        public OrderProcessingService(
            IOrderRepository repository,
            IDiscountRuleEngine discountEngine,
            IPaymentGatewayService paymentGateway)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
            _discountEngine = discountEngine ?? throw new ArgumentNullException(nameof(discountEngine));
            _paymentGateway = paymentGateway ?? throw new ArgumentNullException(nameof(paymentGateway));
        }

        public async Task<Order> ProcessNewOrderAsync(Order order)
        {
            if (order == null) throw new ArgumentNullException(nameof(order));
            if (order.Items == null || order.Items.Count == 0)
            {
                throw new InvalidOperationException("Order must contain at least one item.");
            }

            var customer = await _repository.GetCustomerAsync(order.CustomerId);
            if (customer == null)
            {
                throw new InvalidOperationException($"Customer {order.CustomerId} does not exist.");
            }
            if (!customer.IsActive)
            {
                throw new InvalidOperationException("Customer account is deactivated.");
            }

            // RULE-006: Inventory Availability Check
            // Verify all items have sufficient warehouse stock prior to order placement
            foreach (var item in order.Items)
            {
                int stock = await _repository.GetInventoryLevelAsync(item.ProductId);
                if (stock < item.Quantity)
                {
                    throw new InvalidOperationException($"Insufficient inventory for SKU {item.Sku}. In stock: {stock}, requested: {item.Quantity}.");
                }
            }

            // Calculate Subtotal
            decimal subtotal = 0m;
            foreach (var item in order.Items)
            {
                if (item.UnitPrice <= 0)
                {
                    throw new InvalidOperationException($"Invalid unit price for SKU {item.Sku}.");
                }
                subtotal += item.UnitPrice * item.Quantity;
            }
            order.Subtotal = subtotal;

            // RULE-007: Minimum Order Total Requirement
            // Orders must meet minimum threshold of $10.00 before taxes and discounts
            if (order.Subtotal < MinimumOrderAmount)
            {
                throw new InvalidOperationException($"Order subtotal ${order.Subtotal} is below minimum required threshold of ${MinimumOrderAmount}.");
            }

            // Apply discounts via discount engine
            order.DiscountAmount = _discountEngine.CalculateDiscount(order, customer);

            // Compute standard tax (8.25%) and shipping
            order.TaxAmount = Math.Round((order.Subtotal - order.DiscountAmount) * 0.0825m, 2);
            order.ShippingFee = (order.Subtotal >= 75.00m) ? 0.00m : 9.99m; // Free shipping over $75
            order.TotalAmount = order.Subtotal - order.DiscountAmount + order.TaxAmount + order.ShippingFee;

            // RULE-008: Credit Limit Enforcement
            // Total outstanding debt plus current order amount must not exceed the customer credit limit
            if (customer.OutstandingBalance + order.TotalAmount > customer.CreditLimit)
            {
                throw new InvalidOperationException($"Order exceeds customer credit limit. Limit: ${customer.CreditLimit}, Current Balance: ${customer.OutstandingBalance}, Order Total: ${order.TotalAmount}.");
            }

            // State Transition: Draft -> PendingPayment
            order.Status = OrderStatus.PendingPayment;
            order.CreatedAtUtc = DateTime.UtcNow;
            await _repository.InsertOrderAsync(order);

            // Execute Payment Authorization
            string authCode = await _paymentGateway.AuthorizePaymentAsync(order.Id, order.TotalAmount, customer);

            // State Transition: PendingPayment -> Confirmed
            order.Status = OrderStatus.Confirmed;
            await _repository.UpdateOrderStatusAsync(order.Id, OrderStatus.Confirmed);
            await _repository.RecordAuditLogAsync("ORDER_CONFIRMED", order.Id, $"AuthCode: {authCode}, Total: {order.TotalAmount}");

            return order;
        }

        public async Task<bool> CancelOrderAsync(Guid orderId, string reason, string userRole)
        {
            var order = await _repository.GetByIdAsync(orderId);
            if (order == null) throw new InvalidOperationException($"Order {orderId} not found.");

            // RULE-009: Cancellation Role Authorization
            // High-value orders (> $5,000) require Manager role to cancel; SalesAgent can only cancel orders <= $5,000
            if (order.TotalAmount > 5000.00m && !string.Equals(userRole, "Manager", StringComparison.OrdinalIgnoreCase))
            {
                throw new UnauthorizedAccessException("Manager authorization required to cancel orders exceeding $5,000.");
            }

            // State Transition Guard: Can only cancel Draft, PendingPayment, or Confirmed orders
            if (order.Status == OrderStatus.Shipped || order.Status == OrderStatus.Delivered)
            {
                throw new InvalidOperationException($"Cannot cancel order in status {order.Status}. A return workflow must be initiated.");
            }

            order.Status = OrderStatus.Cancelled;
            order.CancelledAtUtc = DateTime.UtcNow;
            order.CancellationReason = reason;

            await _repository.UpdateOrderStatusAsync(order.Id, OrderStatus.Cancelled);
            await _repository.RecordAuditLogAsync("ORDER_CANCELLED", order.Id, $"Reason: {reason}, Role: {userRole}");
            return true;
        }
    }
}
