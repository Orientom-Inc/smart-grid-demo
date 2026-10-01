#!/usr/bin/env python3
"""QMEMS -- ONE-CLICK LAUNCHER.  Starts the API and opens it in your browser.

    Windows : double-click RUN_DEMO.py
    macOS   : double-click RUN_DEMO.command  (or: python3 RUN_DEMO.py)
    Linux   : python3 RUN_DEMO.py

Run INSTALL.py first. If you have not, this still tries its best: it will use
whatever interpreter you launched it with, build the cache if it is missing,
and fall back to a dependency-free server if FastAPI is not installed -- so
you always end up looking at a working API rather than a stack trace.

Stop it with Ctrl+C.

Flags:
  --port N       listen on a different port (default 8000)
  --no-browser   do not open a browser window
  --lite         force the dependency-free server even if FastAPI is present
  --rebuild      rebuild the cache before starting
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
VENV = HERE / ".venv"
PREFIX = "/api/v1"

C = {"b": "\033[1m", "g": "\033[32m", "y": "\033[33m", "r": "\033[31m",
     "c": "\033[36m", "d": "\033[2m", "x": "\033[0m"}
if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
    C = dict.fromkeys(C, "")


def say(msg: str = "", style: str = "") -> None:
    print(f"{C.get(style, '')}{msg}{C['x']}", flush=True)


def hold() -> None:
    if sys.stdin and sys.stdin.isatty():
        try:
            input(f"\n{C['d']}Press Enter to close...{C['x']}")
        except (EOFError, KeyboardInterrupt):
            pass


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def reexec_in_venv() -> None:
    """Relaunch inside .venv if we were started by a different interpreter."""
    if os.environ.get("QMEMS_RELAUNCHED"):
        return
    py = venv_python()
    if not py.exists() or Path(sys.executable).resolve() == py.resolve():
        return
    say(f"  switching to the project environment ({VENV.name}/)", "d")
    env = {**os.environ, "QMEMS_RELAUNCHED": "1"}
    raise SystemExit(subprocess.run([str(py), str(Path(__file__).resolve()),
                                     *sys.argv[1:]], env=env).returncode)


def free_port(preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return preferred


def ensure_cache(rebuild: bool) -> bool:
    sys.path[:0] = [str(SRC), str(SRC / "qmems")]
    cache = HERE / "cache"
    if (cache / "manifest.json").exists() and not rebuild:
        return True
    say("\n  No cache found -- precomputing results (about a minute) ...", "y")
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    r = subprocess.run(
        [sys.executable, "-m", "qmems_cache.build_cache",
         "--days", "10", "--test-days", "3", "--seed", "0"],
        cwd=HERE, env=env, text=True, capture_output=True)
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-12:])
        say(f"\n  Could not build the cache:\n{tail}", "r")
        say("\n  Run INSTALL.py first -- numpy, scipy and pandas are required.", "y")
        return False
    say("  cache ready", "g")
    return True


def banner(url: str, mode: str, health: dict) -> None:
    say("\n" + "=" * 66, "b")
    say("  QMEMS API is running", "b")
    say("=" * 66, "b")
    say(f"\n  Open:  {C['c']}{url}{C['x']}", "b")
    say(f"  Mode:  {mode}")
    say(f"  Data:  {len(health.get('sites', []))} site(s), "
        f"{health.get('n_days')} days, {len(health.get('methods', []))} methods")
    say(f"\n  Try these:", "d")
    for path in ("/docs", f"{PREFIX}/comparison/99/7",
                 f"{PREFIX}/quantum/99/7/qubo_sa",
                 f"{PREFIX}/leaderboard?held_out_only=true"):
        say(f"    http://127.0.0.1:{url.rsplit(':', 1)[1].split('/')[0]}{path}", "d")
    say(f"\n  Stop with Ctrl+C.\n", "d")


def open_later(url: str, delay: float = 1.5) -> None:
    threading.Timer(delay, lambda: webbrowser.open(url)).start()


# ---------------------------------------------------------------------------
# Fallback server: stdlib only.
#
# This exists so the launcher NEVER dead-ends. store.py has no third-party
# dependencies, so the same data layer the real API uses can be served by
# http.server. It is a thin path router over Store -- all logic still lives in
# one place, so the two servers cannot disagree about numbers. It has no
# OpenAPI docs and no validation, which is exactly why it is the fallback and
# not the product.
# ---------------------------------------------------------------------------
INDEX_HTML = """<!doctype html><meta charset=utf-8>
<title>QMEMS API</title>
<style>
 body{{font:15px/1.6 system-ui,sans-serif;max-width:820px;margin:3rem auto;padding:0 1.5rem;color:#1a1a1a}}
 h1{{margin-bottom:.2rem}} .sub{{color:#666;margin-top:0}}
 .warn{{background:#fff8e1;border-left:3px solid #f0ad4e;padding:.8rem 1rem;margin:1.5rem 0}}
 a{{color:#0b6bcb;text-decoration:none}} a:hover{{text-decoration:underline}}
 li{{margin:.35rem 0}} code{{background:#f4f4f5;padding:.1rem .35rem;border-radius:3px}}
</style>
<h1>QMEMS API</h1>
<p class=sub>Quantum Microgrid EMS &mdash; precomputed benchmark, served read-only.</p>
<div class=warn><b>Lite mode.</b> FastAPI is not installed, so this is the
dependency-free fallback server: same data, same numbers, but no
<code>/docs</code> page and no request validation.
Run <code>INSTALL.py</code> for the full API.</div>
<h3>Catalog</h3><ul>
<li><a href="{p}/health">/health</a> &mdash; is the cache loaded</li>
<li><a href="{p}/meta">/meta</a> &mdash; seed, build command, dataset</li>
<li><a href="{p}/verify">/verify</a> &mdash; re-checksum the cache</li>
<li><a href="{p}/methods">/methods</a> &mdash; method registry</li>
<li><a href="{p}/sites">/sites</a> &middot; <a href="{p}/sites/{s}/days">/sites/{s}/days</a></li></ul>
<h3>Results</h3><ul>
<li><a href="{p}/comparison/{s}/{d}">/comparison/{s}/{d}</a> &mdash; every method on one day</li>
<li><a href="{p}/comparison/{s}/{d}/race">/comparison/{s}/{d}/race</a> &mdash; cumulative cost per step</li>
<li><a href="{p}/runs/{s}/{d}/qubo_sa">/runs/{s}/{d}/qubo_sa</a></li>
<li><a href="{p}/leaderboard?held_out_only=true">/leaderboard?held_out_only=true</a></li></ul>
<h3>Quantum</h3><ul>
<li><a href="{p}/quantum/{s}/{d}">/quantum/{s}/{d}</a> &mdash; all quantum methods</li>
<li><a href="{p}/quantum/{s}/{d}/qubo_sa">/quantum/{s}/{d}/qubo_sa</a> &mdash; formulation + measured gap</li>
<li><a href="{p}/quantum/{s}/{d}/qubo_sa/matrix">/quantum/{s}/{d}/qubo_sa/matrix</a> &mdash; coupling structure</li></ul>
"""


def make_lite_server(port: int, store):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse

    from qmems_api.store import CacheError, NotInCache

    health = store.health()
    site = (health.get("sites") or ["99"])[0]
    day = max((health.get("n_days") or 1) - 1, 0)

    def route(path: str, qs: dict):
        parts = [p for p in path.split("/") if p]
        q = lambda k, default=None: (qs.get(k, [default]) or [default])[0]
        truthy = lambda v: str(v).lower() in ("1", "true", "yes")

        match parts:
            case ["health"]:                    return store.health()
            case ["meta"]:                      return store.manifest()
            case ["verify"]:                    return store.verify()
            case ["methods"]:                   return store.methods()
            case ["sites"]:                     return store.sites()
            case ["sites", sid]:                return store.site(sid)
            case ["sites", sid, "days"]:        return store.days(sid)
            case ["runs", sid, d, m]:           return store.run(sid, int(d), m)
            case ["comparison", sid, d]:        return store.comparison(sid, int(d))
            case ["comparison", sid, d, "race"]: return store.race(sid, int(d))
            case ["leaderboard"]:
                return store.leaderboard(site_id=q("site_id"), method=q("method"),
                                         held_out_only=truthy(q("held_out_only", "0")))
            case ["quantum", sid, d]:
                comp = store.comparison(sid, int(d))
                panels = {k: {**v["quantum"], "summary": v["summary"]}
                          for k, v in comp["runs"].items() if "quantum" in v}
                if not panels:
                    raise NotInCache(f"no quantum methods for {sid} day {d}")
                return {"site_id": sid, "day": int(d), "methods": list(panels),
                        "panels": panels}
            case ["quantum", sid, d, m]:        return store.quantum(sid, int(d), m)
            case ["quantum", sid, d, m, "matrix"]:
                store.quantum(sid, int(d), m)
                return store.qubo_structure(sid, int(d), max_couplings=1500)
        raise NotInCache(f"no route for /{'/'.join(parts)}")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:            # noqa: N802
            u = urlparse(self.path)
            if u.path in ("/", "/index.html", "/dashboard"):
                dash = HERE / "app" / "dashboard.html"
                if dash.is_file():
                    return self._send(200, dash.read_bytes(),
                                      "text/html; charset=utf-8")
            if u.path in ("/", "/docs", "/endpoints", "/index.html"):
                html = INDEX_HTML.format(p=PREFIX, s=site, d=day).encode()
                return self._send(200, html, "text/html; charset=utf-8")
            if not u.path.startswith(PREFIX):
                return self._send(404, b'{"detail":"not found"}', "application/json")
            try:
                payload, code = route(u.path[len(PREFIX):], parse_qs(u.query)), 200
            except NotInCache as exc:
                payload, code = {"detail": str(exc)}, 404
            except CacheError as exc:
                payload, code = {"detail": str(exc)}, 503
            except Exception as exc:                       # noqa: BLE001
                payload, code = {"detail": f"{type(exc).__name__}: {exc}"}, 500
            self._send(code, json.dumps(payload, indent=1).encode(),
                       "application/json; charset=utf-8")

        def log_message(self, fmt: str, *a) -> None:
            say(f"    {self.command} {self.path}", "d")

    return ThreadingHTTPServer(("0.0.0.0", port), Handler), health


# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--lite", action="store_true")
    p.add_argument("--rebuild", action="store_true")
    args = p.parse_args()

    say("=" * 66, "b")
    say("  QMEMS -- starting the API", "b")
    say("=" * 66, "b")

    reexec_in_venv()

    if not ensure_cache(args.rebuild):
        hold()
        return 1

    os.environ.setdefault("QMEMS_CACHE_DIR", str(HERE / "cache"))
    port = free_port(args.port)
    if port != args.port:
        say(f"  port {args.port} is busy, using {port}", "y")

    have_fastapi = True
    try:
        import fastapi  # noqa: F401
        import uvicorn
    except ImportError:
        have_fastapi = False

    if have_fastapi and not args.lite:
        from qmems_api.main import app
        from qmems_api.store import Store
        health = Store(HERE / "cache").health()
        url = f"http://127.0.0.1:{port}/"
        banner(url, "dashboard + full API (docs at /docs)", health)
        if not args.no_browser:
            open_later(url)
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
        return 0

    if not args.lite:
        say("\n  FastAPI is not installed -- starting the lite server instead.", "y")
        say("  Run INSTALL.py to get the full API with /docs.", "y")
    from qmems_api.store import Store
    server, health = make_lite_server(port, Store(HERE / "cache"))
    url = f"http://127.0.0.1:{port}/"
    banner(url, "dashboard + lite API (stdlib fallback, no /docs)", health)
    if not args.no_browser:
        open_later(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        say("\n  stopped", "y")
        server.shutdown()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        say("\n  stopped", "y")
        sys.exit(130)
