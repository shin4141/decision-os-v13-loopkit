# V13 A7 Creator-Live Whole-Flow Re-entry Charter v0.1

## Charter Identity

```text
Layer:
V13 — Field Notes / Companion Creator-Live End-to-End Closure
A7 Creator-Live Proof Re-entry Preparation

Artifact type:
Execution Charter only

Fixed repository:
shin4141/decision-os-v13-loopkit

Fixed main:
03a39f82f832f1655d1f25fc8ae982d606c7729d

Decision Owner:
Shin

Current Gate:
GO — Charter preparation only

Live Execution Gate:
BLOCK — independent Charter review, Charter merge, and separate explicit Shin
authorization are all required
```

This Charter defines the conditions for one future, separate creator-live proof
cycle. It does not open or execute that cycle.

## Objective and Authorized Scope

The future cycle is intended to test one exact whole-flow lineage:

```text
Run 1
→ new Field Note A1 capture
→ fresh Run 2
→ exact Note reconnect
→ demonstrable specific-structure reuse
→ A3 assessment
→ A4 durability
→ A5 confirmation
→ A6 review
→ A7 Whole-Flow verification
```

The current authorization covers only Charter drafting, repository recording,
review, and merge. It does not authorize proof execution, product/runtime model
invocation, Run 1, Run 2, Note creation, Companion installation or restart,
runtime modification, proof-attempt creation, Warehouse Import, release, or
publication.

## Historical Closure

### Proof 001

Historical identity:
`proof_a7_creator_live_001_59a75977337edbec`

Result:
`Permanent FAIL — direct-write A1 path violation`

Proof 001 is permanently closed. It has no retry, reopening, or replacement
under the same proof identity.

### Proof 002

Historical identity:
`proof_a7_creator_live_002_1d4c714b11c3f614`

Result:
`Permanent FAIL — A1_PROPOSAL_INVALID`

Historical diagnosis:
`B — Cause family narrowed`

Exact lower cause:
`UNRESOLVABLE`

Proof 002 is permanently closed. It has no retry, reopening, retroactive
reconstruction, or replacement under the same proof identity. This Charter
does not change its terminal record, diagnosis, or claim boundary.

### Completed controls

- PR #82 added durable bounded A1 proposal diagnostics and exact failure-family
  precedence.
- PR #84 recorded the bounded Proof 002 diagnosis and adversarial
  reconciliation without changing historical Outcome B.
- PR #85 repaired the current malformed-versus-missing A1 taxonomy so that no
  recognizable proposal request remains `A1_PROPOSAL_MISSING`, while a
  recognizable malformed request becomes
  `A1_PROPOSAL_REQUEST_SHAPE_INVALID`.

These controls qualify future observability. They do not repair either
historical proof or establish Creator-Live Proof.

## Strict Proof Line

The future cycle is governed by this unmodified strict proof line:

```text
1 creator
1 repository
1 exact model/runtime identity
1 new Field Note
2 distinct fresh Runs
1 exact A1–A6 lineage
0 retry
0 replacement
0 retroactive repair
0 evidence rewrite

A successful cycle additionally requires:

Run 1 creates exactly one eligible new A1 Note candidate
the exact Note bytes and identity are durably saved and read back
Run 2 is fresh and distinct from Run 1
Run 2 reconnects the exact saved Note
one specific Note structure is demonstrably used
use is evidenced through RULE_TRACE or OUTPUT_ARTIFACT
task success alone does not establish proof success
Note Outcome and Whole-Flow Result remain separate
HELP­FUL is not required if evidence and disposition are complete
A3, A4, A5, and A6 identities remain one exact lineage
journal, anchor, runtime identity, and all checkpoint identities survive exact durable readback
A7 verifier returns PASS
only after A7 PASS may a Whole-Flow Proof Receipt and Portable Candidate Warehouse Manifest be created
```

## New-Cycle Identity Boundary

No live proof-attempt identity is assigned or created by this Charter.

Proof 001 and Proof 002 remain permanently closed. A future authorized run must
use one fresh proof-attempt identity, created only after separate live execution
authorization. The future cycle is a new cycle; it is not a retry, reopening,
repair, continuation, or replacement of Proof 002.

## Qualification and Authorization Separation

### Repository qualification

Repository qualification establishes only that the source tree is eligible for
later runtime qualification. It requires read-only confirmation of:

- repository `shin4141/decision-os-v13-loopkit`;
- exact main `03a39f82f832f1655d1f25fc8ae982d606c7729d`;
- a clean tracked worktree and index;
- PR #82 diagnostic retention in the exact source state;
- PR #85 malformed-versus-missing taxonomy behavior in the exact source state;
- focused A1 diagnostic and creator-live qualification tests passing; and
- no unauthorized local code modification.

Passing repository tests does not qualify an installed runtime and does not
authorize a live run.

### Installation and runtime qualification

Installation and runtime qualification is a separate read-only identity check.
It requires confirmation of:

- the exact installed Companion build identity and its binding to the
  authorized repository state;
- the exact intended product model and runtime identity;
- the protected Proof 001 and Proof 002 artifacts remaining unchanged against
  their authoritative byte identities;
- no existing open creator-live proof attempt; and
- no unauthorized installed-code, configuration, or runtime modification.

This Charter does not authorize installing, rebuilding, changing, or restarting
Companion to satisfy these conditions. A mismatch is a stop, not permission to
repair the runtime.

### Live execution authorization

Live execution requires all of the following as distinct conditions:

1. this Charter receives independent review;
2. this Charter is merged;
3. repository qualification passes at execution preflight;
4. installation and runtime qualification passes at execution preflight; and
5. Shin separately and explicitly authorizes the one bounded live cycle.

No combination of artifact existence, merge status, passing tests, or runtime
qualification substitutes for condition 5. Live execution is currently
`BLOCK / NOT AUTHORIZED`.

## Preflight Requirements

Before execution may be authorized, P0 must record read-only confirmation of
every repository and runtime qualification condition above, including these
fixed boundaries:

```text
Repository main:
03a39f82f832f1655d1f25fc8ae982d606c7729d

Historical proofs:
Proof 001 unchanged and permanently closed
Proof 002 unchanged and permanently closed

Open creator-live attempts:
none

Unauthorized local code or runtime modification:
none
```

The exact installed build identity and exact intended model/runtime identity
must be recorded from the authorized environment; labels, assumptions, or
repository test results are insufficient substitutes. Any mismatch or missing
identity produces `BLOCK` before model invocation.

## Strictly Sequential Stage Sequence

The stages are ordered P0 through P7. A stage may begin only after the prior
stage has durably satisfied its exit conditions. No stage may be skipped,
parallelized, inferred from task success, or opened after a stop condition.

### P0 — Preflight

Verify and record all fixed identities, repository qualification, installation
and runtime qualification, artifact protections, absence of an open attempt,
and separate live authorization.

Failure result:

```text
BLOCK
No model invocation.
```

### P1 — Fresh Attempt Opening

After P0 passes, create exactly one fresh proof-attempt identity and exactly one
fresh Run 1 identity. Bind both to the qualified repository, installed build,
model/runtime identity, Charter, and zero-retry rule.

Failure result: terminalize where possible, stop, and create no replacement.

### P2 — Run 1 / A1 Capture

Run one creator-live task. The model may propose exactly once through the Field
Note proposal path. Direct write is prohibited. Require exact A1 diagnostics,
terminal persistence, anchor binding, and typed durable readback.

Failure result: stop permanently and do not open Run 2.

### P3 — A1 Save and Readback

Save only the exact eligible new candidate produced by Run 1. Verify the exact
Note identity, Note bytes, source Run identity, repository identity,
model/runtime identity, and As-of ordering through durable readback.

Failure result: stop permanently and do not open Run 2.

### P4 — Fresh Run 2 / A2 Reconnect

Create one fresh Run 2 identity that is distinct from Run 1. Reconnect the exact
saved Note and verify the Note, lineage, runtime, and Run identities.

Failure result: stop permanently. No alternate Note or replacement Run is
admissible.

### P5 — A3 Demonstrable Reuse

Require demonstrated use of one exact bounded Note structure. Evidence must be
specific, attributable to the exact Note and Run 2, and retained as
`RULE_TRACE` or `OUTPUT_ARTIFACT`. Generic similarity, later narrative, or task
success is insufficient.

Failure result: stop permanently. Do not infer reuse or advance maturity.

### P6 — A4 / A5 / A6

Append exact maturity evidence, confirm its durable readback, and produce the
exact review packet. Preserve one exact A3, A4, A5, and A6 lineage without
identity substitution, evidence repair, or reconstruction.

Failure result: stop permanently. Do not open A7 verification.

### P7 — A7 Whole-Flow Verification

Verify the complete durable A1–A6 evidence bundle, including exact journal,
anchor, repository, model/runtime, Note, Run, checkpoint, and lineage
identities. Return `PASS` only when every strict proof condition and boundary
matches.

Only after an A7 `PASS` may a Whole-Flow Proof Receipt and Portable Candidate
Warehouse Manifest be created. A non-PASS result creates neither.

## Universal Stop Rules

At any stage:

```text
FAIL / NOT_READY / identity mismatch / write failure / durability failure
→ stop immediately
→ do not open the next stage
→ do not retry
→ do not replace the Run
→ do not repair evidence
→ do not rewrite the journal or anchor
```

A model, transport, protocol, persistence, or runtime failure must not be
converted into another attempt under the same Charter execution. Partial task
success, external observation, or operator confidence cannot override a stop
or authorize replay, replacement, or advancement.

## Known Persistence Limits

- A refusal or process loss before the first terminal journal byte is written
  may leave only the prior durable `OPEN` state.
- A journal append followed by anchor-write failure must fail closed as a
  journal/anchor mismatch; the unanchored tail is not admissible proof.
- An external observation of failure cannot rewrite the durable proof record.
- Any disagreement between observed execution and durable readback produces
  `NOT ESTABLISHED` and an immediate stop.
- These limits do not authorize automatic recovery, replay, rollback,
  roll-forward, replacement, or evidence reconstruction.

### Optional out-of-band execution receipt boundary

A separately authorized future execution may use a bounded out-of-band receipt
only to record that the authorized attempt started and that durable readback
failed. Such a receipt:

- remains separate from the proof journal and anchor;
- does not change or supplement proof evidence;
- does not make an `OPEN` journal count as `PASS` or as cleanly unused;
- does not establish proof success; and
- does not authorize replay, recovery, or another attempt.

This Charter does not implement, create, or authorize implementation of that
receipt.

## Success and Completion Contract

The future cycle succeeds only if the strict proof line and every P0–P7 entry,
exit, identity, durability, and stop condition are satisfied, with A7 returning
`PASS`. Task success alone does not establish proof success. Note Outcome and
Whole-Flow Result remain separate, and `HELPFUL` is not required when evidence
and disposition are complete.

Any other result is `NOT ESTABLISHED` for Creator-Live Whole-Flow proof. It must
not be promoted, repaired retroactively, or recast as a successful partial
cycle.

## Claim Boundary

Even after this Charter is reviewed and merged:

- Creator-Live Proof remains `NOT ESTABLISHED`;
- no new proof attempt exists;
- no real Note has been created;
- no Run 1 or Run 2 has occurred;
- portability has not been demonstrated;
- Warehouse Import has not begun;
- cross-repository or cross-model reuse is not claimed;
- `PROMOTABLE` remains unset; and
- execution still requires separate explicit Shin authorization.

This Charter establishes only a governed re-entry contract. It is not proof
evidence, a proof receipt, a Warehouse manifest, or live execution authority.

## Decision Responsibility

Shin remains Decision Owner and retains the final Seat. Review or merge of this
Charter does not transfer that authority. The current authorization ends at
Charter drafting, repository recording, review, and merge.

## Gates

```text
Current Gate:
GO — Charter preparation only

Live Execution Gate:
BLOCK — requires independent Charter review, Charter merge, and separate
explicit Shin authorization

Third live attempt:
BLOCK / NOT AUTHORIZED
```

## Completion Line

Exactly one reviewed Charter artifact is committed and opened as a Draft PR,
with no live proof activity.
