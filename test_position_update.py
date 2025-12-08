#!/usr/bin/env python3
"""
Тест для проверки обновления позиции
Отправляет тестовые данные на сервер и проверяет что они доходят
"""
import requests
import json
import time

PORT = 58080  # Измените если используете другой порт
BASE_URL = f"http://localhost:{PORT}"

def test_position_update():
    """Тестирует отправку обновлений позиции"""
    
    print("🧪 Тест обновления позиции")
    print(f"📡 Сервер: {BASE_URL}")
    print()
    
    # Тест 1: Отправляем начальное состояние
    print("1️⃣ Отправляем начальное состояние...")
    data1 = {
        "artist": "Test Artist",
        "title": "Test Track",
        "position": 10.0,
        "duration": 180.0,
        "is_playing": True,
        "source_id": "test.source"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/update_from_cs", json=data1, timeout=2)
        print(f"   Ответ: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    time.sleep(0.5)
    
    # Тест 2: Отправляем обновление позиции (перемотка)
    print("\n2️⃣ Отправляем обновление позиции (перемотка на 50s)...")
    data2 = {
        "artist": "Test Artist",
        "title": "Test Track",
        "position": 50.0,  # Перемотка
        "duration": 180.0,
        "is_playing": True,
        "source_id": "test.source"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/update_from_cs", json=data2, timeout=2)
        print(f"   Ответ: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    time.sleep(0.5)
    
    # Тест 3: Еще одна перемотка
    print("\n3️⃣ Отправляем еще одну перемотку (на 100s)...")
    data3 = {
        "artist": "Test Artist",
        "title": "Test Track",
        "position": 100.0,  # Еще одна перемотка
        "duration": 180.0,
        "is_playing": True,
        "source_id": "test.source"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/update_from_cs", json=data3, timeout=2)
        print(f"   Ответ: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    print("\n✅ Все тесты прошли успешно!")
    print("📺 Проверьте виджет в браузере - позиция должна обновиться")
    return True

if __name__ == "__main__":
    test_position_update()
