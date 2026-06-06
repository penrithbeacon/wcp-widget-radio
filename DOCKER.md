# WCP Widget: Radio

A [Widget Context Protocol (WCP)](https://widgetcontextprotocol.com) compliant internet radio
player with four components: a full radio player widget, a masthead play/stop control, a
playing LED indicator, and a now-playing ticker. Powered by
[Radio Browser API](https://api.radio-browser.info/) — free, no API key required.
Designed to run alongside any WCP-compatible host dashboard.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com)

## Quick Start

```bash
docker run -d \
  --name wcp-widget-radio \
  -p 3741:3741 \
  --restart unless-stopped \
  docker.io/penrithbeacon/wcp-widget-radio:latest
```

Then add it to your WCP dashboard at the container's network address.

## Docker Compose

```yaml
services:
  radio:
    image: docker.io/penrithbeacon/wcp-widget-radio:latest
    container_name: wcp-widget-radio
    ports:
      - "3741:3741"
    restart: unless-stopped
```

## Components

This widget exposes four components — a host may deploy any or all of them:

| Component | Role | Description |
|-----------|------|-------------|
| Radio Player | widget | Full station search + playback on the stave |
| Radio Control | control | Masthead play/stop with station name (160–240px) |
| Playing LED | control | Masthead LED indicator — green when playing (40–60px square) |
| Radio Ticker | ticker | Masthead scrolling now-playing strip |

## WCP Request Headers

This widget supports the WCP 2.0.0 request headers:

| Header | Required | Description |
|--------|----------|-------------|
| `Wcp-Instance-Id` | Required | UUID identifying this widget instance |
| `Wcp-Dashboard-Id` | Optional | UUID identifying the requesting dashboard |
| `Wcp-Version` | Optional | Protocol version the dashboard speaks |
| `Wcp-Widget-Id` | Optional | Widget ID from Container Directory selection |
| `Wcp-Orchestration-Id` | Optional | UUID of the active orchestration — shared state key for multi-component coordination |
| `Wcp-Application-Id` | Optional | UUID of the active application window (kiosk only) — combined with orchestration ID for full isolation |

## WCP Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /wcp` | WCP 2.0.0 Container Directory |
| `GET /widget/` | Compact radio player (iframe) |
| `GET /widget/wcp` | WCP 2.0.0 manifest |
| `GET /widget/health` | Health check |
| `GET /widget/icon.svg` | Widget icon (SVG) |
| `GET /widget/full` | Full radio player page |
| `GET /widget/control/radio` | Masthead control: play/stop + station |
| `GET /widget/led` | Masthead LED: playing indicator |
| `GET /widget/ticker` | Masthead ticker: scrolling now-playing |
| `GET /widget/api/search?q=<query>` | Station search via Radio Browser API |
| `GET /widget/api/top` | Top 12 stations by click count |
| `GET /widget/api/state` | Current playback state |
| `POST /widget/api/state` | Update playback state |

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 2.0.0 |
| Widget Version | 1.3.0 |
| Render mode | iframe |
| Auth | none |
| Default card size | 4×4 |
| Components | 4 (widget + 2 controls + ticker) |

## Technical Details

- **Base image:** `python:3.12-slim`
- **Platforms:** `linux/amd64`, `linux/arm64`
- **Port:** `3741`
- **Dependencies:** Flask, requests
- **Radio data:** [Radio Browser API](https://api.radio-browser.info/) — free, no API key needed
- **No persistent storage required** — playback state is in-memory

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release — multi-arch (`linux/amd64`, `linux/arm64`) |
| `1.5.0-wcp2.1.0` | Widget v1.5.0, WCP 2.1.0 — `/widget/health` returns `container` name |
| `1.4.0-wcp2.1.0` | Widget v1.4.0, WCP 2.1.0 — WCP 2.1.0 upgrade, orchestration ID context |
| `1.3.0-wcp2.0.0` | Widget v1.3.0, WCP 2.0.0 — container block, manifest image source |
| `1.2.1-wcp1.4.0` | Widget v1.2.1, WCP 2.0.0 — server UUID, Container Directory, Wcp-Widget-Id |
| `1.2.0-wcp1.3.1` | Widget v1.2.0, WCP 1.3.1 — CORS headers, multi-instance support |

> **Platform history:** `latest` was rebuilt as a multi-arch image on 2026-06-05, adding `linux/amd64` support (Synology NAS, Intel/AMD servers). All version-specific tags (`1.2.0-wcp1.3.1` through `1.3.0-wcp2.0.0`) were originally built on Apple Silicon and are `linux/arm64` only.

## Source

- Docker Hub: [penrithbeacon/wcp-widget-radio](https://hub.docker.com/r/penrithbeacon/wcp-widget-radio)
- GitHub: [penrithbeacon/wcp-widget-radio](https://github.com/penrithbeacon/wcp-widget-radio)
- WCP Specification: [widgetcontextprotocol.com](https://widgetcontextprotocol.com)
