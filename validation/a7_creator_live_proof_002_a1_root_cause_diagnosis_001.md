# V13 A7 Creator-Live Proof 002 — A1 Root-Cause Diagnosis 001

## Diagnosis Identity

```text
Layer:
V13 — A7 Creator-Live Proof / A1 Proposal Boundary

Proof attempt:
proof_a7_creator_live_002_1d4c714b11c3f614

Historical code:
a033b6a7c8968d17744d0f85342b54dbfb73fa85

Diagnosis base:
49a7026954405ba4ca2c9024b1cb34c5b7da0ff2

Terminal result:
FAILED / A1_CAPTURE / A1_PROPOSAL_INVALID

Outcome class:
B — CAUSE FAMILY NARROWED

Current Gate:
HOLD — root-cause diagnosis before repair
```

This is a diagnosis-only record. It does not change Proof 002, claim that the
proof succeeded, authorize a third attempt, or begin a repair.

## Evidence Inventory

### Protected journal

Path:
`.decision-os/field-notes/proofs/proof_a7_creator_live_002_1d4c714b11c3f614/creator-live-proof-v0.1.jsonl`

```text
Exact file SHA-256:
8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c

Bytes:
2463

Records:
2
```

Record 0 binds the proof attempt, Run 1, source repository and commit, runtime,
and the one-attempt/no-retry rule. Record 1 retains only:

```text
kind: ATTEMPT_FAILED
failure_boundary: A1_CAPTURE
failure_reason: A1_PROPOSAL_INVALID
repair_action: NONE
```

It contains no proposal call count, call/request/argument identity, request
shape result, gate result, accepted proposal state, item lifecycle, replay fact,
protocol phase, or lower proposal sub-cause.

### Protected anchor

Path:
`.decision-os/field-notes/proofs/proof_a7_creator_live_002_1d4c714b11c3f614/creator-live-proof-v0.1.anchor.jsonl`

```text
Exact file SHA-256:
3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c

Bytes:
1118

Anchor generations:
2

Final bound journal SHA-256:
8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c

Final record count:
2

Final record-chain head:
5c2072eb1e77c8b8399bce36403e2377c7beaaa1307c5af3acb0a6357d830a6e
```

Typed load and readback on current main verify the chain and project:

```text
durable_readback_verified: true
state: FAILED
failure_reason: A1_PROPOSAL_INVALID
repair_action: NONE
trace_event_count: 0
run_2: none
a1_proposal_diagnostic: none
```

The `none` diagnostic is a faithful legacy projection. It is not evidence for
any one lower cause.

### Local bounded logs and receipts

A repository-scoped exact-identity search used both the proof attempt ID and
Run 1 ID. The proof directory contains only the protected journal and anchor.
No separate proposal transport log, adapter result, controller receipt, or
capture-bridge diagnostic belonging to Proof 002 survives locally.

`validation/a7_creator_live_post_repair_settlement_001.md` is a later
settlement record. It correctly preserves the lower sub-cause as unknown and
is not contemporaneous lower-cause evidence.

### Historical code and later taxonomy

The journal binds source commit
`a033b6a7c8968d17744d0f85342b54dbfb73fa85`. The relevant historical paths
are:

- `decision_os/companion/field_notes_adapter.py`
- `decision_os/companion/field_notes_model.py`
- `decision_os/companion/field_notes_controller.py`
- `decision_os/companion/field_notes_creator_live_capture.py`

PR #82, `Retain bounded A1 proposal failure diagnostics`, is used only to name
and separate lower-cause families. Its later diagnostic values are not read
back into Proof 002 and do not retroactively prove a cause.

## Historical Failure Map

### Exact historical umbrella

At historical `field_notes_adapter.py:429-449`, after direct-write, zero-call,
and distinct-multiple-call checks, the adapter returned
`A1_PROPOSAL_INVALID` exactly when:

```python
attempts == 1 and (
    self._capture_proposal_malformed
    or self._field_note_gate.accepted is None
    or not all_proposals_completed
)
```

Here:

```python
all_proposals_completed = set(self._proposal_responses).issubset(
    self._completed_proposal_items
)
```

At historical `field_notes_controller.py:430-453`, a second umbrella emitter
existed: after no stored capture failure, the controller raised
`A1_PROPOSAL_INVALID` if `_field_note_draft is None`. That state was reachable
with a contract-inconsistent adapter result and was defensive rather than a
normal success state from the production adapter.

### Candidate map

| Candidate | Exact historical predicate or path | Evidence needed to prove it | Survives Proof 002 | Offline | Confidence |
|---|---|---|---|---|---|
| No proposal call | `len(_capture_proposal_call_ids) == 0` at adapter lines 439-441 | Captured call count or adapter result | No | Yes; returns `A1_PROPOSAL_MISSING` | **EXCLUDED** |
| Multiple proposal calls | `len(_capture_proposal_call_ids) != 1` after the zero check at lines 442-443; count is distinct non-empty call IDs | Captured call IDs/count | No | Yes; two distinct IDs return `A1_PROPOSAL_DUPLICATE` | **EXCLUDED** |
| Malformed request shape | `valid_shape` false at lines 368-397 sets `_capture_proposal_malformed`; with one non-empty call ID, line 445 enters the umbrella | Raw request and started item, or retained `request_shape_valid`/malformed fact | No | Yes; extra request field returns the umbrella | **POSSIBLE** |
| Schema rejection | `FieldNoteProposalGate.propose()` at model lines 478-504 catches `TypeError`/`ValueError`, leaves `accepted is None`, and returns `proposal_schema_invalid`; adapter line 446 enters the umbrella | Proposal arguments or gate response code/result | No | Yes; invalid `value_level` returns the umbrella | **POSSIBLE** |
| Other gate rejection | Historical gate had only `proposal_attempt_already_consumed` beyond schema rejection. A clean adapter run cannot reach that with one distinct call ID: a second distinct ID is duplicate, and the same ID is replayed from the saved response | Gate response code plus call identities | No | Synthetic gate stub only; production path not reachable | **EXCLUDED** |
| Accepted state missing after successful gate response | Historical successful gate path assigns `self.accepted = compile_draft(...)` before returning `True`; there is no clean path returning success with missing accepted state | Gate success and accepted-state fact | No | Synthetic inconsistent gate stub returns the umbrella | **EXCLUDED** |
| Item not completed | A proposal response exists but its ID is absent from `_completed_proposal_items`, so `not all_proposals_completed` at adapter line 447 | Item-start/completion facts and response ID | No | Yes; omit `item/completed` and the umbrella returns | **POSSIBLE** |
| Item status mismatch | Completion status differs from `completed` for accepted or `failed` for rejected at adapter lines 518-540; completion is not admitted, making `all_proposals_completed` false | Observed and expected item status | No | Yes; accepted response plus `failed` completion returns the umbrella | **POSSIBLE** |
| Request/response identity mismatch | Request ID binds to another call ID at lines 354-363, replay arguments differ at lines 401-411, or completion arguments/success/content/resolution differ at lines 521-540 | Request/call/argument identities and response/completion content identities | No | Yes; mismatched completion content returns the umbrella | **POSSIBLE** |
| Inconsistent replay | Same logical call is replayed with changed start/request arguments; historical paths mark identity failure and/or malformed shape while the unique call count remains one | Both replay envelopes and their identities | No | Yes; changed arguments under one call ID return the umbrella | **POSSIBLE** |
| Proposal item protocol identity failure | Proposal request IDs/thread/turn/settings/item binding fail, or completion `_ids_match`/item identity checks fail; the item is not admitted completed and the umbrella precedes `A1_RUN_INCOMPLETE` | Latched protocol phase and exact failed identity check | No | Yes; mismatched completion thread returns the umbrella with phase `dynamic_tool_call` | **POSSIBLE** |
| Controller accepted candidate missing | Stored failure is `None` but `_eligible_creator_live_draft(...)` returns `None`, leaving `_field_note_draft is None`; candidate read raises the umbrella at controller lines 450-451 | Exact `FieldNoteCodexRunResult`, controller capture failure, and eligibility state | No | Yes only with a contract-inconsistent injected adapter result | **EXCLUDED** for the historical production adapter |

The request-shape predicate required all of the following: bounded parameter
keys; required `arguments`, `callId`, `threadId`, `tool`, and `turnId`; one
non-empty string call ID; object arguments; the exact Field Note tool;
`namespace is None`; matching thread/turn IDs; verified settings; a matching
started dynamic-tool item; and arguments equal to that started item. Failure of
any one conjunct was not separately retained.

Schema rejection covered the trusted model-class checks and any
`compile_draft()` `TypeError` or `ValueError`, including the typed Field Note
shape and value constraints. The historical terminal record retained neither
the rejected payload nor the bounded gate code.

The candidate rows overlap. For example, inconsistent replay can also set the
malformed flag, and a protocol identity failure can also prevent item
completion. PR #82 later introduced a precedence taxonomy for those overlaps;
that later precedence cannot be applied to facts that were never retained.

## Offline Reproduction Matrix

All reproduction used detached historical commit
`a033b6a7c8968d17744d0f85342b54dbfb73fa85`, the repository's fake app-server
transport, temporary repositories, and deterministic local inputs. No product
or runtime model was invoked.

| Deterministic input/state | Historical terminal | Attempts | Key observed historical state | Result |
|---|---:|---:|---|---|
| No proposal message | `A1_PROPOSAL_MISSING` | 0 | no response, no accepted state | Excludes no-call cause |
| Two distinct valid call IDs | `A1_PROPOSAL_DUPLICATE` | 2 | two responses | Excludes distinct multiple-call cause |
| One valid ID, request has unexpected field | `A1_PROPOSAL_INVALID` | 1 | malformed true; identity failure | Reproduces umbrella |
| One shape-valid call, invalid `value_level` | `A1_PROPOSAL_INVALID` | 1 | accepted missing; response completed failed | Reproduces umbrella |
| Controlled non-schema rejecting gate stub | `A1_PROPOSAL_INVALID` | 1 | accepted missing | Synthetic equivalence only; not a reachable historical production gate state |
| Controlled success-without-accepted-state gate stub | `A1_PROPOSAL_INVALID` | 1 | accepted missing | Synthetic equivalence only; violates historical gate invariant |
| Accepted proposal, no completion item | `A1_PROPOSAL_INVALID` | 1 | response count 1; completed count 0 | Reproduces umbrella |
| Accepted proposal, completion status `failed` | `A1_PROPOSAL_INVALID` | 1 | identity failure at `dynamic_tool_call` | Reproduces umbrella |
| Accepted proposal, completion content mismatch | `A1_PROPOSAL_INVALID` | 1 | response identity failure; completed count 0 | Reproduces umbrella |
| Accepted proposal, completion thread mismatch | `A1_PROPOSAL_INVALID` | 1 | protocol identity failure at `dynamic_tool_call` | Reproduces umbrella |
| Same call ID, changed replay arguments | `A1_PROPOSAL_INVALID` | 1 | malformed plus identity failure | Reproduces umbrella |
| Exact same request replay | no failure | 1 | one accepted response; one completed item | Control passes; exact replay is not itself a cause |
| Injected controller result has no failure and no candidate | `A1_PROPOSAL_INVALID` | 1 | durable failure, zero trace events, no Run 2 | Synthetic fallback equivalence; violates the production adapter contract |

Historical repository tests covering missing, duplicate, malformed, inconsistent
replay, valid exact replay, and bridge failure behavior passed 7/7. The
additional matrix cases passed through the historical adapter or controller
bridge with only local fake messages or explicitly identified
invariant-breaking stubs.

Reproduction establishes behavioral equivalence, not historical occurrence.
Many different inputs and states produce the exact protected terminal value.

## Exclusions

The protected terminal reason and historical predicate order exclude these
normal production paths:

- no proposal call: it would have terminalized as `A1_PROPOSAL_MISSING`;
- two or more distinct proposal call IDs: they would have terminalized as
  `A1_PROPOSAL_DUPLICATE`;
- direct write: it had higher precedence and would have terminalized as
  `A1_DIRECT_WRITE_REQUESTED`;
- failed read evidence, missing/mismatched runtime identity, or incomplete Run
  after an otherwise valid completed proposal: those had distinct later codes;
- an exact idempotent proposal request replay: deterministic control succeeds;
- a clean generic historical gate-policy rejection or clean success with
  missing accepted state: neither state is reachable through the historical
  gate implementation; and
- the controller's no-failure/no-candidate fallback under the production
  adapter: every adapter path that withholds the candidate first supplies a
  distinct capture failure, while its failure-free path supplies the accepted
  draft and satisfies the controller eligibility predicates.

These exclusions are bounded to the historical production adapter and clean
gate initialization. The synthetic gate and controller cases demonstrate code
equivalence only; they are not promoted into Proof 002 candidates.

## Surviving Cause Candidates

The surviving bounded family is:

1. one observed proposal call with a malformed protocol request shape;
2. one shape-valid proposal whose typed arguments failed schema compilation;
3. one accepted or rejected proposal response whose item never completed;
4. one item completion with status or response identity mismatch;
5. one inconsistent replay under a single call identity;
6. one proposal-phase protocol identity failure that prevented valid
   completion.

Candidates 3 through 6 can overlap in one transport event. Candidate 2 is the
only surviving family that can be attributed directly to semantically invalid
model-supplied proposal arguments. Candidates 1 and 3 through 6 can arise from
model-emitted tool-call behavior, transport/protocol behavior, or their
interaction.

No surviving evidence selects one member of this family.

## Root-Cause Classification

```text
B — CAUSE FAMILY NARROWED
```

This is B, rather than an exact-cause result, because the exact historical
terminal code excludes zero-call, distinct-multiple-call, direct-write, and
later non-proposal failure families, while deterministic replay bounds the
remaining umbrella-producing states.

The exact lower cause within the surviving family cannot be recovered from the
protected journal, protected anchor, or any separate local bounded receipt.
Offline reproduction cannot recreate absent historical facts; it only proves
which inputs are behaviorally equivalent.

## Repair Recommendation

### Model behavior

Possible, not proven. Schema-invalid arguments, malformed tool-call shape, a
changed replay, or failure to complete the proposal item could have originated
in Run 1 behavior. The evidence does not justify selecting any one of them or
claiming that model behavior was the cause.

### Protocol weakness

Possible, not proven. Historical request, item-completion, response-identity,
and protocol-identity failures collapsed into the same terminal umbrella. The
evidence does not distinguish model emission from transport or protocol
handling.

### Missing observability

Proven implementation defect. Historical code computed enough transient state
to choose the umbrella but did not durably retain the lower lifecycle facts or
sub-cause. Process teardown therefore made the candidates indistinguishable.

PR #82 removed this observability defect before current main. It added a typed,
payload-free, SHA-256-bound diagnostic taxonomy through the adapter,
controller, capture bridge, terminal journal, anchor, and typed readback. It
also preserved non-proposal failure-family precedence. Current main
`49a7026954405ba4ca2c9024b1cb34c5b7da0ff2` contains that merged repair.

### Remaining repairable control

No current-code repair is required by this diagnosis. The only implementation
defect proven by surviving evidence is the missing lower-cause observability,
and PR #82 already removed it. This task does not propose or implement another
change.

PR #82's code surface was bounded to A1 diagnostic capture and propagation in:

- `decision_os/companion/field_notes_adapter.py`
- `decision_os/companion/field_notes_controller.py`
- `decision_os/companion/field_notes_creator_live.py`
- `decision_os/companion/field_notes_creator_live_capture.py`

Its tests covered the lower taxonomy, legacy journal readback, terminal
durability, no Note, no Run 2, and non-proposal precedence. A2-A7 contracts and
artifacts require no change because this diagnosis identifies no defect in
those stages, Proof 002 recorded zero trace events before A2, and the existing
repair changes only A1 failure observation and propagation. There is no new
rollback plan because no new repair is recommended or implemented; PR #82's
existing rollback boundary remains its own four-file A1 control surface.

A current-main focused deterministic check of the proposal taxonomy, legacy
readback, diagnostic anchor sealing, and capture-bridge failure behavior passes
17/17. `git diff --check` also passes for this diagnosis-only change.

Any new repair requires a separately reviewed defect and fresh authority after
13-31 review. Diagnosis uncertainty is not itself authority to alter code.

## Claim Boundary

- Proof 002 remains `FAILED / A1_CAPTURE / A1_PROPOSAL_INVALID`.
- This record does not retroactively change the terminal reason to `UNKNOWN`.
- The exact lower cause is not claimed.
- The later PR #82 taxonomy is classification aid, not reconstructed evidence.
- No Note was created by this diagnosis.
- No Run 2, live attempt, runtime model invocation, journal rewrite, anchor
  rewrite, or evidence mutation occurred.
- The protected journal and anchor remain byte-identical to their supplied
  SHA-256 identities.
- Outcome B does not establish Creator-Live Proof success.

## Third Attempt Gate

```text
Third live attempt:
BLOCK / NOT AUTHORIZED

Re-entry condition:
13-31 independently reviews this diagnosis; any future proof cycle then
requires a separate Charter and explicit Shin authorization.

Current authorized next action:
Independent diagnosis review only.
```

## Canonical Base Report

```text
V12 State:
PASS

V13 Next Loop Gate:
HOLD

Reason:
The bounded diagnosis is complete at Outcome B, but no repair or third attempt
is authorized before independent 13-31 review.

Next Authorized Action:
13-31 independently reviews this diagnosis artifact.

Not Authorized:
- code repair
- third live attempt or product/runtime model invocation
- Proof 002 journal, anchor, Note, or evidence mutation

Decision Packet Required:
no

Decision Owner:
Shin

Completion Line:
One diagnosis artifact records the verified evidence, historical failure map,
deterministic reproduction, bounded Outcome B, and no-current-repair result.
```
