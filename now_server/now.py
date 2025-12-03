# now_server/now.py
import asyncio
from aiohttp import web
import os
import socket
import json
from pathlib import Path
import sys
from now_server.cover_fetcher import cover_fetcher
# Импорт config_manager из новой структуры
from src.config.config_manager import config_manager



# Загрузка конфигурации через единый менеджер
current_config = config_manager.load_config()

# Определяем пути
PROJECT_ROOT = Path(__file__).parent.parent
output_dir = PROJECT_ROOT / "songinfo"
output_dir.mkdir(exist_ok=True)
output_dir = str(output_dir)

visualisation_dir = PROJECT_ROOT / "now_server"
visualisation_dir.mkdir(exist_ok=True)
visualisation_dir = str(visualisation_dir)


app = web.Application()
routes = web.RouteTableDef()

current_data = {
    "artist": "Не воспроизводится",
    "title": "Нет данных",
    "cover_version": 1,
    "listeners": set(),
    "position": 0,      # текущая позиция в секундах
    "duration": 0,      # длительность трека в секундах
    "is_playing": False, # статус воспроизведения
    "source_id": ""     # идентификатор источника медиа
}

# Добавляем переменные для оптимизации
last_update_time = 0
UPDATE_COOLDOWN = 0.1  # Минимальный интервал между обновлениями (100мс)


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0




async def cleanup_dead_websockets():
    """Удаляет неактивные WebSocket соединения из списка"""
    if not current_data['listeners']:
        return 0
        
    dead_ws = []
    for ws in current_data['listeners']:
        if ws.closed:
            dead_ws.append(ws)
    for ws in dead_ws:
        current_data['listeners'].discard(ws)
    return len(dead_ws)

async def send_to_listeners(msg):
    """Безопасно отправляет сообщение всем активным WebSocket соединениям"""
    if not current_data['listeners']:
        return
    
    dead_ws = []
    for ws in list(current_data['listeners']):
        try:
            # Проверяем, что соединение открыто
            if not ws.closed:
                await ws.send_json(msg)
            else:
                dead_ws.append(ws)
        except Exception:
            dead_ws.append(ws)
    
    # Удаляем мертвые соединения
    if dead_ws:
        for ws in dead_ws:
            current_data['listeners'].discard(ws)

async def notify_cover_replaced(artist, title):
    """Уведомляет о замене обложки с троттлингом"""
    global last_update_time
    current_time = asyncio.get_event_loop().time()
    
    # Троттлинг чтобы избежать частых обновлений
    if current_time - last_update_time < UPDATE_COOLDOWN:
        return
        
    current_data["cover_version"] += 1
    msg = {
        "type": "update",
        "data": {
            "artist": artist,
            "title": title,
            "position": current_data["position"],
            "duration": current_data["duration"],
            "is_playing": current_data["is_playing"],
            "cover_url": f"/cover?v={current_data['cover_version']}",
            "config": current_config,
            "status": "active",
            "source_id": current_data["source_id"]
        }
    }
    await send_to_listeners(msg)
    last_update_time = current_time

# 💥 назначаем callback для cover_fetcher
cover_fetcher.on_cover_replaced = notify_cover_replaced




@routes.get('/external_cover')
async def external_cover(request):
    cover_path = os.path.join(output_dir, "external_cover.png")
    if not os.path.exists(cover_path):
        return web.Response(status=404)
    return web.FileResponse(cover_path)

@routes.get('/')
async def index(request):
    return web.FileResponse(os.path.join(visualisation_dir, 'index.html'))

@routes.get('/template/{name}')
async def template_handler(request):
    template_name = request.match_info['name']
    template_path = os.path.join(visualisation_dir, template_name)
    if os.path.exists(template_path):
        return web.FileResponse(template_path)
    else:
        return web.Response(status=404, text="Template not found")


@routes.get('/cover')
async def cover(request):
    cover_path = os.path.join(output_dir, "cover.png")
    if not os.path.exists(cover_path):
        return web.Response(status=404)
    return web.FileResponse(cover_path)

@routes.get('/no_cover')
async def no_cover(request):
    no_cover_path = os.path.join(output_dir, "NO COVER.png")
    if not os.path.exists(no_cover_path):
        return web.Response(status=404)
    return web.FileResponse(no_cover_path)

@routes.get('/songinfo/NoCover.png')
async def no_cover_png(request):
    no_cover_path = os.path.join(output_dir, "NoCover.png")
    if not os.path.exists(no_cover_path):
        return web.Response(status=404)
    return web.FileResponse(no_cover_path)

@routes.get('/songinfo/effect.png')
async def effect_png(request):
    effect_path = os.path.join(output_dir, "effect.png")
    if not os.path.exists(effect_path):
        return web.Response(status=404, text="effect.png not found")
    return web.FileResponse(effect_path)



# ЭНДПОИНТ ДЛЯ ПОЛУЧЕНИЯ НАСТРОЕК
@routes.get('/get_config')
async def get_config(request):
    return web.json_response(current_config)

# ЭНДПОИНТ ДЛЯ ОБНОВЛЕНИЯ НАСТРОЕК
@routes.post('/update_config')
async def update_config(request):
    global current_config
    try:
        new_config = await request.json()

        # Обновляем текущую конфигурацию
        current_config.update(new_config)

        # Сохраняем в файл
        config_manager.save_config(current_config)

        # ОТПРАВЛЯЕМ ОБНОВЛЕННЫЕ НАСТРОЙКИ ВСЕМ КЛИЕНТАМ
        msg = {
            "type": "config_update",
            "config": current_config
        }
        await send_to_listeners(msg)

        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)})


# ЭНДПОИНТ ДЛЯ ПРИЕМА ДАННЫХ ОТ C# MediaMonitor
@routes.post('/update_from_cs')
async def update_from_cs(request):
    global last_update_time
    try:
        data = await request.json()
        
        artist = data.get("artist", "Unknown Artist")
        title = data.get("title", "Unknown Title")
        source_id = data.get("source_id", "")
        
        # Проверяем, сменился ли трек
        track_changed = (current_data["artist"] != artist or current_data["title"] != title)
        
        # Обновляем текущие данные
        current_data.update({
            "artist": artist,
            "title": title,
            "position": data.get("position", 0),
            "duration": data.get("duration", 0),
            "is_playing": data.get("is_playing", False),
            "source_id": source_id
        })
        
        # Если трек сменился, сначала загружаем обложку, потом отправляем данные
        if track_changed and artist != "Не воспроизводится":
            print(f"🎵 Новый трек от C#: {artist} - {title}")
            # Загружаем обложку и отправляем обновление
            await fetch_cover_for_track(artist, title)
        else:
            # Если трек не сменился, отправляем обновление позиции/статуса
            current_time = asyncio.get_event_loop().time()
            should_send = current_time - last_update_time >= UPDATE_COOLDOWN
            
            if should_send:
                msg = {
                    "type": "update",
                    "data": {
                        "artist": current_data["artist"],
                        "title": current_data["title"],
                        "position": current_data["position"],
                        "duration": current_data["duration"],
                        "is_playing": current_data["is_playing"],
                        "cover_url": f"/cover?v={current_data['cover_version']}",
                        "config": current_config,
                        "status": data.get("status", "active"),
                        "source_id": current_data["source_id"]
                    }
                }
                await send_to_listeners(msg)
                last_update_time = current_time
        
        return web.json_response({"status": "success"})
    except Exception as e:
        print(f"❌ Ошибка обработки данных от C#: {e}")
        return web.json_response({"status": "error", "message": str(e)})

async def fetch_cover_for_track(artist, title):
    """Загружает обложку для трека через cover_fetcher"""
    try:
        # Используем cover_fetcher для получения обложки
        cover_path, cover_updated = await cover_fetcher.get_best_cover(
            None,  # mediaInfo не нужен, так как нет системной обложки
            artist,
            title,
            output_dir
        )
        
        # ВСЕГДА увеличиваем версию при смене трека, даже если обложка та же
        # Это заставит браузер перезагрузить изображение и пересчитать цвета
        current_data["cover_version"] += 1
        print(f"✅ Обложка {'обновлена' if cover_updated else 'загружена'} для: {artist} - {title}")
        
        # Небольшая задержка чтобы убедиться что файл записан на диск
        await asyncio.sleep(0.1)
        
        # Отправляем обновление клиентам с новой обложкой
        msg = {
            "type": "update",
            "data": {
                "artist": current_data["artist"],
                "title": current_data["title"],
                "position": current_data["position"],
                "duration": current_data["duration"],
                "is_playing": current_data["is_playing"],
                "cover_url": f"/cover?v={current_data['cover_version']}",
                "config": current_config,
                "status": "active",
                "source_id": current_data["source_id"]
            }
        }
        await send_to_listeners(msg)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки обложки: {e}")


@routes.get('/{filename}.html')
async def serve_html(request):
    filename = request.match_info['filename']
    file_path = os.path.join(visualisation_dir, f"{filename}.html")
    if os.path.exists(file_path):
        return web.FileResponse(file_path)
    return web.Response(status=404, text="Template not found")

@routes.get('/{filename}.js')
async def serve_js(request):
    filename = request.match_info['filename']
    file_path = os.path.join(visualisation_dir, f"{filename}.js")
    if os.path.exists(file_path):
        return web.FileResponse(file_path, headers={'Content-Type': 'application/javascript'})
    return web.Response(status=404, text="JavaScript file not found")

# Глобальная переменная для хранения списка источников
available_sources = []

@routes.get('/sources')
async def get_sources(request):
    """Возвращает список источников медиа"""
    return web.json_response({"sources": available_sources})

@routes.post('/update_sources')
async def update_sources(request):
    """Обновляет список доступных источников медиа от C# MediaMonitor"""
    global available_sources
    try:
        data = await request.json()
        available_sources = data.get("sources", [])
        print(f"📻 Получено {len(available_sources)} источников от C# MediaMonitor")
        return web.json_response({"status": "success"})
    except Exception as e:
        print(f"❌ Ошибка обновления источников: {e}")
        return web.json_response({"status": "error", "message": str(e)})




async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    current_data['listeners'].add(ws)
    try:
        # ОТПРАВЛЯЕМ КОНФИГ ПРИ ПОДКЛЮЧЕНИИ
        initial_data = {
            "type": "init",
            "data": {
                "artist": current_data["artist"],
                "title": current_data["title"],
                "position": current_data["position"],
                "duration": current_data["duration"],
                "is_playing": current_data["is_playing"],
                "cover_url": f"/cover?v={current_data['cover_version']}",
                "status": "active" if current_data["artist"] != "Не воспроизводится" else "inactive",
                "config": current_config,
                "source_id": current_data["source_id"]
            }
        }
        await ws.send_json(initial_data)
        async for msg in ws:
            pass
    finally:
        current_data['listeners'].discard(ws)
    return ws


app.add_routes([
    web.get('/', index),
    web.get('/index.html', index),
    web.get('/cover', cover),
    web.get('/no_cover', no_cover),
    web.get('/songinfo/NoCover.png', no_cover_png),
    web.get('/songinfo/effect.png', effect_png),
    web.get('/ws', websocket_handler),
    web.get('/get_config', get_config),
    web.get('/sources', get_sources),
    web.post('/update_config', update_config),
    web.post('/update_sources', update_sources),
    web.post('/update_from_cs', update_from_cs),
    web.get('/{filename}.html', serve_html),
    web.get('/{filename}.js', serve_js),
])


async def start_background_tasks(app):
    print("⚙️ Сервер готов. Ожидание данных от MediaMonitor...")
    # MediaMonitor теперь управляется через MediaMonitorManager в app.py


async def cleanup_background_tasks(app):
    """Cleanup function for server shutdown"""
    # MediaMonitor cleanup is handled by MediaMonitorManager in app.py
    pass

app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)


def run_server(port=80):
    if is_port_in_use(port):
        raise OSError(f"Порт {port} занят")
    print(f"🚀 Сервер запущен: http://localhost:{port}")
    web.run_app(app, port=port)


if __name__ == "__main__":
    run_server()