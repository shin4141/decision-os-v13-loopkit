# Minimum Autonomous Loop v0.2

## Lineage-Aware Gap Routing Loop

## Status

```text
Specification: COMPLETE
Relationship to v0.1: FORWARD-ONLY SUCCESSOR
MAL v0.1: PRESERVED / PRIOR VALIDATION SCOPE UNCHANGED
Runtime implementation: NOT STARTED / BLOCK
Automation: NOT STARTED / BLOCK
Fresh isolated validation: NOT STARTED / PARKED
Automatic lineage scanning: BLOCK
Automatic Canon propagation: BLOCK
Automatic learning: BLOCK
Self-modification: BLOCK
Canon / authority / public action: BLOCK
```

This document specifies a bounded autonomous judgment unit. It does not
implement or execute that unit.

## Purpose

Minimum Autonomous Loop v0.2 is a Forward-only successor to
[Minimum Autonomous Loop v0.1](minimum_autonomous_loop_v0_1.md). It preserves
the v0.1 read-only routing boundary and adds one mandatory stage before a
question may be returned to the Decision Owner:

```text
Decision Lineage Reconnection Preflight
```

The preflight prevents a definition that is absent from the current repository
from being misclassified as unanswered by the Decision Owner.

The fixed rule is:

```text
Local undefined
≠
Lineage undefined
≠
Human unanswered
```

Only the final state may justify a Human Seat question.

## Relationship to v0.1

MAL v0.2 inherits all v0.1 boundaries:

- read-only routing;
- zero or one gap;
- zero or one Human Seat question;
- established context before asking;
- AI-owned routine work is not returned to the Decision Owner;
- `CHALLENGE REQUIRED` remains visible;
- only `GO / CAP / HOLD / BLOCK` are V13 Gate outcomes;
- stop before execution;
- no branch activation;
- no automatic propagation;
- no Canon or authority modification;
- no runtime learning or self-modification.

MAL v0.1 and its Run 001 remain fixed at their own historical As-of. v0.2 does
not rewrite, rescore, or expand the evidence claims of v0.1.

## Source Basis

This specification uses:

- [Agent operating rules](../AGENTS.md);
- [current Codex handoff](../handoff/current_codex_handoff.md);
- [Minimum Autonomous Loop v0.1](minimum_autonomous_loop_v0_1.md);
- [Decision Lineage Reconnection Register v0.1](decision_lineage_reconnection_register_v0_1.md);
- [Roadmap Anchors](roadmap_anchors.md);
- [Aspire-Oriented Loop Map](aspire_oriented_loop_map.md);
- [Field Note 125 — Execution Context Proof Selection](../field_notes/125_execution_context_proof_selection.md);
- [Field Note 126 — High-Leverage Definition Return](../field_notes/126_high_leverage_definition_return.md);
- [FN126 Case 004 — Aspire-Anchored Independent Evolution Evaluation](../validation/field_note_126_case_004_aspire_anchored_independent_evaluation.md).

The lineage register is a reconnectable pointer surface. It is not a duplicated
Canon or permission to load adjacent theory without decision relevance.

## Scope and Non-Scope

### In scope

- read persisted local evidence;
- establish continuation identity and authority;
- detect zero or one consequential gap;
- reconnect apparently unresolved terms or joints to bounded, verified lineage
  pointers;
- apply explicit Human Seat decisions and later Forward-only deltas before
  relying on older source meaning;
- distinguish source definitions from current-layer operational mappings;
- classify the gap as local-closed, lineage-closed, lineage-conflicted, truly
  unanswered, or source-proof-insufficient;
- route the result to AI ownership, Human Seat, evidence recovery, or stop;
- produce zero or one Human Seat question;
- assign one existing V13 Gate;
- stop.

### Out of scope

- repository or workspace modification by a loop run;
- execution of a proposed next action;
- automatic source discovery, crawling, indexing, embeddings, or full-history
  loading;
- automatic source binding or Canon propagation;
- source-document modification;
- answer-driven dependency propagation;
- runtime learning or adaptation;
- persistent user profiling;
- Canon, authority, ownership, Protected Object, Aspire, or lineage-source
  modification;
- public or external action;
- branch activation;
- Skill, script, hook, plugin, MCP, package, service, schema implementation, or
  execution engine creation;
- self-modification or modification of this loop's own success criteria.

## Required Input Contract

The loop receives the v0.1 inputs:

- repository root or bounded workspace identity;
- canonical authority surface;
- current Gate;
- Active Branch;
- Next Authorized Action;
- current Protected Object when known;
- current roadmap / Aspire direction;
- current task or exposed incident;
- available persisted evidence and source pointers.

For an apparently unresolved term, condition, authority boundary, or value
definition, it may additionally receive:

- a bounded lineage-register entry;
- verified source identity and retrieval pointer;
- relevant explicit Human Seat decisions;
- relevant later Forward-only delta pointers;
- historical As-of information.

Artifact existence alone is not authority. A local omission is not proof of
lineage omission. A lineage pointer without sufficient source identity is not
proof of source meaning.

If repository identity, current authority, ownership, or sufficient
continuation proof cannot be established, return `BLOCK` under the full output
contract and stop.

## Loop Invariants

Every conforming run must preserve all v0.1 invariants and all of the following:

- Decision Lineage Reconnection occurs before Human-Seat Distinguishability;
- current explicit Human Seat decisions and later Forward-only deltas take
  precedence over an older source meaning;
- older historical As-of remains visible after a Forward-only delta;
- AI inference never silently overrides a source-defined term;
- local absence is never treated as lineage absence without a bounded source
  check;
- missing source access never becomes permission to infer or ask;
- source definition and current-layer mapping remain labeled separately;
- verified pointers are preferred over full-history reload;
- only decision-relevant source sections are retrieved;
- lineage-closed operational binding remains AI-owned;
- genuine authoritative conflicts remain visible;
- no proposed binding, propagation, or action is executed.

## Mandatory Pre-Question Evidence Order

Before Human-Seat Distinguishability, inspect in this order:

```text
1. Current local authority
2. Current explicit Human Seat decisions
3. Later Forward-only deltas
4. Authoritative Decision-OS lineage source
5. Historical As-of
6. AI inference
```

This is both a retrieval and precedence rule. Later explicit Human Seat deltas
must be identified before older source text is allowed to govern the current
meaning. AI inference is last and must remain labeled as inference. It may
propose a bounded current-layer mapping, but it cannot redefine the source
concept.

## Processing Stages

### Stage 1 — Authority and State Preflight

Perform the v0.1 authority and state checks:

- repository or workspace identity;
- canonical authority source;
- current Gate;
- Active Branch;
- Next Authorized Action;
- current owner;
- relevant As-of;
- whether the current task is authorized.

If this proof is insufficient:

```text
Established Context Check:
UNKNOWN

Lineage Reconnection Check:
SOURCE-PROOF-INSUFFICIENT

Lineage Source:
none

Local Binding Required:
no

Decision Route:
STOP

V13 Gate:
BLOCK

Human Seat Question:
none
```

In this Stage 1 route, continuation identity or authority proof failed before
lineage preflight could run, so the v0.1 continuation-proof `BLOCK` controls.
The `SOURCE-PROOF-INSUFFICIENT` result value records that the lineage check was
unavailable; it is not the Stage 3
`SOURCE-PROOF-INSUFFICIENT / HOLD` classification used after continuation
authority has already been established.

Stop before gap analysis or source interpretation.

### Stage 2 — Gap Detection

Apply the v0.1 zero-or-one gap rule. A qualifying gap must be grounded,
decision-relevant, capable of changing the next decision, and neither wording
polish nor an inactive parked horizon.

If no qualifying gap exists, complete the full result contract using:

```text
Detected Gap:
none

Established Context Check:
CLOSED

Lineage Reconnection Check:
LOCAL-CLOSED

Lineage Source:
none

Local Binding Required:
no

Decision Route:
STOP

V13 Gate:
HOLD

Human Seat Question:
none

Proposed AI-Owned Next Action:
none
```

For this no-gap route, `LOCAL-CLOSED` means that no unresolved joint reached
lineage preflight. It does not claim that a particular term received a new
local definition.

Stop.

### Stage 3 — Decision Lineage Reconnection Preflight

Run this stage for any apparently unresolved term, condition, authority
boundary, or value definition.

#### Step 1 — Local Check

Determine whether current local authority, explicit Human Seat decisions, or
current validated records already close the joint.

Outcome:

```text
LOCAL-CLOSED
```

Do not ask the Decision Owner again.

#### Step 2 — Later Forward-Only Delta Check

Inspect later explicit Human Seat judgments and current Forward-only deltas
before applying an older lineage definition.

Determine whether a later judgment:

- superseded the original definition;
- narrowed it;
- expanded it;
- remapped its current operational use;
- introduced a material conflict without resolving it.

Do not erase the older As-of. Do not let the older source overwrite the later
explicit Human Seat delta.

#### Step 3 — Lineage Source Check

If still locally unresolved, use the bounded lineage register and its verified
source pointers.

Check:

- source title and role;
- source identity such as DOI, version, commit, file hash, or equivalent;
- source-defined core relevant to the current joint;
- whether the pointer is retrievable or explicitly marked `UNKNOWN`;
- whether the current claim is source text or current-layer mapping.

Do not treat absence from the current repository as absence from Decision-OS.
Do not invent a path, hash, commit, DOI, source meaning, or authority relation.

If a verified pointer and bounded source section are sufficient, do not reload
the full lineage history.

#### Step 4 — Historical As-of Check

Preserve:

- the source's own version or As-of;
- later Forward-only deltas;
- the current local mapping As-of;
- the retrieval or reconnection path.

Do not collapse these into an atemporal summary.

#### Step 5 — AI Inference Boundary

AI inference may derive only a bounded operational mapping already authorized
by the current layer. It must be labeled as mapping rather than source
definition.

AI inference must not:

- redefine a source term;
- silently reconcile a material lineage conflict;
- upgrade missing source proof into a Human Seat question;
- import adjacent theory without decision relevance;
- propagate a binding automatically.

#### Step 6 — Classification

Use exactly one:

```text
LOCAL-CLOSED

LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

LINEAGE-CONFLICT / HUMAN-SEAT-REQUIRED

TRULY-UNANSWERED / HUMAN-SEAT-REQUIRED

SOURCE-PROOF-INSUFFICIENT / HOLD
```

The full classification maps to the required result field as follows:

```text
LOCAL-CLOSED
-> Lineage Reconnection Check: LOCAL-CLOSED

LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED
-> Lineage Reconnection Check: LINEAGE-CLOSED

LINEAGE-CONFLICT / HUMAN-SEAT-REQUIRED
-> Lineage Reconnection Check: CONFLICT

TRULY-UNANSWERED / HUMAN-SEAT-REQUIRED
-> Lineage Reconnection Check: UNANSWERED

SOURCE-PROOF-INSUFFICIENT / HOLD
-> Lineage Reconnection Check: SOURCE-PROOF-INSUFFICIENT
```

`Established Context Check` is `CLOSED` for verified local or lineage closure,
`NOT CLOSED` for a proved conflict or truly unanswered joint, and `UNKNOWN`
when source proof is insufficient.

`Local Binding Required` is `yes` only for verified
`LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED`. Every other classification uses
`no`; in those routes, `no` means that a binding may not proceed, not that a
future binding could never become necessary.

The suffix `HUMAN-SEAT-REQUIRED` marks a candidate route into the
Human-Seat Distinguishability check. It does not by itself grant permission to
ask a question.

Classification meanings:

##### LOCAL-CLOSED

The current local authority already supplies the established answer. Use it.
Do not ask.

##### LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

An authoritative lineage source closes the meaning, and no later valid delta
conflicts with it. The Human Seat question is `none`.

AI owns, within separate current authority:

- source binding;
- bounded operational mapping;
- evidence pointers;
- handoff and Git work;
- authorized Forward-only propagation.

The loop run only reports that route. It executes none of it.

##### LINEAGE-CONFLICT / HUMAN-SEAT-REQUIRED

Two materially valid authoritative meanings remain after As-of and
Forward-only precedence have been applied. Preserve both meanings and their
source identities. Do not silently reconcile them.

Continue to Human-Seat Distinguishability and ask at most one question only if
all question-permission conditions are satisfied.

##### TRULY-UNANSWERED / HUMAN-SEAT-REQUIRED

Sufficient bounded source proof establishes that neither local authority nor
the relevant Decision-OS lineage answers the Human-distinguishable joint.

Continue to Human-Seat Distinguishability.

##### SOURCE-PROOF-INSUFFICIENT / HOLD

Source identity, access, freshness, or relevant meaning is not sufficiently
proved. Do not guess. Do not convert missing access into Human Seat necessity.
Return `HOLD` with no question.

### Stage 4 — Human-Seat Distinguishability

Only `LINEAGE-CONFLICT / HUMAN-SEAT-REQUIRED` or
`TRULY-UNANSWERED / HUMAN-SEAT-REQUIRED` may reach this stage.

Apply the v0.1 distinction between operational difference and an irreducible
Human Seat difference in value direction, risk tolerance, Protected Object,
ownership, public exposure, irreversible commitment, Aspire, or materially
valid incompatible meanings.

If no Human-distinguishable difference remains, route the bounded reversible
work as `AI-OWNED` and return no question.

### Stage 5 — Adaptive Question Depth

For a justified question, retain the v0.1 minimum-sufficient levels:

1. Recognition
2. Correction
3. Trade-off
4. Definition
5. Propagation Boundary

Calibrate by `person × domain × current state × decision consequence`.
Preserve `CHALLENGE REQUIRED` at every depth.

### Stage 6 — Independent Improvement Check

Apply the full v0.1 Aspire-directed, update-independent comparison check. A
lineage binding does not itself prove improvement, self-evolution, burden
reduction, generalization, or runtime reliability.

### Stage 7 — Result and Stop

Return exactly one complete result. Do not:

- execute a proposed binding;
- apply a Human Seat answer;
- modify files or external state;
- activate another branch;
- continue into another gap;
- recursively run this loop;
- revise its own criteria.

After emitting the result, stop.

## Question Permission Rule

MAL v0.2 may return a Human Seat question only when all four conditions hold:

```text
Local Check:
NOT CLOSED

Lineage Reconnection Check:
CONFLICT or UNANSWERED

Source Proof:
SUFFICIENT

Human-Seat Distinguishability:
PRESENT
```

If any condition is absent, the Human Seat question is `none`.

For `CONFLICT`, source proof is sufficient only when both applicable
authoritative meanings, their identities, and their As-of relations are
verified. For `UNANSWERED`, source proof is sufficient only when the bounded
registered lineage and applicable Forward-only deltas have been checked enough
to establish absence inside that declared authority boundary. This is not a
claim that every historical artifact everywhere has been exhaustively searched.

## First Bounded Lineage-Binding Example — PIC

This is a specification example and registered source binding. It is not a
fresh MAL run.

```text
Apparently unresolved joint:
PIC preservation / break condition in FN126 Case 004

Local status at the Case 004 As-of:
not locally defined by V13

Lineage status:
V6 defines PIC
V7 Addendum states its necessity and minimal failure conditions
V8 inherits PIC-compatible operation
V11 supplies reconnectable source and As-of requirements

Later Human Seat correction:
PIC is lineage-closed and requires AI-owned local binding

Classification:
LINEAGE-CLOSED / LOCAL-BINDING-REQUIRED

Human Seat Question:
none
```

The source-defined PIC core and the bounded V13 operational mapping are kept
separate in the
[Decision Lineage Reconnection Register](decision_lineage_reconnection_register_v0_1.md).

The minimal V13 operational witnesses apply when V13 integrates an update into
a commitment-ready canonical judgment, not while it preserves competing
frontier candidates:

1. Order Independence
2. Idempotence
3. Monotone Safety Preservation
4. Canonical Reconnection

For V13 evaluation, `PIC BROKEN` if any one witness fails at that commitment
boundary.

`Canonical Reconnection` is a V13/V11 operational witness mapped from the
original V6 canonical-convergence formulation, the later V6 v2
commitment-boundary scope, and V11 reconnectability. It is not presented as a
newly discovered V6 axiom.

## Required Routing Outcomes

The v0.1 meanings of `GO / CAP / HOLD / BLOCK` remain unchanged.

- `GO`: a qualifying AI-owned bounded continuation is clear and already
  authorized; report it without execution.
- `CAP`: one bounded reversible or evidence-recovery action is useful; state
  the exact cap without execution.
- `HOLD`: a Human Seat answer, missing source proof, later observation, fresh
  validation, or separate authorization is required.
- `BLOCK`: identity, authority, ownership, Protected Object, continuation
  proof, or independent evaluation is unsafe or unproven.

Lineage closure does not automatically produce `GO`. A local binding may still
be `CAP`, `HOLD`, or `BLOCK` under current authority.

## Required Output Contract

All v0.1 fields remain required. The three lineage fields are mandatory.

```text
# Minimum Autonomous Loop v0.2 Result

Observed State:
<one short paragraph>

Detected Gap:
<one gap or none>

Established Context Check:
CLOSED / NOT CLOSED / UNKNOWN

Lineage Reconnection Check:
LOCAL-CLOSED / LINEAGE-CLOSED / CONFLICT / UNANSWERED /
SOURCE-PROOF-INSUFFICIENT

Lineage Source:
<verified pointer or none>

Local Binding Required:
yes / no

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

The result is invalid if a required field is omitted, if more than one gap or
question is returned, if a source identity is invented, if source definition
and local mapping are conflated, or if the result implies execution occurred.

## Success Criteria

The specification succeeds only if a future conforming run can:

- prevent a locally missing definition from being automatically returned to
  the Decision Owner;
- check explicit Human Seat decisions and later Forward-only deltas before an
  older source governs current use;
- preserve historical As-of;
- separate source definition from current-layer mapping;
- route lineage-closed items to AI ownership;
- expose genuine lineage conflicts rather than silently reconcile them;
- stop on insufficient source proof;
- avoid full-history reload when verified pointers are sufficient;
- preserve all v0.1 stopping and authority boundaries;
- return zero or one Human Seat question;
- stop before repository modification or external action.

## Falsifiers

A future run fails conformance if it:

- asks the Decision Owner a question answered by the lineage;
- treats local absence as lineage absence;
- imports an old definition over a later Human Seat delta;
- invents a source pointer, path, hash, commit, DOI, or source meaning;
- presents current-layer inference as source-defined Canon;
- silently reconciles a material lineage conflict;
- loads adjacent theory without decision relevance;
- performs automatic source binding or Canon propagation;
- changes source documents;
- omits a required v0.1 or v0.2 result field;
- continues after returning its routing result;
- violates any v0.1 falsifier.

One observed falsifier is sufficient to classify the affected run as `FAIL`
until reviewed. It does not automatically invalidate v0.1 or its historical
Run 001.

## Rollback

MAL v0.2 is read-only when run. Rollback of a future result is:

1. reject the result;
2. preserve the complete pre-run state;
3. reconnect to the source and As-of used;
4. record the falsifier only under separate authorization;
5. make no compensating write, automatic repair, or retry.

## Evidence Status

```text
Specification: yes
First lineage binding: PIC
Runtime: no
Fresh v0.2 validation: no / PARKED
Autonomous learning: no
Automatic lineage scan: no / BLOCK
Automatic Canon propagation: no / BLOCK
Self-modification: no
Generalization: not established
```

## Future Validation Path — PARKED

A fresh v0.2 validation requires separate authorization. No evaluator, packet,
receiver run, benchmark, implementation, automation, or publication is
activated by this specification.

## Completion Line

Minimum Autonomous Loop v0.2 distinguishes locally missing knowledge from
lineage-defined knowledge and genuinely unanswered Human Seat questions while
preserving v0.1, historical As-of, source-defined meaning, current-layer
mapping boundaries, and the stop before execution.
