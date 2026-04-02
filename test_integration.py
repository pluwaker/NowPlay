"""
Тестовый скрипт для проверки интеграции C# MediaMonitor с Python сервером
"""
import requests
import json
import time

SERVER_URL = "http://localhost:58080"

def test_update_from_cs():
    """Тестирует endpoint /update_from_cs"""
    print("🧪 Тестирование endpoint /update_from_cs...")
    
    test_data = {
        "artist": "Test Artist",
        "title": "Test Track",
        "position": 30.5,
        "duration": 180.0,
        "is_playing": True,
        "cover_version": 1,
        "status": "active"
    }
    
    try:
        response = requests.post(
            f"{SERVER_URL}/update_from_cs",
            json=test_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("✅ Тест пройден! Сервер принял данные.")
                return True
            else:
                print(f"❌ Ошибка: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что Python сервер запущен.")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_server_availability():
    """Проверяет доступность сервера"""
    print("🧪 Проверка доступности сервера...")
    
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер доступен!")
            return True
        else:
            print(f"⚠️ Сервер вернул код: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Сервер недоступен. Запустите: python main.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_multiple_updates():
    """Тестирует отправку нескольких обновлений подряд"""
    print("🧪 Тестирование множественных обновлений...")
    
    success_count = 0
    for i in range(5):
        test_data = {
            "artist": f"Artist {i}",
            "title": f"Track {i}",
            "position": i * 10.0,
            "duration": 180.0,
            "is_playing": i % 2 == 0,
            "cover_version": i + 1,
            "status": "active"
        }
        
        try:
            response = requests.post(
                f"{SERVER_URL}/update_from_cs",
                json=test_data,
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"  ✓ Обновление {i+1}/5 отправлено")
            else:
                print(f"  ✗ Обновление {i+1}/5 не удалось")
                
        except Exception as e:
            print(f"  ✗ Ошибка при обновлении {i+1}/5: {e}")
        
        time.sleep(0.2)  # Небольшая задержка между запросами
    
    if success_count == 5:
        print(f"✅ Все обновления отправлены успешно! ({success_count}/5)")
        return True
    else:
        print(f"⚠️ Отправлено {success_count}/5 обновлений")
        return False

def main():
    print("=" * 60)
    print("  Тест интеграции C# MediaMonitor ↔ Python Server")
    print("=" * 60)
    print()
    
    # Тест 1: Доступность сервера
    if not test_server_availability():
        print("\n❌ Сервер недоступен. Дальнейшие тесты невозможны.")
        return
    
    print()
    
    # Тест 2: Отправка одного обновления
    test_update_from_cs()
    
    print()
    
    # Тест 3: Множественные обновления
    test_multiple_updates()
    
    print()
    print("=" * 60)
    print("  Тестирование завершено!")
    print("=" * 60)
    print()
    print("💡 Для полного теста запустите C# MediaMonitor:")
    print("   cd MediaMonitor && dotnet run")

if __name__ == "__main__":
    main()
