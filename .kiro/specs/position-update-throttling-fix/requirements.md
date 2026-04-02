# Requirements Document

## Introduction

Данный документ описывает требования к исправлению проблемы с обновлением позиции воспроизведения трека в виджете при перемотке. 

**Корневая причина проблемы:** В `EventSubscriptionManager.cs` обработчики событий `OnTimelinePropertiesChanged` (перемотка/позиция) и `OnPlaybackInfoChanged` (play/pause) получают события от Windows Media API, но **не вызывают** `OnMediaUpdated()` для передачи данных в MediaMonitor. Они только логируют события, но не отправляют обновления дальше по цепочке.

В результате:
- События перемотки получаются ✅
- Но не передаются в UpdateQueue ❌
- И не отправляются на Python сервер ❌
- И не доходят до виджета ❌

## Glossary

- **MediaMonitor**: C# компонент, который отслеживает медиа-события Windows и отправляет данные на Python сервер
- **Python Server**: Сервер на aiohttp (now.py), который получает данные от MediaMonitor и передает их через WebSocket клиентам
- **Widget**: HTML/JavaScript виджет в браузере, который отображает информацию о воспроизводимом треке
- **Position**: Текущая позиция воспроизведения трека в секундах
- **Throttling**: Механизм ограничения частоты отправки обновлений для снижения нагрузки
- **Seek Event**: Событие перемотки трека пользователем

## Requirements

### Requirement 1

**User Story:** Как пользователь, я хочу видеть актуальную позицию воспроизведения в виджете при перемотке трека, чтобы понимать текущее положение в треке.

#### Acceptance Criteria

1. WHEN событие TimelinePropertiesChanged происходит THEN EventSubscriptionManager SHALL вызвать OnMediaUpdated для передачи данных позиции
2. WHEN событие PlaybackInfoChanged происходит THEN EventSubscriptionManager SHALL вызвать OnMediaUpdated для передачи данных статуса воспроизведения
3. WHEN OnMediaUpdated вызывается THEN система SHALL передать обновление в UpdateQueue
4. WHEN UpdateQueue обрабатывает обновление THEN система SHALL отправить данные на Python сервер через HttpClientPool
5. WHEN Python сервер получает обновление позиции THEN он SHALL отправить данные всем подключенным WebSocket клиентам

### Requirement 2

**User Story:** Как разработчик, я хочу чтобы EventSubscriptionManager корректно обрабатывал все типы медиа-событий и передавал их дальше по цепочке.

#### Acceptance Criteria

1. WHEN OnTimelinePropertiesChanged получает событие THEN он SHALL извлечь текущую позицию и длительность трека
2. WHEN OnTimelinePropertiesChanged извлекает данные THEN он SHALL создать MediaUpdateEventArgs с актуальными данными
3. WHEN OnPlaybackInfoChanged получает событие THEN он SHALL извлечь статус воспроизведения (Playing/Paused)
4. WHEN OnPlaybackInfoChanged извлекает данные THEN он SHALL создать MediaUpdateEventArgs с актуальным статусом
5. WHEN MediaUpdateEventArgs создан THEN система SHALL вызвать OnMediaUpdated для передачи события подписчикам

### Requirement 3

**User Story:** Как пользователь, я хочу чтобы виджет корректно отображал позицию при любых сценариях использования медиа-плеера.

#### Acceptance Criteria

1. WHEN пользователь перематывает трек вперед THEN виджет SHALL отобразить новую позицию немедленно
2. WHEN пользователь перематывает трек назад THEN виджет SHALL отобразить новую позицию немедленно
3. WHEN пользователь быстро перематывает трек несколько раз подряд THEN виджет SHALL отображать каждое изменение позиции
4. WHEN трек воспроизводится без перемотки THEN виджет SHALL плавно обновлять позицию с учетом троттлинга
5. WHEN происходит смена трека THEN система SHALL сбросить состояние отслеживания позиции
