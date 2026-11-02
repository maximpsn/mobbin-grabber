"""Collect all screen URLs from a Mobbin app /screens page via CDP scroll.

Usage:
  python collect_screens.py <page_url> <out_json> [cdp_port]

Requires: websocket-client (installed). A headless Edge with --remote-debugging-port
must already be running with the mobbinprof session profile.
"""
import json, sys, time, urllib.request, websocket

page_url = sys.argv[1]
out_json = sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 9333
HEIGHT = int(sys.argv[4]) if len(sys.argv) > 4 else 16000


def get_json(url):
    return json.load(urllib.request.urlopen(url, timeout=10))


tabs = get_json(f"http://127.0.0.1:{PORT}/json")
tab = next(t for t in tabs if t.get("type") == "page")
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=300)
msg_id = [0]


def send(method, params=None):
    msg_id[0] += 1
    ws.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id[0]:
            return resp.get("result", {})


def eval_js(expr):
    res = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return res.get("result", {}).get("value")


items = {}


def collect():
    expr = """
    (() => {
      const out = [];
      document.querySelectorAll('li[data-sentry-component="ScreenCell"] a[href^="/screens/"]').forEach(a => {
        const img = a.querySelector('img');
        let src = '';
        if (img) src = img.src || (img.srcset ? img.srcset.split(' ')[0] : '');
        out.push(a.getAttribute('href') + '|' + src);
      });
      return out;
    })()
    """
    res = eval_js(expr) or []
    for item in res:
        href, src = item.split("|", 1)
        if href not in items:
            items[href] = src
        elif items[href] == "" and src != "":
            items[href] = src


# Tall viewport makes Mobbin's virtualized grid mount many ScreenCells at once.
# Without it, the grid renders only ~15 cells and scroll jumps miss most of them.
send("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": HEIGHT, "deviceScaleFactor": 1, "mobile": False})
send("Page.navigate", {"url": page_url})
time.sleep(12)
title = eval_js("document.title")
counter = eval_js("(document.body.innerText.match(/Showing\\s+(\\d+)\\s+screens/) || [])[1]")
print("title:", title, flush=True)
print("counted:", counter, flush=True)

def save():
    out = [{"href": k, "src": v} for k, v in items.items()]
    json.dump(out, open(out_json, "w", encoding="utf-8"), indent=1)
    print("CHECKPOINT", len(out), "with_src", sum(1 for v in items.values() if v), flush=True)


selected = None
if counter:
    try:
        selected = int(counter)
    except ValueError:
        selected = None

for cycle in range(4):
    print(f"--- cycle {cycle} ---", flush=True)
    max_h = int(eval_js("document.body.scrollHeight") or 40000)
    y = 0
    step = 900
    while y <= max_h + step:
        collect()
        eval_js(f"window.scrollTo(0, {y})")
        y += step
        time.sleep(1.5)
        max_h = max(max_h, int(eval_js("document.body.scrollHeight") or max_h))
    collect()
    print(f"after cycle: {len(items)} items, {sum(1 for v in items.values() if v)} with src", flush=True)
    save()  # checkpoint after every cycle so an interrupted run never loses data
    if selected and len(items) >= selected and sum(1 for v in items.values() if v) >= selected:
        print("target reached, stopping", flush=True)
        break
    eval_js("window.scrollTo(0, 0)")
    time.sleep(5)

save()
ws.close()