using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using LegacyOrders.Models;

namespace LegacyOrders.Data
{
    public interface IOrderRepository
    {
        Task<Order> GetByIdAsync(Guid id);
        Task<Customer> GetCustomerAsync(Guid customerId);
        Task<int> GetInventoryLevelAsync(Guid productId);
        Task InsertOrderAsync(Order order);
        Task UpdateOrderStatusAsync(Guid orderId, OrderStatus status);
        Task RecordAuditLogAsync(string action, Guid entityId, string details);
    }

    public class OrderRepository : IOrderRepository
    {
        // Simulated database storage for legacy repository pattern
        public async Task<Order> GetByIdAsync(Guid id)
        {
            await Task.Yield();
            return null; // DB select from Orders where Id = @id
        }

        public async Task<Customer> GetCustomerAsync(Guid customerId)
        {
            await Task.Yield();
            return new Customer
            {
                Id = customerId,
                CreditLimit = 5000.00m,
                OutstandingBalance = 1200.00m,
                IsActive = true,
                Tier = CustomerTier.Gold
            };
        }

        public async Task<int> GetInventoryLevelAsync(Guid productId)
        {
            await Task.Yield();
            return 100; // DB select StockQuantity from Inventory where ProductId = @productId
        }

        public async Task InsertOrderAsync(Order order)
        {
            await Task.Yield();
            // INSERT INTO Orders (Id, CustomerId, Subtotal, DiscountAmount, TotalAmount, Status) VALUES (...)
        }

        public async Task UpdateOrderStatusAsync(Guid orderId, OrderStatus status)
        {
            await Task.Yield();
            // UPDATE Orders SET Status = @status, UpdatedAt = GETUTCDATE() WHERE Id = @orderId
        }

        public async Task RecordAuditLogAsync(string action, Guid entityId, string details)
        {
            await Task.Yield();
            // INSERT INTO AuditLogs (Action, EntityId, Details, CreatedAt) VALUES (@action, @entityId, @details, GETUTCDATE())
        }
    }
}
