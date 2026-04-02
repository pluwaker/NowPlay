using System;
using System.Threading;
using System.Threading.Tasks;

namespace NowMediaMonitor
{
    /// <summary>
    /// Manages update batching with debounce timer and timeout-protected locks
    /// </summary>
    public class UpdateQueue : IDisposable
    {
        private readonly SemaphoreSlim updateLock = new SemaphoreSlim(1, 1);
        private readonly TimeSpan lockTimeout = TimeSpan.FromSeconds(5);
        // ОТКЛЮЧЕН debounce - отправляем обновления немедленно для быстрой реакции на перемотку
        
        private readonly object stateLock = new object();
        
        // Timeout tracking for recovery trigger
        private int consecutiveTimeouts = 0;
        private const int TIMEOUT_THRESHOLD_FOR_RECOVERY = 3;
        
        // Events
        public event EventHandler? RecoveryNeeded;
        public event EventHandler<CurrentMediaState>? UpdateReady;
        
        public UpdateQueue()
        {
            Console.WriteLine($"✅ UpdateQueue initialized (lockTimeout: {lockTimeout.TotalSeconds}s, debounce: DISABLED)");
        }
        
        /// <summary>
        /// Queues an update and processes it immediately (no debouncing)
        /// </summary>
        public void QueueUpdate(CurrentMediaState state)
        {
            if (state == null)
            {
                throw new ArgumentNullException(nameof(state));
            }
            
            // Обрабатываем немедленно без debounce для быстрой реакции на перемотку
            _ = Task.Run(async () => await ProcessUpdate(state));
        }
        
        /// <summary>
        /// Processes the update with timeout-protected lock acquisition
        /// </summary>
        private async Task ProcessUpdate(CurrentMediaState state)
        {
            bool lockAcquired = false;
            
            try
            {
                Console.WriteLine($"🔄 UpdateQueue: Attempting to acquire update lock (timeout: {lockTimeout.TotalSeconds}s)");
                var startTime = DateTime.Now;
                
                // Use timeout-protected lock acquisition
                lockAcquired = await updateLock.WaitAsync(lockTimeout);
                
                if (!lockAcquired)
                {
                    // Lock timeout occurred
                    var elapsed = DateTime.Now - startTime;
                    consecutiveTimeouts++;
                    
                    Console.WriteLine($"⚠️ UpdateQueue: Lock acquisition timeout after {elapsed.TotalSeconds:F2}s");
                    Console.WriteLine($"⚠️ UpdateQueue: Skipping update (consecutive timeouts: {consecutiveTimeouts})");
                    
                    DiagnosticLogger.LogLockOperation("Acquire", false, (long)elapsed.TotalMilliseconds, 
                        $"Consecutive timeouts: {consecutiveTimeouts}");
                    
                    // Check if we need to trigger recovery
                    if (consecutiveTimeouts >= TIMEOUT_THRESHOLD_FOR_RECOVERY)
                    {
                        Console.WriteLine($"❌ UpdateQueue: Timeout threshold reached ({TIMEOUT_THRESHOLD_FOR_RECOVERY}), triggering recovery");
                        OnRecoveryNeeded();
                        consecutiveTimeouts = 0; // Reset counter after triggering recovery
                    }
                    
                    return;
                }
                
                // Lock acquired successfully
                var lockAcquireTime = DateTime.Now - startTime;
                Console.WriteLine($"✅ UpdateQueue: Lock acquired in {lockAcquireTime.TotalMilliseconds:F0}ms");
                
                DiagnosticLogger.LogLockOperation("Acquire", true, (long)lockAcquireTime.TotalMilliseconds);
                
                // Reset timeout counter on successful lock acquisition
                if (consecutiveTimeouts > 0)
                {
                    Console.WriteLine($"✅ UpdateQueue: Resetting timeout counter (was: {consecutiveTimeouts})");
                    consecutiveTimeouts = 0;
                }
                
                try
                {
                    // Process the update
                    Console.WriteLine($"📤 UpdateQueue: Processing update for {state.Artist} - {state.Title}");
                    DiagnosticLogger.LogDiagnostic("UpdateQueue", $"Processing update: {state.Artist} - {state.Title}");
                    OnUpdateReady(state);
                    Console.WriteLine($"✅ UpdateQueue: Update processed successfully");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ UpdateQueue: Error processing update: {ex.Message}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ UpdateQueue: Unexpected error in ProcessUpdate: {ex.Message}");
            }
            finally
            {
                if (lockAcquired)
                {
                    updateLock.Release();
                    Console.WriteLine($"🔓 UpdateQueue: Lock released");
                    DiagnosticLogger.LogLockOperation("Release", true, 0);
                }
            }
        }
        
        /// <summary>
        /// Raises the RecoveryNeeded event
        /// </summary>
        private void OnRecoveryNeeded()
        {
            RecoveryNeeded?.Invoke(this, EventArgs.Empty);
        }
        
        /// <summary>
        /// Raises the UpdateReady event
        /// </summary>
        private void OnUpdateReady(CurrentMediaState state)
        {
            UpdateReady?.Invoke(this, state);
        }
        
        /// <summary>
        /// Gets the current consecutive timeout count (for testing/diagnostics)
        /// </summary>
        public int ConsecutiveTimeouts => consecutiveTimeouts;
        
        /// <summary>
        /// Resets the consecutive timeout counter (for testing/recovery)
        /// </summary>
        public void ResetTimeoutCounter()
        {
            consecutiveTimeouts = 0;
            Console.WriteLine($"🔄 UpdateQueue: Timeout counter reset");
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
                        updateLock?.Dispose();
                        Console.WriteLine("🧹 UpdateQueue disposed");
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"⚠️ Error disposing UpdateQueue: {ex.Message}");
                    }
                }
                disposed = true;
            }
        }
    }
}
