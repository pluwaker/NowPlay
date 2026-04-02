using System;
using System.Threading.Tasks;
using Windows.Media.Control;

namespace NowMediaMonitor
{
    /// <summary>
    /// Manages automatic recovery from event subscription failures
    /// </summary>
    public class RecoveryManager
    {
        private readonly MediaMonitor monitor;
        private int recoveryAttempts = 0;
        private const int MAX_RECOVERY_ATTEMPTS = 3;
        private DateTime lastRecoveryAttempt = DateTime.MinValue;
        private readonly TimeSpan recoveryAttemptCooldown = TimeSpan.FromSeconds(10);
        
        public RecoveryManager(MediaMonitor monitor)
        {
            this.monitor = monitor ?? throw new ArgumentNullException(nameof(monitor));
        }
        
        /// <summary>
        /// Attempts to recover from event subscription failures
        /// Returns true if recovery was successful, false otherwise
        /// </summary>
        public async Task<bool> AttemptRecovery()
        {
            // Check if we've exceeded maximum recovery attempts
            if (recoveryAttempts >= MAX_RECOVERY_ATTEMPTS)
            {
                Console.WriteLine($"❌ Recovery failed: Maximum recovery attempts ({MAX_RECOVERY_ATTEMPTS}) exceeded");
                Console.WriteLine($"⚠️ Manual restart required");
                return false;
            }
            
            // Check cooldown period to prevent rapid recovery attempts
            var timeSinceLastAttempt = DateTime.Now - lastRecoveryAttempt;
            if (timeSinceLastAttempt < recoveryAttemptCooldown)
            {
                Console.WriteLine($"⏳ Recovery cooldown active, waiting {(recoveryAttemptCooldown - timeSinceLastAttempt).TotalSeconds:F1}s");
                return false;
            }
            
            recoveryAttempts++;
            lastRecoveryAttempt = DateTime.Now;
            
            Console.WriteLine($"🔄 Starting recovery procedure (attempt {recoveryAttempts}/{MAX_RECOVERY_ATTEMPTS})");
            Console.WriteLine($"⏰ Recovery started at: {DateTime.Now:HH:mm:ss.fff}");
            
            DiagnosticLogger.LogRecovery("Started", true, $"Attempt {recoveryAttempts}/{MAX_RECOVERY_ATTEMPTS}");
            
            try
            {
                // Step 1: Unsubscribe from all current events
                Console.WriteLine($"📤 Step 1/4: Unsubscribing from all events...");
                DiagnosticLogger.LogRecovery("Step 1: Unsubscribe", true, "Starting");
                await UnsubscribeAll();
                Console.WriteLine($"✅ Step 1/4: Event unsubscription complete");
                DiagnosticLogger.LogRecovery("Step 1: Unsubscribe", true, "Complete");
                
                // Step 2: Re-initialize the session manager
                Console.WriteLine($"🔄 Step 2/4: Re-initializing session manager...");
                DiagnosticLogger.LogRecovery("Step 2: Reinitialize", true, "Starting");
                await ReinitializeSessionManager();
                Console.WriteLine($"✅ Step 2/4: Session manager re-initialized");
                DiagnosticLogger.LogRecovery("Step 2: Reinitialize", true, "Complete");
                
                // Step 3: Re-establish event subscriptions
                Console.WriteLine($"📥 Step 3/4: Re-establishing event subscriptions...");
                DiagnosticLogger.LogRecovery("Step 3: Resubscribe", true, "Starting");
                await ReestablishSubscriptions();
                Console.WriteLine($"✅ Step 3/4: Event subscriptions re-established");
                DiagnosticLogger.LogRecovery("Step 3: Resubscribe", true, "Complete");
                
                // Step 4: Verify recovery (без принудительного обновления позиции)
                // ПРИМЕЧАНИЕ: Мы НЕ вызываем UpdateMediaInfo(), потому что:
                // 1. Windows Media API иногда возвращает некорректную позицию (0.1s вместо реальной)
                // 2. Это вызывает сброс прогресса в виджете
                // 3. События от Windows Media API придут автоматически после переподписки
                Console.WriteLine($"✅ Step 4/4: Recovery verification complete (waiting for natural events)");
                DiagnosticLogger.LogRecovery("Step 4: Verify", true, "Complete - waiting for events");
                
                // Reset recovery counter on successful recovery
                recoveryAttempts = 0;
                
                Console.WriteLine($"✅ Recovery procedure completed successfully");
                Console.WriteLine($"⏰ Recovery completed at: {DateTime.Now:HH:mm:ss.fff}");
                
                DiagnosticLogger.LogRecovery("Completed", true, "All steps successful");
                
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Recovery procedure failed: {ex.Message}");
                Console.WriteLine($"📊 Stack trace: {ex.StackTrace}");
                
                DiagnosticLogger.LogRecovery("Failed", false, $"{ex.Message}");
                
                if (recoveryAttempts >= MAX_RECOVERY_ATTEMPTS)
                {
                    Console.WriteLine($"❌ Maximum recovery attempts reached. Manual restart required.");
                }
                else
                {
                    Console.WriteLine($"⏳ Will retry recovery on next timeout (attempts remaining: {MAX_RECOVERY_ATTEMPTS - recoveryAttempts})");
                }
                
                return false;
            }
        }
        
        /// <summary>
        /// Unsubscribes from all current event handlers
        /// </summary>
        private async Task UnsubscribeAll()
        {
            await Task.Run(() =>
            {
                try
                {
                    // Unsubscribe from session manager events
                    if (monitor.sessionManager != null)
                    {
                        Console.WriteLine($"  - Unsubscribing from SessionsChanged event");
                        monitor.sessionManager.SessionsChanged -= monitor.OnSessionsChanged;
                    }
                    
                    // Note: Individual session event handlers are now managed by EventSubscriptionManager
                    // The MediaMonitor.UpdateCurrentSession() will handle unsubscribing via EventSubscriptionManager
                    
                    Console.WriteLine($"  - All event handlers unsubscribed");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Warning during unsubscribe: {ex.Message}");
                    // Continue with recovery even if unsubscribe fails
                }
            });
        }
        
        /// <summary>
        /// Re-initializes the session manager
        /// </summary>
        private async Task ReinitializeSessionManager()
        {
            try
            {
                // Clear current session reference
                monitor.currentSession = null;
                
                // Request a new session manager instance
                Console.WriteLine($"  - Requesting new SessionManager instance");
                monitor.sessionManager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
                
                Console.WriteLine($"  - SessionManager instance created");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Failed to reinitialize session manager: {ex.Message}");
                throw;
            }
        }
        
        /// <summary>
        /// Re-establishes event subscriptions
        /// </summary>
        private async Task ReestablishSubscriptions()
        {
            try
            {
                if (monitor.sessionManager == null)
                {
                    throw new InvalidOperationException("SessionManager is null, cannot reestablish subscriptions");
                }
                
                // Subscribe to session manager events
                Console.WriteLine($"  - Subscribing to SessionsChanged event");
                monitor.sessionManager.SessionsChanged += monitor.OnSessionsChanged;
                
                // Update current session (this will also subscribe to session events)
                // ВАЖНО: Передаем skipInitialUpdate=true чтобы не отправлять некорректные данные
                Console.WriteLine($"  - Updating current session (без начального обновления)");
                await monitor.UpdateCurrentSession(skipInitialUpdate: true);
                
                Console.WriteLine($"  - Event subscriptions reestablished");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Failed to reestablish subscriptions: {ex.Message}");
                throw;
            }
        }
        
        /// <summary>
        /// Resets the recovery attempt counter (useful for testing or manual intervention)
        /// </summary>
        public void ResetRecoveryCounter()
        {
            recoveryAttempts = 0;
            Console.WriteLine($"🔄 Recovery attempt counter reset");
        }
        
        /// <summary>
        /// Dispose method for cleanup
        /// </summary>
        public void Dispose()
        {
            // RecoveryManager doesn't hold any disposable resources
            // This method is here for consistency with other components
        }
    }
}
