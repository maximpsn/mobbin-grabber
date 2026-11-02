"""Download screens from a collected mobbin items JSON into a destination folder.

Usage:
  python download_screens.py <items_json> <dest_dir> <file_prefix>

Files are written as <file_prefix>-screen-<N>.webp with N starting at the first
free number found in dest_dir (so reruns continue numbering). Prints progress
every 50 files; failures are logged to <items_json>.failures.json.
"""
import json, os, sys, time, urllib.request

items = json.load(open(sys.argv[1], encoding="utf-8"))
dest = sys.argv[2]
prefix = sys.argv[3]

existing = set()
for f in os.listdir(dest):
    if f.startswith(prefix + "-screen-") and f.endswith(".webp"):
        try:
            existing.add(int(f[len(prefix) + 8:-len(".webp")]))
        except ValueError:
            pass
next_num = max(existing) + 1 if existing else 1
print("starting from", next_num, "existing:", len(existing), flush=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"


def download(u, out, tries=3):
    for t in range(tries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            open(out, "wb").write(data)
            return len(data)
        except Exception as e:
            if t == tries - 1:
                return "FAIL:" + str(e)
            time.sleep(2)


ok = 0
fail = []
for i, item in enumerate(items, 1):
    n = next_num + i - 1
    out = os.path.join(dest, f"{prefix}-screen-{n}.webp")
    if os.path.exists(out) and os.path.getsize(out) > 500:
        ok += 1
        continue
    res = download(item["src"], out)
    if isinstance(res, int):
        ok += 1
    else:
        fail.append((n, item["href"], res))
    if i % 50 == 0:
        print(f"batch {i // 50}: {ok} ok, {len(fail)} fail", flush=True)

print("DONE ok:", ok, "fail:", len(fail))
if fail:
    print("recent fails:", fail[-3:], flush=True)
    json.dump(fail, open(sys.argv[1] + ".failures.json", "w", encoding="utf-8"), indent=1)