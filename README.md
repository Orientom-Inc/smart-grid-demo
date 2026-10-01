# QMEMS — Quantum Microgrid EMS: benchmark, API and demo

A validated MILP → QUBO → quantum/RL benchmark for microgrid energy
management, served as a read-only HTTP API and an interactive dashboard.

Cost comparison across **rule-based, MILP, QUBO (classical / quantum-inspired /
quantum hardware), classical RL and quantum RL** — with measured optimality
gaps and provenance attached to every number.

## Architecture

Three layers, strictly separated.

| Layer | Package | Role |
|---|---|---|
| Science | `src/qmems/` | The validated codebase. **Never edited.** |
| Precompute | `src/qmems_cache/` | Runs every method offline, writes JSON to `cache/` |
| API | `src/qmems_api/` | Reads the cache. Never solves. |
| Client | `app/` | Streamlit dashboard over the API |

**The API never solves.** That is not a convention, it is structural:
`store.py` has no dependency that can reach a solver. It is what keeps
responses in the tens of milliseconds and makes a live walkthrough safe.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

make cache          # ~1 min: runs every method on 10 days, writes cache/
make api            # http://localhost:8000/docs
```

## Endpoints

```
GET  /api/v1/health                              liveness + cache warmth
GET  /api/v1/meta                                seed, build cmd, git sha, dataset
GET  /api/v1/verify                              re-checksum cache vs manifest
GET  /api/v1/methods                             registry: ids, colors, provenance flags
GET  /api/v1/sites                               sites with battery specs
GET  /api/v1/sites/{sid}/days                    day index + headroom hint
GET  /api/v1/runs/{sid}/{day}/{method}           one run, four blocks
GET  /api/v1/comparison/{sid}/{day}              every method  ← the hot path
GET  /api/v1/comparison/{sid}/{day}/race         cumulative cost per step
GET  /api/v1/leaderboard?held_out_only=true      aggregated scores
GET  /api/v1/quantum/{sid}/{day}/{method}        formulation + measured gap
GET  /api/v1/quantum/{sid}/{day}/{method}/matrix sparse coupling structure
GET  /api/v1/quantum/{sid}/{day}                 all quantum methods side by side
POST /api/v1/solve                               optional, OFF by default
GET  /api/v1/jobs/{job_id}                       poll a live solve
```

### The four blocks

Every run returns the same shape, so no method is measured differently:

- **`summary`** — cost, savings, score, optimality gap, peak import, CO₂,
  self-consumption, cycles, wall time. *What a stakeholder asks.*
- **`timeseries`** — columnar dispatch: load, PV, import, export, charge,
  discharge, SoC, step and cumulative cost. *What an operator runs.*
- **`feasibility`** — the stage-1 residual checks. *Whether to trust it.*
- **`quantum`** — formulation, measured solve, provenance. *Quantum methods only.*

## Two honesty invariants

These are enforced by tests, not by convention.

**1. `hardware_backed` is true only if a QPU processed the instance.**
`qubo_sa` solves the identical QUBO on a CPU — it is labelled
`executed_on: "quantum_inspired"`, grouped with the quantum methods in the UI
but hatched and flagged, so no chart can imply a QPU ran what a CPU did.

**2. Gaps are measured, never assumed.** Every quantum result carries
`reference_dp_eur` — the exact optimum from dynamic programming — computed on
the same instance. There is no code path producing an estimated gap.

## Feasibility vs performance

`solution.check()` folds `cost_leq_dummy` into its `all_ok`. Correct for the
MILP, which cannot lose to the dummy; wrong for a demo that also serves
heuristics, which can. `metrics.split_checks()` separates them without
touching `solution.py`:

```json
"feasibility": {
  "balance_residual": 3.55e-15,
  "soc_dynamics_residual": 1.11e-16,
  "physical_ok": true,     // operator: is this runnable?
  "beats_dummy": true,     // stakeholder: did it earn its keep?
  "stage1_all_ok": true    // original verdict, preserved verbatim
}
```

The rule-based controller genuinely loses money on 7 of 10 days. That is
reported, not hidden behind a red flag.

## Results (synthetic site 99, held-out days 7–9, seed 0)

| method | cost € | savings € | score | mean gap % |
|---|---|---|---|---|
| anticipative *(bound)* | 322.62 | 13.78 | 112.2% | −0.63 |
| **qubo_dp** *(exact discrete)* | 324.13 | 12.28 | 100.0% | 0.00 |
| **qubo_sa** *(quantum-inspired)* | 324.21 | 12.19 | 99.3% | 0.04 |
| milp *(forecast, open loop)* | 324.26 | 12.14 | 98.9% | 0.04 |
| rl_tabular | 328.96 | 7.44 | 60.6% | 1.85 |
| rule_based | 334.27 | 2.14 | 17.4% | 3.43 |
| dummy | 336.41 | 0.00 | 0.0% | 4.24 |
| **qrl_vqc** | 336.41 | 0.00 | 0.0% | 4.24 |

Rule-based 17.4%, tabular 60.6%, QRL 0% reproduce the stage-3 benchmark
exactly. The QRL null result is reported as-is — see the QRL analysis in
`src/qmems/README.md`.

**Score can exceed 100%.** The reference is the *discrete* optimum
(`SCORE_REFERENCE = "qubo_dp"`, matching the stage-3 benchmark), so a
continuous method beats it by the discretization gap. Set `SCORE_REFERENCE`
to `"anticipative"` in `build_cache.py` if you want everything in 0–100%.

## Deployment

Streamlit Community Cloud runs Streamlit only — it cannot host FastAPI. So:

| Component | Host | Config |
|---|---|---|
| API | Render / Fly / Railway | `render.yaml` or `Dockerfile` |
| Client | Streamlit Community Cloud | `API_BASE_URL` in secrets |

**Cold starts kill live demos.** Free API tiers sleep after ~15 minutes and
take 30–60 s to wake. The client therefore falls back to the committed
`cache/demo/` slice when the API does not answer within 2 s, and shows an
"offline mode" badge. The walkthrough survives a dead network entirely.

Hit `/api/v1/health` a few minutes before presenting.

## Reproducibility

Every run payload carries its seed and the literal command that regenerates
it:

```json
"reproducibility": {
  "seed": 0,
  "reproduce_cmd": "python -m qmems_cache.build_cache --days 10 --seed 0",
  "schema_version": "1.0.0"
}
```

`GET /api/v1/verify` re-checksums every cached file against the manifest, so
an auditor can prove the served numbers are the ones the build produced.

## Tests

```bash
make test
```

`tests/test_store.py` needs no web framework. `tests/test_api.py` skips
automatically if FastAPI is absent. CI runs `run_validation.py` and
`run_qubo_validation.py` first — nothing downstream matters if the MILP and
QUBO stop agreeing — then builds a cache from synthetic data and runs the
suite. The dataset is never committed.

## Live solving

Off by default. Enabling it on a public URL with D-Wave credentials attached
would let a stranger drain a free Leap quota, so hardware additionally
requires a non-zero `QMEMS_DWAVE_SUBMISSION_BUDGET`. Precompute hardware
results before a presentation; treat live QPU calls as a bonus, never a
dependency.

`_execute()` in `routers/jobs.py` raises `NotImplementedError` until you wire
`build_context()` to your dataset paths — deliberately, so it cannot half-work.
