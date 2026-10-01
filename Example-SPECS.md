# QMEMS — Quantum Microgrid Energy Management System

## Overview

QMEMS is a hybrid quantum-classical microgrid energy-management research platform and interactive dashboard.

It is designed to compare classical optimization, rule-based control, reinforcement learning, quantum-inspired optimization, and quantum methods on the same microgrid dispatch problem under a common evaluation pipeline.

The platform focuses on transparent comparison rather than claims of generic quantum advantage. Results are evaluated with the same data, physical constraints, and economic metrics whenever possible.

## Developer and Research Context

**QMEMS is developed by Dr. Lilia Tightiz, Assistant Professor, Dept of Computer Engineering, Sejong University, Seoul, Republic of Korea.**

The project is part of a broader research direction in smart-grid optimization, microgrid energy management, reinforcement learning, quantum computing, and quantum machine learning for energy systems. QMEMS is intended as a public research and demonstration platform that connects these topics through a common microgrid-energy-management benchmark.

Research profile: [Google Scholar — Lilia Tightiz](https://scholar.google.com/citations?hl=en&user=6KPI75UAAAAJ&view_op=list_works&sortby=pubdate)

---

## Main Goals

QMEMS is intended to provide a reproducible environment for studying questions such as:

- How do classical and quantum-oriented approaches compare for microgrid battery dispatch?
- What is the cost difference between exact references and approximate methods?
- Are the produced schedules physically feasible?
- How do learning-based controllers compare with optimization-based controllers?
- When a quantum backend is used, what type of execution actually occurred?

The project keeps classical baselines available so quantum and quantum-inspired results can be interpreted against a clear reference.

---

## Microgrid Model

The current QMEMS demo represents a microgrid with:

- electrical load
- photovoltaic generation
- battery energy storage
- grid import and export
- time-varying electricity tariffs

At each time step, the controller determines how energy should flow between the load, PV generation, battery, and utility grid.

The optimization objective is based on electricity cost and may include a battery-throughput penalty.

The dispatch must respect the main physical constraints, including:

- energy balance
- battery state-of-charge limits
- charging and discharging limits
- battery efficiency
- import/export limits
- initial battery state

---

## Methods

QMEMS supports several method families through a common evaluation format.

### Classical baselines

- no-battery reference
- rule-based battery control
- MILP-based dispatch optimization

### Reinforcement learning

- tabular Q-learning
- experimental quantum reinforcement learning with a variational quantum circuit

### QUBO and quantum-oriented optimization

- exact discrete QUBO reference
- simulated annealing
- QAOA simulation on tractable problem instances
- optional hardware-backed execution through supported quantum services

Simulated annealing is treated as **quantum-inspired**, not as quantum-hardware execution.

---

## QUBO Path

QMEMS includes a QUBO representation of the battery-dispatch problem for quantum-oriented experiments.

The continuous dispatch problem is discretized into a finite state representation. The resulting QUBO can then be evaluated with exact classical references, heuristic solvers, simulators, or supported quantum backends.

The project compares QUBO solutions with classical references and reports the measured gap when an exact comparison is available.

Small problem instances are used for validation before larger experiments are attempted.

---

## Quantum Provenance

QMEMS distinguishes between different execution types so that dashboard labels do not overstate quantum use.

A result can be classified as:

- classical
- quantum-inspired
- quantum simulation
- hardware-backed quantum execution

A result is marked as hardware-backed only when the submitted problem is actually processed through a supported quantum-hardware path.

Where applicable, QMEMS records information such as backend type, formulation size, runtime metadata, and comparison with the available classical or exact reference.

---

## Data

QMEMS is designed around EMS-style time-series data.

Typical inputs include:

- timestamps
- site identifiers
- electrical consumption
- PV generation
- load forecasts
- PV forecasts
- battery parameters
- electricity buy/sell tariffs

A schema-compatible synthetic-data generator is included so the demo can be tested without requiring access to a private dataset.

---

## Architecture

QMEMS is separated into four main parts.

### Scientific core

Contains the microgrid environment, optimization models, QUBO formulation, reinforcement-learning components, feasibility checks, and validation utilities.

### Precomputation layer

Runs experiments offline and stores result artifacts for reproducible comparison.

### API layer

Provides read-only access to prepared benchmark results for the dashboard.

### Dashboard

Provides an interactive interface for method comparison, energy-flow visualization, dispatch inspection, cost analysis, and quantum-provenance reporting.

The dashboard is intended for research demonstration and analysis rather than autonomous real-world grid control.

---

## Dashboard Features

The public dashboard can present:

- site and day selection
- method comparison
- total operating cost
- savings relative to a baseline
- feasibility status
- battery state of charge
- load and PV profiles
- grid import/export
- battery charging/discharging
- cumulative cost through the day
- QUBO / quantum metadata
- backend and execution classification

Physical validity and economic performance are shown separately. A feasible result is not automatically an economically strong result.

---

## Evaluation

Methods are compared with a common set of metrics where applicable, including:

- total operating cost
- savings relative to the reference baseline
- optimality gap
- physical feasibility
- battery usage
- runtime
- quantum execution metadata

QMEMS is intended to preserve negative or null results rather than hiding them. This makes the repository useful as a research benchmark rather than only as a demonstration of favorable cases.

---

## Reproducibility

Generated experiments should preserve the information required to reproduce or audit a result, such as:

- random seed
- dataset/site/day identifiers
- method name
- solver or backend
- version information
- result metadata

Precomputed results can be stored with integrity information so the dashboard can be checked against the artifacts generated by the experimental pipeline.

---

## Running the Demo

The repository supports a lightweight demo workflow and a full development workflow.

Typical entry points include:

```bash
python INSTALL.py
python RUN_DEMO.py
```

A standalone dashboard may also be provided for viewing prepared results without requiring a live quantum service.

Exact installation steps and dependencies are documented in the repository README.

---

## Repository Structure

A typical public layout is:

```text
QGrid-EMS/
├── app/                    # dashboard assets
├── cache/                  # prepared benchmark results
├── docs/                   # documentation and figures
├── src/
│   ├── qmems/              # scientific core
│   ├── qmems_api/          # API service
│   └── qmems_cache/        # experiment/cache generation
├── tests/                  # validation and API tests
├── QMEMS_DASHBOARD.html
├── RUN_DEMO.py
├── README.md
├── Dockerfile
└── requirements*.txt
```

---

## Related Publications and References

The following selected publications by the developer provide research background for the smart-grid, microgrid, reinforcement-learning, and quantum-energy-management directions represented in QMEMS. They are listed as related research references and do not imply that every repository component is a direct implementation of a specific paper.

1. L. Tightiz, et al. **“Quantum-resilient blockchain and federated reinforcement learning for adaptive electricity pricing in South Korea,”** *Sustainable Energy, Grids and Networks*, vol. 46, 10232, 2026. https://doi.org/10.1016/j.segan.2026.102232

2. L. Tightiz, et al., **“A Review on a Data-Driven Microgrid Management System Integrating an Active Distribution Network: Challenges, Issues, and New Trends,”** *Energies*, vol. 15, no. 22, 8739, 2022. https://doi.org/10.3390/en15228739

3. L. Tightiz, et al. **“Novel deep deterministic policy gradient technique for automated micro-grid energy management in rural and islanded areas,”** *Alexandria Engineering Journal*, vol. 82, pp. 145–153, 2023. https://doi.org/10.1016/j.aej.2023.09.066

4. L. Tightiz, et al. **“Quantum Learning in Modern Power Systems: A Critical Appraisal of Current Evidence and Deployment Barriers,”** *Journal of Modern Power Systems and Clean Energy*, 2026. https://doi.org/10.35833/MPCE.2026.000496

5. L. Tightiz, et al. **“Energy-efficient quantum-spiking multi-agent reinforcement learning for adaptive energy management in microgrid networks,”** *International Journal of Electrical Power & Energy Systems*, vol. 179, 112020, 2026. https://doi.org/10.1016/j.ijepes.2026.112020

For the complete and most recent publication list, see the developer’s [Google Scholar profile](https://scholar.google.com/citations?hl=en&user=6KPI75UAAAAJ&view_op=list_works&sortby=pubdate).

---

## Security and Public Use

QMEMS is intended for research and demonstration use.

Do not commit sensitive information such as API keys, passwords, access tokens, private service URLs, confidential datasets, or organization-specific infrastructure details.

Credentials for external quantum services should be provided through environment variables or other secure local configuration mechanisms.

## Scope

QMEMS is a research platform for hybrid quantum-classical energy-management experiments.

It does not claim that quantum methods universally outperform classical optimization. Instead, it provides a structured way to compare methods under the same microgrid model and report both strengths and limitations.

Future public releases may extend the platform with additional datasets, controllers, quantum backends, and energy-management scenarios while preserving the same comparison and provenance principles.
