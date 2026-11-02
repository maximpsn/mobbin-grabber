---
name: mobbin-export
description: Download screenshots from Mobbin (mobbin.com) into a folder on disk. Use when the user gives link(s) of the form mobbin.com/apps/<slug>/<version>/screens and asks to «download/save/grab the screens», «do batches per app», «Mobbin export / mobbin-grabber», «export as usual per our pipeline», or mentions the «Mobbin export» folder. This skill covers: the persisted Mobbin session in an Edge profile, defeating the page's virtualized grid, downloading WebP from the CDN, and sorting into Web/<Product> and Mobile/<Product> folders. Works for iOS and Web apps. Do NOT use for screenshots from other sites, for Screenlane/Page Flows-like services, or for local files — those have their own machinery.
---

# mobbin-grabber

Downloads ALL screenshots of a Mobbin `/screens` app page as WebP into a folder on disk. One folder per app.

## Pipeline

1. User sends links `https://mobbin.com/apps/<slug>/<app-version>/screens` (not `/collections/...`).
2. Ask where to save (directory). After the first download, **remember it for the whole session** and stop asking — put everything there. Default `/G:/Main/Mobbin export`.
3. For each link: determine type and name → collect screen URLs → download into `/Web/<Product>` or `/Mobile/<Product>` → verify file count.
4. Duplicate links (same version already downloaded) — do not re-download; tell the user and ask.

## Naming

- **Type**: from the slug. Contains `-ios-` / `-android-` → `Mobile`. Otherwise → `Web`. Create the type container if needed.
- **Service name** `<Product>`: take it from the page title, matched against the pattern `<Product> Web|iOS | Mobbin`. Strip the platform suffix and any prefix/junk from the slug:
  - `phantom-ios-...` → `Phantom`, `quo-web-...` → `Quo`, `base-44-web-...` → `Base44`, `we-transfer-web-...` → `We Transfer`, `tik-tok-ios-...` → `TikTok`.
- Final path: `G:\Main\Mobbin export\Mobile\Venmo`, `G:\Main\Mobbin export\Web\Quo`.
- Files: `<product>-screen-<N>.webp`, `N` starting at 1 in page order.

## Setup: browser with a session

Mobbin returns a landing page (not app pages) without login. The working session lives in a persistent Edge profile:

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --user-data-dir="$env:LOCALAPPDATA\Temp\gigatool\mobbinprof" --remote-debugging-port=9333 --no-first-run --window-size=1440,1200 about:blank
```

Check CDP: `Invoke-RestMethod http://127.0.0.1:9333/json/version`. If the profile/session is missing — see «Authorization».

## Method 1 (primary): tall viewport

Mobbin renders the grid **based on viewport height** (virtualized grid): with a normal window it mounts ~15 cells and loads the rest in jumps, so scrolling misses most of them. Fix — stretch the viewport up front via emulation so cells mount at once.

`scripts/collect_screens.py <page_url> <out_json> [height=16000]`:
- sets `Emulation.setDeviceMetricsOverride` to `height` (default 16000) before navigating → the grid mounts ~half to all cells;
- waits ~12 s, reads the title and the `Showing N screens` counter;
- keeps scrolling from 0 to `scrollHeight` in steps of 900 and collects `href|src` pairs from `li[data-sentry-component="ScreenCell"] a[href^="/screens/"]` (`src` from `img.src`, fallback `img.srcset.split(' ')[0]`);
- writes JSON `[{href, src}]` with checkpoints. The result must equal the counter.

```bash
python <skill-dir>/scripts/collect_screens.py "https://mobbin.com/apps/.../screens" C:\Temp\apps.json
```

## Method 2 (backup, if method 1 did not return all): plain scroll

If the tall viewport did not work or the counter did not match — collect with plain scroll, small windows, many passes:

- Do NOT set emulated height (or set the window via `--window-size`). Scroll in small steps `window.scrollTo(0, y)`, step ~600–900, **pause 1.5–3 s after each step** (React needs time to mount cells). At the end of the page — return to top, wait 5 s, repeat until saturated. Collect unique `href|src` on each step.
- Usually 1–4 passes are enough. If fewer than the counter — increase pauses, shrink the step, use more passes.

## Method 3 (fallback: get the result no matter what)

If both methods return an incomplete set:
1. Open each screen individually: for already collected `href="/screens/<id>"` navigate to `https://mobbin.com/screens/<id>` through the same CDP, read the `<img>` `src` from the screen's DOM and download it. Slow (~2 s per screen), but reliable.
2. If CDP/headless trips the Vercel checkpoint — open in a normal browser window with the same profile and grab `src` via DevTools, or ask the user to save the pages.
3. Goal — the same result: all `<product>-screen-<N>.webp` in the service folder. Give up only if it is impossible and clearly explain what blocks it.

## Download

`scripts/download_screens.py <items.json> <dest_dir> <prefix>` — downloads by `src` into `<prefix>-screen-<N>.webp`, numbers from the first free index, batches of 50, failures written to `<items.json>.failures.json`.

```bash
python <skill-dir>/scripts/download_screens.py C:\Temp\apps.json "G:\Main\Mobbin export\Mobile\Venmo" venmo
```

- `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36`, timeout 90 s, 3 attempts.
- Verification: file count == counter, each file starts with the WebP signature `RIFF` (`52 49 46 46`).

## Authorization (if the session expired)

1. Without login the app page is a landing page; the `<Product> Web|iOS | Mobbin` title is absent.
2. Ask the user for a fresh magic link `mobbin.com/api/auth/authenticate?token=...&type=magiclink...`.
3. Open it in a **non-headless** Edge with the same `mobbinprof` profile (the Vercel Security Checkpoint blocks headless), wait until the user/check passes, close the browser. After that headless works.
4. Never ask for a password — Mobbin only signs in via magic links.

## Pitfalls (verified)

- **The «PRO / Upgrade for full access» badge is cosmetic** — it shows on free apps too. Don't panic over it; rely on the `Showing N screens` counter and that the cells render.
- **«Collected 13 of 348»** almost always means the tall viewport emulation did not apply → use method 2/3, not «session expired».
- `Input.dispatchMouseEvent` (wheel) does NOT scroll in headless — use `window.scrollTo` only.
- `Emulation.setDeviceMetricsOverride` before navigation needs a height; otherwise the window breaks scrolling — set it before the page loads.
- Supabase URLs (`ujasntkfphywizsdaapi.supabase.co/...`) in the DOM are quiz widgets, NOT screens. Only take from `ScreenCell`.
- Bare bytescale `app_screens/<uuid>` without `enc` → 404; do not construct manually, take `src` from the cell.

## Supporting files

`scripts/collect_screens.py`, `scripts/download_screens.py` — see above. Requires Python with `websocket-client` (already installed), no package installs.