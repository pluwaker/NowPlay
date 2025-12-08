using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace NowMediaMonitor
{
    /// <summary>
    /// Manages HTTP requests with timeout protection, retry logic, and semaphore-based concurrency control
    /// </summary>
    public class HttpClientPool : IDisposable
    {
        private readonly HttpClient client;
        private readonly SemaphoreSlim httpSemaphore = new SemaphoreSlim(1, 1);
        private readonly TimeSpan requestTimeout = TimeSpan.FromSeconds(5);
        private readonly TimeSpan semaphoreTimeout = TimeSpan.FromSeconds(3);
        
        // Retry configuration
        private readonly int[] retryDelaysMs = { 100, 500, 1000 };
        
        public HttpClientPool(string baseUrl)
        {
            if (string.IsNullOrEmpty(baseUrl))
            {
                throw new ArgumentNullException(nameof(baseUrl));
            }
            
            client = new HttpClient
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = requestTimeout
            };
            
            Console.WriteLine($"✅ HttpClientPool initialized (baseUrl: {baseUrl}, requestTimeout: {requestTimeout.TotalSeconds}s, semaphoreTimeout: {semaphoreTimeout.TotalSeconds}s)");
        }
        
        /// <summary>
        /// Sends an update to the specified endpoint with timeout-protected semaphore acquisition
        /// </summary>
        public async Task<bool> SendUpdate(object data, string endpoint)
        {
            if (data == null)
            {
                throw new ArgumentNullException(nameof(data));
            }
            
            if (string.IsNullOrEmpty(endpoint))
            {
                throw new ArgumentNullException(nameof(endpoint));
            }
            
            bool semaphoreAcquired = false;
            var startTime = DateTime.Now;
            
            try
            {
                Console.WriteLine($"🔄 HttpClientPool: Attempting to acquire HTTP semaphore (timeout: {semaphoreTimeout.TotalSeconds}s)");
                
                // Use timeout-protected semaphore acquisition
                semaphoreAcquired = await httpSemaphore.WaitAsync(semaphoreTimeout);
                
                if (!semaphoreAcquired)
                {
                    var elapsed = DateTime.Now - startTime;
                    Console.WriteLine($"⚠️ HttpClientPool: Semaphore acquisition timeout after {elapsed.TotalSeconds:F2}s");
                    Console.WriteLine($"⚠️ HttpClientPool: Skipping request to {endpoint}");
                    return false;
                }
                
                var semaphoreAcquireTime = DateTime.Now - startTime;
                Console.WriteLine($"✅ HttpClientPool: Semaphore acquired in {semaphoreAcquireTime.TotalMilliseconds:F0}ms");
                
                // Serialize data to JSON
                var json = JsonSerializer.Serialize(data);
                using var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                // Send with retry logic
                var requestStartTime = DateTime.Now;
                bool success = await SendWithRetry(content, endpoint, maxRetries: 2);
                var requestDuration = DateTime.Now - requestStartTime;
                
                if (success)
                {
                    Console.WriteLine($"✅ HttpClientPool: Request to {endpoint} succeeded in {requestDuration.TotalMilliseconds:F0}ms");
                    DiagnosticLogger.LogHttpRequest(endpoint, true, (long)requestDuration.TotalMilliseconds);
                }
                else
                {
                    Console.WriteLine($"❌ HttpClientPool: Request to {endpoint} failed after {requestDuration.TotalMilliseconds:F0}ms");
                    DiagnosticLogger.LogHttpRequest(endpoint, false, (long)requestDuration.TotalMilliseconds, "All retry attempts failed");
                }
                
                return success;
            }
            catch (Exception ex)
            {
                var elapsed = DateTime.Now - startTime;
                Console.WriteLine($"❌ HttpClientPool: Unexpected error in SendUpdate after {elapsed.TotalMilliseconds:F0}ms: {ex.Message}");
                return false;
            }
            finally
            {
                // CRITICAL: Always release semaphore in finally block to guarantee release
                if (semaphoreAcquired)
                {
                    httpSemaphore.Release();
                    var totalTime = DateTime.Now - startTime;
                    Console.WriteLine($"🔓 HttpClientPool: Semaphore released (total time: {totalTime.TotalMilliseconds:F0}ms)");
                }
            }
        }
        
        /// <summary>
        /// Sends HTTP request with exponential backoff retry logic
        /// </summary>
        private async Task<bool> SendWithRetry(HttpContent content, string endpoint, int maxRetries)
        {
            int attempt = 0;
            
            while (attempt <= maxRetries)
            {
                try
                {
                    if (attempt > 0)
                    {
                        var delay = retryDelaysMs[attempt - 1];
                        Console.WriteLine($"🔄 HttpClientPool: Retry attempt {attempt}/{maxRetries} after {delay}ms delay");
                        await Task.Delay(delay);
                    }
                    else
                    {
                        Console.WriteLine($"📤 HttpClientPool: Sending request to {endpoint} (attempt {attempt + 1}/{maxRetries + 1})");
                    }
                    
                    var requestStartTime = DateTime.Now;
                    using var response = await client.PostAsync(endpoint, content);
                    var requestDuration = DateTime.Now - requestStartTime;
                    
                    response.EnsureSuccessStatusCode();
                    
                    Console.WriteLine($"✅ HttpClientPool: Request succeeded on attempt {attempt + 1} ({requestDuration.TotalMilliseconds:F0}ms, status: {(int)response.StatusCode})");
                    return true;
                }
                catch (TaskCanceledException ex)
                {
                    // Timeout occurred
                    Console.WriteLine($"⏱️ HttpClientPool: Request timeout on attempt {attempt + 1}: {ex.Message}");
                    
                    if (attempt >= maxRetries)
                    {
                        Console.WriteLine($"❌ HttpClientPool: All retry attempts exhausted due to timeout");
                        return false;
                    }
                }
                catch (HttpRequestException ex)
                {
                    // Network error occurred
                    Console.WriteLine($"🌐 HttpClientPool: Network error on attempt {attempt + 1}: {ex.Message}");
                    
                    if (attempt >= maxRetries)
                    {
                        Console.WriteLine($"❌ HttpClientPool: All retry attempts exhausted due to network error");
                        return false;
                    }
                }
                catch (Exception ex)
                {
                    // Unexpected error
                    Console.WriteLine($"❌ HttpClientPool: Unexpected error on attempt {attempt + 1}: {ex.Message}");
                    
                    if (attempt >= maxRetries)
                    {
                        Console.WriteLine($"❌ HttpClientPool: All retry attempts exhausted due to unexpected error");
                        return false;
                    }
                }
                
                attempt++;
            }
            
            return false;
        }
        
        // IDisposable implementation
        private bool disposed = false;
        
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
        
        protected virtual void Dispose(bool disposing)
        {
            if (!disposed)
            {
                if (disposing)
                {
                    try
                    {
                        httpSemaphore?.Dispose();
                        client?.Dispose();
                        Console.WriteLine("🧹 HttpClientPool disposed");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"⚠️ Error disposing HttpClientPool: {ex.Message}");
                    }
                }
                disposed = true;
            }
        }
    }
}
