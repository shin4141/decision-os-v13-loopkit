# Field Note 037: Execution Loop Audit — Test Until Green

Date: 2026-06-14

## Purpose

This note audits a generic "Test Until Green" execution loop through Decision-OS V13.

The purpose is to show that Decision-OS V13 does not merely cap all loops.

V13 can allow or conditionally allow execution loops when the exit condition is concrete, verification is clear, and the touch surface is bounded.

## Generic Execution Loop

Test Until Green:

```text
Run tests, fix failures, and repeat until the test suite passes.
```

This is a common coding-agent execution loop.

It is stronger than an open-ended polish loop because it has a visible verification target.

## Ordinary Agent Judgment

An ordinary agent would likely GO because:

- the loop has a clear exit condition
- failures are observable
- verification is direct
- the work appears technically bounded

This judgment is often reasonable.

But it is incomplete if the agent does not check touch surface, requirement ambiguity, rollback, or behavior drift.

## Decision-OS V13 Judgment

Decision-OS V13 does not reject this loop by default.

It asks whether the loop is admissible under concrete boundaries.

V13 judgment:

- This loop may be GO only if the touch surface is bounded.
- The loop must not rewrite unrelated files.
- The loop must not silently change behavior to satisfy tests.
- The loop must not expand from fixing test failures into feature work.
- The loop must preserve rollback and report changed files.
- If failures reveal unclear requirements, the loop must switch to HOLD or CAP rather than forcing green.

The core question is not:

```text
Can the agent make tests pass?
```

The core question is:

```text
Can the agent make tests pass without creating hidden debt?
```

## V12 State

If the prior task is incomplete because tests fail:

```text
V12 State:
DELAY
```

until verification passes or the failing evidence is explained.

If tests pass and changed files are explained:

```text
V12 State:
PASS
```

V12 depends on completion integrity, not the agent's confidence.

## V13 Next Loop Gate

V13 Next Loop Gate:
Conditional GO or CAP

Use:

- GO if the failing test, allowed files, and exit condition are clear.
- CAP if the touch surface is broad or the fix path is uncertain.
- HOLD if the failure indicates ambiguous requirements.
- BLOCK if the loop would alter unrelated behavior just to make tests pass.

This loop can be admissible.

It is not automatically safe.

## GO / CAP Conditions

GO allowed when:

- exact test command is known
- failing tests are identified
- allowed files are specified
- max iterations or stop condition exists
- rollback path exists
- no public/adoption/readiness claim is involved

CAP required when:

- fix may touch broad architecture
- failures may be caused by unclear requirements
- test green could be achieved by weakening tests
- loop may become refactor creep

If no concrete cap can be stated, use HOLD.

If the only path crosses a forbidden or approval-required boundary, use BLOCK.

## Required Boundaries

Required boundaries:

- max iteration count
- allowed file or module scope
- no weakening tests without owner approval
- no unrelated refactor
- stop and report if requirement ambiguity appears
- preserve rollback

The loop is only safe when these boundaries are observable.

If the agent cannot tell whether it stayed inside the boundary, the boundary is too vague.

## Debt Risk

Test-until-green can create debt if it optimizes for green status while hiding:

- requirement ambiguity
- behavior drift
- weakened tests
- unrelated refactor
- missing rollback
- unexplained changed files

Green is evidence.

Green is not an absolute guarantee.

The loop should not trade visible red tests for invisible future confusion.

## Delta Condition

The loop produces delta when:

- it turns a known failing verification into passing verification
- the fix is bounded
- evidence is preserved
- no hidden behavior drift is introduced

The delta is not merely:

```text
tests are green
```

The delta is:

```text
the known verification failure was repaired within named boundaries and remains restartable
```

## Contrast With README Polish Loop

README polish was CAP because:

```text
better
```

was not a concrete exit condition.

Test Until Green can be GO because:

```text
tests pass
```

is a concrete exit condition.

But the GO is conditional on strict boundaries.

README polish converts uncertainty into more wording.

Test Until Green can convert a known failing verification into passing evidence.

That difference matters.

## What This Shows

Decision-OS is not anti-loop.

It separates:

- loops with concrete verification and bounded touch surface
- from loops that convert uncertainty into polish, scope creep, or public-readiness debt

V13 can allow execution.

It just refuses to confuse execution momentum with safe progress.

## Boundary

This is an audit note only.

Do not run tests.

Do not modify code.

Do not modify AGENTS.md.

Do not rewrite README.

Do not add implementation.

Do not create a loop gallery.

Do not route this into AGENTS.md yet.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, loop galleries, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / EXECUTION-LOOP-AUDIT-RECORDED
+
🟢 BLUE / TEST-UNTIL-GREEN-CONDITIONAL-GO-DEFINED
+
🟢 BLUE / V13-NOT-ANTI-LOOP-SHOWN
+
🟢 BLUE / EXIT-CONDITION-DIFFERENCE-RECORDED
+
🟡 YELLOW / TOUCH-SURFACE-MUST-BE-BOUNDED
+
🟡 YELLOW / DO-NOT-WEAKEN-TESTS
+
🟡 YELLOW / DO-NOT-BUILD-LOOP-GALLERY

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The Test Until Green loop is recorded as conditionally admissible when verification, touch surface, and stop conditions are concrete, while broad or ambiguous fixes remain capped, held, or blocked.

Next Loop Command:
Compare this with README Polish to show that V13 gates loops by exit-condition clarity, touch surface, and debt risk.
