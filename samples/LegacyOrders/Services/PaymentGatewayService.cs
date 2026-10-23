using System;
using System.Net.Http;
using System.Threading.Tasks;
using LegacyOrders.Models;

namespace LegacyOrders.Services
{
    public interface IPaymentGatewayService
    {
        Task<string> AuthorizePaymentAsync(Guid orderId, decimal amount, Customer customer);
    }

    public class PaymentGatewayService : IPaymentGatewayService
    {
        private const decimal SecondaryFraudReviewThreshold = 10000.00m;
        private readonly HttpClient _httpClient;

        public PaymentGatewayService(HttpClient httpClient)
        {
            _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        }

        public async Task<string> AuthorizePaymentAsync(Guid orderId, decimal amount, Customer customer)
        {
            if (customer.IsFraudSuspected)
            {
                throw new InvalidOperationException($"Payment blocked: Customer {customer.Id} is flagged for suspected fraud.");
            }

            // RULE-005: High-Value Secondary Fraud Review
            // Orders exceeding $10,000 require manual compliance approval before payment authorization
            if (amount > SecondaryFraudReviewThreshold)
            {
                throw new InvalidOperationException($"Secondary fraud review required for transactions exceeding ${SecondaryFraudReviewThreshold}.");
            }

            // Call external payment provider endpoint: /v2/charge
            var payload = new
            {
                TransactionId = Guid.NewGuid(),
                OrderId = orderId,
                CustomerEmail = customer.Email,
                ChargeAmount = amount,
                Currency = "USD"
            };

            int maxAttempts = 3;
            for (int attempt = 1; attempt <= maxAttempts; attempt++)
            {
                try
                {
                    // Simulated external API call to payment gateway
                    var response = await _httpClient.PostAsync("https://api.acmepayments.com/v2/charge", null);
                    if (response.IsSuccessStatusCode)
                    {
                        return $"AUTH_{Guid.NewGuid():N}";
                    }
                    if (attempt == maxAttempts)
                    {
                        throw new HttpRequestException($"Payment gateway returned error: {response.StatusCode}");
                    }
                }
                catch (HttpRequestException ex) when (attempt < maxAttempts)
                {
                    await Task.Delay(1000 * attempt);
                }
            }

            throw new TimeoutException("Payment gateway timed out after 3 retry attempts.");
        }
    }
}
