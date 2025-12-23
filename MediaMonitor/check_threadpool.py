"""
Диагностический скрипт для проверки состояния MediaMonitor
Показывает количество потоков, использование памяти и CPU
"""
import psutil
import time
import sys

def find_mediamonitor_process():
    """Находит процесс MediaMonitor"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Ищем процесс MediaMonitor.exe или dotnet с MediaMonitor
            if proc.info['name'] and 'MediaMonitor' in proc.info['name']:
                return proc
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'MediaMonitor' in cmdline:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def format_bytes(bytes_value):
    """Форматирует байты в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def monitor_process(interval=5, duration=None):
    """Мониторит процесс MediaMonitor"""
    proc = find_mediamonitor_process()
    
    if not proc:
        print("❌ Процесс MediaMonitor не найден!")
        print("   Убедитесь, что MediaMonitor запущен")
        return
    
    print(f"✅ Найден процесс MediaMonitor (PID: {proc.pid})")
    print(f"📊 Мониторинг каждые {interval} секунд")
    if duration:
        print(f"⏱️  Длительность: {duration} секунд")
    print("=" * 80)
    print()
    
    start_time = time.time()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            current_time = time.time() - start_time
            
            try:
                # Получаем информацию о процессе
                with proc.oneshot():
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    memory_info = proc.memory_info()
                    num_threads = proc.num_threads()
                    
                    # Получаем информацию о потоках
                    threads = proc.threads()
                    
                print(f"[{int(current_time)}s] Итерация #{iteration}")
                print(f"  🔢 Потоков: {num_threads}")
                print(f"  💻 CPU: {cpu_percent:.1f}%")
                print(f"  🧠 Память (RSS): {format_bytes(memory_info.rss)}")
                print(f"  📦 Память (VMS): {format_bytes(memory_info.vms)}")
                
                # Показываем топ-5 потоков по времени CPU
                if threads:
                    sorted_threads = sorted(threads, key=lambda t: t.user_time + t.system_time, reverse=True)[:5]
                    print(f"  🔝 Топ-5 потоков по CPU времени:")
                    for i, thread in enumerate(sorted_threads, 1):
                        total_time = thread.user_time + thread.system_time
                        print(f"     {i}. Thread ID {thread.id}: {total_time:.2f}s CPU")
                
                print()
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"❌ Процесс завершился или нет доступа: {e}")
                break
            
            # Проверяем, не истекло ли время
            if duration and current_time >= duration:
                print(f"⏱️  Мониторинг завершен ({duration}s)")
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  Мониторинг остановлен пользователем")

if __name__ == "__main__":
    # Параметры по умолчанию
    interval = 5  # секунд между проверками
    duration = None  # бесконечно
    
    # Парсим аргументы командной строки
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Неверный интервал: {sys.argv[1]}, используем {interval}s")
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print(f"⚠️  Неверная длительность: {sys.argv[2]}, мониторим бесконечно")
    
    print("🔍 Диагностика MediaMonitor ThreadPool")
    print()
    
    monitor_process(interval, duration)
