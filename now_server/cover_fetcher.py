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

    def log(self, msg, error=False):
        if self.debug:
            prefix = "Ошибка" if error else "Отладка"
            print(f"{prefix} [DEBUG] {msg}")

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
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
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

        except Exception as e:
            self.log(f"Ошибка в _maybe_replace_with_external: {e}", error=True)
            return False

    async def _try_external_sources(self, artist, title):
        # 1. iTunes API (первый приоритет)
        if self.use_itunes:
            self.log("Пробуем iTunes API...")
            itunes_data = await self._try_itunes_cover(artist, title)
            if itunes_data:
                return itunes_data

        # 2. Last.fm
        self.log("Пробуем Last.fm...")
        lastfm_data = await self._try_lastfm_safe(artist, title)
        if lastfm_data:
            return lastfm_data

        return None

    import json
    import re
    import urllib.parse

    async def _try_itunes_cover(self, artist, title):
        try:
            self.log(f"iTunes поиск: {artist} - {title}")
            term = urllib.parse.quote(f"{artist} {title}")
            url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=5&media=music"  # limit=5 для выбора лучшего

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://music.apple.com/"
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                session.headers.update(headers)

                async with session.get(url) as resp:
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

                    # --- НОРМАЛИЗАЦИЯ ---
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
                            score += 100  # точное совпадение названия

                        if score > best_score:
                            best_score = score
                            best_match = track

                    if best_match and best_score >= 70:  # порог доверия
                        cover_url = best_match.get("artworkUrl100", "").replace("100x100bb", "1000x1000bb")
                        self.log(f"iTunes: точное совпадение → {cover_url} (score: {best_score})")
                        return await self._download_image(session, cover_url)
                    else:
                        self.log(f"iTunes: нет точного совпадения (лучший score: {best_score})")
                        return None

        except Exception as e:
            self.log(f"iTunes ошибка: {e}", error=True)
            return None

        return None

    def _normalize(self, text):
        """Приводим к нижнему регистру, убираем лишнее"""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^a-zа-я0-9\s]', '', text)  # только буквы, цифры, пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_itunes_cover_sync(self, artist, title):
        """Синхронный поиск через get_cover_art.itunes()"""
        try:
            # Правильный вызов: через экземпляр CoverArt
            results = self._cover_art.itunes(artist=artist, title=title, limit=1)
            if not results:
                self.log(f"iTunes: ничего не найдено для '{artist} - {title}'")
                return None

            track = results[0]
            url = track.artwork_url

            # Заменяем низкое разрешение на максимальное
            if '100x100' in url:
                url = url.replace('100x100', '1000x1000')
            elif '60x60' in url:
                url = url.replace('60x60', '1000x1000')

            return {'url': url, 'source': 'itunes'}

        except Exception as e:
            self.log(f"Ошибка в синхронном iTunes поиске: {e}", error=True)
            return None

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
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
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
                "Referer": "https://music.apple.com/"
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