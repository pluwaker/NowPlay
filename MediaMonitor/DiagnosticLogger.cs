using System;
using System.IO;
using System.Text;

namespace NowMediaMonitor
{
    /// <summary>
    /// Provides diagnostic logging with file output and formatted console output
    /// </summary>
    public static class DiagnosticLogger
    {
        private static bool diagnosticMode = false;
        private static StreamWriter? logFileWriter;
        private static readonly object logLock = new object();
        private static string? logFilePath;
        
        /// <summary>
        /// Initializes the diagnostic logger
        /// </summary>
        public static void Initialize(bool enableDiagnosticMode)
        {
            diagnosticMode = enableDiagnosticMode;
            
            if (diagnosticMode)
            {
                try
                {
                    // Create logs directory if it doesn't exist
                    string logsDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
                    Directory.CreateDirectory(logsDir);
                    
                    // Create log file with timestamp
                    string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                    logFilePath = Path.Combine(logsDir, $"mediamonitor_diagnostic_{timestamp}.log");
                    
                    logFileWriter = new StreamWriter(logFilePath, append: true, Encoding.UTF8)
                    {
                        AutoFlush = true
                    };
                    
                    Console.WriteLine($"📝 Diagnostic log file: {logFilePath}");
                    LogDiagnostic("DiagnosticLogger", "Diagnostic mode initialized");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Failed to initialize diagnostic log file: {ex.Message}");
                }
            }
        }
        
        /// <summary>
        /// Logs a diagnostic message (only in diagnostic mode)
        /// </summary>
        public static void LogDiagnostic(string component, string message)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            lock (logLock)
            {
                string timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
                string formattedMessage = $"[{timestamp}] [{component}] {message}";
                
                // Write to console with formatting
                Console.WriteLine(formattedMessage);
                
                // Write to log file
                try
                {
                    logFileWriter?.WriteLine(formattedMessage);
                }
                catch
                {
                    // Ignore file write errors
                }
            }
        }
        
        /// <summary>
        /// Logs an event with timing information (only in diagnostic mode)
        /// </summary>
        public static void LogEvent(string component, string eventType, string details, long? durationMs = null)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string durationInfo = durationMs.HasValue ? $" (duration: {durationMs.Value}ms)" : "";
            LogDiagnostic(component, $"Event: {eventType} - {details}{durationInfo}");
        }
        
        /// <summary>
        /// Logs an HTTP request (only in diagnostic mode)
        /// </summary>
        public static void LogHttpRequest(string endpoint, bool success, long durationMs, string? errorMessage = null)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string status = success ? "SUCCESS" : "FAILED";
            string error = errorMessage != null ? $" - Error: {errorMessage}" : "";
            LogDiagnostic("HttpClientPool", $"HTTP {status}: {endpoint} ({durationMs}ms){error}");
        }
        
        /// <summary>
        /// Logs a health status change (only in diagnostic mode)
        /// </summary>
        public static void LogHealthStatus(bool isHealthy, TimeSpan timeSinceUpdate, string reason)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string status = isHealthy ? "HEALTHY" : "UNHEALTHY";
            string timeInfo = !isHealthy ? $" (time since last update: {timeSinceUpdate.TotalSeconds:F1}s)" : "";
            LogDiagnostic("HealthMonitor", $"Health Status: {status} - {reason}{timeInfo}");
        }
        
        /// <summary>
        /// Logs a recovery attempt (only in diagnostic mode)
        /// </summary>
        public static void LogRecovery(string step, bool success, string? details = null)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string status = success ? "SUCCESS" : "FAILED";
            string detailsInfo = details != null ? $" - {details}" : "";
            LogDiagnostic("RecoveryManager", $"Recovery {step}: {status}{detailsInfo}");
        }
        
        /// <summary>
        /// Logs a subscription lifecycle event (only in diagnostic mode)
        /// </summary>
        public static void LogSubscription(string action, string sessionId, string? eventType = null)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string eventInfo = eventType != null ? $" - Event: {eventType}" : "";
            LogDiagnostic("EventSubscriptionManager", $"{action}: {sessionId}{eventInfo}");
        }
        
        /// <summary>
        /// Logs a lock operation (only in diagnostic mode)
        /// </summary>
        public static void LogLockOperation(string operation, bool success, long durationMs, string? details = null)
        {
            if (!diagnosticMode)
            {
                return;
            }
            
            string status = success ? "SUCCESS" : "TIMEOUT";
            string detailsInfo = details != null ? $" - {details}" : "";
            LogDiagnostic("UpdateQueue", $"Lock {operation}: {status} ({durationMs}ms){detailsInfo}");
        }
        
        /// <summary>
        /// Gets whether diagnostic mode is enabled
        /// </summary>
        public static bool IsDiagnosticMode => diagnosticMode;
        
        /// <summary>
        /// Gets the current log file path (if diagnostic mode is enabled)
        /// </summary>
        public static string? LogFilePath => logFilePath;
        
        /// <summary>
        /// Closes the diagnostic logger and releases resources
        /// </summary>
        public static void Shutdown()
        {
            lock (logLock)
            {
                if (logFileWriter != null)
                {
                    try
                    {
                        LogDiagnostic("DiagnosticLogger", "Shutting down diagnostic logger");
                        logFileWriter.Flush();
                        logFileWriter.Close();
                        logFileWriter.Dispose();
                        logFileWriter = null;
                    }
                    catch
                    {
                        // Ignore shutdown errors
                    }
                }
            }
        }
    }
}
