# CLAUDE.md — working rules for this repo

## Coding workflow (Renaud, 2026-09-23)

Supersedes the earlier "Claude plans, Cursor writes with `gpt-5.3-codex-high`"
rule. Applies to every Orientom-Inc and finance-quantum repo.

**Plan with Fable models**, when available.

**Review with Fable models**, when available. Reviews are brutal and
adversarial, not a rubber stamp.

**Write the code** with the model matched to the task:

| Task | Who writes it |
|---|---|
| simple, or very generic | a Cursor agent on the default Grok models |
| anything more complex | a **Claude Opus subagent** |

Renaud, later on 2026-09-23, revising the same day's first version: complex work
goes to a Claude Opus subagent, **not** to the Opus model inside Cursor. Cursor
keeps the simple and generic end of the range. This also settles the open
question of what replaces `gpt-5.3-codex-high` while it is quota-refused — for
simple work, the default Grok models; for anything else, Opus on the Claude side.

**Escalate on repeated bad output, and say that you did** (Renaud, 2026-09-23).
If a simpler model produces poor work repeatedly on a task, stop re-prompting it
and move the task to a better model. Do not treat the table above as a ceiling —
it is the starting point, not a constraint to defend. Every switch is reported:
which model, which task, and what it was producing that triggered the move.

**Commit and push everywhere.** CI green before every commit. Save state to the
repo rather than leaving it in a conversation.

### Traps worth knowing before you conclude a model is unavailable

- **Cursor's usage cap is per-model, not account-wide.** Probe with
  `-p --force --trust`. Without those flags a workspace-trust prompt comes
  back looking exactly like a quota refusal — that false reading was reported
  twice on 2026-09-23. Measured that day: `grok-4.7-medium` and `composer-2.5`
  fine, `gpt-5.3-codex-high` refused until 10/4/2026.
- **`claude-fable-5-*` must never be used in Cursor** — flagged NO ZDR. Fable
  is for planning and review on the Claude side, not inside Cursor.
- **`aria-quantum-language-oss-public` is never pushed, fetched, rebased or
  synced.** Local commits only. Reading it is fine.
