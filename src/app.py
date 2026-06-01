"""
WCP Widget: Radio
Internet radio player with three components:
  - radio-player  (widget)  — full pinboard card with station search + playback
  - radio-control (control) — masthead control: play/stop + station name
  - radio-ticker  (ticker)  — masthead ticker: scrolling now-playing strip
Port: 3741  |  Radio data: Radio Browser API (api.radio-browser.info)
"""

import json
import requests
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

# ── State store ──────────────────────────────────────────────────────────────
_state = {"playing": False, "station": "", "country": ""}

# ── WCP Manifest ─────────────────────────────────────────────────────────────

WCP_MANIFEST = {
    "wcp": "1.3.0",
    "name": "Radio",
    "version": "1.0.0",
    "description": "Internet radio player. Search thousands of stations, play directly in the dashboard or masthead.",
    "icon": "/widget/icon.svg",
    "health": "/widget/health",
    "pages": [
        {
            "id": "full",
            "path": "/widget/full",
            "title": "Radio — Full Player",
            "description": "Search and play internet radio stations.",
            "window": {"width": 480, "height": 600},
        }
    ],
    "actions": [
        {"id": "open-full", "type": "wcp:open-window", "label": "Open Full Player", "page": "full"},
        {"id": "open-tab",  "type": "wcp:open-tab",    "label": "Open in Tab",
         "page": "full", "tab": {"title": "Radio", "icon": "/widget/icon.svg"}, "persist": True},
    ],
    "components": [
        {
            "id": "radio-player", "name": "Radio Player", "role": "widget",
            "path": "/widget/", "icon": "/widget/icon.svg",
            "renderMode": "iframe", "defaultSize": {"w": 4, "h": 4},
        },
        {
            "id": "radio-control", "name": "Radio Control", "role": "control",
            "path": "/widget/control/radio", "icon": "/widget/icon.svg",
            "mastheadCapable": True, "size": {"min": 40, "max": 60},
        },
        {
            "id": "radio-led", "name": "Playing LED", "role": "control",
            "path": "/widget/led", "icon": "/widget/icon.svg",
            "mastheadCapable": True, "size": {"min": 40, "max": 60},
        },
        {
            "id": "radio-ticker", "name": "Radio Ticker", "role": "ticker",
            "path": "/widget/ticker", "icon": "/widget/icon.svg",
            "mastheadCapable": True, "size": {"min": 40, "max": 60},
        },
    ],
}

# ── WCP Endpoints ─────────────────────────────────────────────────────────────

@app.route("/widget/")
@app.route("/widget/index.html")
def widget(): return render_template("widget.html", manifest=WCP_MANIFEST)

@app.route("/widget/wcp")
def widget_wcp(): return jsonify(WCP_MANIFEST)

@app.route("/widget/health")
def widget_health(): return jsonify({"status": "ok", "name": WCP_MANIFEST["name"]})

@app.route("/widget/full")
def widget_full(): return render_template("full.html", manifest=WCP_MANIFEST)

@app.route("/widget/control/radio")
def widget_control(): return render_template("control.html", manifest=WCP_MANIFEST)

@app.route("/widget/ticker")
def widget_ticker(): return render_template("ticker.html", manifest=WCP_MANIFEST)

@app.route("/widget/led")
def widget_led(): return render_template("led.html", manifest=WCP_MANIFEST)

@app.route("/widget/api/state", methods=["GET", "POST"])
def widget_state():
    global _state
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        _state.update({k: data[k] for k in data if k in _state})
        return jsonify({"ok": True})
    return jsonify(_state)

@app.route("/widget/icon.svg")
def widget_icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="#f0883e" d="M3.05 3.05a7 7 0 0 0 0 9.9.5.5 0 0 1-.707.707 8 8 0 0 1 0-11.314.5.5 0 0 1 .707.707zm2.122 2.122a4 4 0 0 0 0 5.656.5.5 0 1 1-.708.708 5 5 0 0 1 0-7.072.5.5 0 0 1 .708.708zm5.656-5.656a.5.5 0 0 1 .707 0 8 8 0 0 1 0 11.314.5.5 0 0 1-.707-.707 7 7 0 0 0 0-9.9.5.5 0 0 1 0-.707zm-2.12 2.121a.5.5 0 0 1 .707 0 5 5 0 0 1 0 7.072.5.5 0 1 1-.707-.708 4 4 0 0 0 0-5.656.5.5 0 0 1 0-.708zM10 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/>
</svg>"""
    return Response(svg, mimetype="image/svg+xml")

# ── Radio Browser API proxy ───────────────────────────────────────────────────

RB_BASE = "https://de1.api.radio-browser.info/json"

@app.route("/widget/api/search")
def search_stations():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    try:
        r = requests.get(f"{RB_BASE}/stations/search", params={
            "name": q, "limit": 20, "hidebroken": "true",
            "order": "clickcount", "reverse": "true",
        }, timeout=8)
        stations = r.json()
        results = [{
            "stationuuid": s["stationuuid"],
            "name": s["name"],
            "country": s.get("country", ""),
            "tags": s.get("tags", "")[:40],
            "url_resolved": s.get("url_resolved", s.get("url", "")),
            "favicon": s.get("favicon", ""),
            "bitrate": s.get("bitrate", 0),
        } for s in stations if s.get("url_resolved") or s.get("url")]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

@app.route("/widget/api/top")
def top_stations():
    try:
        r = requests.get(f"{RB_BASE}/stations/topclick/12", params={
            "hidebroken": "true",
        }, timeout=8)
        stations = r.json()
        results = [{
            "stationuuid": s["stationuuid"],
            "name": s["name"],
            "country": s.get("country", ""),
            "tags": s.get("tags", "")[:40],
            "url_resolved": s.get("url_resolved", s.get("url", "")),
            "favicon": s.get("favicon", ""),
            "bitrate": s.get("bitrate", 0),
        } for s in stations if s.get("url_resolved") or s.get("url")]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3741, debug=False)
