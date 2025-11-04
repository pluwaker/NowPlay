# now_server/now.py
import asyncio
from aiohttp import web
import os
import socket
import json
from pathlib import Path
import sys
from now_server.cover_fetcher import cover_fetcher



# Добавляем путь для импорта config_manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_manager import config_manager

from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)
from winsdk.windows.storage.streams import DataReader

# Загрузка конфигурации через единый менеджер
current_config = config_manager.load_config()

def reload_config():
    """Перезагружает конфигурацию из файла"""
    global current_config
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
    "is_playing": False # статус воспроизведения
}


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


# async def save_cover_image(thumbnail):
#     cover_path = os.path.join(output_dir, "cover.png")
#     try:
#         stream = await thumbnail.open_read_async()
#         reader = DataReader(stream)
#         await reader.load_async(stream.size)
#         buffer = reader.read_buffer(stream.size)
#
#         with open(cover_path, 'wb') as f:
#             f.write(buffer)
#         return True
#     except Exception as e:
#         print(f"Ошибка сохранения обложки: {e}")
#         return False

async def notify_cover_replaced(artist, title):
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
            "status": "active"
        }
    }
    for ws in list(current_data['listeners']):
        try:
            await ws.send_json(msg)
        except:
            current_data['listeners'].remove(ws)

# 💥 назначаем callback для cover_fetcher
cover_fetcher.on_cover_replaced = notify_cover_replaced


async def get_session_by_source(sessions, selected_source):
    """Получает сессию по выбранному источнику"""
    if not selected_source or selected_source == "" or selected_source == "auto":
        # Автоматический выбор - текущая сессия
        return sessions.get_current_session()
    
    # Ищем сессию с указанным source_app_user_model_id
    all_sessions = sessions.get_sessions()
    for session in all_sessions:
        try:
            app_id = session.source_app_user_model_id
            if app_id == selected_source:
                return session
        except Exception:
            continue
    
    return None

async def media_monitor():
    last_artist = ""
    last_title = ""
    last_position = 0
    last_is_playing = False
    last_duration = 0
    track_change_time = 0
    pending_track_change = False  # Флаг ожидающей смены трека

    while True:
        try:
            # Перезагружаем конфигурацию для получения актуального источника
            reload_config()
            selected_source = current_config.get("selected_media_source", "")
            
            sessions = await MediaManager.request_async()
            current_session = await get_session_by_source(sessions, selected_source)
            
            if current_session:
                media_info = await current_session.try_get_media_properties_async()
                new_artist = media_info.artist or "Unknown Artist"
                new_title = media_info.title or "Unknown Title"

                # Получаем данные о прогрессе
                timeline_properties = current_session.get_timeline_properties()
                playback_info = current_session.get_playback_info()

                position = timeline_properties.position.total_seconds() if timeline_properties else 0
                duration = timeline_properties.end_time.total_seconds() if timeline_properties else 0
                is_playing = playback_info.playback_status == 4

                # Определяем, сменился ли трек
                track_changed = (last_artist != new_artist or last_title != new_title)

                if track_changed:
                    print(f"🎵 Новый трек: {new_artist} - {new_title}")

                    # Обнуляем всё
                    current_data.update({
                        "artist": new_artist,
                        "title": new_title,
                        "position": 0,
                        "duration": 0,
                        "is_playing": is_playing
                    })

                    # Отправляем моментальное обновление
                    msg = {
                        "type": "update",
                        "data": {
                            "artist": new_artist,
                            "title": new_title,
                            "position": 0,
                            "duration": 0,
                            "is_playing": is_playing,
                            "cover_url": f"/cover?v={current_data['cover_version']}",
                            "config": current_config,
                            "status": "active"
                        }
                    }
                    for ws in list(current_data['listeners']):
                        try:
                            await ws.send_json(msg)
                        except:
                            current_data['listeners'].remove(ws)

                    # Обновляем обложку
                    cover_path, cover_updated = await cover_fetcher.get_best_cover(
                        media_info, new_artist, new_title, output_dir
                    )
                    if cover_updated:
                        current_data["cover_version"] += 1
                        # Отправляем отдельное сообщение с обновленной обложкой
                        cover_update_msg = {
                            "type": "update",
                            "data": {
                                "artist": new_artist,
                                "title": new_title,
                                "position": 0,
                                "duration": 0,
                                "is_playing": is_playing,
                                "cover_url": f"/cover?v={current_data['cover_version']}",
                                "config": current_config,
                                "status": "active"
                            }
                        }
                        for ws in list(current_data['listeners']):
                            try:
                                await ws.send_json(cover_update_msg)
                            except:
                                current_data['listeners'].remove(ws)

                    # ⏳ Принудительно ждём обновления длительности
                    real_duration = 0
                    for i in range(10):  # максимум 5 секунд
                        await asyncio.sleep(0.5)
                        try:
                            timeline = current_session.get_timeline_properties()
                            new_dur = timeline.end_time.total_seconds() if timeline else 0
                            if new_dur > 0 and new_dur != last_duration:
                                real_duration = new_dur
                                break
                        except Exception:
                            pass

                    current_data["duration"] = real_duration

                    # Отправляем финальное обновление с актуальным cover_url и duration
                    final_msg = {
                        "type": "update",
                        "data": {
                            "artist": new_artist,
                            "title": new_title,
                            "position": 0,
                            "duration": real_duration,
                            "is_playing": is_playing,
                            "cover_url": f"/cover?v={current_data['cover_version']}",
                            "config": current_config,
                            "status": "active"
                        }
                    }
                    for ws in list(current_data['listeners']):
                        try:
                            await ws.send_json(final_msg)
                        except:
                            current_data['listeners'].remove(ws)

                    # Обновляем последние значения
                    last_artist = new_artist
                    last_title = new_title
                    last_position = 0
                    last_duration = real_duration
                    last_is_playing = is_playing

                    continue

                # Если у нас ожидающая смены трека, проверяем валидность данных
                if pending_track_change:
                    # Проверяем, не являются ли данные устаревшими (позиция > 10% длительности)
                    if duration > 0 and position > duration * 0.1:
                        print(f"Обнаружены устаревшие данные: position={position}, duration={duration}")
                        position = 0

                    # Снимаем флаг через 3 секунды
                    if asyncio.get_event_loop().time() - track_change_time > 3:
                        pending_track_change = False

                position_changed = abs(last_position - position) > 2
                playback_status_changed = last_is_playing != is_playing
                duration_changed = abs(last_duration - duration) > 1

                if position_changed or playback_status_changed or duration_changed:
                    # Обновляем данные
                    current_data.update({
                        "artist": new_artist,
                        "title": new_title,
                        "position": position,
                        "duration": duration,
                        "is_playing": is_playing
                    })

                    # Отправляем обновление
                    msg = {
                        "type": "update",
                        "data": {
                            "artist": new_artist,
                            "title": new_title,
                            "position": position,
                            "duration": duration,
                            "is_playing": is_playing,
                            "cover_url": f"/cover?v={current_data['cover_version']}",
                            "config": current_config,
                            "status": "active"
                        }
                    }
                    for ws in list(current_data['listeners']):
                        try:
                            await ws.send_json(msg)
                        except:
                            current_data['listeners'].remove(ws)

                    # Обновляем последние значения
                    last_artist = new_artist
                    last_title = new_title
                    last_position = position
                    last_is_playing = is_playing
                    last_duration = duration

            else:
                # Нет активной сессии
                # Проверяем, действительно ли нет активной сессии (не просто временная задержка)
                # Используем небольшую задержку, чтобы не отправлять inactive слишком рано
                if current_data["artist"] != "Не воспроизводится":
                    # Небольшая задержка перед отправкой inactive, чтобы избежать ложных срабатываний
                    await asyncio.sleep(0.5)
                    # Проверяем еще раз после задержки - возможно, сессия появилась
                    sessions_check = await MediaManager.request_async()
                    current_session_check = await get_session_by_source(sessions_check, selected_source)
                    
                    if not current_session_check:
                        # Реально нет сессии - отправляем inactive
                        current_data.update({
                            "artist": "Не воспроизводится",
                            "title": "Нет данных",
                            "position": 0,
                            "duration": 0,
                            "is_playing": False
                        })

                        msg = {
                            "type": "update",
                            "data": {
                                "artist": "Не воспроизводится",
                                "title": "Нет данных",
                                "position": 0,
                                "duration": 0,
                                "is_playing": False,
                                "cover_url": f"/cover?v={current_data['cover_version']}",
                                "config": current_config,
                                "status": "inactive"
                            }
                        }
                        for ws in list(current_data['listeners']):
                            try:
                                await ws.send_json(msg)
                            except:
                                current_data['listeners'].remove(ws)

                        last_artist = "Не воспроизводится"
                        last_title = "Нет данных"
                        last_position = 0
                        last_is_playing = False
                        last_duration = 0
                        pending_track_change = False

        except Exception as e:
            print(f"Ошибка мониторинга медиа: {e}")

        await asyncio.sleep(1)

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


@routes.get('/{filename}.html')
async def serve_html(request):
    filename = request.match_info['filename']
    file_path = os.path.join(visualisation_dir, f"{filename}.html")
    if os.path.exists(file_path):
        return web.FileResponse(file_path)
    return web.Response(status=404, text="Template not found")

@routes.get('/sources')
async def get_sources(request):
    """Возвращает список активных источников (плееров) с их именами"""
    try:
        sessions = await MediaManager.request_async()
        all_sessions = sessions.get_sessions()

        sources = []
        seen_ids = set()
        
        for s in all_sessions:
            try:
                app_id = s.source_app_user_model_id
                if app_id and app_id not in seen_ids:
                    seen_ids.add(app_id)
                    # Пытаемся получить читаемое имя приложения
                    display_name = app_id  # По умолчанию используем ID
                    try:
                        media_info = await s.try_get_media_properties_async()
                        # Пробуем разные способы получить имя
                        if hasattr(media_info, 'display_source') and media_info.display_source:
                            display_name = media_info.display_source
                        elif hasattr(media_info, 'app_display_name') and media_info.app_display_name:
                            display_name = media_info.app_display_name
                        # Упрощаем длинные ID (убираем версии и лишние части)
                        if display_name == app_id and len(app_id) > 40:
                            # Пытаемся извлечь имя приложения из ID
                            parts = app_id.split('!')
                            if len(parts) > 0:
                                app_part = parts[0].split('.')
                                if len(app_part) > 0:
                                    display_name = app_part[-1]
                    except Exception as e:
                        # Если не удалось получить имя, используем ID
                        pass
                    
                    sources.append({
                        "id": app_id,
                        "name": display_name
                    })
            except Exception:
                continue

        return web.json_response({"sources": sources})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


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
    web.get('/index.html', index),
    web.get('/cover', cover),
    web.get('/no_cover', no_cover),
    web.get('/songinfo/NoCover.png', no_cover_png),
    web.get('/ws', websocket_handler),
    web.get('/sources', get_sources),
    web.post('/update_config', update_config),
    web.get('/{filename}.html', serve_html),
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