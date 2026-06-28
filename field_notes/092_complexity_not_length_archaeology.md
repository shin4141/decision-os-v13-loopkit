# Complexity, Not Length, Turns AI Work into Archaeology

## Observation

Long AI-agent work does not become unsafe simply because it is long.

Length increases surface area, but length alone is not the root cause.

A long repo or long AI-agent development line can remain restartable if it has:

- a living source of truth
- fresh handoff
- accepted state / accepted SHA
- clear branch status
- stale vs active artifact labeling
- clear next safe action
- human-seat return when state is unclear

The deeper risk is when complexity grows faster than the repo's restartability structure.

## Core claim

```text
Length is not the root cause.
Complexity without restartability structure turns AI work into archaeology.
```

Japanese framing:

```text
AI作業を考古学にするのは、長さそのものではない。
複雑さに対して、正本・引き継ぎ・検証状態・次アクションが追いつかない時に考古学化する。
```

## Why this matters

A short workflow can be safe.

A long workflow can also be safe.

A short workflow can become unsafe if it hides unresolved complexity across many small fragments.

A long workflow can remain safe if its state remains aligned.

The practical question is not:

```text
Is this repo long?
```

The better question is:

```text
Is this repo's restartability structure strong enough for its current complexity?
```

## MMAR / V13 contrast

In prior health-check experiments, old MMAR-related repos produced `YELLOW` and `RED` signals.

The problem was not merely that the work was long.

The problem was that the current state had split:

- source of truth was unclear
- accepted state differed across docs
- branch state and public state diverged
- stale tests were quarantined
- active / stale / quarantined meanings were mixed
- old artifacts remained without clear status
- next safe action required reconstruction first

By contrast, V13 may be long and active, but can still remain closer to `GREEN` if:

- mainline state is clean
- handoff is current
- field notes are numbered and scoped
- done / not done / parked items are distinguishable
- Loop Library candidates are separated from accepted listings
- public posts, service notes, and internal ideas are not confused
- `CAP / HOLD / BLOCK` boundaries are preserved

This suggests that length is not the decisive factor.

Alignment is.

## Short-fragment archaeology

Short work is not automatically safe.

Complex projects can become archaeological through many small sessions if each session leaves behind only partial state.

Possible pattern:

```text
small task
small change
small unresolved assumption
small missing handoff
small stale artifact
small branch drift
```

Repeated enough times, this becomes a fragmented history.

The repo may not look long in any single chat, but the project state becomes expensive to reconstruct.

This is short-fragment archaeology.

## Complexity vs governance capacity

A useful diagnostic frame:

```text
Archaeology risk rises when:

project complexity
+ state split
+ time gap
+ artifact residue
+ stale assumptions

exceed:

living source of truth
+ handoff freshness
+ accepted-state clarity
+ verification labeling
+ next-action clarity
+ human-seat return
```

This is not a formal equation.

It is a diagnostic lens.

## Health Check implication

The AI Agent Workspace Health Check should not treat length alone as a warning sign.

It should inspect whether complexity is matched by restartability structure.

Useful questions:

- Is there one living source of truth?
- Is the accepted state clear?
- Is the current branch safe?
- Are stale tests labeled as stale?
- Are old artifacts clearly historical-only or parked?
- Is handoff fresh enough for the next AI?
- Is the next safe action obvious?
- Does the repo distinguish active, stale, parked, and superseded context?
- Does the AI know what it must not assume?
- Does uncertainty return to the human seat?

## Misdiagnosis to avoid

Do not classify a repo as unsafe merely because it is long.

Do not classify a repo as safe merely because each chat or task was short.

Do not assume short loops prevent drift.

Do not assume long documentation creates restartability.

The correct question is whether the current complexity has a matching control structure.

## One-sentence summary

Long AI-agent work becomes archaeology not because it is long, but because its complexity exceeds its living source of truth, handoff, verification, and restartability structure.

## Paper relevance

This insight may later belong in a V13 paper or article.

Possible future phrasing:

```text
In long-running AI-agent development, the failure boundary is not duration itself, but the mismatch between accumulated complexity and the system's capacity to preserve a living source of truth.
```

Do not write the paper now.

This field note only preserves the principle.

## Boundary

Do not modify README.

Do not modify the Health Check skill now.

Do not modify AGENTS.md / CLAUDE.md.

Do not create a new loop.

Do not submit to Loop Library.

Do not prepare a public post.

This note only records the diagnostic principle.

## Status

Signal captured.

No README change.
No skill change.
No public post.
No Loop Library submission.
