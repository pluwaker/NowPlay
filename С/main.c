/*
 * ============================================================================
 * WebNowPlaying Rainmeter Plugin - Test Program
 * ============================================================================
 * 
 * Это тестовая программа для плагина WebNowPlaying для Rainmeter.
 * Она тестирует все функции плагина с использованием заглушек для Rainmeter API.
 * 
 * Для компиляции:
 *   1. Убедитесь, что measure.c скомпилирован как обычный объектный файл
 *      (не как DLL) или определен макрос TEST_MODE в measure.c
 *   2. Скомпилируйте: cl main.c measure.c /Fe:test.exe
 *      или: gcc main.c measure.c -o test.exe
 * 
 * ============================================================================
 */

#include "wnp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <stdarg.h>
#include <wchar.h>

// ============================================================================
// Заглушки для функций Rainmeter API (для тестирования)
// ============================================================================

static void* g_test_rm = (void*)0x1234; // Фиктивный указатель Rainmeter

void __cdecl LSLog(int level, LPCWSTR unused, LPCWSTR message) {
    const wchar_t* level_str = L"UNKNOWN";
    switch (level) {
        case 1: level_str = L"ERROR"; break;
        case 2: level_str = L"WARNING"; break;
        case 3: level_str = L"NOTICE"; break;
        case 4: level_str = L"DEBUG"; break;
    }
    wprintf(L"[%ls] %ls\n", level_str, message);
}

void __stdcall RmLog(void* rm, int level, LPCWSTR message) {
    LSLog(level, NULL, message);
}

void __cdecl RmLogF(void* rm, int level, LPCWSTR message, ...) {
    wchar_t buffer[1024];
    va_list args;
    va_start(args, message);
    vswprintf_s(buffer, 1024, message, args);
    va_end(args);
    RmLog(rm, level, buffer);
}

// Глобальная переменная для хранения текущего PlayerType для тестирования
static LPCWSTR g_test_player_type = L"status";
static LPCWSTR g_test_player_id = L"active";

LPCWSTR __stdcall RmReadString(void* rm, LPCWSTR option, LPCWSTR default_value, BOOL replace_measures) {
    // Тестовая версия RmReadString, которая возвращает значения для тестирования
    static wchar_t buffer[WNP_STR_LEN];
    
    if (wcscmp(option, L"PlayerType") == 0) {
        wcscpy_s(buffer, WNP_STR_LEN, g_test_player_type);
        return buffer;
    }
    if (wcscmp(option, L"PlayerId") == 0) {
        wcscpy_s(buffer, WNP_STR_LEN, g_test_player_id);
        return buffer;
    }
    
    // Для остальных опций используем дефолтное значение
    wcscpy_s(buffer, WNP_STR_LEN, default_value);
    return buffer;
}

LPCWSTR __stdcall RmPathToAbsolute(void* rm, LPCWSTR relativePath) {
    // Заглушка - возвращает путь как есть
    return relativePath;
}

// ============================================================================
// Заглушки/Реализация WebNowPlaying API (для тестирования)
// ============================================================================

static bool g_wnp_initialized = false;
static wnp_player_t g_test_players[WNP_MAX_PLAYERS];
static int g_test_player_count = 0;
static int g_active_player_id = -1;
static wnp_args_t g_wnp_args;

// Инициализация WebNowPlaying
wnp_init_ret_t wnp_init(const wnp_args_t* args) {
    if (g_wnp_initialized) {
        return WNP_INIT_SUCCESS;
    }
    
    if (args) {
        memcpy(&g_wnp_args, args, sizeof(wnp_args_t));
    }
    
    // Инициализация тестовых данных
    g_test_player_count = 0;
    g_active_player_id = -1;
    g_wnp_initialized = true;
    
    printf("[WebNowPlaying] Initialized (test mode)\n");
    return WNP_INIT_SUCCESS;
}

void wnp_uninit(void) {
    if (!g_wnp_initialized) {
        return;
    }
    
    g_wnp_initialized = false;
    g_test_player_count = 0;
    g_active_player_id = -1;
    
    printf("[WebNowPlaying] Uninitialized\n");
}

bool wnp_is_initialized(void) {
    return g_wnp_initialized;
}

bool wnp_get_active_player(wnp_player_t* player_out) {
    if (!player_out || !g_wnp_initialized) {
        return false;
    }
    
    if (g_active_player_id >= 0 && g_active_player_id < g_test_player_count) {
        *player_out = g_test_players[g_active_player_id];
        return true;
    }
    
    *player_out = WNP_DEFAULT_PLAYER;
    return false;
}

bool wnp_get_player(int player_id, wnp_player_t* player_out) {
    if (!player_out || !g_wnp_initialized) {
        return false;
    }
    
    for (int i = 0; i < g_test_player_count; i++) {
        if (g_test_players[i].id == player_id) {
            *player_out = g_test_players[i];
            return true;
        }
    }
    
    *player_out = WNP_DEFAULT_PLAYER;
    return false;
}

int wnp_get_all_players(wnp_player_t* players_out) {
    if (!g_wnp_initialized) {
        return 0;
    }
    
    if (players_out && g_test_player_count > 0) {
        memcpy(players_out, g_test_players, sizeof(wnp_player_t) * g_test_player_count);
    }
    
    return g_test_player_count;
}

int wnp_get_remaining_seconds(const wnp_player_t* player) {
    if (!player) return 0;
    int remaining = player->duration - player->position;
    return remaining > 0 ? remaining : 0;
}

double wnp_get_position_percent(const wnp_player_t* player) {
    if (!player || player->duration <= 0) {
        return 0.0;
    }
    return ((double)player->position / (double)player->duration) * 100.0;
}

void wnp_format_seconds(int seconds, bool include_hours, char* out) {
    if (!out) return;
    
    int hours = seconds / 3600;
    int minutes = (seconds % 3600) / 60;
    int secs = seconds % 60;
    
    if (include_hours || hours > 0) {
        snprintf(out, WNP_STR_LEN, "%d:%02d:%02d", hours, minutes, secs);
    } else {
        snprintf(out, WNP_STR_LEN, "%d:%02d", minutes, secs);
    }
}

void wnp_utf8_to_utf16(const char* utf8, int utf8_len, wchar_t* utf16_out, int utf16_max_len) {
    if (!utf8 || !utf16_out || utf16_max_len <= 0) {
        return;
    }
    
    MultiByteToWideChar(CP_UTF8, 0, utf8, utf8_len, utf16_out, utf16_max_len - 1);
    utf16_out[utf16_max_len - 1] = L'\0';
}

// Функции управления плеером (заглушки)
void wnp_try_set_state(wnp_player_t* player, enum wnp_state state) {
    if (player && player->id >= 0) {
        player->state = state;
        printf("[WebNowPlaying] Set state to %d for player %d\n", state, player->id);
    }
}

void wnp_try_play_pause(wnp_player_t* player) {
    if (player && player->id >= 0) {
        if (player->state == WNP_STATE_PLAYING) {
            player->state = WNP_STATE_PAUSED;
        } else {
            player->state = WNP_STATE_PLAYING;
        }
        printf("[WebNowPlaying] Toggle play/pause for player %d\n", player->id);
    }
}

void wnp_try_skip_previous(wnp_player_t* player) {
    if (player && player->id >= 0) {
        printf("[WebNowPlaying] Skip previous for player %d\n", player->id);
    }
}

void wnp_try_skip_next(wnp_player_t* player) {
    if (player && player->id >= 0) {
        printf("[WebNowPlaying] Skip next for player %d\n", player->id);
    }
}

void wnp_try_set_position_percent(wnp_player_t* player, int percent) {
    if (player && player->id >= 0 && player->duration > 0) {
        player->position = (int)((percent / 100.0) * player->duration);
        printf("[WebNowPlaying] Set position to %d%% for player %d\n", percent, player->id);
    }
}

void wnp_try_set_volume(wnp_player_t* player, int volume) {
    if (player && player->id >= 0) {
        if (volume < 0) volume = 0;
        if (volume > 100) volume = 100;
        player->volume = volume;
        printf("[WebNowPlaying] Set volume to %d for player %d\n", volume, player->id);
    }
}

void wnp_try_set_rating(wnp_player_t* player, int rating) {
    if (player && player->id >= 0) {
        player->rating = rating;
        printf("[WebNowPlaying] Set rating to %d for player %d\n", rating, player->id);
    }
}

void wnp_try_set_repeat(wnp_player_t* player, enum wnp_repeat repeat) {
    if (player && player->id >= 0) {
        player->repeat = repeat;
        printf("[WebNowPlaying] Set repeat to %d for player %d\n", repeat, player->id);
    }
}

void wnp_try_toggle_repeat(wnp_player_t* player) {
    if (player && player->id >= 0) {
        switch (player->repeat) {
            case WNP_REPEAT_NONE:
                player->repeat = WNP_REPEAT_ALL;
                break;
            case WNP_REPEAT_ALL:
                player->repeat = WNP_REPEAT_ONE;
                break;
            case WNP_REPEAT_ONE:
                player->repeat = WNP_REPEAT_NONE;
                break;
        }
        printf("[WebNowPlaying] Toggle repeat for player %d\n", player->id);
    }
}

void wnp_try_set_shuffle(wnp_player_t* player, bool shuffle) {
    if (player && player->id >= 0) {
        player->shuffle = shuffle;
        printf("[WebNowPlaying] Set shuffle to %s for player %d\n", shuffle ? "true" : "false", player->id);
    }
}

// ============================================================================
// Внешние функции из measure.c (для тестирования)
// ============================================================================
// 
// ВАЖНО: Для компиляции этой тестовой программы нужно:
// 1. Либо скомпилировать measure.c как обычный объектный файл (не DLL)
// 2. Либо убрать __declspec(dllexport) из measure.c при компиляции для тестов
// 3. Либо определить макрос для условной компиляции (например, TEST_MODE)
//
// Пример компиляции:
//   cl main.c measure.c wnp.c /Fe:test.exe
//   или
//   gcc main.c measure.c wnp.c -o test.exe
//
// Эти функции должны быть определены в measure.c:
// ============================================================================

// Объявляем функции из measure.c (они определены в measure.c)
// Если measure.c компилируется как DLL, эти функции будут экспортированы
// Для тестирования нужно либо убрать __declspec(dllexport), либо линковать с DLL
extern void Initialize(void** data, void* rm);
extern void Reload(void* data, void* rm, double* max_value);
extern double Update(void* data);
extern const wchar_t* GetString(void* data);
extern void ExecuteBang(void* data, const wchar_t* args);
extern void Finalize(void* data);
extern LPCWSTR GetPlayerIds(void* data, int argc, LPCWSTR argv[]);
extern LPCWSTR GetPreviousPlayerId(void* data, int argc, LPCWSTR argv[]);
extern LPCWSTR GetNextPlayerId(void* data, int argc, LPCWSTR argv[]);

// ============================================================================
// Функция для создания тестового плеера
// ============================================================================

static int create_test_player(const char* name, const char* title, const char* artist, 
                               const char* album, enum wnp_state state) {
    if (g_test_player_count >= WNP_MAX_PLAYERS) {
        return -1;
    }
    
    wnp_player_t* player = &g_test_players[g_test_player_count];
    player->id = g_test_player_count;
    strncpy_s(player->name, WNP_STR_LEN, name, _TRUNCATE);
    strncpy_s(player->title, WNP_STR_LEN, title, _TRUNCATE);
    strncpy_s(player->artist, WNP_STR_LEN, artist, _TRUNCATE);
    strncpy_s(player->album, WNP_STR_LEN, album, _TRUNCATE);
    strncpy_s(player->cover, WNP_STR_LEN, "file:///C:/covers/cover1.jpg", _TRUNCATE);
    strncpy_s(player->cover_src, WNP_STR_LEN, "https://example.com/cover1.jpg", _TRUNCATE);
    player->state = state;
    player->position = 45;
    player->duration = 240;
    player->volume = 75;
    player->rating = 0;
    player->repeat = WNP_REPEAT_NONE;
    player->shuffle = false;
    player->rating_system = 2;
    player->available_repeat = 7; // Все режимы доступны
    player->can_set_state = true;
    player->can_skip_previous = true;
    player->can_skip_next = true;
    player->can_set_position = true;
    player->can_set_volume = true;
    player->can_set_rating = true;
    player->can_set_repeat = true;
    player->can_set_shuffle = true;
    player->platform = WNP_PLATFORM_WINDOWS;
    player->is_web_browser = false;
    player->created_at = 1000000;
    player->updated_at = 2000000;
    player->active_at = 3000000;
    
    int id = g_test_player_count;
    g_test_player_count++;
    
    if (g_active_player_id == -1) {
        g_active_player_id = id;
    }
    
    return id;
}

// ============================================================================
// Тестовая функция - симуляция обновления плеера
// ============================================================================

static void simulate_player_update(int player_id) {
    if (player_id < 0 || player_id >= g_test_player_count) {
        return;
    }
    
    wnp_player_t* player = &g_test_players[player_id];
    
    // Симулируем небольшое изменение позиции
    if (player->state == WNP_STATE_PLAYING) {
        player->position += 5;
        if (player->position > player->duration) {
            player->position = player->duration;
        }
    }
    
    // Вызываем callback если он установлен
    if (g_wnp_args.on_player_updated) {
        g_wnp_args.on_player_updated(player, NULL);
    }
}

// ============================================================================
// Вспомогательные функции для тестирования
// ============================================================================

// Функция для тестирования разных PlayerType
static void test_player_type(void* measure_data, const wchar_t* player_type_name, const wchar_t* expected_description) {
    g_test_player_type = player_type_name;
    double max_value = 0;
    Reload(measure_data, g_test_rm, &max_value);
    
    double value = Update(measure_data);
    const wchar_t* string_value = GetString(measure_data);
    
    printf("   %-20ls: ", player_type_name);
    if (string_value != NULL && wcslen(string_value) > 0) {
        wprintf(L"\"%ls\"", string_value);
    } else {
        printf("%.2f", value);
        if (max_value > 0) {
            printf(" (max: %.0f)", max_value);
        }
    }
    if (expected_description) {
        printf(" - %s", expected_description);
    }
    printf("\n");
}

// Функция для тестирования всех команд
static void test_all_bangs(void* measure_data) {
    const wchar_t* bangs[] = {
        L"playpause",
        L"play",
        L"pause",
        L"next",
        L"previous",
        L"setvolume 80",
        L"setvolume +10",
        L"setvolume -5",
        L"setposition 30",
        L"setposition +10",
        L"setposition -5",
        L"setstate playing",
        L"setstate paused",
        L"setstate stopped",
        L"setrepeat none",
        L"setrepeat all",
        L"setrepeat one",
        L"repeat",
        L"setshuffle true",
        L"setshuffle false",
        L"shuffle",
        L"setrating 5",
        L"togglethumbsup",
        L"togglethumbsdown",
    };
    
    int bang_count = sizeof(bangs) / sizeof(bangs[0]);
    for (int i = 0; i < bang_count; i++) {
        printf("   Testing: %ls\n", bangs[i]);
        ExecuteBang(measure_data, bangs[i]);
        // Небольшая задержка для визуализации
        Sleep(50);
    }
}

// Функция для вывода информации о плеере
static void print_player_info(const wnp_player_t* player) {
    if (!player || player->id == -1) {
        printf("   No active player\n");
        return;
    }
    
    printf("   Player ID: %d\n", player->id);
    printf("   Name: %s\n", player->name);
    printf("   Title: %s\n", player->title);
    printf("   Artist: %s\n", player->artist);
    printf("   Album: %s\n", player->album);
    printf("   State: %d (0=stopped, 1=playing, 2=paused)\n", player->state);
    printf("   Position: %d/%d seconds (%.1f%%)\n", 
           player->position, player->duration, 
           wnp_get_position_percent(player));
    printf("   Remaining: %d seconds\n", wnp_get_remaining_seconds(player));
    printf("   Volume: %d\n", player->volume);
    printf("   Rating: %d\n", player->rating);
    printf("   Repeat: %d (0=none, 1=one, 2=all)\n", player->repeat);
    printf("   Shuffle: %s\n", player->shuffle ? "true" : "false");
    printf("   Platform: %d\n", player->platform);
    printf("   Is Web Browser: %s\n", player->is_web_browser ? "true" : "false");
}

// ============================================================================
// Main функция - полноценное тестирование плагина
// ============================================================================

int main(void) {
    printf("========================================\n");
    printf("  WebNowPlaying Rainmeter Plugin Test\n");
    printf("========================================\n\n");
    
    // ========================================================================
    // 1. Инициализация тестовых данных
    // ========================================================================
    printf("[1] Creating test players...\n");
    create_test_player("Spotify", "Bohemian Rhapsody", "Queen", "A Night at the Opera", WNP_STATE_PLAYING);
    create_test_player("YouTube Music", "Stairway to Heaven", "Led Zeppelin", "Led Zeppelin IV", WNP_STATE_PAUSED);
    create_test_player("VLC Media Player", "Hotel California", "Eagles", "Hotel California", WNP_STATE_STOPPED);
    printf("   Created %d test players\n", g_test_player_count);
    
    wnp_player_t active_player = WNP_DEFAULT_PLAYER;
    if (wnp_get_active_player(&active_player)) {
        printf("   Active player: %s\n", active_player.name);
    }
    printf("\n");
    
    // ========================================================================
    // 2. Инициализация плагина
    // ========================================================================
    printf("[2] Initializing plugin...\n");
    void* measure_data = NULL;
    Initialize(&measure_data, g_test_rm);
    printf("   Plugin initialized successfully\n\n");
    
    // ========================================================================
    // 3. Тестирование всех PlayerType (числовые значения)
    // ========================================================================
    printf("[3] Testing all PlayerType values (numeric)...\n");
    test_player_type(measure_data, L"status", "1 = player exists, 0 = no player");
    test_player_type(measure_data, L"playercount", "Number of active players");
    test_player_type(measure_data, L"state", "0=stopped, 1=playing, 2=paused");
    test_player_type(measure_data, L"position", "Position in seconds");
    test_player_type(measure_data, L"duration", "Duration in seconds");
    test_player_type(measure_data, L"remaining", "Remaining seconds");
    test_player_type(measure_data, L"positionpercent", "Position as percentage (0-100)");
    test_player_type(measure_data, L"volume", "Volume (0-100)");
    test_player_type(measure_data, L"rating", "Rating (0-5 or 0-1)");
    test_player_type(measure_data, L"repeat", "Repeat mode (0=none, 1=one, 2=all)");
    test_player_type(measure_data, L"shuffle", "Shuffle (0 or 1)");
    test_player_type(measure_data, L"ratingsystem", "Rating system");
    test_player_type(measure_data, L"cansetstate", "Can set state (0 or 1)");
    test_player_type(measure_data, L"canskipprevious", "Can skip previous (0 or 1)");
    test_player_type(measure_data, L"canskipnext", "Can skip next (0 or 1)");
    test_player_type(measure_data, L"cansetposition", "Can set position (0 or 1)");
    test_player_type(measure_data, L"cansetvolume", "Can set volume (0 or 1)");
    test_player_type(measure_data, L"cansetrating", "Can set rating (0 or 1)");
    test_player_type(measure_data, L"cansetrepeat", "Can set repeat (0 or 1)");
    test_player_type(measure_data, L"cansetshuffle", "Can set shuffle (0 or 1)");
    printf("\n");
    
    // ========================================================================
    // 4. Тестирование всех PlayerType (строковые значения)
    // ========================================================================
    printf("[4] Testing all PlayerType values (string)...\n");
    test_player_type(measure_data, L"name", "Player name");
    test_player_type(measure_data, L"title", "Track title");
    test_player_type(measure_data, L"artist", "Artist name");
    test_player_type(measure_data, L"album", "Album name");
    test_player_type(measure_data, L"cover", "Cover image path");
    test_player_type(measure_data, L"coversrc", "Cover image source URL");
    test_player_type(measure_data, L"position", "Formatted position (MM:SS or HH:MM:SS)");
    test_player_type(measure_data, L"duration", "Formatted duration (MM:SS or HH:MM:SS)");
    test_player_type(measure_data, L"remaining", "Formatted remaining time (MM:SS or HH:MM:SS)");
    printf("\n");
    
    // ========================================================================
    // 5. Тестирование управления плеером (ExecuteBang)
    // ========================================================================
    printf("[5] Testing player control commands (ExecuteBang)...\n");
    printf("   Current player state before commands:\n");
    test_player_type(measure_data, L"state", NULL);
    test_player_type(measure_data, L"volume", NULL);
    test_player_type(measure_data, L"positionpercent", NULL);
    printf("\n");
    
    printf("   Executing control commands...\n");
    test_all_bangs(measure_data);
    printf("\n");
    
    printf("   Player state after commands:\n");
    test_player_type(measure_data, L"state", NULL);
    test_player_type(measure_data, L"volume", NULL);
    test_player_type(measure_data, L"positionpercent", NULL);
    printf("\n");
    
    // ========================================================================
    // 6. Тестирование функций получения списка плееров
    // ========================================================================
    printf("[6] Testing player list functions...\n");
    LPCWSTR player_ids = GetPlayerIds(measure_data, 0, NULL);
    if (player_ids && wcslen(player_ids) > 0) {
        wprintf(L"   Player IDs: %ls\n", player_ids);
    }
    
    // Тестирование переключения между плеерами
    if (g_test_player_count > 1) {
        wchar_t current_id_str[12];
        _snwprintf_s(current_id_str, 12, _TRUNCATE, L"%d", g_active_player_id);
        LPCWSTR argv[] = { current_id_str };
        
        LPCWSTR next_id = GetNextPlayerId(measure_data, 1, argv);
        wprintf(L"   Next player ID from %d: %ls\n", g_active_player_id, next_id);
        
        LPCWSTR prev_id = GetPreviousPlayerId(measure_data, 1, argv);
        wprintf(L"   Previous player ID from %d: %ls\n", g_active_player_id, prev_id);
    }
    printf("\n");
    
    // ========================================================================
    // 7. Тестирование обновлений плеера
    // ========================================================================
    printf("[7] Testing player updates...\n");
    printf("   Initial position: ");
    test_player_type(measure_data, L"position", NULL);
    
    // Симулируем несколько обновлений
    for (int i = 0; i < 3; i++) {
        simulate_player_update(g_active_player_id);
        Sleep(100);
        printf("   After update %d: ", i + 1);
        test_player_type(measure_data, L"position", NULL);
    }
    printf("\n");
    
    // ========================================================================
    // 8. Тестирование детальной информации о плеере
    // ========================================================================
    printf("[8] Detailed player information...\n");
    wnp_player_t player_info = WNP_DEFAULT_PLAYER;
    if (wnp_get_active_player(&player_info)) {
        print_player_info(&player_info);
    }
    printf("\n");
    
    // ========================================================================
    // 9. Тестирование всех плееров
    // ========================================================================
    printf("[9] Testing all players...\n");
    wnp_player_t all_players[WNP_MAX_PLAYERS] = {0};
    int player_count = wnp_get_all_players(all_players);
    printf("   Total players: %d\n", player_count);
    for (int i = 0; i < player_count; i++) {
        printf("   Player %d: %s - %s by %s\n", 
               all_players[i].id, 
               all_players[i].name,
               all_players[i].title,
               all_players[i].artist);
    }
    printf("\n");
    
    // ========================================================================
    // 10. Финациализация
    // ========================================================================
    printf("[10] Finalizing plugin...\n");
    Finalize(measure_data);
    printf("   Plugin finalized successfully\n\n");
    
    printf("========================================\n");
    printf("  Test completed successfully!\n");
    printf("========================================\n");
    
    return 0;
}

