using System;
using System.Threading;

namespace NowMediaMonitor
{
    /// <summary>
    /// Event arguments for health status changes
    /// </summary>
    public class HealthStatusEventArgs : EventArgs
    {
        public bool IsHealthy { get; set; }
        public TimeSpan TimeSinceLastUpdate { get; set; }
        public string Reason { get; set; } = string.Empty;
    }

    /// <summary>
    /// Monitors the health of media update flow and triggers recovery when needed
    /// </summary>
    public class HealthMonitor : IDisposable
    {
        // Configuration
        private readonly TimeSpan updateTimeout = TimeSpan.FromSeconds(120); // Увеличено с 30 до 120 секунд
        private readonly TimeSpan heartbeatInterval = TimeSpan.FromSeconds(10); // Увеличено с 5 до 10 секунд
        
        // State tracking
        private DateTime lastUpdateReceived;
        private Timer? heartbeatTimer;
        private bool isHealthy = true;
        private readonly object lockObject = new object();
        
        // Events
        public event EventHandler<HealthStatusEventArgs>? HealthStatusChanged;
        public event EventHandler? RecoveryNeeded;
        
        public HealthMonitor()
        {
            lastUpdateReceived = DateTime.Now;
        }
        
        /// <summary>
        /// Records that an update was received, resetting the timeout counter
        /// </summary>
        public void RecordUpdate()
        {
            lock (lockObject)
            {
                lastUpdateReceived = DateTime.Now;
                
                DiagnosticLogger.LogDiagnostic("HealthMonitor", "Update recorded");
                
                // If we were unhealthy, mark as healthy now
                if (!isHealthy)
                {
                    isHealthy = true;
                    LogHealthStatusChange(true, TimeSpan.Zero, "Update received after recovery");
                    OnHealthStatusChanged(new HealthStatusEventArgs
                    {
                        IsHealthy = true,
                        TimeSinceLastUpdate = TimeSpan.Zero,
                        Reason = "Update received after recovery"
                    });
                }
            }
        }
        
        /// <summary>
        /// Starts the health monitoring heartbeat
        /// </summary>
        public void Start()
        {
            Console.WriteLine("🔄 HealthMonitor.Start() вызван");
            
            lock (lockObject)
            {
                if (heartbeatTimer != null)
                {
                    Console.WriteLine("⚠️ HealthMonitor уже запущен, пропускаем");
                    return; // Already started
                }
                
                Console.WriteLine($"📅 Устанавливаем lastUpdateReceived = {DateTime.Now:HH:mm:ss.fff}");
                lastUpdateReceived = DateTime.Now;
                
                Console.WriteLine($"⏰ Создаем Timer с интервалом {heartbeatInterval.TotalSeconds}s");
                heartbeatTimer = new Timer(
                    CheckHealth,
                    null,
                    heartbeatInterval,
                    heartbeatInterval
                );
                
                Console.WriteLine($"✅ HealthMonitor started (timeout: {updateTimeout.TotalSeconds}s, heartbeat: {heartbeatInterval.TotalSeconds}s)");
                DiagnosticLogger.LogDiagnostic("HealthMonitor", "Started successfully");
            }
        }
        
        /// <summary>
        /// Stops the health monitoring heartbeat
        /// </summary>
        public void Stop()
        {
            lock (lockObject)
            {
                if (heartbeatTimer != null)
                {
                    heartbeatTimer.Dispose();
                    heartbeatTimer = null;
                    Console.WriteLine("🛑 HealthMonitor stopped");
                }
            }
        }
        
        /// <summary>
        /// Checks if updates have been received within the timeout period
        /// </summary>
        private void CheckHealth(object? state)
        {
            lock (lockObject)
            {
                var timeSinceLastUpdate = DateTime.Now - lastUpdateReceived;
                
                Console.WriteLine($"[HEALTH] Heartbeat check: Last update {timeSinceLastUpdate.TotalSeconds:F1} seconds ago {(isHealthy ? "(healthy)" : "(UNHEALTHY)")}");
                DiagnosticLogger.LogDiagnostic("HealthMonitor", $"Heartbeat: {timeSinceLastUpdate.TotalSeconds:F1}s ago");
                
                // Логируем количество дескрипторов для отслеживания утечек
                DiagnosticLogger.LogHandleCount();
                
                if (timeSinceLastUpdate >= updateTimeout)
                {
                    if (isHealthy)
                    {
                        // Transition from healthy to unhealthy
                        isHealthy = false;
                        string reason = $"No updates received for {timeSinceLastUpdate.TotalSeconds:F1} seconds";
                        
                        LogHealthStatusChange(false, timeSinceLastUpdate, reason);
                        
                        // Fire health status changed event
                        OnHealthStatusChanged(new HealthStatusEventArgs
                        {
                            IsHealthy = false,
                            TimeSinceLastUpdate = timeSinceLastUpdate,
                            Reason = reason
                        });
                        
                        // Fire recovery needed event
                        Console.WriteLine("🚨 Вызываем OnRecoveryNeeded()");
                        OnRecoveryNeeded();
                    }
                    else
                    {
                        Console.WriteLine($"⚠️ Всё еще нездоров: {timeSinceLastUpdate.TotalSeconds:F1}s без обновлений");
                    }
                }
            }
        }
        
        /// <summary>
        /// Raises the HealthStatusChanged event
        /// </summary>
        private void OnHealthStatusChanged(HealthStatusEventArgs e)
        {
            HealthStatusChanged?.Invoke(this, e);
        }
        
        /// <summary>
        /// Raises the RecoveryNeeded event
        /// </summary>
        private void OnRecoveryNeeded()
        {
            RecoveryNeeded?.Invoke(this, EventArgs.Empty);
        }
        
        /// <summary>
        /// Logs health status changes for diagnostics
        /// </summary>
        private void LogHealthStatusChange(bool healthy, TimeSpan timeSinceUpdate, string reason)
        {
            if (healthy)
            {
                Console.WriteLine($"💚 Health Status: HEALTHY - {reason}");
                DiagnosticLogger.LogHealthStatus(true, timeSinceUpdate, reason);
            }
            else
            {
                Console.WriteLine($"❤️ Health Status: UNHEALTHY - {reason}");
                Console.WriteLine($"⚠️ Triggering recovery procedure...");
                DiagnosticLogger.LogHealthStatus(false, timeSinceUpdate, reason);
            }
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
                    Stop();
                }
                disposed = true;
            }
        }
    }
}
