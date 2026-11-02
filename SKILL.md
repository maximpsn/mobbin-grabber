---
name: mobbin-export
description: Выгрузка скриншотов с Mobbin (mobbin.com) в папку на диске. Используй, когда пользователь даёт ссылку(и) вида mobbin.com/apps/<slug>/<version>/screens и просит «выгрузи/скачай/сохрани скриншоты», «сделай пачки по приложениям», «Mobbin export / mobbin-grabber», «выгрузи как обычно по пайплайну» или упоминает папку «Mobbin export». Навык покрывает: сессия Mobbin в профиле Edge, обход виртуализации страницы, скачивание WebP с CDN, раскладку по папкам Web/<Product> и Mobile/<Product>. iOS и Web приложения. НЕ используй для скриншотов с других сайтов, для сервисов а-ля Screenlane/Page Flows и для локальных файлов — там свои механизмы.
---

# mobbin-grabber

Скачивает ВСЕ скриншоты страницы `/screens` приложения Mobbin как WebP в папку на диске. Одна папка на приложение.

## Пайплайн

1. Юзер присылает ссылки `https://mobbin.com/apps/<slug>/<app-version>/screens` (не коллекции `/collections/...`).
2. Спроси, куда класть (директория). После первого скачивания **запомни её на всю сессию** и больше не спрашивай — клади всё туда же. По умолчанию `/G:/Main/Mobbin export`.
3. Для каждой ссылки: определить тип и имя → собрать URL экранов → скачать в `/Web/<Product>` или `/Mobile/<Product>` → проверить число файлов.
4. Ссылки-дубли (та же версия уже скачана) — не перекачивай, сообщи и спроси.

## Нейминг

- **Тип**: по slug. Есть `-ios-` / `-android-` → `Mobile`. Иначе → `Web`. Контейнер типа при необходимости создать.
- **Имя сервиса** `<Product>`: возьми из тайтла страницы, сопоставив с шаблоном `<Product> Web|iOS | Mobbin`. Сними суффикс платформы и префиксы/мусор из slug:
  - `phantom-ios-...` → `Phantom`, `quo-web-...` → `Quo`, `base-44-web-...` → `Base44`, `we-transfer-web-...` → `We Transfer`, `tik-tok-ios-...` → `TikTok`.
- Итог пути: `G:\Main\Mobbin export\Mobile\Venmo`, `G:\Main\Mobbin export\Web\Quo`.
- Файлы: `<product>-screen-<N>.webp`, `N` с 1 в порядке появления на странице.

## Подготовка: браузер с сессией

Mobbin без входа отдаёт лендинг вместо страниц приложений. Рабочая сессия — в постоянном профиле Edge:

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --user-data-dir="$env:LOCALAPPDATA\Temp\gigatool\mobbinprof" --remote-debugging-port=9333 --no-first-run --window-size=1440,1200 about:blank
```

Проверка CDP: `Invoke-RestMethod http://127.0.0.1:9333/json/version`. Если профиля/сессии нет — см. «Авторизация».

## Способ 1 (основной): высокий viewport

Mobbin рендерит сетку **по высоте окна** (virtualized grid): при стандартном окне монтирует ~15 ячеек и догружает рывками, из-за чего скролл теряет большую часть. Решение — растянуть viewport заранее через эмуляцию, тогда ячейки монтируются разом.

`scripts/collect_screens.py <page_url> <out_json> [height=16000]`:
- ставит `Emulation.setDeviceMetricsOverride` высотой `height` (по умолчанию 16000) до навигации → сетка монтирует ~половину-все ячейки;
- ждёт ~12 с, читает тайтл и счётчик `Showing N screens`;
- дососкролливает от 0 до `scrollHeight` шагом 900 и собирает пары `href|src` с ячеек `li[data-sentry-component="ScreenCell"] a[href^="/screens/"]` (`src` из `img.src`, fallback `img.srcset.split(' ')[0]`);
- пишет JSON `[{href, src}]` и checkpoint'и. Итог должен равняться счётчику.

```bash
python <skill-dir>/scripts/collect_screens.py "https://mobbin.com/apps/.../screens" C:\Temp\apps.json
```

## Способ 2 (бэкап, если способ 1 не дал все): обычный скролл

Если высокий viewport не сработал или счётчик не сошёлся — собрать обычным скроллом, малыми окнами, много проходов:

- НЕ ставить эмуляцию высоты (или поставить `--window-size` окна). Скролл маленькими шагами `window.scrollTo(0, y)`, шаг ~600–900, **пауза 1.5–3 с** после каждого шага (React успевает смонтировать клетки). После конца страницы — вернуться наверх, подождать 5 с, повторять до насыщения. Собирать уникальные `href|src` на каждом шаге.
- Обычно хватает 1–4 проходов. Если собрано < счётчика — увеличить паузы, уменьшить шаг, больше проходов.

## Способ 3 (fallback: добиться результата в любом случае)

Если оба способа не дали полный набор:
1. Открыть каждый экран по отдельности: для уже собранных `href="/screens/<id>"` перейти на `https://mobbin.com/screens/<id>` через тот же CDP, в DOM `<img>` экрана достать `src` и скачать. Медленно (по ~2 с на экран), но надёжно.
2. Если CDP/headless режет Vercel-чек — открыть в обычном окне браузера с тем же профилем и снять src вручную через DevTools, либо попросить юзера сохранить страницы.
3. Цель — тот же результат: все `<product>-screen-<N>.webp` в папке сервиса. Сдайся только если недостижимо и явно объясни, что именно блокирует.

## Скачивание

`scripts/download_screens.py <items.json> <dest_dir> <prefix>` — качает по `src` в `<prefix>-screen-<N>.webp`, нумерует от первого свободного, пачками по 50, сбои пишет в `<items.json>.failures.json`.

```bash
python <skill-dir>/scripts/download_screens.py C:\Temp\apps.json "G:\Main\Mobbin export\Mobile\Venmo" venmo
```

- `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36`, таймаут 90 с, 3 попытки.
- Проверка: число файлов == счётчику, каждый файл начинается с сигнатуры WebP `RIFF` (`52 49 46 46`).

## Авторизация (если сессия протухла)

1. Без входа страница приложения — лендинг, заголовка `<Product> Web|iOS | Mobbin` нет.
2. Попроси юзера прислать свежую magic-ссылку `mobbin.com/api/auth/authenticate?token=...&type=magiclink...`.
3. Открой её в **не-headless** Edge с тем же профилем `mobbinprof` (Vercel Security Checkpoint режет headless), подожди, пока юзер/чек пройдёт, закрой браузер. После этого headless работает.
4. Пароль не проси — у Mobbin вход только по magic-ссылкам.

## Грабли (проверено)

- **Бейдж «PRO / Upgrade for full access» — косметический**, висит и на бесплатных. НЕ паникуй из-за него; ориентир — счётчик `Showing N screens` и то, что ячейки рендерятся.
- **«Собралось 13 из 348»** почти всегда = не сработала эмуляция высоты → используй способ 2/3, а не «сессия протухла».
- `Input.dispatchMouseEvent` (колесо) в headless НЕ скроллит — только `window.scrollTo`.
- `Emulation.setDeviceMetricsOverride` до навигации нужен высотой, иначе окно ломает скролл — ставь его до загрузки страницы.
- Supabase-URL (`ujasntkfphywizsdaapi.supabase.co/...`) в DOM — quiz-виджеты, НЕ скрины. Бери только из `ScreenCell`.
- Прямые bytescale `app_screens/<uuid>` без `enc` → 404; не конструируй вручную, бери `src` из ячейки.

## Вспомогательные файлы

`scripts/collect_screens.py`, `scripts/download_screens.py` — см. выше. Нужен Python с `websocket-client` (уже установлен), без установки пакетов.