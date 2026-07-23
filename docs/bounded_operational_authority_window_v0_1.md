# Bounded Operational Authority Window v0.1

## Three-Loop Repository Effect Authority for V13 Validation

## Status

```text
CANONICAL SPECIFICATION / NOT ACTIVE

Bounded Operational Authority Window v0.1:
MERGED / CANONICAL ON MAIN

PR #6:
PASS / COMPLETE

BOAW-001:
NOT ACTIVE

Run 002:
NOT STARTED

Activation authority:
SHIN ONLY

Merge approval:
COMPLETE

Activation decision:
NOT YET GIVEN

Current Gate:
HOLD — SEPARATE BOAW-001 ACTIVATION DECISION REQUIRED

Active Branch:
none

Codex Next Authorized Action:
none
```

This document defines the bounded authority specification now canonical on
`main`. Its merge did not activate the authority window, start Run 002, or
grant standing permission to write to `main`. An inactive BOAW has no standing
authority.

## Core Rule

> A claimed `1.01` may receive present Aspire-movement credit only when its
> intended effect is operationally available on the actual target surface
> under current authority by the end of the loop.

This rule distinguishes preparation from present operational effect:

- branch-only work is not automatically invalid;
- branch-local scripts, fixtures, prompts, and checks may have an immediate
  operational effect on that branch;
- features whose operation depends on the default branch, release state,
  repository settings, public deployment, or another external surface do not
  receive present-movement credit until that surface is actually active;
- future merge or publication cannot be silently counted as present movement;
  and
- preparation may still be useful, but it must be classified as preparation
  or provisional residue rather than completed Aspire movement.

## Authority Window

```text
Authority Window:
BOAW-001

Maximum completed loops:
3

Maximum active branches:
1 at a time

Maximum PRs:
1 per loop

Main integration:
permitted only after all loop-specific checks pass

Human questions during the three loops:
0 unless a true Human Seat decision is encountered

External actions:
0

Self-extension:
BLOCK

Criteria modification:
BLOCK

Authority renewal:
requires a new explicit Shin approval
```

The window is repository-only, temporary, loop-count limited, reversible,
auditable, and incapable of expanding its own scope. The authority-proposal PR
that became PR #6 was not a loop PR because BOAW-001 was not active and Run
002 had not started. Its merge did not consume a loop or activate the window.

## Activation

Activation requires a separate explicit Decision Owner statement containing:

```text
I activate BOAW-001 for Run 002.
```

Merge approval is not activation. The authority window remains `NOT ACTIVE`
unless Shin provides that exact separate statement. No Codex statement,
repository event, successful validation, PR approval, or merge may substitute
for it.

## Permitted Change Classes

Only bounded repository changes in these classes are permitted:

1. user or buyer first-use paths;
2. existing offer or README functional routing;
3. copy-paste operational surfaces;
4. Issue templates and repository-native intake surfaces;
5. examples and fixtures;
6. validation scripts;
7. restart, handoff, or verification-cost reduction;
8. correction of a demonstrated contract mismatch; and
9. bounded documentation changes required for the selected functional change.

A loop may use only one primary variable. Supporting edits are permitted only
when they are strictly required to make that one variable operational and
verifiable on its named target surface.

## Prohibited Change Classes

The authority window does not permit:

- outreach;
- posting;
- releases;
- client contact;
- payment handling;
- pricing changes;
- repository settings;
- secrets;
- permissions;
- Actions secrets;
- branch-protection changes;
- destructive history rewriting;
- deletion of published evidence;
- Canon changes;
- research-paper changes;
- V7 publication changes;
- runtime services;
- persistent automation;
- self-modification;
- new theory, taxonomy, or framework creation;
- modification of this authority document during an active window;
- modification of Run 002 evaluation criteria; or
- automatic renewal beyond three completed loops.

No permitted-class label may be used to route around a prohibited surface.

## Per-Loop Execution Contract

Each authorized loop must use this order:

1. verify current `main`, authority-window identity, remaining-loop count, and
   clean repository state;
2. select no more than one qualifying variable;
3. record why it is the highest-priority admissible candidate;
4. create one bounded branch;
5. implement one primary change;
6. validate the change;
7. verify the claimed operational surface;
8. open one PR;
9. independently inspect the PR diff and target-surface effect;
10. merge only if every predefined loop condition passes;
11. verify remote `main`, target-surface availability, rollback commit, and
    clean state;
12. record the completed loop;
13. decrement the remaining-loop count; and
14. stop before selecting the next variable unless the current loop is fully
    closed.

Multiple incomplete loops must not overlap. One active branch and one loop PR
are the maximum at any time.

## Merge Authority Boundary

During an activated authority window, Codex may merge its own loop PR only
when all of the following are true:

- the selected change is inside the permitted classes;
- exactly one primary variable changed;
- no Human Seat decision was required;
- no prohibited surface changed;
- all relevant validation passes;
- the PR head is verified immediately before merge;
- the actual target surface becomes operationally available through the merge;
- rollback is possible through a named pre-merge `main` SHA;
- no unresolved review thread or known defect remains;
- no second correction attempt was required; and
- the authority window still has at least one remaining loop.

A merge is not permitted merely because the implementation is useful. If any
condition is not satisfied:

```text
Loop Gate:
HOLD
```

Do not merge. Do not reinterpret preparation as present movement.

## Correction Limit

Each loop permits one bounded correction attempt.

A second required correction produces:

```text
Loop Result:
FAIL

Authority Window:
EXHAUSTED / BLOCK
```

The entire authority window then stops. No later loop may begin.

## Immediate Stop Conditions

The authority window must stop immediately when any occurs:

1. selected work is outside the permitted classes;
2. current authority or repository identity cannot be proven;
3. actual target-surface effect cannot be verified;
4. a Human Seat decision is required;
5. a prohibited external action is required;
6. one loop needs a second correction;
7. the selected change creates unowned Successor Debt;
8. rollback identity is missing;
9. the authority criteria are changed;
10. an incomplete loop remains open;
11. no qualifying `1.01` exists; or
12. three loops have completed.

No qualifying candidate is a successful stop, not permission to manufacture
work.

## Required Loop Receipt

Each completed or stopped loop must record:

- authority-window ID;
- loop number;
- starting `main` SHA;
- selected variable;
- priority;
- target operational surface;
- pre-change availability;
- post-change availability;
- implementation commit;
- PR number;
- verified PR head;
- merge SHA, if merged;
- final `main` SHA;
- rollback SHA;
- correction attempts;
- present Aspire movement;
- next-loop starting-condition effect;
- Load-Bearing Compliance;
- Improvement Credit;
- Successor Transfer;
- remaining authorized loops; and
- exact stop or continue state.

The receipt is incomplete if any required identity or availability result is
unknown.

## Rollback and Reversibility

Before each loop merge, the exact pre-merge `main` SHA is the required rollback
identity. Before merge, rollback means abandoning the branch and closing the
loop PR without changing `main`.

After merge, the only admissible history-preserving rollback is a revert of the
named loop merge commit toward the recorded pre-merge tree state. Reset,
force-push, rebase of published history, evidence deletion, and criteria
rewriting are prohibited.

If rollback cannot be performed without exceeding the one-PR limit, touching a
prohibited surface, or requiring a Human Seat decision, the loop and authority
window stop immediately. BOAW-001 does not expand itself to force recovery.
The rollback identity, required recovery, and exact re-entry authority must be
recorded before any later work.

## Authority Exhaustion

After three completed loops, or any immediate-stop condition:

```text
Authority Window:
EXHAUSTED

Further main write:
BLOCK

Further loop selection:
BLOCK

Reactivation:
REQUIRES NEW EXPLICIT SHIN APPROVAL
```

A partially used authority window is not standing permission. Codex cannot
renew, reinterpret, extend, or transfer the remaining authority.

## Run 001 Relationship

- Stress Run 001 remains `FAIL / CLOSED`;
- its evidence branches and Draft PRs remain non-merge evidence;
- BOAW-001 is a Forward-only response to the observed authority/effect
  mismatch;
- no Run 001 score, artifact, or evaluation is rewritten;
- the rule does not retroactively validate Iteration 01; and
- Run 002 remains unstarted.

## Existing Surface State

The current state is also recorded in the
[Loop Map](loop_map.md), [Current Signal](current_signal.md), and
[current Codex handoff](../handoff/current_codex_handoff.md):

```text
Bounded Operational Authority Window v0.1:
MERGED / CANONICAL ON MAIN

PR #6:
PASS / COMPLETE

BOAW-001:
NOT ACTIVE

Run 002:
NOT STARTED

Activation authority:
SHIN ONLY

Merge approval:
COMPLETE

Activation decision:
NOT YET GIVEN

Current Gate:
HOLD — SEPARATE BOAW-001 ACTIVATION DECISION REQUIRED

Active Branch:
none

Codex Next Authorized Action:
none
```

Completion Line:

Bounded Operational Authority Window v0.1は`main`上でcanonicalになったが、
BOAW-001はinactive、Run 002はunstartedのままであり、Shinの別個のactivation
判断まで停止する。
