# now_server/cover_fetcher.py
import aiohttp
import asyncio
import os
import io
from PIL import Image
from config_manager import config_manager
import urllib.parse
import json
import re

# Правильный импорт get_cover_art
try:
    from get_cover_art import CoverArt

    HAS_GET_COVER_ART = True
except ImportError:
    HAS_GET_COVER_ART = False
    CoverArt = None
    print("⚠️ get_cover_art не установлен, будет использоваться только Last.fm")


class CoverFetcher:
    def __init__(self):
        self.config = config_manager.load_config()
        self.replace_after_system = self.config.get("replace_after_system", True)
        self.debug = True
        self.on_cover_replaced = None
        self.use_itunes = self.config.get("use_itunes", True)
        self.use_yandex_music = self.config.get("use_yandex_music", True)
        self.use_vk_music = self.config.get("use_vk_music", True)
        self.active_replace_task = None  # Отслеживание активной задачи замены обложки
        self._session = None  # Переиспользуемая aiohttp сессия
        self._connector = None  # Переиспользуемый коннектор

    def log(self, msg, error=False):
        if self.debug:
            prefix = "Ошибка" if error else "Отладка"
            print(f"{prefix} [DEBUG] {msg}")

    async def _get_session(self):
        """Получает или создает переиспользуемую aiohttp сессию"""
        if self._session is None or self._session.closed:
            # Создаем коннектор с ограничениями для предотвращения накопления соединений
            self._connector = aiohttp.TCPConnector(
                limit=10,  # Максимум 10 соединений
                limit_per_host=5,  # Максимум 5 соединений на хост
                ttl_dns_cache=300,  # Кэш DNS на 5 минут
                force_close=False,  # Переиспользование соединений
                enable_cleanup_closed=True  # Автоматическая очистка закрытых соединений
            )
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout
            )
            self.log("Создана новая aiohttp сессия")
        return self._session

    async def close(self):
        """Закрывает aiohttp сессию и коннектор"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.log("aiohttp сессия закрыта")
        if self._connector and not self._connector.closed:
            await self._connector.close()
            self.log("aiohttp коннектор закрыт")
        self._session = None
        self._connector = None

    async def get_best_cover(self, media_info, artist, title, output_dir):
        cover_path = os.path.join(output_dir, "cover.png")
        found = False
        system_quality = 0

        # --- системная обложка ---
        if media_info and media_info.thumbnail:
            self.log("Пытаемся получить системную обложку...")
            system_data = await self._get_system_cover_data(media_info.thumbnail)
            if system_data:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    with open(cover_path, 'wb') as f:
                        f.write(system_data)
                    found = True
                    self.log(f"Системная обложка сохранена: {cover_path}")
                except Exception as e:
                    self.log(f"Ошибка сохранения системной обложки: {e}", error=True)
                    found = False

                try:
                    system_quality = await self._assess_quality(system_data)
                    self.log(f"Качество системной: {system_quality}")
                except Exception as e:
                    self.log(f"Ошибка оценки системной обложки: {e}", error=True)
                    system_quality = 0

                if self.replace_after_system:
                    # Отменяем предыдущую задачу замены, если она существует
                    if self.active_replace_task and not self.active_replace_task.done():
                        self.log("Отменяем предыдущую задачу замены обложки")
                        self.active_replace_task.cancel()
                        try:
                            await self.active_replace_task
                        except asyncio.CancelledError:
                            pass
                    
                    # Создаем новую задачу замены обложки
                    try:
                        self.active_replace_task = asyncio.create_task(
                            self._maybe_replace_with_external(artist, title, cover_path, system_quality)
                        )
                        self.log("Асинхронный поиск внешней обложки запущен.")
                    except RuntimeError:
                        self.log("Нет активного цикла событий — выполняем внешний поиск синхронно.")
                        await self._maybe_replace_with_external(artist, title, cover_path, system_quality)
                return cover_path, True
            else:
                self.log("Системная обложка отсутствует или нечитабельна", error=True)

        # --- если системной нет ---
        if artist and title:
            self.log("Системной обложки нет — пробуем внешние источники.")
            cover_data = await self._try_external_sources(artist, title)
            if cover_data:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    with open(cover_path, 'wb') as f:
                        f.write(cover_data)
                    self.log("Внешняя обложка сохранена.")
                    return cover_path, True
                except Exception as e:
                    self.log(f"Ошибка записи внешней обложки: {e}", error=True)

        self.log("Обложка не найдена ни системно, ни внешне.", error=True)
        return cover_path, False

    async def _maybe_replace_with_external(self, artist, title, cover_path, system_quality):
        try:
            self.log(f"Ищем внешнюю обложку для: '{artist} - {title}'")
            external = await self._try_external_sources(artist, title)
            if not external:
                self.log("Внешние источники ничего не вернули для замены.", error=True)
                return False

            ext_quality = await self._assess_quality(external)
            self.log(f"Качество внешней: {ext_quality} (системная: {system_quality})")

            if ext_quality > system_quality:
                with open(cover_path, 'wb') as f:
                    f.write(external)
                self.log("Обложка заменена на внешнюю.")
                if callable(self.on_cover_replaced):
                    await self.on_cover_replaced(artist, title)
                return True

            self.log("Внешняя обложка не лучше системной — пропускаем замену.")
            return False

        except asyncio.CancelledError:
            self.log(f"Задача замены обложки отменена: {artist} - {title}")
            raise
        except Exception as e:
            self.log(f"Ошибка в _maybe_replace_with_external: {e}", error=True)
            return False

    async def _try_external_sources(self, artist, title):
        # 1. Яндекс Музыка (высокий приоритет для русского контента)
        if self.use_yandex_music:
            self.log("Пробуем Яндекс Музыку...")
            yandex_data = await self._try_yandex_music_cover(artist, title)
            if yandex_data:
                return yandex_data

        if self.use_vk_music:
            vk_data = await self._try_vk_music_cover(artist, title)
            if vk_data: return vk_data

        # 2. iTunes API
        if self.use_itunes:
            self.log("Пробуем iTunes API...")
            itunes_data = await self._try_itunes_cover(artist, title)
            if itunes_data:
                return itunes_data

        # 3. Last.fm
        self.log("Пробуем Last.fm...")
        lastfm_data = await self._try_lastfm_safe(artist, title)
        if lastfm_data:
            return lastfm_data

        return None

    async def _try_yandex_music_cover(self, artist, title):
        """Поиск обложки через Яндекс Музыку"""
        try:
            self.log(f"Яндекс Музыка поиск: {artist} - {title}")

            # Кодируем запрос
            query = urllib.parse.quote(f"{artist} {title}")
            url = f"https://api.music.yandex.net/search?text={query}&type=track&page=0&pageSize=5"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://music.yandex.ru/",
                "Origin": "https://music.yandex.ru"
            }

            session = await self._get_session()
            async with session.get(url, headers=headers) as resp:
                    self.log(f"Яндекс Музыка → {resp.status}")

                    if resp.status != 200:
                        self.log(f"Яндекс Музыка: ошибка HTTP {resp.status}", error=True)
                        return None

                    try:
                        data = await resp.json()
                    except Exception as e:
                        self.log(f"Яндекс Музыка: ошибка парсинга JSON: {e}", error=True)
                        return None

                    # Парсим структуру ответа Яндекс Музыки
                    tracks = data.get('result', {}).get('tracks', {}).get('results', [])

                    if not tracks:
                        self.log("Яндекс Музыка: треки не найдены")
                        return None

                    # Нормализуем для сравнения
                    orig_artist = self._normalize(artist)
                    orig_title = self._normalize(title)

                    best_match = None
                    best_score = 0

                    for track in tracks:
                        # Получаем основного артиста
                        track_artists = track.get('artists', [])
                        track_artist = self._normalize(track_artists[0].get('name', '')) if track_artists else ""
                        track_title = self._normalize(track.get('title', ''))

                        # Вычисляем score совпадения
                        score = 0
                        if orig_artist in track_artist or track_artist in orig_artist:
                            score += 50
                        if orig_title in track_title or track_title in orig_title:
                            score += 50
                        if track.get('title', '').lower() == title.lower():
                            score += 100  # точное совпадение названия

                        # Получаем обложку альбома
                        album = track.get('albums', [{}])[0] if track.get('albums') else {}
                        cover_uri = album.get('coverUri')

                        if cover_uri and score > best_score:
                            best_score = score
                            # Формируем URL обложки максимального качества
                            cover_url = f"https://{cover_uri.replace('%%', '1000x1000')}"
                            best_match = cover_url

                    if best_match and best_score >= 70:
                        self.log(f"Яндекс Музыка: найдено совпадение (score: {best_score}) → {best_match}")
                        return await self._download_image(session, best_match)
                    else:
                        self.log(f"Яндекс Музыка: нет точного совпадения (лучший score: {best_score})")
                        return None

        except asyncio.TimeoutError:
            self.log("Яндекс Музыка: таймаут запроса", error=True)
            return None
        except Exception as e:
            self.log(f"Яндекс Музыка ошибка: {e}", error=True)
            return None

    async def _try_itunes_cover(self, artist, title):
        try:
            self.log(f"iTunes поиск: {artist} - {title}")
            term = urllib.parse.quote(f"{artist} {title}")
            url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=5&media=music"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://music.apple.com/"
            }

            session = await self._get_session()
            async with session.get(url, headers=headers) as resp:
                    self.log(f"iTunes → {resp.status} | {resp.headers.get('content-type')}")

                    if resp.status != 200:
                        return None

                    try:
                        text = await resp.text()
                        data = json.loads(text)
                    except:
                        self.log(f"JSON parse error", error=True)
                        return None

                    results = data.get("results", [])
                    if not results:
                        self.log("iTunes: ничего не найдено")
                        return None

                    # Нормализация
                    orig_artist = self._normalize(artist)
                    orig_title = self._normalize(title)

                    best_match = None
                    best_score = 0

                    for track in results:
                        itunes_artist = self._normalize(track.get("artistName", ""))
                        itunes_title = self._normalize(track.get("trackName", ""))

                        score = 0
                        if orig_artist in itunes_artist or itunes_artist in orig_artist:
                            score += 50
                        if orig_title in itunes_title or itunes_title in orig_title:
                            score += 50
                        if track.get("trackName", "").lower() == title.lower():
                            score += 100

                        if score > best_score:
                            best_score = score
                            best_match = track

                    if best_match and best_score >= 70:
                        cover_url = best_match.get("artworkUrl100", "").replace("100x100bb", "1000x1000bb")
                        self.log(f"iTunes: точное совпадение → {cover_url} (score: {best_score})")
                        return await self._download_image(session, cover_url)
                    else:
                        self.log(f"iTunes: нет точного совпадения (лучший score: {best_score})")
                        return None

        except Exception as e:
            self.log(f"iTunes ошибка: {e}", error=True)
            return None

    def _normalize(self, text):
        """Приводим к нижнему регистру, убираем лишнее"""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-zа-я0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def _get_system_cover_data(self, thumbnail):
        try:
            from winsdk.windows.storage.streams import DataReader
            stream = await thumbnail.open_read_async()
            reader = DataReader(stream)
            await reader.load_async(stream.size)
            data = bytearray(stream.size)
            reader.read_bytes(data)
            return bytes(data)
        except Exception as e:
            self.log(f"Ошибка получения системной обложки: {e}", error=True)
            return None

    async def _try_lastfm_safe(self, artist, title):
        try:
            api_key = self.config.get("lastfm_api_key") or "f46c4ca29c329b1b3d6fcd0cc7aa60f3"
            url = (
                "http://ws.audioscrobbler.com/2.0/"
                f"?method=track.getInfo&api_key={api_key}&artist={artist}&track={title}&format=json&autocorrect=1"
            )
            self.log(f"Last.fm URL: {url}")
            session = await self._get_session()
            async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    images = data.get('track', {}).get('album', {}).get('image', [])
                    if not images:
                        self.log("Last.fm не вернул images", error=True)
                        return None
                    img_url = images[-1].get('#text')
                    if img_url and not self._is_default_lastfm_cover(img_url):
                        self.log(f"Last.fm: найдено {img_url}")
                        return await self._download_image(session, img_url)
        except Exception as e:
            self.log(f"Last.fm error: {e}", error=True)
        return None

    async def _try_vk_music_cover(self, artist, title):
        """Поиск через VK Music с улучшенным парсингом"""
        try:
            self.log(f"VK Music поиск: {artist} - {title}")

            query = urllib.parse.quote(f"{artist} {title}")
            url = f"https://vk.com/audio?act=search&q={query}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://vk.com/",
            }

            session = await self._get_session()
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    self.log(f"VK Music: HTTP {resp.status}")
                    return None

                html = await resp.text()

                # Ищем данные в нескольких местах
                import re
                import html as html_module

                # 1. Ищем в JSON данных
                json_patterns = [
                    r'window\.AudioPage\s*=\s*({.*?});',
                    r'var\s+audioData\s*=\s*({.*?});',
                    r'<script[^>]*>.*?AudioPage\.data\s*=\s*({.*?});.*?</script>',
                ]

                for pattern in json_patterns:
                    match = re.search(pattern, html, re.DOTALL)
                    if match:
                        try:
                            json_str = html_module.unescape(match.group(1))
                            data = json.loads(json_str)
                            # Пробуем найти обложку в JSON структуре
                            cover_url = self._extract_cover_from_vk_json(data)
                            if cover_url:
                                self.log(f"VK Music: найдено в JSON → {cover_url}")
                                return await self._download_image(session, cover_url)
                        except Exception as e:
                            self.log(f"VK Music JSON parse error: {e}")
                            continue

                # 2. Ищем напрямую в HTML по классам VK
                html_patterns = [
                    r'class="audio_page_audio_cover[^"]*"[^>]*style="[^"]*url\(([^)]+)\)',
                    r'data-background-image="([^"]+)"',
                    r'<img[^>]*class="[^"]*cover[^"]*"[^>]*src="([^"]+)"',
                    r'background-image:\s*url\([\'"]?([^\'")]+)',
                ]

                for pattern in html_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if match and any(x in match for x in ['cover', 'album', 'thumb', 'audio']):
                            cover_url = match
                            if 'http' not in cover_url:
                                cover_url = 'https:' + cover_url if cover_url.startswith(
                                    '//') else 'https://vk.com' + cover_url
                            self.log(f"VK Music: найдено в HTML → {cover_url}")
                            return await self._download_image(session, cover_url)

                # 3. Ищем по прямым ссылкам на изображения
                image_urls = re.findall(r'https://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*', html)
                for img_url in image_urls:
                    if any(x in img_url for x in ['/audio/', '/cover/', '/album/', 'thumb_']):
                        self.log(f"VK Music: найдена прямая ссылка → {img_url}")
                        return await self._download_image(session, img_url)

                self.log("VK Music: обложка не найдена после всех попыток")
                return None

        except Exception as e:
            self.log(f"VK Music ошибка: {e}", error=True)
            return None

    def _extract_cover_from_vk_json(self, data):
        """Извлекаем обложку из JSON структуры VK"""
        try:
            # Пробуем разные пути в JSON
            if isinstance(data, dict):
                # Пробуем найти в списке аудио
                for key in ['list', 'audios', 'items']:
                    if key in data and isinstance(data[key], list) and data[key]:
                        first_track = data[key][0]
                        if 'album' in first_track and 'thumb' in first_track['album']:
                            return first_track['album']['thumb'].get('photo_600')
                        elif 'thumb' in first_track:
                            return first_track['thumb']
        except:
            pass
        return None

    def _extract_cover_from_vk_json(self, data):
        """Извлекаем обложку из JSON структуры VK"""
        try:
            # Пробуем разные пути в JSON
            if isinstance(data, dict):
                # Пробуем найти в списке аудио
                for key in ['list', 'audios', 'items']:
                    if key in data and isinstance(data[key], list) and data[key]:
                        first_track = data[key][0]
                        if 'album' in first_track and 'thumb' in first_track['album']:
                            return first_track['album']['thumb'].get('photo_600')
                        elif 'thumb' in first_track:
                            return first_track['thumb']
        except:
            pass
        return None

    def _is_default_lastfm_cover(self, image_url):
        return any(
            x in image_url
            for x in ['2a96cbd8b46e442fc41c2b86b821562f', 'c6f59c1e5e7240a4c0d427abd71f3dbb']
        )

    async def _assess_quality(self, image_data):
        try:
            img = Image.open(io.BytesIO(image_data))
            w, h = img.size
            score = min((w * h) / 10000, 10)
            aspect = max(w, h) / min(w, h) if min(w, h) else 2
            score += 5 if 0.9 <= aspect <= 1.1 else (2 if 0.7 <= aspect <= 1.3 else 0)
            score += min(len(image_data) / 50000, 5)
            if img.format and img.format.upper() in ['PNG', 'JPEG', 'JPG']:
                score += 2
            self.log(f"Оценка качества: {w}x{h}, {len(image_data)} байт => {score:.1f}")
            return score
        except Exception as e:
            self.log(f"Ошибка оценки качества: {e}", error=True)
            return 0

    async def _download_image(self, session, url):
        try:
            self.log(f"Скачиваем: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://music.yandex.ru/"
            }
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    self.log(f"Скачано: {len(data)} байт")
                    return data
                else:
                    self.log(f"Ошибка скачивания: {resp.status}", error=True)
        except Exception as e:
            self.log(f"Ошибка: {e}", error=True)
        return None


# глобальный инстанс
cover_fetcher = CoverFetcher()