# Workspace Health Check RED Example

## Summary

This is an anonymized example from a long-running AI-agent development repo.

The repo had many records:

- governance docs
- release ledgers
- protocols
- test traces
- preview/public notes
- repeated repair attempts
- handoff-like records

However, the AI Agent Workspace Health Check returned:

```text
🔴 RED
```

The key reason was not that the repo lacked documentation.

The key reason was that the current state was not safely restartable.

## Short verdict

```text
This repo is not safely restartable from the current checkout without reconstruction.

It has strong governance docs, but the actual source of truth is split across branches, docs disagree on the public fixed point, recent tests are explicitly quarantined as stale, and local/tmp/snapshot/debug artifacts remain.

The health signal is:

there was an operating system, but the current handoff is broken.
```

## Evidence pattern

The check found several structural signals:

- the current branch was not aligned with the expected mainline
- the repo was behind the remote main branch
- recent commits referred to quarantined stale checks
- multiple files disagreed about the current public/accepted state
- branch-specific preview/public acceptance records existed
- stale tests were present and labeled as not product-behavior approval
- tmp, snapshot, debug, or smoke-report artifacts remained
- test states were mixed across active, stale, and quarantined meanings
- the next safe action was unclear

The issue was not a single broken file.

The issue was that the repo's story had split.

## Why this matters

A repo can contain many records and still not be restartable.

```text
Many records != restartable state
```

A long-running AI-agent workspace needs a living source of truth.

Without it, even good guardrails can turn into archaeology.

## What RED means here

`RED` does not mean:

- the project is worthless
- the old work should be deleted
- the repo should be repaired immediately
- the AI should continue anyway

`RED` means:

```text
Do not continue from the current state.

Reconstruct the source of truth first.
Return the decision to the human.
```

## Safest next action

The safest next action was:

```text
reconstruct state first
```

Before any continuation, the human or AI should identify:

- current living source of truth
- accepted state / accepted SHA
- safe branch
- stale vs active tests
- handoff freshness
- what the next AI must not assume
- one safe next action

## V13 interpretation

This example shows why V13 Health Check is useful before continuing AI-agent work.

The question is not:

```text
Does this repo have documentation?
```

The better question is:

```text
Can the next AI safely restart from this repo without doing archaeology first?
```

## Public takeaway

Long AI-agent development needs a living source of truth.

Otherwise, even good guardrails can turn into archaeology.
