# CLAUDE.md — working rules for this repo

## Coding workflow (Renaud, 2026-09-23)

Supersedes the earlier "Claude plans, Cursor writes with `gpt-5.3-codex-high`"
rule. Applies to every Orientom-Inc and finance-quantum repo.

**Plan with Fable models**, and plan in **detail** — the plan is the deliverable
Fable is there for, not a sketch handed off half-finished.

**Review with Fable models.** Reviews are brutal and adversarial, not a rubber
stamp.

**Write the code by climbing this ladder in order.** The goal is to spend the
**Cursor token quotas** — that is the reason for the ordering, not a side effect
of it. Start at rung 1 and only go up when the task genuinely needs it.

| rung | who writes it | when |
|---|---|---|
| 1 | a **Cursor agent on the default Grok models** | simple, or very generic |
| 2 | a **Cursor agent on the Opus model** | more complex than rung 1 can carry |
| 3 | a **Claude agent / subagent on Claude Opus** | complex enough that rung 2 cannot carry it either, or Cursor is unavailable |

Rung 3 is the last resort, not the default: going straight to a Claude Opus
subagent for work a Cursor agent could do burns the wrong budget.

**Escalate on repeated bad output, and say that you did** (Renaud, 2026-09-23).
If the model at your current rung produces poor work repeatedly, stop
re-prompting it and move up a rung. Every switch is reported: which model, which
task, and what it was producing that triggered the move.

**Commit and push everywhere.** CI green before every commit. Save state to the
repo rather than leaving it in a conversation.

### Traps worth knowing before you conclude a model is unavailable

- **Cursor's usage cap is per-model, not account-wide.** Probe with
  `-p --force --trust`. Without those flags a workspace-trust prompt comes
  back looking exactly like a quota refusal — that false reading was reported
  twice on 2026-09-23. Measured that day: `grok-4.7-medium` and `composer-2.5`
  fine, `gpt-5.3-codex-high` refused until 10/4/2026. A single model being
  capped does not empty rung 1 or rung 2; probe the others before climbing.
- **`claude-fable-5-*` must never be used in Cursor** — flagged NO ZDR. Fable
  is for planning and review on the Claude side, not inside Cursor.
- **`aria-quantum-language-oss-public` is never pushed, fetched, rebased or
  synced.** Local commits only. Reading it is fine.
