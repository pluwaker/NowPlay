@echo off
chcp 65001 >nul
echo ========================================
echo MediaMonitor with console (for debugging)
echo ========================================
echo.
echo Starting MediaMonitor...
echo Console will stay open to view logs
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd MediaMonitor\bin\Release\net6.0-windows10.0.19041.0
MediaMonitor.exe

pause
