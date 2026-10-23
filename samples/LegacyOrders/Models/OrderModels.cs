using System;
using System.Collections.Generic;

namespace LegacyOrders.Models
{
    public enum OrderStatus
    {
        Draft = 0,
        PendingPayment = 1,
        Confirmed = 2,
        Shipped = 3,
        Delivered = 4,
        Cancelled = 5
    }

    public enum CustomerTier
    {
        Standard = 1,
        Silver = 2,
        Gold = 3,
        VIP = 4
    }

    public class Customer
    {
        public Guid Id { get; set; }
        public string Email { get; set; }
        public CustomerTier Tier { get; set; }
        public decimal CreditLimit { get; set; }
        public decimal OutstandingBalance { get; set; }
        public bool IsActive { get; set; }
        public bool IsFraudSuspected { get; set; }
    }

    public class OrderItem
    {
        public Guid ProductId { get; set; }
        public string Sku { get; set; }
        public int Quantity { get; set; }
        public decimal UnitPrice { get; set; }
        public bool IsPromotional { get; set; }
    }

    public class Order
    {
        public Guid Id { get; set; }
        public Guid CustomerId { get; set; }
        public List<OrderItem> Items { get; set; } = new List<OrderItem>();
        public decimal Subtotal { get; set; }
        public decimal DiscountAmount { get; set; }
        public decimal TaxAmount { get; set; }
        public decimal ShippingFee { get; set; }
        public decimal TotalAmount { get; set; }
        public OrderStatus Status { get; set; }
        public string PromoCode { get; set; }
        public DateTime CreatedAtUtc { get; set; }
        public DateTime? CancelledAtUtc { get; set; }
        public string CancellationReason { get; set; }
    }
}
