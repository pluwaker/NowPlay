#!/usr/bin/env python3
"""
Тестовый скрипт для проверки получения событий от MediaMonitor
"""
import asyncio
import aiohttp
from aiohttp import web
import json
from datetime import datetime

# Счетчик полученных обновлений
update_count = 0
last_update_time = None
updates_log = []

async def handle_update(request):
    """Обработчик обновлений от MediaMonitor"""
    global update_count, last_update_time
    
    try:
        data = await request.json()
        update_count += 1
        last_update_time = datetime.now()
        
        # Логируем обновление
        log_entry = {
            'count': update_count,
            'time': last_update_time.strftime('%H:%M:%S.%f')[:-3],
            'artist': data.get('artist', 'N/A'),
            'title': data.get('title', 'N/A'),
            'position': data.get('position', 0),
            'is_playing': data.get('is_playing', False)
        }
        updates_log.append(log_entry)
        
        # Выводим в консоль
        print(f"\n{'='*60}")
        print(f"📥 Обновление #{update_count} получено в {log_entry['time']}")
        print(f"🎵 {log_entry['artist']} - {log_entry['title']}")
        print(f"▶️  Позиция: {log_entry['position']:.1f}s | Играет: {log_entry['is_playing']}")
        print(f"{'='*60}")
        
        # Если это первое обновление
        if update_count == 1:
            print("\n✅ Первое обновление получено!")
            print("⏳ Ожидаем следующие обновления...")
            print("   (Смените трек или нажмите play/pause)")
        
        return web.json_response({"status": "success", "count": update_count})
    
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def handle_sources(request):
    """Обработчик списка источников"""
    try:
        data = await request.json()
        sources = data.get('sources', [])
        print(f"\n📻 Получено источников: {len(sources)}")
        for source in sources:
            print(f"   - {source.get('name', 'Unknown')}")
        return web.json_response({"status": "success"})
    except Exception as e:
        print(f"❌ Ошибка обработки источников: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def handle_get_config(request):
    """Возвращает конфигурацию"""
    config = {
        "selected_media_source": "auto",
        "test_mode": True
    }
    return web.json_response(config)

async def handle_status(request):
    """Показывает статус тестового сервера"""
    global update_count, last_update_time
    
    status = {
        "update_count": update_count,
        "last_update": last_update_time.strftime('%H:%M:%S.%f')[:-3] if last_update_time else "N/A",
        "recent_updates": updates_log[-5:] if updates_log else []
    }
    
    return web.json_response(status)

async def monitor_updates():
    """Мониторит получение обновлений"""
    global update_count, last_update_time
    
    await asyncio.sleep(5)  # Ждем первое обновление
    
    last_count = 0
    no_update_seconds = 0
    
    while True:
        await asyncio.sleep(5)
        
        if update_count == last_count:
            no_update_seconds += 5
            
            if no_update_seconds == 10:
                print(f"\n⚠️  Обновлений не было {no_update_seconds} секунд")
                print("   Попробуйте сменить трек или нажать play/pause")
            elif no_update_seconds == 30:
                print(f"\n❌ ПРОБЛЕМА: Обновлений не было {no_update_seconds} секунд!")
                print("   MediaMonitor должен был запустить восстановление")
                print("   Проверьте консоль MediaMonitor на наличие сообщений о восстановлении")
            elif no_update_seconds % 30 == 0:
                print(f"\n❌ Обновлений не было {no_update_seconds} секунд")
        else:
            if no_update_seconds >= 10:
                print(f"\n✅ Обновления возобновились после {no_update_seconds} секунд")
            no_update_seconds = 0
            last_count = update_count

async def start_background_tasks(app):
    """Запускает фоновые задачи"""
    app['monitor_task'] = asyncio.create_task(monitor_updates())

async def cleanup_background_tasks(app):
    """Останавливает фоновые задачи"""
    app['monitor_task'].cancel()
    await app['monitor_task']

def main():
    """Запускает тестовый сервер"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_post('/update_from_cs', handle_update)
    app.router.add_post('/update_sources', handle_sources)
    app.router.add_get('/get_config', handle_get_config)
    app.router.add_get('/status', handle_status)
    
    # Добавляем фоновые задачи
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    port = 58080
    
    print("="*60)
    print("🧪 ТЕСТОВЫЙ СЕРВЕР ДЛЯ MEDIAMONITOR")
    print("="*60)
    print(f"\n🚀 Сервер запущен на http://localhost:{port}")
    print(f"\n📋 Инструкции:")
    print(f"   1. Запустите MediaMonitor.exe")
    print(f"   2. Включите музыку в любом плеере")
    print(f"   3. Наблюдайте за обновлениями в этой консоли")
    print(f"   4. Смените трек или нажмите play/pause")
    print(f"\n📊 Статус: http://localhost:{port}/status")
    print(f"\n⏳ Ожидаем подключения MediaMonitor...\n")
    
    web.run_app(app, host='localhost', port=port, print=lambda x: None)

if __name__ == "__main__":
    main()
