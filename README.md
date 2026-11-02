# mobbin-grabber

Downloads all screenshots of a Mobbin app `/screens` page into a folder on disk, one folder per app, as WebP.

Mobbin requires authorization and renders the grid via a virtualized grid — the skill knows how to get around it (session in an Edge profile + CDP, tall viewport to mount cells, fallback to plain scroll and to visiting each screen individually).

## Layout

- `SKILL.md` — instructions for the LLM agent: pipeline, naming, collection methods (primary → backup → fallback), download, pitfalls.
- `scripts/collect_screens.py` — collects the page's screen URLs via CDP (tall viewport).
- `scripts/download_screens.py` — downloads files by the collected URLs into a folder, numbered and verified.

## Naming

- Folders: `G:\Main\Mobbin export\Web\<Product>` or `...\Mobile\<Product>`.
- Files: `<product>-screen-<N>.webp`.

## Requirements

- Windows, Edge installed.
- Python with `websocket-client`.
- A Mobbin session in the Edge profile `%LOCALAPPDATA%\Temp\gigatool\mobbinprof` (how to get it — in SKILL.md).

See `SKILL.md` for the full pipeline.