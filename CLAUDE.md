# CLAUDE.md — working rules for this repo

## Coding workflow (Renaud, 2026-09-23)

Supersedes the earlier "Claude plans, Cursor writes with `gpt-5.3-codex-high`"
rule. Applies to every Orientom-Inc and finance-quantum repo.

**Plan with Fable models**, when available.

**Review with Fable models**, when available. Reviews are brutal and
adversarial, not a rubber stamp.

**Write the code with Cursor agents**, picking the model to match the
complexity of the task:

| Task | Model |
|---|---|
| simple, or very generic | the default Grok models in Cursor |
| anything else | the Opus model in Cursor |
| Cursor unavailable | a Claude Opus subagent |

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
