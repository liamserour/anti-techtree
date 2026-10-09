import hashlib, json, time
from pathlib import Path
import httpx

CACHE = Path(".cache")
UA = "techtree/0.1 (open research tool; contact via repo)"
_last_call: dict[str, float] = {}


def get(url: str, params: dict | None = None, min_interval: float = 0.0, ttl_hours: float = 12, method: str = "GET", json_body: dict | None = None) -> str:
    """GET/POST with a tiny disk cache and per-host politeness delay."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha1(json.dumps([method, url, params, json_body], sort_keys=True).encode()).hexdigest()
    f = CACHE / f"{key}.txt"
    if f.exists() and (time.time() - f.stat().st_mtime) < ttl_hours * 3600:
        return f.read_text()
    host = httpx.URL(url).host
    wait = _last_call.get(host, 0) + min_interval - time.time()
    if wait > 0:
        time.sleep(wait)
    with httpx.Client(timeout=40, headers={"User-Agent": UA}, follow_redirects=True) as c:
        for attempt in range(4):
            r = c.post(url, json=json_body) if method == "POST" else c.get(url, params=params)
            _last_call[host] = time.time()
            if r.status_code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 * (attempt + 1) ** 2)  # 2, 8, 18 s
                continue
            break
    r.raise_for_status()
    f.write_text(r.text)
    return r.text
