# Minimum Autonomous Loop v0.1

## Read-Only Gap Routing Loop

## Status

```text
Specification: COMPLETE
Runtime implementation: NOT STARTED
Automation: NOT STARTED
Fresh isolated validation: NOT STARTED / PARKED
Automatic learning: BLOCK
Self-modification: BLOCK
Canon / authority / public action: BLOCK
```

This document specifies a bounded autonomous judgment unit. It does not implement or execute that unit.

## Purpose

Minimum Autonomous Loop v0.1 is the smallest loop that can improve V13's operating condition without changing repository state, taking the Human Seat, or activating an adjacent branch.

It autonomously:

1. reads the current canonical operating state;
2. detects at most one exposed high-value gap;
3. checks whether established context already closes it;
4. distinguishes AI-owned ambiguity from an irreducible Human Seat judgment;
5. selects the minimum sufficient question depth;
6. assigns one existing V13 Gate;
7. returns one bounded result;
8. stops before executing its proposed next action.

The first autonomous unit is therefore not autonomous execution. It is autonomous routing that can decide whether continuation is admissible and then stop.

## Source Basis

This specification reuses the existing governed foundation:

- [Agent operating rules](../AGENTS.md);
- [current Codex handoff](../handoff/current_codex_handoff.md);
- [Roadmap Anchors](roadmap_anchors.md);
- [Aspire-Oriented Loop Map](aspire_oriented_loop_map.md);
- [Field Note 120 — EV-Bounded Clarification Gate](../field_notes/120_ev_bounded_clarification_gate.md);
- [Field Note 125 — Execution Context Proof Selection](../field_notes/125_execution_context_proof_selection.md);
- [Field Note 126 — High-Leverage Definition Return](../field_notes/126_high_leverage_definition_return.md);
- [FN126 Case 002 — Human-Seat Distinguishability](../validation/field_note_126_case_002_human_seat_distinguishability.md);
- [FN126 Case 003 — Adaptive Human-Seat Question Depth](../validation/field_note_126_case_003_adaptive_human_seat_question_depth.md);
- [FN126 Case 004 — Aspire-Anchored Independent Evolution Evaluation](../validation/field_note_126_case_004_aspire_anchored_independent_evaluation.md).

FN126 Cases 001–004 are design evidence. They are not proof that this loop operates correctly in an automated or fresh isolated context.

## Scope and Non-Scope

### In scope

- read persisted evidence;
- establish continuation identity and authority;
- detect zero or one consequential gap;
- apply established context before asking;
- route the gap to AI ownership, Human Seat, evidence recovery, or stop;
- select `GO / HOLD / CAP / BLOCK`;
- produce zero or one Human Seat question;
- produce one restartable result;
- stop.

### Out of scope

- repository or workspace modification;
- execution of the proposed next action;
- answer-driven rewriting or dependency propagation;
- runtime learning or adaptation;
- persistent user profiling;
- Canon, authority, ownership, Protected Object, or Aspire modification;
- public or external action;
- branch activation;
- Skill, script, hook, plugin, MCP, package, service, schema implementation, or execution engine creation;
- self-modification or modification of this loop's own success criteria.

## Required Input Contract

The loop receives only:

- repository root or bounded workspace identity;
- canonical authority surface;
- current Gate;
- Active Branch;
- Next Authorized Action;
- current Protected Object when known;
- current roadmap / Aspire direction;
- current task or exposed incident;
- available persisted evidence and source pointers.

Inputs may be explicit values or resolvable persisted pointers. Artifact existence alone is not authority.

If repository identity, current authority, ownership, or sufficient continuation proof cannot be established:

```text
V13 Gate:
BLOCK

Reason:
BLOCK — sufficient continuation proof unavailable
```

The loop must not guess paths, authority, ownership, current state, or missing evidence.

## Loop Invariants

Every run must preserve all of the following:

- read-only operation;
- zero or one detected gap;
- zero or one Human Seat question;
- no option menu unless one question contains provisional framing and explicitly permits a third principle;
- established context before clarification;
- routine operational judgment remains AI-owned;
- `CHALLENGE REQUIRED` remains visible at every question depth;
- only `GO / HOLD / CAP / BLOCK` are V13 Gate outcomes;
- parked horizons do not become active work;
- uncertainty does not become permission;
- Aspire-directed, update-independent evaluation remains available;
- the result contains evidence pointers and a stop condition;
- no proposed action is executed.

## Processing Stages

### Stage 1 — Authority and State Preflight

Verify:

- repository or workspace identity;
- canonical authority source;
- current Gate;
- Active Branch;
- Next Authorized Action;
- current owner;
- relevant As-of;
- whether the current task is authorized.

Use the minimum sufficient continuation proof. Persisted artifact provenance is preferred. Add context-specific identity proof only when continuation genuinely depends on unpersisted judgment.

Failure result:

Populate the complete required output contract with at least these values:

```text
Observed State:
Repository identity, authority, ownership, or continuation proof is insufficient.

Detected Gap:
continuation proof unavailable

Established Context Check:
UNKNOWN

Decision Route:
STOP

V13 Gate:
BLOCK

Reason:
BLOCK — sufficient continuation proof unavailable

Human Seat Question:
none

Proposed AI-Owned Next Action:
none

CHALLENGE REQUIRED:
The loop cannot prove that continuation is authorized.

Evidence / Source Pointers:
- <attempted authority or evidence pointer>

Stop Condition:
No action is executed by this loop.
```

Stop. Do not continue to gap analysis or execution.

### Stage 2 — Gap Detection

Identify at most one gap that is:

- grounded in current evidence;
- relevant to the current roadmap;
- capable of changing the next decision;
- not merely wording polish;
- not a speculative improvement;
- not an inactive parked horizon.

Rank only grounded candidates and retain the strongest one. Do not expose a discarded candidate list or convert nearby ideas into a work queue.

If no qualifying gap exists, populate the complete required output contract with at least these values:

```text
Detected Gap:
none

Decision Route:
STOP

V13 Gate:
HOLD

Human Seat Question:
none

Proposed AI-Owned Next Action:
none
```

Stop.

### Stage 3 — Established-Context Closure

Inspect current authority, prior Human Seat decisions, Field Notes, handoffs, validation records, and established boundaries that directly bear on the gap.

If established context closes the gap:

- use the established answer;
- do not ask the Decision Owner again;
- classify any remaining bounded operational work as AI-owned where appropriate;
- assign a Gate from current authority;
- report the proposed route without executing it;
- stop after the result.

`CLOSED` does not itself mean `GO`. An AI-owned route may still be `CAP`, `HOLD`, or `BLOCK` because evidence or authority is insufficient.

If established context does not close the gap, continue to Stage 4.

### Stage 4 — Human-Seat Distinguishability

Determine whether a residual human-distinguishable difference remains in:

- value direction;
- risk tolerance;
- Protected Object priority;
- ownership or authority;
- public exposure;
- irreversible commitment;
- Aspire definition or change;
- materially valid incompatible meanings.

Operational difference is not automatically Human-Seat difference.

If no residual Human Seat difference remains:

- select the highest-EV bounded and reversible route from established context;
- do not present a menu;
- do not return routine comparison burden to the Decision Owner;
- return the proposed `AI-OWNED` route without executing it.

If a residual Human Seat difference remains:

- classify the route as `HUMAN-SEAT`;
- generate exactly one bounded question;
- do not answer it for the Decision Owner;
- stop.

If material consequence remains but Human Seat necessity cannot be determined, use `HOLD` and expose the exact uncertainty. Do not convert uncertainty into a question merely to keep the loop moving.

### Stage 5 — Adaptive Question Depth

For a justified Human Seat question, use the minimum sufficient level:

1. Recognition
2. Correction
3. Trade-off
4. Definition
5. Propagation Boundary

Calibrate by:

```text
person × domain × current state × decision consequence
```

Do not create a permanent user classification.

Downshift, narrow, or reformulate when evidence shows:

- confusion;
- passive agreement;
- repeated equivalent-choice delegation;
- unnecessary reconstruction;
- fatigue;
- repeated explanation;
- low propagation value.

The question may use provisional A/B framing only when it also states that the Decision Owner may reject both and define a third principle. It remains one question, not a menu.

Question simplification must not suppress:

```text
CHALLENGE REQUIRED
```

Material contradictions, irreversible risks, authority conflicts, Protected Object damage, and evidence capable of changing the Decision Owner's judgment remain visible at every depth.

### Stage 6 — Independent Improvement Check

For any proposed improvement, determine whether:

- it expands reachable paths toward the Decision Owner's current Aspire;
- it can be compared independently of its own new criteria;
- material counterevidence remains visible;
- the Decision Owner can reject it;
- historical reconnection remains available;
- a stable stop or return point remains available.

If these conditions cannot be established:

```text
V13 Gate:
HOLD
```

If the proposal removes one or more of these conditions:

```text
V13 Gate:
BLOCK
```

The loop does not modify Aspire, Canon, authority, ownership, or Protected Object. Capability, speed, autonomy, reuse, or burden reduction alone must not be classified as self-evolution.

### Stage 7 — Result and Stop

Return exactly one result using the output contract below.

The loop must never:

- execute its proposed next action;
- apply the Human Seat answer;
- modify files or external state;
- activate another branch;
- continue into another gap;
- recursively run itself;
- revise its own criteria.

After emitting the result, stop.

## Required Routing Outcomes

### GO

A qualifying AI-owned bounded continuation is clear and already authorized.

In v0.1, report the continuation but do not execute it.

### CAP

One small evidence-recovery or reversible action could close the gap.

State the exact cap axis and limit in `Reason` or `Proposed AI-Owned Next Action`. Do not execute the action.

### HOLD

A Human Seat answer, missing evidence, later observation, or separate authorization is required.

Return exactly one question when a Human Seat question is justified; otherwise return `none` and the exact hold condition.

### BLOCK

Identity, authority, ownership, Protected Object, continuation proof, or independent evaluation is unsafe or unproven.

State the exact blocking proof. Do not continue analysis past a Stage 1 proof failure.

## Required Output Contract

```text
# Minimum Autonomous Loop v0.1 Result

Observed State:
<one short paragraph>

Detected Gap:
<one gap or none>

Established Context Check:
CLOSED / NOT CLOSED / UNKNOWN

Decision Route:
AI-OWNED / HUMAN-SEAT / EVIDENCE-RECOVERY / STOP

V13 Gate:
GO / CAP / HOLD / BLOCK

Reason:
<1-3 lines>

Human Seat Question:
<exactly one question or none>

Proposed AI-Owned Next Action:
<one bounded action or none>

CHALLENGE REQUIRED:
<material contradiction or none>

Evidence / Source Pointers:
- <pointer>

Stop Condition:
No action is executed by this loop.
```

The output is invalid if a required field is omitted, if more than one gap or question is returned, or if the result implies execution occurred.

## Success Criteria

The specification succeeds only if a future conforming run can:

- return zero or one question, never a routine option menu;
- use established context before asking;
- avoid returning routine work to the Decision Owner;
- distinguish Human Seat from operational difference;
- preserve `CHALLENGE REQUIRED` at every depth;
- state `none` honestly when no qualifying gap exists;
- stop before repository modification or external action;
- expose uncertainty rather than converting it into permission;
- preserve Aspire-directed independent evaluation;
- produce a restartable result with evidence pointers and a stable stop.

## Falsifiers

A future run fails conformance if it:

- invents a gap to continue;
- asks the Decision Owner an AI-owned operational question;
- returns multiple choices without a genuine Human Seat distinction;
- hides material counterevidence;
- assumes authority from artifact existence;
- activates a parked branch;
- changes files or state;
- modifies its own success criteria;
- claims burden reduction without evidence;
- calls capability improvement self-evolution without Aspire-directed reachability;
- continues after producing its result.

One observed falsifier is sufficient to classify the affected run as `FAIL` until reviewed. This does not automatically invalidate the entire specification.

## Rollback

v0.1 is read-only.

Rollback is:

1. reject the result;
2. preserve the complete pre-run state;
3. record the observed falsifier in the separately authorized validation record;
4. make no repository, authority, Canon, Aspire, or external-state change.

No compensating write, automatic repair, or retry is part of v0.1.

## Evidence Status

```text
Specification: yes
Runtime: no
Autonomous learning: no
Self-modification: no
Fresh isolated validation: no
Automated operation proof: no
```

FN126 Cases 001–004 show manual design evidence for latent propagation, Human-Seat distinguishability, adaptive question depth, and Aspire-anchored independent evaluation. They do not demonstrate that an automated loop can reproduce those judgments.

## Future Validation Path — PARKED

Preserve this path without activating it:

1. freeze one bounded evidence packet;
2. run one fresh isolated receiver with this specification;
3. compare its result against the established Human Seat and Gate outcome;
4. measure unnecessary questions, missed Human Seat questions, missed `CHALLENGE REQUIRED` evidence, authority errors, branch activation errors, correction burden, and re-explanation burden;
5. classify the run `PASS / PARTIAL / FAIL`;
6. stop before implementation.

No new chat, receiver run, benchmark, implementation, automation, or publication is authorized by this specification.

## Completion Line

Minimum Autonomous Loop v0.1 specifies a Read-Only Gap Routing Loop that can inspect governed state, detect at most one consequential gap, route it to AI ownership or one irreducible Human Seat question, assign one V13 Gate, and stop before execution without implementing runtime learning or self-modification.
