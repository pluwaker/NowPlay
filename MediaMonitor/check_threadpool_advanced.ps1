# Продвинутая диагностика MediaMonitor с .NET метриками
# Использует Performance Counters для детальной информации

param(
    [int]$Interval = 5,
    [int]$Duration = 0
)

Write-Host "🔍 Продвинутая диагностика MediaMonitor" -ForegroundColor Cyan
Write-Host ""

# Находим процесс MediaMonitor
$process = Get-Process | Where-Object { $_.ProcessName -like "*MediaMonitor*" } | Select-Object -First 1

if (-not $process) {
    Write-Host "❌ Процесс MediaMonitor не найден!" -ForegroundColor Red
    Write-Host "   Убедитесь, что MediaMonitor запущен" -ForegroundColor Yellow
    exit 1
}

$processId = $process.Id
$processName = $process.ProcessName

Write-Host "✅ Найден процесс: $processName (PID: $processId)" -ForegroundColor Green
Write-Host "📊 Мониторинг каждые $Interval секунд" -ForegroundColor Cyan
if ($Duration -gt 0) {
    Write-Host "⏱️  Длительность: $Duration секунд" -ForegroundColor Cyan
}
Write-Host ("=" * 80) -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date
$iteration = 0

try {
    while ($true) {
        $iteration++
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        # Обновляем информацию о процессе
        $process.Refresh()
        
        # Базовые метрики
        $threads = $process.Threads.Count
        $handles = $process.HandleCount
        $workingSet = [math]::Round($process.WorkingSet64 / 1MB, 2)
        $privateMemory = [math]::Round($process.PrivateMemorySize64 / 1MB, 2)
        $virtualMemory = [math]::Round($process.VirtualMemorySize64 / 1MB, 2)
        
        Write-Host "[$([int]$elapsed)s] Итерация #$iteration" -ForegroundColor White
        Write-Host "  🔢 Потоков: $threads" -ForegroundColor Yellow
        Write-Host "  🔗 Handles: $handles" -ForegroundColor Yellow
        Write-Host "  🧠 Working Set: $workingSet MB" -ForegroundColor Cyan
        Write-Host "  📦 Private Memory: $privateMemory MB" -ForegroundColor Cyan
        Write-Host "  💾 Virtual Memory: $virtualMemory MB" -ForegroundColor Cyan
        
        # Пытаемся получить .NET метрики через Performance Counters
        try {
            # ThreadPool метрики
            $threadPoolCounter = Get-Counter "\Process($processName)\Thread Count" -ErrorAction SilentlyContinue
            if ($threadPoolCounter) {
                $threadCount = $threadPoolCounter.CounterSamples[0].CookedValue
                Write-Host "  🎯 Thread Count (Counter): $threadCount" -ForegroundColor Magenta
            }
            
            # CPU метрики
            $cpuCounter = Get-Counter "\Process($processName)\% Processor Time" -ErrorAction SilentlyContinue
            if ($cpuCounter) {
                $cpuPercent = [math]::Round($cpuCounter.CounterSamples[0].CookedValue, 2)
                Write-Host "  💻 CPU: $cpuPercent%" -ForegroundColor Green
            }
        }
        catch {
            # Игнорируем ошибки Performance Counters
        }
        
        # Показываем топ потоков по CPU времени
        $topThreads = $process.Threads | 
            Sort-Object -Property TotalProcessorTime -Descending | 
            Select-Object -First 5
        
        if ($topThreads) {
            Write-Host "  🔝 Топ-5 потоков по CPU времени:" -ForegroundColor White
            $rank = 1
            foreach ($thread in $topThreads) {
                $cpuTime = $thread.TotalProcessorTime.TotalSeconds
                $state = $thread.ThreadState
                Write-Host "     $rank. Thread ID $($thread.Id): $([math]::Round($cpuTime, 2))s CPU (State: $state)" -ForegroundColor Gray
                $rank++
            }
        }
        
        Write-Host ""
        
        # Проверяем длительность
        if ($Duration -gt 0 -and $elapsed -ge $Duration) {
            Write-Host "⏱️  Мониторинг завершен ($Duration s)" -ForegroundColor Green
            break
        }
        
        Start-Sleep -Seconds $Interval
    }
}
catch {
    Write-Host ""
    Write-Host "⏹️  Мониторинг остановлен" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Диагностика завершена" -ForegroundColor Green
