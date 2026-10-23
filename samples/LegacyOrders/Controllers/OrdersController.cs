using System;
using System.Threading.Tasks;
using LegacyOrders.Models;
using LegacyOrders.Services;

namespace LegacyOrders.Controllers
{
    // Attributes simulating ASP.NET Web API / ASP.NET Core
    public class HttpPostAttribute : Attribute { public HttpPostAttribute(string template = "") { } }
    public class HttpGetAttribute : Attribute { public HttpGetAttribute(string template = "") { } }
    public class RouteAttribute : Attribute { public RouteAttribute(string template) { } }
    public class AuthorizeAttribute : Attribute { public string Roles { get; set; } }

    public class ActionResult<T>
    {
        public T Value { get; set; }
        public int StatusCode { get; set; }
        public string Message { get; set; }
    }

    [Route("api/v1/orders")]
    [Authorize(Roles = "SalesAgent,Manager")]
    public class OrdersController
    {
        private readonly IOrderProcessingService _orderService;

        public OrdersController(IOrderProcessingService orderService)
        {
            _orderService = orderService ?? throw new ArgumentNullException(nameof(orderService));
        }

        [HttpPost("")]
        public async Task<ActionResult<Order>> CreateOrder(Order request)
        {
            try
            {
                if (request == null)
                {
                    return new ActionResult<Order> { StatusCode = 400, Message = "Order payload cannot be null" };
                }

                var processedOrder = await _orderService.ProcessNewOrderAsync(request);
                return new ActionResult<Order> { StatusCode = 201, Value = processedOrder };
            }
            catch (UnauthorizedAccessException ex)
            {
                return new ActionResult<Order> { StatusCode = 403, Message = ex.Message };
            }
            catch (InvalidOperationException ex)
            {
                return new ActionResult<Order> { StatusCode = 422, Message = ex.Message };
            }
            catch (Exception ex)
            {
                return new ActionResult<Order> { StatusCode = 500, Message = $"Internal processing error: {ex.Message}" };
            }
        }

        [HttpPost("{id}/cancel")]
        public async Task<ActionResult<bool>> CancelOrder(Guid id, string reason, string userRole)
        {
            try
            {
                bool result = await _orderService.CancelOrderAsync(id, reason, userRole);
                return new ActionResult<bool> { StatusCode = 200, Value = result };
            }
            catch (UnauthorizedAccessException ex)
            {
                return new ActionResult<bool> { StatusCode = 403, Message = ex.Message };
            }
            catch (InvalidOperationException ex)
            {
                return new ActionResult<bool> { StatusCode = 409, Message = ex.Message };
            }
            catch (Exception ex)
            {
                return new ActionResult<bool> { StatusCode = 500, Message = ex.Message };
            }
        }
    }
}
