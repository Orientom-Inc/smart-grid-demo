# CLAUDE.md — working rules for this repo

## Coding workflow (Renaud, 2026-09-23)

Supersedes the earlier "Claude plans, Cursor writes with `gpt-5.3-codex-high`"
rule. Applies to every Orientom-Inc and finance-quantum repo.

### The ladder — in Renaud's own words

> this is a fucking ladder
> `[ grok model/cursor  >>  opus model/cursor  >>  claude agent with latest opus model ]`

**Climb it in order. Start at rung 1. Go up only when the rung you are on
genuinely cannot carry the task.**

| rung | who writes the code | when |
|---|---|---|
| 1 | **Cursor agent, default Grok models** | simple, or very generic |
| 2 | **Cursor agent, Opus model** | more complex than rung 1 can carry |
| 3 | **Claude agent / subagent, latest Claude Opus** | rung 2 cannot carry it either, or Cursor is genuinely unavailable |

**Why the order is what it is: to spend the Cursor token quotas.** That is the
purpose of the ladder, not a side effect. Rung 3 spends the expensive budget, so
it is the last resort.

**The misreading to avoid — it has already happened twice.** "Complex work goes
to a Claude Opus subagent" is **wrong**. Complexity moves you to **rung 2, the
Opus model inside Cursor**, and only a task rung 2 has actually failed to carry
reaches rung 3. Skipping rung 2 burns the wrong budget, which is the one thing
this rule exists to prevent.

**Plan with Fable models, and plan in detail** — the plan is the deliverable
Fable is there for, not a sketch handed off half-finished.

**Review with Fable models.** Brutal and adversarial, not a rubber stamp.

**Escalate on repeated bad output, and say that you did.** If the model at your
current rung produces poor work repeatedly, stop re-prompting it and move up a
rung. Report every switch: which model, which task, and what it was producing
that triggered the move.

**Commit and push everywhere.** CI green before every commit. Save state to the
repo rather than leaving it in a conversation.

### Traps worth knowing before you conclude a rung is unavailable

- **Cursor's usage cap is per-model, not account-wide.** Probe with
  `-p --force --trust`. Without those flags a workspace-trust prompt comes back
  looking exactly like a quota refusal — that false reading was reported twice
  on 2026-09-23. A single capped model does not empty a rung; probe the others
  before climbing.
- **Measured 2026-09-23:** `grok-4.7-medium` and `composer-2.5` answer fine, so
  rung 1 is healthy. `gpt-5.3-codex-high` **and** `claude-opus-5-thinking-high`
  are both refused until **10/4/2026** — so for that window rung 2 is capped and
  complex work falls through to rung 3 *by the ladder's own terms*. Re-probe
  after 10/4 rather than assuming rung 2 is still dead; a cap expiring silently
  restores it.
- **`claude-fable-5-*` must never be used in Cursor** — flagged NO ZDR. Fable is
  for planning and review on the Claude side, not inside Cursor.
- **`aria-quantum-language-oss-public` is never pushed, fetched, rebased or
  synced.** Local commits only. Reading it is fine.
