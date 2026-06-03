# WCP Widget — Radio

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) internet radio player
with four components: a full radio player widget, a masthead play/stop control, a playing LED
indicator, and a now-playing ticker. Powered by the
[Radio Browser API](https://api.radio-browser.info/) — free, no API key required.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)  
**Part of the** [Penrith Beacon WCP](https://penrithbeacon.com) widget suite.

> **WCP 1.5.0 certified.** This widget implements the full
> [Widget Context Protocol 1.5.0](https://widgetcontextprotocol.com) specification,
> including server UUID, Container Directory (`GET /wcp`), all six `Wcp-*` request headers, and context-scoped runtime state isolation (`Wcp-Orchestration-Id`, `Wcp-Application-Id`).

---

## Components

| Component | Role | Default size | What it shows |
|-----------|------|:------------:|---------------|
| **Radio Player** | widget | 4 × 4 | Station search, play/stop, now-playing display |
| **Radio Control** | control | masthead | Compact play/stop button + station name |
| **Playing LED** | control | masthead | Green/grey LED indicating playing/stopped state |
| **Radio Ticker** | ticker | masthead | Scrolling now-playing strip |

---

## Requirements

- Docker and Docker Compose

No API keys required — powered by the free Radio Browser API.

---

## Quick Start

```bash
docker run -d \
  --name wcp-widget-radio \
  -p 3741:3741 \
  --restart unless-stopped \
  penrithbeacon/wcp-widget-radio:latest
```

Then add it to your WCP dashboard at `http://localhost:3741`.

---

## Docker Compose

```yaml
services:
  radio:
    image: penrithbeacon/wcp-widget-radio:latest
    container_name: wcp-widget-radio
    ports:
      - "3741:3741"
    restart: unless-stopped
```

---

## WCP Request Headers

This widget supports the WCP 1.5.0 request headers:

| Header | Required | Description |
|--------|----------|-------------|
| `Wcp-Instance-Id` | Required | UUID identifying this widget instance |
| `Wcp-Dashboard-Id` | Optional | UUID identifying the requesting dashboard |
| `Wcp-Version` | Optional | Protocol version the dashboard speaks |
| `Wcp-Widget-Id` | Optional | Widget ID from Container Directory selection |
| `Wcp-Orchestration-Id` | Optional | UUID of the active orchestration — shared state key for multi-component coordination |
| `Wcp-Application-Id` | Optional | UUID of the active application window (kiosk only) — combined with orchestration ID for full isolation |

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /wcp` | GET | WCP 1.5.0 Container Directory |
| `GET /widget/` | GET | Compact radio player (iframe) |
| `GET /widget/wcp` | GET | WCP 1.5.0 manifest |
| `GET /widget/health` | GET | `{"status":"ok","name":"Radio"}` |
| `GET /widget/icon.svg` | GET | Widget icon (SVG) |
| `GET /widget/full` | GET | Full radio player page |
| `GET /widget/control/radio` | GET | Masthead control component |
| `GET /widget/led` | GET | Masthead LED component |
| `GET /widget/ticker` | GET | Masthead ticker component |
| `GET /widget/api/guids` | GET | Server and component UUIDs for Bonjour discovery |
| `GET /widget/api/search` | GET | Station search — `?q=<query>` |
| `GET /widget/api/state` | GET | Current playback state |
| `POST /widget/api/state` | POST | Update playback state |
| `GET /widget/export.wcp` | GET | Self-export as a `.wcp` package |

---

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 1.5.0 |
| Widget Version | 1.2.1 |
| Render mode | iframe |
| Auth | none |
| Multi-instance | Stateless — playback state is global |

---

## Technical Details

- **Base image:** `python:3.12-slim`
- **Port:** `3741`
- **Dependencies:** Flask, requests
- **No external API keys** — powered by Radio Browser API (free)
- **No persistent storage required** — stateless

---

## Links

- [Penrith Beacon](https://penrithbeacon.com)
- [Widget Context Protocol specification](https://widgetcontextprotocol.com)
- [Radio Browser API](https://api.radio-browser.info/)
- [Docker Hub — penrithbeacon/wcp-widget-radio](https://hub.docker.com/r/penrithbeacon/wcp-widget-radio)
