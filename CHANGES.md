# Changes — RL/QRL confound investigation

Everything below was measured on this machine (Windows, Python 3.12.10, 8 cores).
`src/qmems/` — the validated science — is **unchanged** except for one restored
file. All edits are in `src/qmems_cache/` (the harness) and `app/` (the demo).

---

## The headline result

The published benchmark reported **tabular RL 68.1% vs QRL 0.0%** and attributed
the null to the quantum function approximator. That comparison was not
like-for-like.

The two agents were trained with **different discount factors and different
episode budgets**, and both differences are visible in the source you supplied:

| | file:line | gamma | episodes |
|---|---|---|---|
| Tabular Q | `bench_step.py:77-78`, `evaluate.py:156` | 0.99 | 8000 |
| VQC-DQN | `bench_step.py:31,50`, `evaluate.py:161` | 0.95 | 200–300 |

Rerunning the **classical** tabular agent across that 2×2 (3 seeds, one dataset
build per process):

| gamma | episodes | | held-out score | charge |
|---|---|---|---|---|
| 0.99 | 8000 | baseline config | **68.1% ± 5.8%** | 8% |
| 0.99 | 200 | VQC's budget only | 5.1% ± 7.1% | 0% |
| 0.95 | 8000 | VQC's discount only | 30.3% ± 0.0% | 3% |
| 0.95 | 200 | **the VQC's config, exactly** | **0.0% ± 0.0%** | **0%** |

**A 1296-entry classical lookup table, given the VQC's discount and budget,
collapses to exactly 0.0% with zero charge actions — the identical failure.**

Episode budget is the dominant factor (68.1 → 5.1); the discount is a strong
secondary (68.1 → 30.3); both together reach zero. The conclusion is that the
0% is a property of the **RL configuration**, not evidence about quantum
function approximation.

This is consistent with the brief: M4 names *"3–10k episodes"* as the target,
so 200–300 was always far short of what the method needs.

### Why reward scaling was guaranteed to fail

Charging one SoC level draws `20/0.95 = 21.053 kWh` at off-peak `0.1320`
(2.7789 EUR); discharging returns `20 × 0.95 = 19.0 kWh` at peak `0.1789`
(3.3991 EUR — which equals `max_action_gap_eur` in the artifact exactly). The
discounted break-even is `gamma^k = 2.7789/3.3991 = 0.8175`:

| discount | break-even lag |
|---|---|
| 0.95 (the VQC) | 3.93 h |
| 0.99 (the baseline) | 20.04 h |
| 0.95 + ×3 tariff spike | 19.58 h |

Off-peak-to-peak is an overnight gap, so at 3.93 h charging is genuinely
negative-value under the VQC's own objective. Reward scaling multiplies **both**
sides, leaving the break-even exactly invariant — the ×5/×15 runs could not have
worked. It also shows the ×3 tariff variant and a discount change are nearly the
same intervention (19.58 h vs 20.04 h), except one modifies the problem.

### What correcting the confound did *not* do

Fixing the discount and raising the budget did **not** rescue the VQC:

| VQC run | held-out score | charge | CPU |
|---|---|---|---|
| γ=0.99, 200 episodes | −4.2% ± 5.9% | 0% | ~8 min/seed |
| γ=0.99, **1,000 episodes** | **−2.2% ± 3.1%** | 0% | ~30 min/seed |

So the confound is **necessary but not sufficient** to explain the null. A
classical table reproduces the 0% exactly under the VQC's settings — but
correcting the discount and quintupling the budget still leaves the VQC at zero,
while the table reaches 5.1% on only 200 episodes.

**The budgets are still not matched.** The table needed 8,000 episodes to reach
68.1%; the VQC has had at most 1,000. Closing that gap on CPU is ~4 h per seed,
which is exactly why the brief's M4 routes 3–10k episodes through the GPU port
with adjoint gradients.

The honest claim is therefore narrower than "QRL works": the headline
68.1%-vs-0% was confounded and is not by itself evidence about quantum function
approximation — **and** it does not follow that the VQC would match the table at
equal budget. That remains untested.

---

## Bugs found and fixed

| what | where | effect |
|---|---|---|
| Per-day cost divided by **SoC levels (6)** instead of **test days (3)** | `evaluate.py` | every per-day figure was halved; "56 EUR day" was really **112.14 EUR** |
| `merge()` globbed `seed_*.json` | `evaluate.py` | would average variant runs into the headline mean — three experiments in one number. Now filtered to untagged baseline seeds |
| Variant tag omitted the QRL episode budget | `evaluate.py` | two runs differing only in budget wrote the same filename and silently overwrote |
| **`bench_step.py` was missing entirely** | `src/qmems/` | `fqi_step.py:28` could not import, yet `README.md:92` reported an FQI result. Restored from your zip — it imports now |
| `"it never charge"` | `app/dashboard.html` | grammar |
| Default day was the **highest-headroom** day | `app/dashboard.html` | that is a **training** day and the single worst day for RL (11.2%). Now defaults to the highest-headroom **held-out** day — RL shows 40.8%, badge reads "held-out day" |

### A trap worth knowing about

`synthetic_emsx.py:19` holds a module-level `RNG = np.random.default_rng(42)`
that **every** `write_synthetic_site()` call advances. Looping seeds in one
process silently trains each seed on a **different dataset**. This is pitfall 6
in the brief; it cost one wrong ablation before it was caught (seed 0 matched
the committed baseline, seeds 1–2 did not). Every result here uses **one seed
per process**.

---

## Verification on this machine

- `run_validation.py` → `all_ok: True`, residuals ~1e-16, 187.48 EUR optimal vs
  200.06 dummy. **Ran on `pyomo+highs`** — the real MILP backend, exercised here
  for the first time.
- `run_qubo_validation.py` → `PASS`. Brute force == DP at 18 qubits; SA == DP at
  144 qubits, 0.000% gap; MILP continuous == QUBO discrete.
- Baseline scores reproduce **exactly**: rule-based 17.4%, tabular 68.1% ± 5.8%
  (60.6 / 69.0 / 74.8), QRL 0.0%.

---

## New / changed commands

```bash
# gamma and budget are now explicit and recorded in every artifact
python -m qmems_cache.evaluate --seed 0 --qrl-gamma 0.99 --qrl-episodes 1000
python -m qmems_cache.evaluate --seed 0 --tabular-gamma 0.95 --tabular-episodes 200
python -m qmems_cache.evaluate --merge          # baseline seeds only

python scripts/build_standalone.py              # rebuild QMEMS_DASHBOARD.html
```

Every seed artifact now carries a `gamma` block, so no score can be read without
the discount that produced it.

---

## Still open

- **The matched-budget run has not been done.** The decisive experiment is the
  VQC at **8,000 episodes**, γ=0.99 — the table's exact configuration. On CPU
  that is ~4 h per seed (~12 h for 3 seeds, parallelised). Until it exists,
  "the VQC fails because of its budget" is a hypothesis supported by the 2×2 on
  the classical agent, not a measured result for the quantum one. This is the
  single highest-value remaining experiment and it is what M4's GPU port is for.
- **QAOA has never run.** `qaoa_slice.py:116` computes `nq = 6 × 6 = 36` qubits
  → 2^36 amplitudes → **~1 TiB** for one statevector. Not a sandbox limit — it
  cannot run anywhere. Runnable sizes are **18 qubits** (T=3 at 6 levels, or T=6
  at 3 levels). Also `slice_qubo()` at line 42 is `return full  # placeholder
  replaced below` — nothing replaces it and nothing calls it, so the Hamiltonian
  is a masked sub-block, and the penalty is derived from the full 24-hour cost
  range (~4× too large for a 6-step slice).
- **`fqi_step.py` now imports but has not been run**, so the FQI line in
  `src/qmems/README.md:92` is still unverified.
