# API Examples - Примеры использования API

## Обзор

Этот документ содержит примеры использования API для интеграции с MediaMonitor системой.

## Endpoints

### 1. POST /update_from_cs

Отправка данных о текущем треке от C# MediaMonitor.

#### C# пример

```csharp
using System.Net.Http;
using System.Text;
using System.Text.Json;

var data = new
{
    artist = "The Beatles",
    title = "Hey Jude",
    position = 45.5,
    duration = 431.0,
    is_playing = true,
    cover_version = 1,
    status = "active"
};

var json = JsonSerializer.Serialize(data);
var content = new StringContent(json, Encoding.UTF8, "application/json");

var httpClient = new HttpClient();
var response = await httpClient.PostAsync(
    "http://localhost:80/update_from_cs", 
    content
);

if (response.IsSuccessStatusCode)
{
    Console.WriteLine("✅ Данные отправлены успешно!");
}
```

#### Python пример

```python
import requests

data = {
    "artist": "The Beatles",
    "title": "Hey Jude",
    "position": 45.5,
    "duration": 431.0,
    "is_playing": True,
    "cover_version": 1,
    "status": "active"
}

response = requests.post(
    "http://localhost:80/update_from_cs",
    json=data
)

if response.status_code == 200:
    print("✅ Данные отправлены успешно!")
    print(response.json())
```

#### JavaScript пример

```javascript
const data = {
    artist: "The Beatles",
    title: "Hey Jude",
    position: 45.5,
    duration: 431.0,
    is_playing: true,
    cover_version: 1,
    status: "active"
};

fetch("http://localhost:80/update_from_cs", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
    console.log("✅ Данные отправлены успешно!", result);
})
.catch(error => {
    console.error("❌ Ошибка:", error);
});
```

#### cURL пример

```bash
curl -X POST http://localhost:80/update_from_cs \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "The Beatles",
    "title": "Hey Jude",
    "position": 45.5,
    "duration": 431.0,
    "is_playing": true,
    "cover_version": 1,
    "status": "active"
  }'
```

### 2. GET /cover

Получение текущей обложки альбома.

#### HTML пример

```html
<img src="http://localhost:80/cover?v=1" alt="Album Cover">
```

#### JavaScript пример

```javascript
// Динамическое обновление обложки
function updateCover(version) {
    const img = document.getElementById('cover');
    img.src = `http://localhost:80/cover?v=${version}`;
}
```

#### Python пример

```python
import requests

response = requests.get("http://localhost:80/cover")
if response.status_code == 200:
    with open("downloaded_cover.png", "wb") as f:
        f.write(response.content)
    print("✅ Обложка загружена!")
```

### 3. WebSocket /ws

Подключение к WebSocket для получения обновлений в реальном времени.

#### JavaScript пример

```javascript
const ws = new WebSocket("ws://localhost:80/ws");

ws.onopen = () => {
    console.log("✅ WebSocket подключен!");
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === "init") {
        console.log("📦 Начальные данные:", message.data);
        updateUI(message.data);
    } 
    else if (message.type === "update") {
        console.log("🔄 Обновление:", message.data);
        updateUI(message.data);
    }
    else if (message.type === "config_update") {
        console.log("⚙️ Обновление конфигурации:", message.config);
        updateConfig(message.config);
    }
};

ws.onerror = (error) => {
    console.error("❌ WebSocket ошибка:", error);
};

ws.onclose = () => {
    console.log("🔌 WebSocket отключен");
    // Переподключение через 5 секунд
    setTimeout(() => {
        location.reload();
    }, 5000);
};

function updateUI(data) {
    document.getElementById('artist').textContent = data.artist;
    document.getElementById('title').textContent = data.title;
    document.getElementById('cover').src = data.cover_url;
    
    const progress = (data.position / data.duration) * 100;
    document.getElementById('progress').style.width = progress + '%';
    
    const playButton = document.getElementById('play-button');
    playButton.textContent = data.is_playing ? '⏸' : '▶';
}
```

#### Python пример (websockets library)

```python
import asyncio
import websockets
import json

async def listen_to_updates():
    uri = "ws://localhost:80/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket подключен!")
        
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "init":
                print("📦 Начальные данные:", data["data"])
            elif data["type"] == "update":
                print(f"🎵 {data['data']['artist']} - {data['data']['title']}")
                print(f"⏱ {data['data']['position']:.1f}/{data['data']['duration']:.1f}s")

asyncio.run(listen_to_updates())
```

### 4. POST /update_config

Обновление конфигурации сервера.

#### JavaScript пример

```javascript
const newConfig = {
    selected_media_source: "Spotify.exe",
    use_builtin_monitor: false,
    custom_setting: "value"
};

fetch("http://localhost:80/update_config", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(newConfig)
})
.then(response => response.json())
.then(result => {
    console.log("✅ Конфигурация обновлена!", result);
})
.catch(error => {
    console.error("❌ Ошибка:", error);
});
```

#### Python пример

```python
import requests

new_config = {
    "selected_media_source": "Spotify.exe",
    "use_builtin_monitor": False,
    "custom_setting": "value"
}

response = requests.post(
    "http://localhost:80/update_config",
    json=new_config
)

if response.status_code == 200:
    print("✅ Конфигурация обновлена!")
    print(response.json())
```

### 5. GET /sources

Получение списка доступных источников медиа.

#### JavaScript пример

```javascript
fetch("http://localhost:80/sources")
    .then(response => response.json())
    .then(data => {
        console.log("📻 Доступные источники:", data.sources);
        
        const select = document.getElementById('source-select');
        data.sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source.id;
            option.textContent = source.name;
            select.appendChild(option);
        });
    });
```

#### Python пример

```python
import requests

response = requests.get("http://localhost:80/sources")
if response.status_code == 200:
    data = response.json()
    print("📻 Доступные источники:")
    for source in data["sources"]:
        print(f"  - {source['name']} ({source['id']})")
```

## Полный пример: Веб-виджет

```html
<!DOCTYPE html>
<html>
<head>
    <title>Now Playing Widget</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: white;
            padding: 20px;
        }
        .widget {
            max-width: 400px;
            background: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
        }
        #cover {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        .info {
            margin-bottom: 10px;
        }
        .artist {
            font-size: 18px;
            font-weight: bold;
        }
        .title {
            font-size: 16px;
            color: #aaa;
        }
        .progress-bar {
            width: 100%;
            height: 5px;
            background: #444;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress {
            height: 100%;
            background: #1db954;
            transition: width 0.3s;
        }
        .time {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="widget">
        <img id="cover" src="http://localhost:80/cover" alt="Cover">
        <div class="info">
            <div class="artist" id="artist">Не воспроизводится</div>
            <div class="title" id="title">Нет данных</div>
        </div>
        <div class="progress-bar">
            <div class="progress" id="progress"></div>
        </div>
        <div class="time">
            <span id="current-time">0:00</span>
            <span id="total-time">0:00</span>
        </div>
    </div>

    <script>
        const ws = new WebSocket("ws://localhost:80/ws");

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === "init" || message.type === "update") {
                const data = message.data;
                
                document.getElementById('artist').textContent = data.artist;
                document.getElementById('title').textContent = data.title;
                document.getElementById('cover').src = data.cover_url;
                
                const progress = (data.position / data.duration) * 100;
                document.getElementById('progress').style.width = progress + '%';
                
                document.getElementById('current-time').textContent = 
                    formatTime(data.position);
                document.getElementById('total-time').textContent = 
                    formatTime(data.duration);
            }
        };

        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    </script>
</body>
</html>
```

## Тестирование API

### Проверка доступности сервера

```bash
curl http://localhost:80/
```

### Проверка endpoint обновления

```bash
curl -X POST http://localhost:80/update_from_cs \
  -H "Content-Type: application/json" \
  -d '{"artist":"Test","title":"Track","position":0,"duration":180,"is_playing":true,"cover_version":1,"status":"active"}'
```

### Проверка WebSocket

```javascript
// В консоли браузера
const ws = new WebSocket("ws://localhost:80/ws");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Обработка ошибок

### Пример с обработкой ошибок (JavaScript)

```javascript
async function sendUpdate(data) {
    try {
        const response = await fetch("http://localhost:80/update_from_cs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.status === "success") {
            console.log("✅ Успешно!");
        } else {
            console.error("❌ Ошибка:", result.message);
        }
    } catch (error) {
        console.error("❌ Ошибка сети:", error);
    }
}
```

### Пример с обработкой ошибок (Python)

```python
import requests
from requests.exceptions import RequestException

def send_update(data):
    try:
        response = requests.post(
            "http://localhost:80/update_from_cs",
            json=data,
            timeout=5
        )
        response.raise_for_status()
        
        result = response.json()
        if result.get("status") == "success":
            print("✅ Успешно!")
        else:
            print(f"❌ Ошибка: {result.get('message')}")
            
    except RequestException as e:
        print(f"❌ Ошибка сети: {e}")
```

## Rate Limiting

Рекомендуется не отправлять обновления чаще чем раз в 100ms:

```javascript
let lastUpdate = 0;
const UPDATE_COOLDOWN = 100; // ms

function throttledUpdate(data) {
    const now = Date.now();
    if (now - lastUpdate < UPDATE_COOLDOWN) {
        return; // Пропускаем обновление
    }
    
    lastUpdate = now;
    sendUpdate(data);
}
```

## Дополнительные ресурсы

- [Документация по архитектуре](ARCHITECTURE.md)
- [Руководство по интеграции](../INTEGRATION_GUIDE_RU.md)
- [Тестовый скрипт](../test_integration.py)
