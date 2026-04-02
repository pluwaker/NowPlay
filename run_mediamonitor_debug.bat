@echo off
echo ========================================
echo MediaMonitor Debug Mode
echo ========================================
echo.

REM Ищем MediaMonitor.exe
set MEDIAMONITOR_PATH=

if exist "MediaMonitor\bin\Release\net6.0-windows10.0.19041.0\MediaMonitor.exe" (
    set MEDIAMONITOR_PATH=MediaMonitor\bin\Release\net6.0-windows10.0.19041.0\MediaMonitor.exe
) else if exist "MediaMonitor\bin\Debug\net6.0-windows10.0.19041.0\MediaMonitor.exe" (
    set MEDIAMONITOR_PATH=MediaMonitor\bin\Debug\net6.0-windows10.0.19041.0\MediaMonitor.exe
) else if exist "MediaMonitor.exe" (
    set MEDIAMONITOR_PATH=MediaMonitor.exe
) else (
    echo ERROR: MediaMonitor.exe not found!
    echo.
    echo Please build MediaMonitor first:
    echo   cd MediaMonitor
    echo   dotnet build -c Release
    echo.
    pause
    exit /b 1
)

echo Found MediaMonitor at: %MEDIAMONITOR_PATH%
echo.
echo Starting MediaMonitor on port 58080...
echo.
echo ========================================
echo.

"%MEDIAMONITOR_PATH%" --port 58080

echo.
echo ========================================
echo MediaMonitor stopped
echo ========================================
pause
