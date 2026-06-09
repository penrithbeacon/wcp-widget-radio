# Radio — Specification

## Overview
Internet radio player. Search thousands of stations, play directly in the dashboard or masthead. Five controls for flexible layouts.

- **Port:** 3741
- **Container:** `wcp-widget-radio`
- **Image:** `docker.io/penrithbeacon/wcp-widget-radio`

## Version
- **Widget:** 1.6.0
- **WCP:** 2.1.0
- **Docker tag:** `1.6.0-wcp2.1.0`

## Controls (HTML Templates)

| Template | Route | Purpose | Default Size |
|----------|-------|---------|--------------|
| widget.html | `/widget/` | Compact radio player card | 4×8 |
| full.html | `/widget/full` | Full-page player with station list | Window: 480×600 |
| control.html | `/widget/control/radio` | Play/pause control strip | Masthead |
| ticker.html | `/widget/ticker` | Now-playing marquee ticker | Masthead |
| led.html | `/widget/led` | Playing status LED indicator | Masthead |
| volume.html | `/widget/control/volume` | Volume slider (vertical/horizontal) | 1×2 |

## Components

| ID | Name | Role | Size |
|----|------|------|------|
| radio-player | Radio Player | widget | 4×8 |
| radio-control | Radio Control | widget | (masthead) |
| radio-led | Playing LED | widget | (masthead) |
| radio-ticker | Radio Ticker | widget | (masthead) |
| radio-volume | Volume | widget | 1×2 |

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/wcp` | Container directory |
| GET | `/widget/wcp` | Widget manifest |
| GET | `/widget/index` | Widget index directory |
| GET | `/widget/` | Compact player |
| GET | `/widget/full` | Full player |
| GET | `/widget/control/radio` | Control strip |
| GET | `/widget/ticker` | Now-playing ticker |
| GET | `/widget/led` | Status LED |
| GET | `/widget/control/volume` | Volume slider |
| GET | `/widget/health` | Health check |
| GET | `/widget/icon.svg` | Widget icon |
| GET | `/widget/api/guids` | Component UUIDs |
| GET | `/widget/export.wcp` | WCP export package |
| GET | `/widget/api/search` | Station search |
| GET | `/widget/api/top` | Top/popular stations |
| GET/POST | `/widget/api/state` | Shared playback state |
| POST | `/widget/publish` | Publish SPA |
| DELETE | `/widget/publish` | Remove published SPA |
| GET | `/` | Serve published SPA |

## Features
- Station search via Radio Browser API
- Top/popular stations listing
- Play/pause with shared state across controls
- Compact, control, ticker, LED, and volume sub-controls
- Volume slider (vertical for masthead, horizontal for wide layout)
- State synchronisation between all controls via server-side shared state
- `radio:state` postMessage for cross-widget communication
- Publish to Web support

## Configuration
- No persistent configuration — station selected at runtime

## Data Persistence
- No data volume (playback state in memory)

## Dependencies
- Python: `flask`, `requests`
- External API: Radio Browser API (free, no key required)
