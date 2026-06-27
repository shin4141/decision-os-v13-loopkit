# Repo Health Check and Archaeology Signal

## Observation

Old long-running AI-agent development repos can contain enough evidence for a V12/V13-style health check.

In this experiment, old MMAR-related repos were given to Codex in no-edit mode and reviewed through a V12/V13 lens.

The goal was not to repair or restart MMAR.

The goal was to see whether repo artifacts could reveal restartability, source-of-truth health, handoff quality, stale-state risk, and next-action safety.

## Experiment shape

Codex was asked to inspect evidence such as:

- README and docs
- recent commits
- branch state
- handoff or status files
- test, preview, and demo traces
- stale tests
- snapshot / tmp / debug artifacts
- repeated fixes
- forced reruns
- unresolved verdicts
- preview / public mismatch
- agent handoff failure traces

The requested output format was:

- Overall Signal: 🟢 / 🟡 / 🔴
- Short verdict
- Evidence
- Likely failure modes
- What should have been recorded earlier
- Safest next action today
- One-sentence public takeaway

## Result 1: YELLOW

One repo was judged as `🟡 YELLOW`.

The repo had durable process documentation, release ledgers, and protocols.

However, the current story was split across README, recent commits, tests, docs, branch state, stale contracts, and unclear accepted fixed points.

The verdict was:

```text
Records exist, but the current source of truth, accepted state, and next safe action are unclear. Reconstruction is required before safe continuation.
```

This indicates a repo that is not necessarily broken, but is not immediately restartable.

## Result 2: RED

Another long-running repo was judged as `🔴 RED`.

Codex summarized the situation as:

```text
There was an operating system, but the current handoff is broken.
```

Evidence included:

- current branch not aligned with expected mainline
- origin/main divergence
- stale contract checks quarantine
- conflicting public/current SHA across docs
- branch-specific preview / public acceptance
- multiple stale contract tests
- leftover `.env`, tmp files, snapshots, and smoke reports
- mixed active / stale / quarantined test-contract states
- split source of truth
- unclear next safe action

The safest next action was:

```text
reconstruct state first
```

## Key finding

More records do not automatically mean better restartability.

A repo can contain many docs, ledgers, protocols, mistakes, snapshots, and handoff traces, while still lacking a living source of truth.

When that happens, the repo becomes a maze of partial truths.

```text
Many records != restartable state
```

## Archaeology signal

A strong public takeaway from the experiment:

```text
Long AI-agent development needs a single living source of truth, because otherwise even good guardrails turn into archaeology.
```

Japanese framing:

```text
長期AI-agent開発には、生きた単一の正本が必要になる。
そうでなければ、どれだけ良いガードレールがあっても、最後は考古学になる。
```

## Failure modes observed

The health check surfaced failure modes such as:

- false completion
- missing handoff
- unclear source of truth
- unresolved verdict
- context drift
- stale assumptions
- repeated rerun
- preview / demo mismatch
- incomplete verification
- agent handoff failure
- unclear next action
- stale tests
- branch / public state mismatch
- artifact residue without accepted state

## Why YELLOW and RED matter

The experiment did not simply label old repos as unsafe.

It distinguished between:

```text
YELLOW:
records exist, but reconstruction is needed before continuation

RED:
source of truth, branch state, handoff, and next safe action are broken enough that continuation is unsafe
```

This suggests that V13 Health Check can read repo evidence and produce differentiated restartability signals.

## V13 interpretation

V13 is not only a next-loop slogan.

It can function as a repo health gate for long AI-agent development.

A V13 Health Check asks:

- What is the living source of truth?
- What is the accepted SHA or accepted state?
- Is the current branch safe?
- Are stale tests quarantined or still confusing the story?
- Are preview and public states aligned?
- Is the handoff fresh?
- What should the next AI/human not assume?
- What is the safest next action?
- Should this repo be `GO / HOLD / CAP / BLOCK`?

## Service connection

This evidence strengthens the practical case for AI Agent Handoff Audit.

The audit should not only inspect `CLAUDE.md` / `AGENTS.md`.

It can also inspect whether a repo has become:

- restartable
- source-of-truth aligned
- safe to continue
- or archaeological

Possible audit language:

```text
I can check whether your AI-agent repo is restartable, or whether the next AI will have to do archaeology before it can safely continue.
```

## Boundary

Do not repair MMAR now.

Do not restart MMAR development.

Do not rewrite README.

Do not modify services.

Do not create a public article now.

Do not add automation.

This note is evidence capture only.

## Status

Signal captured.

No MMAR repair.
No README change.
No service-page change.
No feature expansion.
