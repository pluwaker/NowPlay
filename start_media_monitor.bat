@echo off
echo ========================================
echo   MediaMonitor + Python Server Launcher
echo ========================================
echo.

echo [1/2] Запуск Python сервера...
start "Python Server" cmd /k "python main.py"
timeout /t 3 /nobreak >nul

echo [2/2] Запуск C# MediaMonitor...
cd MediaMonitor
start "MediaMonitor" cmd /k "dotnet run"
cd ..

echo.
echo ✅ Оба компонента запущены!
echo.
echo Python Server: http://localhost:80
echo MediaMonitor: отправляет данные на Python сервер
echo.
pause
