using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace NowMediaMonitor
{
    internal class Program
    {
        private static CancellationTokenSource? shutdownCts;
        private static MediaMonitor? monitor;

        static async Task Main(string[] args)
        {
            // Parse command-line arguments for diagnostic mode
            bool diagnosticMode = args.Contains("--diagnostic") || args.Contains("-d");
            
            // Parse port argument
            int port = 58080; // Default port
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "--port" || args[i] == "-p")
                {
                    if (int.TryParse(args[i + 1], out int parsedPort))
                    {
                        port = parsedPort;
                        Console.WriteLine($"🔌 Using port: {port}");
                    }
                }
            }
            
            // Initialize diagnostic logger
            DiagnosticLogger.Initialize(diagnosticMode);
            
            if (diagnosticMode)
            {
                Console.WriteLine("🔍 Diagnostic mode enabled");
                Console.WriteLine("📝 Verbose logging active - all events will be logged");
                Console.WriteLine("📁 Log file will be created in the 'logs' directory");
                Console.WriteLine();
            }

            // Set up graceful shutdown handler for Ctrl+C
            shutdownCts = new CancellationTokenSource();
            Console.CancelKeyPress += OnCancelKeyPress;

            try
            {
                // Wrap MediaMonitor in using statement for proper disposal
                using (monitor = new MediaMonitor(port))
                {
                    // Start monitoring with cancellation support
                    var monitorTask = monitor.Start();
                    
                    // Wait for either completion or cancellation
                    await Task.WhenAny(monitorTask, Task.Delay(Timeout.Infinite, shutdownCts.Token));
                }
                
                Console.WriteLine("✅ MediaMonitor shutdown complete");
            }
            catch (OperationCanceledException)
            {
                Console.WriteLine("✅ MediaMonitor shutdown complete");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error during shutdown: {ex.Message}");
            }
            finally
            {
                // Shutdown diagnostic logger
                DiagnosticLogger.Shutdown();
                shutdownCts?.Dispose();
            }
        }

        private static void OnCancelKeyPress(object? sender, ConsoleCancelEventArgs e)
        {
            // Prevent immediate termination
            e.Cancel = true;
            
            Console.WriteLine("\n🛑 Shutdown signal received, cleaning up...");
            
            // Signal shutdown
            shutdownCts?.Cancel();
        }
    }
}
