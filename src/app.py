"""
WCP Widget: Radio
Internet radio player with four components:
  - radio-player  (widget)  — full stave instrument with station search + playback
  - radio-control (control) — masthead control: play/stop + station name
  - radio-led     (control) — masthead LED: playing/stopped indicator
  - radio-ticker  (ticker)  — masthead ticker: scrolling now-playing strip
Port: 3741  |  Radio data: Radio Browser API (api.radio-browser.info)
Specification: https://widgetcontextprotocol.com
"""

import io, json, os, zipfile
import requests
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

PUBLISHED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'published', 'index.html')

# ── CORS ──────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Wcp-Instance-Id, Wcp-Dashboard-Id, Wcp-Version, Wcp-Widget-Id, '
        'Wcp-Orchestration-Id, Wcp-Application-Id'
    )
    return response

@app.route('/widget/<path:p>', methods=['OPTIONS'])
@app.route('/widget/', methods=['OPTIONS'])
@app.route('/wcp', methods=['OPTIONS'])
def cors_preflight(p=''):
    return Response('', status=204)

# ── Instance ID helper ────────────────────────────────────────────────────────

def get_instance_id():
    iid = request.headers.get("Wcp-Instance-Id", "").strip()
    if not iid:
        iid = (request.args.get("wcpInstanceId", "") or "").strip()
    return iid

def get_orchestration_id():
    oid = request.headers.get("Wcp-Orchestration-Id", "").strip()
    if not oid:
        oid = (request.args.get("wcpOrchestrationId", "") or "").strip()
    return oid

def get_application_id():
    aid = request.headers.get("Wcp-Application-Id", "").strip()
    if not aid:
        aid = (request.args.get("wcpApplicationId", "") or "").strip()
    return aid

# ── State store (WCP 1.5.0 — keyed by orchestration + application context) ───
_DEFAULT_STATE = {"playing": False, "station": "", "country": "", "station_url": "", "volume": 80}
_states = {}  # { state_key: {…} }

def get_state_key():
    """Derive compound state key from WCP 1.5.0 context headers.
    Pseudocode reference: widgetcontextprotocol.com — WCP Request Headers.
    """
    orch_id = get_orchestration_id()
    app_id  = get_application_id()
    if orch_id and app_id:
        return f"{orch_id}:{app_id}"
    if orch_id:
        return orch_id
    return "global"  # fallback for hosts that pre-date WCP 1.5.0

def _state_for(key):
    if key not in _states:
        _states[key] = dict(_DEFAULT_STATE)
    return key

# ── WCP Manifest ─────────────────────────────────────────────────────────────

WCP_MANIFEST = {
    "wcp": "2.1.0",
    "uuid": "f839cffc-573b-48fd-b7d6-1dc2b1aa8699",
    "name": "Radio",
    "version": "1.6.0",
    "description": "Internet radio player. Search thousands of stations, play directly in the dashboard or masthead.",
    "icon": "/widget/icon.svg",
    "health": "/widget/health",
    "container": {
        "image":            "docker.io/penrithbeacon/wcp-widget-radio",
        "source":           {"type": "registry"},
        "tag":              "1.6.0-wcp2.1.0",
        "port":             3741,
        "defaultLifecycle": "always",
    },
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
            "id": "radio-player", "uuid": "fb11989e-c443-4171-9387-068025ded7a4", "name": "Radio Player", "role": "widget",
            "path": "/widget/", "icon": "/widget/icon.svg",
            "renderMode": "iframe", "defaultSize": {"w": 4, "h": 8},
        },
        {
            "id": "radio-control", "uuid": "0be9d536-c947-4042-af49-c5d9a2ad2c0f", "name": "Radio Control", "role": "control",
            "path": "/widget/control/radio", "icon": "/widget/icon.svg",
            "mastheadCapable": True,
            "masthead": {"height": {"min": 40, "max": 60}, "width": {"min": 160, "max": 240}},
        },
        {
            "id": "radio-led", "uuid": "67c3fb15-eb48-4f60-a7fc-32b9e0a20032", "name": "Playing LED", "role": "control",
            "path": "/widget/led", "icon": "/widget/icon.svg",
            "mastheadCapable": True,
            "masthead": {"height": {"min": 40, "max": 60}, "width": {"min": 40, "max": 60}},
        },
        {
            "id": "radio-ticker", "uuid": "5d781e16-5d9c-4b1d-bf0e-85cbd92b08fd", "name": "Radio Ticker", "role": "ticker",
            "path": "/widget/ticker", "icon": "/widget/icon.svg",
            "mastheadCapable": True,
            "masthead": {"height": {"min": 40, "max": 60}},
        },
        {
            "id": "radio-volume", "uuid": "a2c71f8e-9b34-4e60-b1a7-6d0e3f5c8a92", "name": "Volume", "role": "control",
            "path": "/widget/control/volume", "icon": "/widget/icon.svg",
            "renderMode": "iframe", "defaultSize": {"w": 1, "h": 2},
            "mastheadCapable": True,
            "masthead": {"height": {"min": 40, "max": 60}, "width": {"min": 48, "max": 48}},
        },
    ],
}

# ── JSON-LD structured data (injected into every widget template <head>) ──────

WIDGET_JSONLD = json.dumps({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": WCP_MANIFEST["name"],
    "softwareVersion": WCP_MANIFEST["version"],
    "description": WCP_MANIFEST["description"],
    "identifier": WCP_MANIFEST["uuid"],
    "applicationCategory": "WCP Widget",
    "operatingSystem": "Web",
    "isBasedOn": {
        "@type": "WebSite",
        "name": "Widget Context Protocol",
        "url": "https://widgetcontextprotocol.com",
    },
    "additionalProperty": [
        {"@type": "PropertyValue", "name": "wcpVersion", "value": WCP_MANIFEST["wcp"]},
        {"@type": "PropertyValue", "name": "containerImage", "value": WCP_MANIFEST["container"]["image"]},
        {"@type": "PropertyValue", "name": "containerTag", "value": WCP_MANIFEST["container"]["tag"]},
        {"@type": "PropertyValue", "name": "containerPort", "value": str(WCP_MANIFEST["container"]["port"])},
    ],
}, indent=2)

# ── WCP Endpoints ─────────────────────────────────────────────────────────────

@app.route("/wcp")
def container_directory():
    return jsonify({
        "type":    "directory",
        "wcp":     "2.1.0",
        "widgets": [{
            "id":          "radio",
            "uuid":        WCP_MANIFEST["uuid"],
            "name":        WCP_MANIFEST["name"],
            "description": WCP_MANIFEST["description"],
            "icon":        WCP_MANIFEST["icon"],
            "manifest":    "/widget/wcp",
        }]
    })

@app.route("/widget/")
@app.route("/widget/index.html")
def widget():
    return render_template("widget.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/wcp")
def widget_wcp():
    manifest = dict(WCP_MANIFEST)
    manifest['web'] = {'published': os.path.exists(PUBLISHED_PATH)}
    return jsonify(manifest)

@app.route("/widget/index")
def widget_index():
    return render_template("index-page.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route('/')
def published_spa():
    if os.path.exists(PUBLISHED_PATH):
        with open(PUBLISHED_PATH, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/html')
    return Response('Not Found', status=404, mimetype='text/plain')

@app.route('/widget/publish', methods=['POST'])
def publish():
    html = request.get_data(as_text=True)
    if not html:
        return jsonify({'success': False, 'error': 'Empty body'}), 400
    try:
        os.makedirs(os.path.dirname(PUBLISHED_PATH), exist_ok=True)
        with open(PUBLISHED_PATH, 'w', encoding='utf-8') as f:
            f.write(html)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/widget/publish', methods=['DELETE'])
def unpublish():
    try:
        if os.path.exists(PUBLISHED_PATH):
            os.remove(PUBLISHED_PATH)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/widget/health")
def widget_health():
    return jsonify({"status": "ok", "name": WCP_MANIFEST["name"],
                    "container": os.environ.get("CONTAINER_NAME", "unknown")})

@app.route("/widget/full")
def widget_full():
    return render_template("full.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/control/radio")
def widget_control():
    return render_template("control.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/ticker")
def widget_ticker():
    return render_template("ticker.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/led")
def widget_led():
    return render_template("led.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/control/volume")
def widget_volume():
    return render_template("volume.html", manifest=WCP_MANIFEST, jsonld=WIDGET_JSONLD,
        wcp_instance_id=get_instance_id(),
        wcp_orchestration_id=get_orchestration_id(), wcp_application_id=get_application_id())

@app.route("/widget/api/state", methods=["GET", "POST"])
def widget_state():
    key = _state_for(get_state_key())
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        _states[key].update({k: data[k] for k in data if k in _DEFAULT_STATE})
        return jsonify({"ok": True})
    return jsonify(_states[key])

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="#f0883e" d="M3.05 3.05a7 7 0 0 0 0 9.9.5.5 0 0 1-.707.707 8 8 0 0 1 0-11.314.5.5 0 0 1 .707.707zm2.122 2.122a4 4 0 0 0 0 5.656.5.5 0 1 1-.708.708 5 5 0 0 1 0-7.072.5.5 0 0 1 .708.708zm5.656-5.656a.5.5 0 0 1 .707 0 8 8 0 0 1 0 11.314.5.5 0 0 1-.707-.707 7 7 0 0 0 0-9.9.5.5 0 0 1 0-.707zm-2.12 2.121a.5.5 0 0 1 .707 0 5 5 0 0 1 0 7.072.5.5 0 1 1-.707-.708 4 4 0 0 0 0-5.656.5.5 0 0 1 0-.708zM10 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/>
</svg>"""

@app.route("/widget/icon.svg")
def widget_icon():
    return Response(ICON_SVG, mimetype="image/svg+xml")

@app.route("/widget/api/guids")
def api_guids():
    return jsonify({
        "uuid": WCP_MANIFEST["uuid"],
        "components": [
            {"id": c["id"], "uuid": c["uuid"], "name": c["name"]}
            for c in WCP_MANIFEST.get("components", [])
        ]
    })

@app.route("/widget/export.wcp")
def export_wcp():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(WCP_MANIFEST, indent=2))
        z.writestr("icon.svg", ICON_SVG)
        z.writestr("DOCKER.md", f"""# {WCP_MANIFEST['name']} — WCP Container

## Pull
```
docker pull penrithbeacon/wcp-widget-radio
```

## Run
```
docker compose up -d
```

Port: 3741 | Spec: https://widgetcontextprotocol.com
""")
    buf.seek(0)
    name = WCP_MANIFEST["name"].lower().replace(" ", "-")
    resp = Response(buf.read(), mimetype="application/zip")
    resp.headers["Content-Disposition"] = f'attachment; filename="{name}.wcp"'
    return resp

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
