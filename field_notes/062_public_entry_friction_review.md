# Field Note 062: Public Entry Friction Review

Date: 2026-06-15

## Purpose

This note reviews the current public entry surface from two reader routes:

1. constrained user route
2. powerful-agent user route

The review checks whether the current repository entry path communicates the pain, first action, and benefit without requiring internal field notes.

This is an evidence note only.

It does not rewrite public copy.

It does not promote anything to canonical instructions.

## Scope

Reviewed public entry surface:

- `README.md`

Supporting internal anchors used only to frame the review:

- `field_notes/045_two_entry_pains_token_cost_and_damage_risk.md`
- `field_notes/046_entry_pain_routing_check.md`
- `field_notes/061_v13_loop_close_and_restart_handoff.md`

This review does not reopen Lane Recall / Transfer Packet.

## Current Entry Surface Summary

The current README opens with:

- completion and loop cost
- bad completion causing future AI context recovery
- bad handoff causing stronger models to do cleanup
- bad loops burning cost
- a no-install Lite Footer
- V12 completion check
- V13 next-loop gate
- `CAP` as protection against scope creep

It then gives:

- a first action: try the Lite Footer
- a choose-one path for `AGENTS.md`, `CLAUDE.md`, one-off prompt, or roadmap anchors
- before/after examples
- gate outcomes
- practical use paths
- current prototype status and current signal

## Route 1: Constrained User

### Reader Pain

The reader feels:

- limited prompts
- time spent retrying
- token or message budget pressure
- cost from unclear next loops
- frustration when the agent spends another turn recovering context

Pain statement:

```text
AI is wasting my limited prompts, time, or money.
```

### What The Current Entry Surface Communicates

The README directly communicates that:

- bad loops burn cost
- bad completion makes future AI spend tokens recovering context
- V13 is no-install
- the Lite Footer is the first low-cost action
- `CAP`, `HOLD`, and `BLOCK` can prevent unnecessary continuation

The cost route is visible early because the first screen includes:

```text
Good completion reduces future AI cost.
Good loops reduce lifetime AI cost.
```

### What The Reader Likely Understands Within 60 Seconds

The reader likely understands:

- this is a copy-paste kit, not an app to install
- it helps decide whether another AI loop should run
- the first action is to ask the agent to append the Lite Footer
- `CAP` means continue only within limits
- the benefit is fewer wasteful follow-up loops

### What The Reader Likely Does Not Understand

The reader may not yet understand:

- how much cost this saves in practice
- whether the footer will feel natural in their own tool
- whether the one-off prompt is enough or `AGENTS.md` is better
- how to judge a borderline case without reading more docs
- whether this is mainly for coding agents or also useful for ordinary chat usage

### Whether The First Action Is Clear

First action:

```text
Try the Lite Footer.
```

Assessment:

```text
clear
```

The README names the footer, gives the copyable format, and says the user can copy `AGENTS.md` later if useful.

### Whether The Benefit Is Clear

Benefit:

```text
reduce unnecessary AI loops and context-recovery cost
```

Assessment:

```text
mostly clear
```

The cost benefit is visible, but it is not proven by real reader behavior or usage evidence.

### Whether The Route Requires Internal Field Notes To Understand

Assessment:

```text
no
```

The constrained-user route does not require field notes for basic understanding. Internal field notes sharpen the route, but the public entry surface already communicates the cost-pressure path.

### Friction Points

Friction points:

- The README explains the mechanism better than it proves the savings.
- A reader may understand the Lite Footer but not know which first task to test it on.
- The phrase "AI coding sessions" may make non-coding constrained users uncertain whether the kit applies to them.
- The Quick Links section may feel large after the first action.

### Gate Tendency

Gate tendency:

```text
CAP
```

Reason:

The entry route is understandable enough to keep using the current README, but public value is not proven by real user evidence.

### Recommended Next 0.01, If Any

Recommended next 0.01:

```text
No README edit yet. If future real reader evidence shows confusion, consider one bounded README edit that names a first test task for constrained users.
```

## Route 2: Powerful-Agent User

### Reader Pain

The reader feels:

- a strong agent may over-implement
- the touch surface may broaden without approval
- tests may be weakened or moved around
- dependencies or environment assumptions may drift
- the repo may become polished but wrong
- owner intent may be damaged by continuation momentum

Pain statement:

```text
AI may over-edit, broaden touch surface, weaken tests, or damage my repo.
```

### What The Current Entry Surface Communicates

The README communicates that:

- `CAP` prevents small finished tasks from expanding into expensive scope creep
- V12 checks whether work is complete and restartable
- V13 checks whether the next loop should run, pause, limit, or stop
- the agent must report allowed and not-allowed next actions
- prototype status pauses feature growth and caps public exposure

The powerful-agent route is present, but less explicit than the cost route.

### What The Reader Likely Understands Within 60 Seconds

The reader likely understands:

- this tool can stop "done" from turning into uncontrolled follow-up work
- `CAP` is the main protection against scope expansion
- the Lite Footer forces the agent to name boundaries
- `AGENTS.md` is the ongoing-project path for coding agents
- the examples include "Not Allowed" boundaries

### What The Reader Likely Does Not Understand

The reader may not yet understand:

- that touch-surface classification is a central damage-control concern
- that tests, dependencies, and measuring instruments should be protected surfaces
- how V13 handles broad edit risk before implementation starts
- whether this is strong enough for high-power Codex / Claude Code repo work
- how to apply the gate before an agent starts an execution loop

### Whether The First Action Is Clear

First action:

```text
Try the Lite Footer, or use `AGENTS.md` for an ongoing coding-agent project.
```

Assessment:

```text
clear enough
```

The README gives a clear action, but the powerful-agent reader may skip the Lite Footer and need stronger confidence that `AGENTS.md` protects repo surfaces.

### Whether The Benefit Is Clear

Benefit:

```text
limit continuation momentum before it becomes damaging scope creep
```

Assessment:

```text
partly clear
```

The scope-creep benefit is clear. The deeper repo-damage benefit is only partially visible because the README does not foreground tests, touch surfaces, dependency drift, or measuring-instrument protection.

### Whether The Route Requires Internal Field Notes To Understand

Assessment:

```text
partly
```

The reader can understand basic scope control from the README. To understand the fuller powerful-agent route, especially touch-surface and damage-risk framing, the reader benefits from internal field notes or `AGENTS.md`.

### Friction Points

Friction points:

- The damage-risk route is less direct than the cost route.
- "Scope creep" is visible, but "repo damage" is not yet strongly named on the public entry surface.
- The README does not quickly show an example where V13 prevents broad edits, test weakening, or dependency drift.
- Powerful-agent users may need evidence that this works before trusting it in a real repo.

### Gate Tendency

Gate tendency:

```text
CAP
```

Reason:

There is a concrete exposed gap candidate for powerful-agent readers: the README does not make the damage-risk route as explicit as the cost route. However, no real reader has yet shown that this gap blocks adoption.

### Recommended Next 0.01, If Any

Recommended next 0.01:

```text
If a future README edit is authorized, consider exactly one bounded public-entry edit that names the powerful-agent damage route without expanding the document: for example, one sentence or one compact example about preventing broad edits, test weakening, dependency drift, or repo damage.
```

This is a candidate only.

It is not authorization to edit README now.

## Public Value Status

Public value status:

```text
still unproven
```

Reason:

The current entry surface is understandable in a read-only review, especially for the constrained-user route, but this is not real user evidence.

Understanding by internal review does not prove:

- adoption value
- star-worthiness
- conversion value
- sustained usage
- revenue relevance

## README / Public Edit Justification

README/public edits justified yet:

```text
not yet
```

Reason:

The review found one concrete candidate gap for the powerful-agent route, but not enough evidence to justify public copy changes immediately.

The correct state is:

```text
CAP or HOLD
```

Do not rewrite public copy from internal clarity alone.

## Concrete Exposed Gap

Concrete exposed gap:

```text
possible but not yet proven by real reader evidence
```

Candidate gap:

```text
The powerful-agent damage-risk route is less explicit than the constrained-user cost route.
```

Bounded future edit candidate:

```text
Add one compact README sentence or example that names damage-risk protection for powerful-agent repo work.
```

This candidate should not run unless Shin explicitly authorizes a README/public-entry edit.

## Future Direction

Review outcome:

```text
HOLD public edits unless real reader evidence appears or Shin explicitly authorizes one bounded README edit candidate.
```

The review should not lead directly to a README change.

The review may be used later as evidence if a real reader, adoption attempt, or owner decision exposes the same powerful-agent route gap.

## What Must Not Happen Next

Do not:

- edit README from this note alone
- rewrite public copy
- start outreach
- claim public readiness
- promote this review to AGENTS.md
- promote this review to AGENTS.ja.md
- modify `CLAUDE.md`
- modify docs, schema, examples, prompts, or `USE_CASES`
- modify public release state
- modify external repos
- reopen Lane Recall / Transfer Packet without a real trigger
- implement automation, hooks, MCP, pluginization, package setup, server setup, or CLI surfaces
- turn the bounded edit candidate into an active TODO

## Final Status

Final status:

```text
evidence note only / public edits held / one possible future bounded edit candidate
```

The current public entry surface is:

- understandable for the constrained-user cost route
- understandable but less explicit for the powerful-agent damage-risk route
- not proven by real users
- not ready for public-readiness claims
- not authorization for README edits

## Boundary

This note only records a bounded public-entry friction review.

Do not modify `README.md`.

Do not modify `AGENTS.md`.

Do not modify `AGENTS.ja.md`.

Do not modify `CLAUDE.md`.

Do not modify docs, schema, examples, prompts, or `USE_CASES`.

Do not modify public/release state.

Do not modify external repos.

Do not implement automation, hooks, MCP, pluginization, package/server/CLI surfaces, or outreach.

Do not promote anything to canonical.

## V13 Signal

Signal:
BLUE / PUBLIC-ENTRY-FRICTION-REVIEW-RECORDED
+
BLUE / CONSTRAINED-USER-ROUTE-UNDERSTANDABLE
+
BLUE / POWERFUL-AGENT-ROUTE-GAP-CANDIDATE-IDENTIFIED
+
YELLOW / PUBLIC-VALUE-STILL-UNPROVEN
+
YELLOW / README-EDIT-HOLD
+
YELLOW / NO-CANONICAL-PROMOTION
+
YELLOW / REAL-READER-EVIDENCE-STILL-NEEDED

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The review produced bounded evidence and one possible future public-entry edit candidate, but it did not prove public value or authorize README/public/canonical changes.

Next Loop Command:
Stop after this evidence note. Do not edit public surfaces unless Shin separately authorizes a bounded README/public-entry edit or real reader evidence exposes the same gap.
