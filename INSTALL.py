#!/usr/bin/env python3
"""QMEMS -- ONE-CLICK INSTALLER.  Run this once, then run RUN_DEMO.py.

    Windows : double-click INSTALL.py
    macOS   : double-click INSTALL.command  (or: python3 INSTALL.py)
    Linux   : python3 INSTALL.py

What it does, in order:

  1. checks the Python version
  2. creates a private virtual environment in .venv/
  3. installs every dependency into it (never into your system Python)
  4. builds the results cache the API serves
  5. self-checks the cache and tells you what to run next

Safe to re-run. Nothing outside this folder is modified. Delete .venv/ to
undo everything.

Flags:
  --no-venv        install into the current interpreter instead
  --minimal        API only, skip test/lint tooling
  --days N         days of data to precompute (default 10)
  --skip-cache     install dependencies but do not build the cache
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
MIN_PY = (3, 10)

C = {"b": "\033[1m", "g": "\033[32m", "y": "\033[33m", "r": "\033[31m",
     "d": "\033[2m", "x": "\033[0m"}
if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
    C = dict.fromkeys(C, "")


def say(msg: str = "", style: str = "") -> None:
    print(f"{C.get(style, '')}{msg}{C['x']}", flush=True)


def step(n: int, total: int, msg: str) -> None:
    say(f"\n[{n}/{total}] {msg}", "b")


def die(msg: str, hint: str = "") -> None:
    say(f"\n  FAILED: {msg}", "r")
    if hint:
        say(f"  {hint}", "y")
    hold()
    sys.exit(1)


def hold() -> None:
    """Keep the window open when double-clicked from a file manager."""
    if sys.stdin and sys.stdin.isatty():
        try:
            input(f"\n{C['d']}Press Enter to close...{C['x']}")
        except (EOFError, KeyboardInterrupt):
            pass


def venv_python(root: Path = VENV) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], cwd=HERE, text=True, **kw)


# ---------------------------------------------------------------------------
def check_python() -> None:
    v = sys.version_info
    if v[:2] < MIN_PY:
        die(f"Python {v.major}.{v.minor} is too old; {MIN_PY[0]}.{MIN_PY[1]}+ is required.",
            "Install a newer Python from https://python.org and run this again.")
    say(f"  Python {v.major}.{v.minor}.{v.micro} on {platform.system()} -- OK", "g")


def make_venv(use_venv: bool) -> Path:
    if not use_venv:
        say("  --no-venv: installing into the current interpreter", "y")
        return Path(sys.executable)
    py = venv_python()
    if py.exists():
        say(f"  reusing existing environment at {VENV.name}/", "d")
        return py
    say(f"  creating {VENV.name}/ ...", "d")
    r = run([sys.executable, "-m", "venv", str(VENV)], capture_output=True)
    if r.returncode != 0 or not py.exists():
        die("could not create the virtual environment.\n" + (r.stderr or ""),
            "On Debian/Ubuntu you may need: sudo apt install python3-venv")
    say(f"  environment ready: {py}", "g")
    return py


def pip_install(py: Path, minimal: bool) -> None:
    req = HERE / ("requirements-api.txt" if minimal else "requirements-dev.txt")
    if not req.exists():
        die(f"{req.name} is missing -- is this the repository root?")

    say("  upgrading pip ...", "d")
    run([py, "-m", "pip", "install", "--upgrade", "pip", "-q"], capture_output=True)

    say(f"  installing from {req.name} (this is the slow part, 1-3 min) ...", "d")
    t0 = time.time()
    r = run([py, "-m", "pip", "install", "-r", str(req)],
            capture_output=True)
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-15:])
        die(f"dependency installation failed:\n{tail}",
            "Most common cause is no internet access. Check your connection or "
            "proxy, then run this file again -- it resumes safely.")
    say(f"  dependencies installed in {time.time() - t0:.0f}s", "g")


def verify_imports(py: Path) -> None:
    code = (
        "import numpy, scipy, pandas, fastapi, uvicorn, pydantic;"
        "print('core ok')"
    )
    r = run([py, "-c", code], capture_output=True)
    if r.returncode != 0:
        die("a dependency is missing after installation:\n" + (r.stderr or ""),
            "Try deleting .venv/ and running INSTALL.py again.")
    say("  all imports resolve", "g")


def build_cache(py: Path, days: int) -> None:
    env = {**os.environ, "PYTHONPATH": str(HERE / "src")}
    say(f"  precomputing {days} days x 8 methods ...", "d")
    t0 = time.time()
    r = run([py, "-m", "qmems_cache.build_cache", "--days", str(days),
             "--test-days", "3", "--seed", "0"],
            env=env, capture_output=True)
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-15:])
        die(f"cache build failed:\n{tail}")
    for line in (r.stdout or "").strip().splitlines()[-3:]:
        say(f"    {line}", "d")
    say(f"  cache built in {time.time() - t0:.0f}s", "g")


def self_check(py: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(HERE / "src")}
    code = (
        "from qmems_api.store import Store;"
        "s=Store('cache');h=s.health();v=s.verify();"
        "assert h['status']=='ok', h;"
        "assert v['ok'], v;"
        "print(f\"{len(h['sites'])} site(s), {h['n_days']} days, \""
        "      f\"{len(h['methods'])} methods, {v['n_files']} files verified\")"
    )
    r = run([py, "-c", code], env=env, capture_output=True)
    if r.returncode != 0:
        die("cache self-check failed:\n" + (r.stderr or ""))
    say(f"  {r.stdout.strip()}", "g")


# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--no-venv", action="store_true")
    p.add_argument("--minimal", action="store_true")
    p.add_argument("--skip-cache", action="store_true")
    p.add_argument("--days", type=int, default=10)
    args = p.parse_args()

    say("=" * 66, "b")
    say("  QMEMS -- Quantum Microgrid EMS  |  installer", "b")
    say("=" * 66, "b")
    say(f"  folder: {HERE}", "d")

    total = 4 if args.skip_cache else 5
    step(1, total, "Checking Python")
    check_python()

    step(2, total, "Creating the environment")
    py = make_venv(not args.no_venv)

    step(3, total, "Installing dependencies")
    pip_install(py, args.minimal)
    verify_imports(py)

    if not args.skip_cache:
        step(4, total, "Building the results cache")
        build_cache(py, args.days)
        step(5, total, "Verifying")
        self_check(py)
    else:
        step(4, total, "Skipping cache build (--skip-cache)")

    say("\n" + "=" * 66, "g")
    say("  INSTALLATION COMPLETE", "g")
    say("=" * 66, "g")
    say("\n  Next: run RUN_DEMO.py  (double-click it, or:)\n", "b")
    say(f"     {py} RUN_DEMO.py\n", "d")
    say("  It starts the API and opens the interactive docs in your browser.")
    hold()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        say("\n  cancelled", "y")
        sys.exit(130)
