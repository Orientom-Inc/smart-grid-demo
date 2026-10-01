# START HERE

Three ways to run this, from zero-effort to full development. Pick one.

---

## 1. Just look at the results — no install, no server

Double-click **`QMEMS_DASHBOARD.html`**.

One self-contained file, ~1 MB, all data baked in. No Python, no network, no
install. Works offline and on any machine. This is the file to email or put on a
USB stick before a presentation.

## 2. Run the API — no install, no Python

Double-click **`dist/QMEMS-API.exe`** (16.5 MB, Windows).

It starts the API and opens your browser at the dashboard. You get:

| | |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| Interactive API docs (Swagger) | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/api/v1/health |

Close the window or press Ctrl+C to stop. If port 8000 is busy it picks the next
free one and prints the URL.

**What the exe can and cannot do.** It serves precomputed results — that is the
whole design; the API never solves. It bundles fastapi, uvicorn, pydantic and
the cache, and it deliberately contains **no** numpy/scipy/pandas/pyomo, which
is why it is 16 MB rather than 700 MB. To *regenerate* results you need option 3.

A `cache/` folder or `dashboard.html` placed next to the exe overrides the
bundled copies, so you can drop in a freshly built cache without rebuilding.

## 3. Full environment — to change or rerun anything

```bash
python INSTALL.py
```

Python 3.10+ required. Builds a private `.venv/`, installs everything, verifies.
Then:

```bash
python RUN_DEMO.py
```

**Warning:** plain `INSTALL.py` also rebuilds the cache, which overwrites
`cache/evaluation.json` — and `build_cache.py` does not regenerate the
experiment blocks in it. Back it up first, or use `python INSTALL.py --skip-cache`.

---

## Reproducing the numbers

```bash
python src/qmems/run_validation.py
```

```bash
python src/qmems/run_qubo_validation.py
```

Expect `all_ok: True` and `PASS`. Both verified on Windows + Python 3.12.10,
Stage 1 running on the real `pyomo+highs` backend.

The RL/QRL benchmark — **one seed per process**, always. `synthetic_emsx.py`
holds a module-level RNG that every dataset build advances, so looping seeds in
one process trains each on different data (pitfall 6 in the brief):

```bash
python -m qmems_cache.evaluate --seed 0
```

```bash
python -m qmems_cache.evaluate --merge
```

Discount factor and episode budget are explicit and recorded in every artifact:

```bash
python -m qmems_cache.evaluate --seed 0 --qrl-gamma 0.99 --qrl-episodes 1000
```

Rebuild the standalone dashboard after any cache change:

```bash
python scripts/build_standalone.py
```

Rebuild the exe (isolated build env, ~15 s):

```bash
python packaging/build_exe.py
```

---

## What the results say

Read **`CHANGES.md`** for the full account. The short version:

- **The QUBO track is the real quantum result.** 100% of achievable savings at a
  measured 0.04% gap to the exact optimum, 144 qubits, zero slack. Validated:
  brute force == DP at 18 qubits, SA == DP at 144.
- **The RL comparison was confounded.** Tabular was trained at γ=0.99 for 8000
  episodes, the VQC at γ=0.95 for 200–300 (`bench_step.py:31,50,77-78`). Given
  the VQC's exact settings, a *classical* lookup table also scores 0.0% ± 0.0%
  with zero charge actions.
- **But that does not rescue QRL.** Correcting the discount and giving it 5×
  the episodes still leaves it at zero. The budgets are still not matched — the
  table needed 8000 episodes and the VQC has had 1000. That run is the one
  experiment that would settle it, and it has not been done.
- **QAOA has never run.** `qaoa_slice.py:116` computes 36 qubits → ~1 TiB for
  one statevector. Runnable at 18 qubits.

Honest framing for a panel: lead with the QUBO win, present the RL section as a
controlled diagnosis, and state plainly what is still untested.
