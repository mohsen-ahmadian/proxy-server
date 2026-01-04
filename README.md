# Smart HTTP/HTTPS Proxy Server (Python) — Cache • Filter • Rate Limit • Dashboard

A lightweight **multi-threaded TCP proxy** written in Python.  
It forwards **HTTP** requests, supports **HTTPS tunneling via `CONNECT`**, and adds practical features like **caching**, **domain blacklisting**, **rate limiting**, **structured logging**, and a built-in **stats dashboard**.

---

## Features

- **HTTP proxying (TCP)**
  - Accepts client connections, forwards requests to the destination server, streams responses back.

- **HTTPS support (CONNECT tunnel)**
  - Creates a TCP tunnel so TLS traffic passes through without inspection.

- **Caching**
  - In-memory cache keyed by URL (simple FIFO eviction).
  - **Conditional cache validation** using `ETag` and/or `Last-Modified` via a `HEAD` request (serves cached response when `304 Not Modified`).

- **Filtering (Blacklist)**
  - Blocks requests to blacklisted domains (returns `403 Forbidden`).

- **Rate limiting**
  - Per-client-IP rate limiting (returns `429 Too Many Requests`).

- **Logging**
  - Logs each request with time, client IP, method, URL/host, status and result.
  - Writes to `proxy_log.txt` and prints to console.

- **Live Dashboard**
  - Visit `http://proxy-stats` (through the proxy) to view a simple HTML dashboard:
    - Uptime, requests, active threads, cache hits/misses, blocked, recent activity.

---

## Project Structure

```text
.
├── main.py           # Starts the proxy server and accepts connections
├── proxy_handler.py  # Per-connection handler (HTTP forwarding + HTTPS tunnel)
├── cache.py          # In-memory cache with max-entry eviction
├── filter_module.py  # Blacklist + rate limiter
├── stats.py          # Counters + HTML dashboard (auto-refresh)
├── logger.py         # Thread-safe logging to console + file
├── config.py         # Configuration (host/port, limits, blacklist, etc.)
└── proxy_log.txt     # Generated log file (runtime output)
```

---

## Requirements

- Python **3.8+**
- No external dependencies (standard library only)

---

## Quick Start

### 1) Run the proxy
```bash
python main.py
```

By default it listens on **127.0.0.1:8080**.

You should see:
- `Proxy Running on 127.0.0.1:8080`
- `Visit http://proxy-stats for Dashboard`

### 2) Configure your browser / system proxy
Set the HTTP/HTTPS proxy to:

- **Host:** `127.0.0.1`
- **Port:** `8080`

Then browse normally.

> For HTTPS sites, your browser will use the `CONNECT` method and the proxy will tunnel TCP.

---

## Dashboard

After your browser is configured to use the proxy, open:

- `http://proxy-stats`

This is a special internal route handled by the proxy, returning an HTML dashboard that auto-refreshes every 5 seconds.

---

## Configuration

All settings are in `config.py`:

- `HOST`, `PORT` — listening address/port (default `127.0.0.1:8080`)
- `MAX_CONN` — backlog / max pending connections
- `BUFFER_SIZE` — read buffer size (bytes)
- `SOCKET_TIMEOUT` — client socket timeout (seconds)

Caching:
- `CACHE_ENABLED` — enable/disable caching (note: current implementation always saves; see Limitations)
- `MAX_CACHE_ENTRIES` — max in-memory cache entries

Filtering / Rate limiting:
- `BLACKLIST` — list of blocked domain substrings
- `RATE_LIMIT_COUNT` — max requests per period
- `RATE_LIMIT_PERIOD` — period window (seconds)

Logging:
- `LOG_FILE` — output log file name (default `proxy_log.txt`)

---

## Response / Error Codes

- **200** — OK / Tunnel established
- **403** — Blocked domain (blacklist)
- **429** — Rate limit exceeded
- **502** — Upstream / connection errors

---

## How Caching Works

1. Proxy checks the cache for the requested URL.
2. If present, it tries **conditional validation** by sending a `HEAD` request to the server:
   - `If-None-Match: <ETag>` and/or `If-Modified-Since: <Last-Modified>`
3. If the server responds **304 Not Modified**, the proxy serves the cached response.
4. Otherwise, it fetches fresh content and replaces the cache entry.

Eviction policy is **FIFO-like** (removes the oldest inserted entry when max entries is reached).

---

## Notes / Limitations

- **No HTTP keep-alive pooling**: client connections are handled per request/connection thread.
- **Cache policy is simplified**: does not parse/obey full `Cache-Control` semantics.
- **In-memory cache only**: cache is lost when the proxy restarts.
- **HTTPS is tunneled, not decrypted**: the proxy does not inspect TLS traffic (by design).

---

## Suggested `.gitignore`

If you don’t want logs in your repo, add:

```gitignore
proxy_log.txt
__pycache__/
*.pyc
```

---

## Authors

- Mohsen Ahmadian
