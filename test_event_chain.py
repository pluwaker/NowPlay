"""
Тест для проверки цепочки передачи событий от MediaMonitor до Python сервера
"""
import subprocess
import time
import sys

print("=" * 80)
print("ТЕСТ ЦЕПОЧКИ СОБЫТИЙ MediaMonitor → Python Server")
print("=" * 80)
print()
print("Этот тест запустит MediaMonitor и покажет полную цепочку логов:")
print("1. EventSubscriptionManager получает события (TimelinePropertiesChanged, PlaybackInfoChanged)")
print("2. OnMediaUpdated вызывается и передает данные в MediaMonitor")
print("3. MediaMonitor.OnMediaUpdated обновляет State и вызывает updateQueue.QueueUpdate")
print("4. UpdateQueue.ProcessUpdate обрабатывает обновление")
print("5. OnUpdateReady отправляет данные на Python сервер")
print()
print("=" * 80)
print()

# Запускаем MediaMonitor
import os
mediamonitor_path = os.path.abspath(r"MediaMonitor\bin\Release\net6.0-windows10.0.19041.0\MediaMonitor.exe")

if not os.path.exists(mediamonitor_path):
    print(f"ОШИБКА: Файл не найден: {mediamonitor_path}")
    print("Пожалуйста, сначала соберите проект: cd MediaMonitor && dotnet build -c Release")
    sys.exit(1)

print(f"Запускаем MediaMonitor: {mediamonitor_path}")
print()
print("Теперь переключите трек или перемотайте позицию в плеере...")
print("Смотрите на логи ниже, чтобы увидеть полную цепочку событий")
print()
print("-" * 80)
print()

try:
    # Запускаем MediaMonitor и показываем его вывод
    process = subprocess.Popen(
        [mediamonitor_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Читаем и выводим логи в реальном времени
    for line in process.stdout:
        print(line, end='')
        sys.stdout.flush()
        
except KeyboardInterrupt:
    print("\n\nОстановка теста...")
    process.terminate()
    process.wait()
    print("Тест завершен")
