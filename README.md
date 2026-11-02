# mobbin-grabber

Выгружает все скриншоты страницы `/screens` приложения с [Mobbin](https://mobbin.com) в папку на диске, по одной папке на приложение, в формате WebP.

Mobbin требует авторизацию и рендерит сетку через virtualized grid — навык умеет это обходить (сессия в профиле Edge + CDP, высокий viewport для монтирования ячеек, fallback на обычный скролл и посещение каждого экрана по отдельности).

## Структура

- `SKILL.md` — инструкция для LLM-агента: пайплайн, нейминг, способы сбора (основной → бэкап → fallback), скачивание, грабли.
- `scripts/collect_screens.py` — собирает URL экранов страницы через CDP (высокий viewport).
- `scripts/download_screens.py` — качает файлы по собранным URL в папку с нумерацией и проверкой.

## Naming

- Папки: `G:\Main\Mobbin export\Web\<Product>` или `...\Mobile\<Product>`.
- Файлы: `<product>-screen-<N>.webp`.

## Требования

- Windows, Edge установлен.
- Python с `websocket-client`.
- Сессия Mobbin в профиле Edge `%LOCALAPPDATA%\Temp\gigatool\mobbinprof` (как получить — в SKILL.md).

См. `SKILL.md` для полного пайплайна.