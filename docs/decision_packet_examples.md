# Decision Packet Examples

This file contains non-executing examples of Decision Packets.

A Decision Packet is not an alert.

It is a compressed choice surface that allows a human to decide quickly without losing the final Seat.

These examples are documentation only.

They do not trigger automation, Telegram, execution, push, deletion, release, or any external action.

## Example 001: Push or Review Once

### Context

Codex completed a documentation-only update.

Local `main` is ahead of `origin/main` by 1 commit.

The working tree is clean.

The change updates README and docs only.

No files were deleted.

No credentials, money, package setup, public promotion, or execution permissions are involved.

The question is:

> Should Codex push now or hold for one more review?

### Decision Packet

```text
Signal:
🟡 CAP / Human decision needed

Situation:
Codex completed a documentation-only update. Local main is ahead of origin/main by 1 commit.

Decision:
Choose A or B.

Option A:
Push now.

Pros:
- Public repo becomes restartable.
- Future agents can resume from GitHub.
- No useful state remains local-only.
- The change is documentation-only and reversible.

Cons:
- If the docs are wrong, the public repo may briefly mislead readers.

Option B:
Hold and review once.

Pros:
- Reduces public mismatch risk.
- Gives the operator one more chance to inspect the wording.

Cons:
- Delays the proof loop.
- Leaves useful state local-only.
- Adds review burden for a low-risk change.

Recommendation:
A

Confidence:
medium

Why:
The change is documentation-only, reversible, and V12 state is PASS. No deletion, credential, package setup, money movement, public promotion, or execution permission is involved.

Reply:
A / B / HOLD
```

### V12 State

PASS

The work is complete and restartable because:

* the changed files are known
* the working tree is clean
* the commit exists locally
* the next agent can inspect the diff and commit
* the public state will become restartable after push

### V13 State

CAP

The push is allowed under a narrow cap:

* push only the existing commit
* do not add new files
* do not broaden scope
* do not add features
* do not trigger public promotion

### Human Reply Contract

If the human replies:

```text
A
```

then Codex may push the existing commit and report the signal.

If the human replies:

```text
B
```

then Codex should stop and provide a short review summary.

If the human replies:

```text
HOLD
```

then Codex should stop without pushing.

### Why This Is Better Than an Alert

Bad alert:

```text
Local branch is ahead by 1 commit.
```

This tells the human something changed, but does not reduce the decision burden.

Better Decision Packet:

```text
A: Push now
B: Hold and review once
Recommendation: A
Reply: A / B / HOLD
```

The Decision Packet compresses the decision while keeping the final Seat with the human.

## Boundary

This example is non-executing.

It does not implement Telegram.

It does not implement a bot.

It does not give Codex autonomous permission.

For irreversible, high-impact, public, financial, deletion, credential, or authority-changing actions, explicit human confirmation remains required.

## One-Line Lesson

A useful notification should not merely report state.

It should compress the next valid decision.
