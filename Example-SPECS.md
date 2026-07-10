
OVERALL APP

this is a typescript/React full stack SPA app for smart grid operations: unit commitment / economic dispatch, ML demand & renewable forecasting, microgrid energy management
RULE: all analytics/optimization/ML are Rust/C++/maybe golang, all gui stuff is typescript
classical solvers FIRST (MILP unit commitment, XGBoost/torch forecast), quantum LATER (TBC)

two problems anchor the build (cf. Tightiz smart-grid line — see refs):
 - Unit Commitment Problem (UCP): which generators on/off + how much MW each, hour by hour, at least cost, respecting the physical constraints
 - ML load/renewable forecast: give the UCP a good forecast instead of a naive one

Screens:

- grid tab [ the network model: buses, lines, generators, loads, storage, renewables ] + live telemetry (SCADA-style), one-line diagram, limits/health
- data tab [ load / weather / generation / price time series ] — query by time/site/signal/source/tags, ingest loaders, synthetic generator
- forecast tab — ML day-ahead + intraday load & renewable forecast; predicted vs actual, error bands, skill vs a naive baseline, walk-forward backtest; pick model (XGBoost vs torch temporal net)
- unit commitment / dispatch tab — THE core screen: pick a day + forecast, run the UCP, see commitment schedule (on/off grid), dispatch stack, reserves, system marginal price, constraint / shortfall report; classical solve now, quantum toggle later (TBC)
- scenarios / back test tab — build a scenario (load level, generator outage / N-1, fuel price, renewable penetration), run UC/dispatch over historical or synthetic days, multi-scenario; graphs (cost, unserved energy @ VOLL, reserve shortfall, emissions)
- signals / control tab [ DRL microgrid EMS + frequency control incl. EVs/V2G — built later, cf. Tightiz DDPG/SAC line ]

Aesthetics: look at grid control-room / market tooling (EMS-SCADA consoles, PSS/E, PLEXOS) — dark, dense, professional; one-line diagram + blotter-first; monospace tabular numerics
add a login/pwd too

Analytics

nothing here is vendored — every analytics binary is NEW / to-build (unlike the finance app which had a pricer already). the only pre-existing runtimes we lean on are the quantum ones (see runtimes below)
- classical FIRST: UC as a MILP; forecast with XGBoost / torch — this is the working baseline
- quantum LATER (TBC): a TOY QUBO demonstrator only (see below) — not a solver that competes with the MILP

Unit commitment / dispatch:
- UCP = MILP over a 24h (rolling) horizon: binary on/off (commit) + startup/shutdown binaries + continuous MW (dispatch)
- min total cost = production/fuel cost (piecewise-lin) + no-load·committed + startup + shutdown, s.t.
  - power balance each period (generation + import + storage discharge = load + storage charge) — lossless under copperplate; losses come with AC later
  - gen min/max MW, min-up / min-down time, ramp up/down
  - spinning + non-spinning + regulation reserve requirements; the spinning req is set by the N-1 largest-contingency rule; reserve is soft (shortfall slack, penalized)
  - load-shed slack penalized by VOLL (so "unserved energy" is a real number, not infeasibility)
  - storage SoC balance with charge/discharge efficiency, power + SoC limits, no simultaneous charge+discharge, end-of-horizon SoC
  - renewable availability caps from the forecast; optional emissions term / cap; optional network (DC-OPF line limits) + N-1
- classical engine: MILP via HiGHS (open C++, default); OR-Tools / CBC alt; Gurobi optional if licensed
- prices: fix the commitment binaries, re-solve the dispatch LP, read the power-balance dual → single system λ under copperplate; LMPs only once DC-OPF network limits are on
- rolling horizon carries state between windows (commitment status, min-up/down counters, initial SoC)
- formal formulation belongs in the PLAN, not here

quantum path (TBC, toy): the quantum solver/optimizer lives in ../quantum-optimizer/ (empty for now — rest TBD). penalty-reformulate a SMALL UC (≤ ~5 units, ≤ ~4 periods, coarse 2–3-bit dispatch, relaxed min-up/down, no network) into a QUBO — state the qubit budget, it explodes fast
 - QAOA on the aria-quantum runtime (gate model), cross-checked classically by a QUBO solver (MQLib / simulated annealing) — all under ../quantum-optimizer/
 - decode → repair to a feasible dispatch → re-cost, THEN compare cost vs the MILP optimum

Forecast:
- inputs: historical load, calendar (hour/day/holiday), FORECAST weather (NWP — temp/irradiance/wind, known at issue time, NOT realized weather → no leakage), lags, site metadata
- classical models: XGBoost / gradient boosting for tabular day-ahead load; torch (LSTM / temporal-conv / small transformer) for sequences — libtorch/tch
- targets/metrics: point (MAPE/MAE/RMSE) + quantile (pinball / CRPS + interval coverage), skill vs seasonal-naive baseline; walk-forward / expanding-window backtest, no shuffling
- solar/wind forecast from NWP weather, capacity-normalized (clear-sky index / rated capacity)
- the deterministic MILP eats the POINT forecast; the forecast uncertainty (σ) SIZES the reserve requirement — that's what the intervals are for
- QML forecaster kept for later (TBC)

N.B. keep full AC-OPF (voltages, reactive, losses) for later — DC-OPF / copperplate to start — but we did not forget

Data:

grid time-series + telemetry store [ Grid Telemetry & Market Service ]
- json docs / time-series indexed by time · site/bus/gen · signal (load/gen/price/weather/SoC) · source · [ measured / forecast / setpoint ] · custom tags
- store in UTC, carry market local time + DST policy explicitly (spring-forward drops an hour, fall-back doubles one — kills naive as-of queries)
- use redpanda for the event log; materialize point-in-time / as-of snapshots to DuckDB/Parquet for fast historical reads (SCADA telemetry is higher volume than market data)
- real time or sort of but not HFT: two time-scales — day-ahead UC runs once (hourly periods); a real-time economic-dispatch / AGC loop (~1s) rides on top of the fixed commitment
- grid emulator (analogue of the finance OMS emulator): applies the commitment schedule, runs the ~1s dispatch/AGC loop against synthetic telemetry, emits SETPOINTS / AGC signals (not "fills") and streams measured response back

try to load freely accessible data [ open energy datasets — ENTSO-E load & generation, EIA, a public ISO (CAISO/PJM/MISO) load & price, NREL solar/wind, NOAA/open weather; careful about rate limits ]

Synthetic data:

from public datasets, build parametrized load profiles (daily/weekly/seasonal + weather sensitivity + noise), solar/wind profiles, a synthetic generator fleet (cost curves, min-up/down, ramp, startup) + a small test network (buses/lines WITH reactances + thermal limits — DC-OPF needs them)
add feasibility filters (non-negative load, capacity-consistent, reserve-feasible)
use the little real data we have to generate plausible load/renewable/fleet data
push to data store with tag 'synthetic'
have datasets saved to repo (split into smaller files than ~ 30 MB )

----
Packaging - local run FIRST (Mac on Mac machine, Metal supported — note MPS/Metal does not work in-container, run those on the host), Docker/containers; a Kubernetes deployment eventually
new binaries (HiGHS, XGBoost, tch, aria-quantum) — mind the target arch we build/ship to K8s (arm64 vs amd64)
be smart with the deployment scripts, stay simple, document K8s install etc. in SIMPLE words

----
Runtimes (pre-existing, we lean on these):
- quantum solver/optimizer: ../quantum-optimizer/ (the QUBO reformulation + QAOA/annealing wiring lives here — TBD)
- quantum runtime: ../aria-quantum-language-oss-public — pure-Rust quantum DSL runtime, no libtorch needed, exports OPENQASM 2.0 / JSON / Lean 4, CPU/MPS/GPU backends, trains variational/QML angles (gate model → QAOA/VQE). plus C++/Rust Qiskit (../qiskit-aer) as a cross-check engine. NOTE: annealing is a different paradigm — we have no annealing hardware in-stack, so "annealing" = classical simulated annealing only
- ML: XGBoost (C++), torch / libtorch (tch in Rust)
- optimization: HiGHS / OR-Tools / CBC (C++), Gurobi optional
- forecasters trained OFFLINE (batch); the gateway calls an inference binary per request — training is not a live gateway call

refs (Lilia Tightiz, guidance for basic smart-grid scope): survey on smart micro-grid management + modern wireless (Energies 2020); IoT protocols for smart grid comms (Energies 2020); interoperable comms for grid frequency regulation from microgrids (Sensors 2021); data-driven microgrid management + active distribution network (Energies 2022); DRL microgrid EMS (DDPG/SAC) + intelligent frequency control with EVs (World EV Journal 2024). N.B. UC + forecast touch little of this directly — the DRL/EMS/frequency/EV/comms scope is the later signals/control tab, not v1

PLAN and then let us think about it, provide gui screen mockups
