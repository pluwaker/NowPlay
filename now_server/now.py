# now_server/now.py
import asyncio
from aiohttp import web
import os
import socket
import json
from pathlib import Path
import sys

# Добавляем путь для импорта config_manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_manager import config_manager

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)
from winsdk.windows.storage.streams import DataReader

# Загрузка конфигурации через единый менеджер
current_config = config_manager.load_config()

# Определяем пути
PROJECT_ROOT = Path(__file__).parent.parent
output_dir = PROJECT_ROOT / "songinfo"
output_dir.mkdir(exist_ok=True)
output_dir = str(output_dir)

app = web.Application()
routes = web.RouteTableDef()

current_data = {
    "artist": "Не воспроизводится",
    "title": "Нет данных",
    "cover_version": 1,
    "listeners": set()
}


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


async def save_cover_image(thumbnail):
    cover_path = os.path.join(output_dir, "cover.png")
    try:
        stream = await thumbnail.open_read_async()
        reader = DataReader(stream)
        await reader.load_async(stream.size)
        buffer = reader.read_buffer(stream.size)

        with open(cover_path, 'wb') as f:
            f.write(buffer)
        return True
    except Exception as e:
        print(f"Ошибка сохранения обложки: {e}")
        return False


async def media_monitor():
    while True:
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()
            if current_session:
                media_info = await current_session.try_get_media_properties_async()
                new_artist = media_info.artist or "Unknown Artist"
                new_title = media_info.title or "Unknown Title"

                if (current_data["artist"] != new_artist or
                        current_data["title"] != new_title):

                    cover_updated = False
                    if media_info.thumbnail:
                        cover_updated = await save_cover_image(media_info.thumbnail)

                    current_data.update({
                        "artist": new_artist,
                        "title": new_title,
                        "cover_version": current_data["cover_version"] + 1
                        if cover_updated else current_data["cover_version"]
                    })

                    # ОТПРАВЛЯЕМ НАСТРОЙКИ ВМЕСТЕ С ДАННЫМИ О ТРЕКЕ
                    msg = {
                        "type": "update",
                        "data": {
                            "artist": new_artist,
                            "title": new_title,
                            "cover_url": f"/cover?v={current_data['cover_version']}",
                            "config": current_config
                        }
                    }
                    for ws in list(current_data['listeners']):
                        try:
                            await ws.send_json(msg)
                        except:
                            current_data['listeners'].remove(ws)
            else:
                # Нет активной сессии
                if current_data["artist"] != "Не воспроизводится":
                    current_data.update({
                        "artist": "Не воспроизводится",
                        "title": "Нет данных"
                    })
                    msg = {
                        "type": "update",
                        "data": {
                            "artist": "Не воспроизводится",
                            "title": "Нет данных",
                            "cover_url": f"/cover?v={current_data['cover_version']}",
                            "config": current_config
                        }
                    }
                    for ws in list(current_data['listeners']):
                        try:
                            await ws.send_json(msg)
                        except:
                            current_data['listeners'].remove(ws)
        except Exception as e:
            print(f"Ошибка мониторинга медиа: {e}")

        await asyncio.sleep(3)


@routes.get('/')
async def index(request):
    return web.FileResponse(os.path.join(output_dir, 'visualisation.html'))


@routes.get('/cover')
async def cover(request):
    cover_path = os.path.join(output_dir, "cover.png")
    if not os.path.exists(cover_path):
        return web.Response(status=404)
    return web.FileResponse(cover_path)


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
        for ws in list(current_data['listeners']):
            try:
                await ws.send_json(msg)
            except:
                current_data['listeners'].remove(ws)

        return web.json_response({"status": "success"})
    except Exception as e:
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
                "cover_url": f"/cover?v={current_data['cover_version']}",
                "status": "active",
                "config": current_config
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
    web.get('/visualisation.html', index),
    web.get('/cover', cover),
    web.get('/ws', websocket_handler),
    web.post('/update_config', update_config)
])


async def start_background_tasks(app):
    app['media_monitor'] = asyncio.create_task(media_monitor())


app.on_startup.append(start_background_tasks)


def run_server(port=80):
    if is_port_in_use(port):
        raise OSError(f"Порт {port} занят")
    print(f"🚀 Сервер запущен: http://localhost:{port}")
    web.run_app(app, port=port)


if __name__ == "__main__":
    run_server()