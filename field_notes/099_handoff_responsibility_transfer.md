# Handoff Responsibility Transfer

## Context

During V13 LoopKit operation, a handoff failure appeared around routine cleanup after a completed line.

The artifact state was clean enough to close.

The remaining issue was not missing information.

The issue was whether the receiving AI started with a clear understanding of what it now owned.

## Observed Failure

The failure pattern:

- a completion line already implies routine cleanup
- the executing AI can close the cleanup directly
- instead of converting the cleanup into execution-agent instructions, the handoff returns the burden to Shin
- the next chat starts with information, but not with clear ownership

This creates a false handoff.

Information moved, but responsibility did not.

Handoff is not complete until the receiving AI knows what it now owns.

Japanese framing:

```text
受け側AIが「自分が今なにを引き受けたか」を持って開始できなければ、引き継ぎは完了ではない。
```

## Root Layer

Root layer:

```text
V12 Completion Integrity / Handoff Responsibility Transfer
```

V12 completion integrity is not only whether the artifact can be restarted.

It also includes whether the remaining operational responsibility is transferred to the right actor.

If the next AI must ask Shin what to do with routine cleanup that the completion line already identifies, the handoff is incomplete.

## Responsibility Transfer Rule

Handoff is not only information movement.

It must transfer:

- current state
- accepted completion line
- remaining cleanup
- responsible actor
- next executable action
- stop condition

The receiving AI must know:

```text
This is what I now own.
This is what I should close.
This is what I must not expand.
This is when I should stop.
```

Never return operational cleanup to Shin when an execution agent can close it.

Japanese framing:

```text
実行AIが閉じられる後始末を、Shinに判断や操作として返してはいけない。
```

## Resource Justice Boundary

Resource Justice matters here because Shin's attention is a limited operational resource.

Returning routine cleanup to Shin creates unnecessary coordination cost.

It can make Shin:

- re-parse the completion line
- decide an already-decided cleanup step
- translate human intent back into agent instructions
- carry avoidable operational residue across chats

This is not good seat return.

Good seat return asks Shin for judgment only when judgment is actually required.

Routine execution-agent cleanup should be closed by the execution agent.

## Receiving AI Checklist

When receiving a handoff, the AI should check:

1. What did the previous line already complete?
2. What cleanup remains?
3. Can an execution agent close that cleanup without Shin's judgment?
4. What exact files, commands, or verification steps are in scope?
5. What surfaces must not be touched?
6. What would count as V12 PASS?
7. What is the V13 gate after closure?
8. What is the stop condition?

If the cleanup is routine and executable, the receiving AI should proceed.

If judgment, risk, exposure, money, credentials, release state, or external action is involved, the AI should return the seat to Shin.

## Correct Closure Pattern

Incorrect closure:

```text
The remaining cleanup is X. Shin, what do you want to do?
```

Correct closure:

```text
The remaining cleanup is X.
The execution AI can close it.
Do X only, verify Y, do not touch Z, then stop.
```

For Codex or another execution AI, convert routine cleanup into clear execution instructions, not commands returned to Shin.

Examples:

- commit and push an already-approved file
- verify a clean working tree
- confirm `main...origin/main`
- run `git diff --check`
- close the handoff after the agreed file is added

When the Completion Line already shows the cleanup, do not close with:

```text
What should we do?
```

Close with:

```text
Do the bounded cleanup and stop.
```

## Status

Signal captured.

No README change.
No AGENTS.md change.
No CLAUDE.md change.
No docs change.
No loop_skills change.
No external post.
No exposure candidate search.
No Loop Library submission.
