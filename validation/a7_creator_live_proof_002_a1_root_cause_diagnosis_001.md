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

The original historical diagnosis, standing alone, required no additional
current-code repair: the only defect proven by Proof 002's surviving evidence
was the missing lower-cause observability removed by PR #82. The later
adversarial reconciliation below independently proves one current A1 taxonomy
defect. It does not change Outcome B or establish what happened in Proof 002,
but it supersedes the earlier no-repair conclusion for the current-control
assessment. Repair remains unauthorized in this PR.

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

## Claude Adversarial Review Reconciliation

### Scope and method

Claude's `PASS WITH BOUNDED CONDITIONS` was structural and did not inspect the
repository or PR. This reconciliation inspected the historical implementation
at `a033b6a7c8968d17744d0f85342b54dbfb73fa85`, the current application code at
`49a7026954405ba4ca2c9024b1cb34c5b7da0ff2`, and the protected Proof 002
readback. It then used only the repository fake app-server transport,
temporary repositories, deterministic envelopes, and local fault injection.
No product/runtime model was invoked and no live attempt was made.

The current focused suites passed 136/136 after the matrix and fault checks.
The one-off harness lived outside the repository and is not a product change or
PR artifact.

The seven requested determinations are:

| Item | Classification | Determination |
|---|---|---|
| 1. Attempt-count timing | **CONFIRMED** | A proposal identity is counted after params parsing and request-ID validation, but before full request-shape validation, gate invocation, and completion. Two production-format malformed deliveries select `A1_PROPOSAL_MISSING` despite retained malformed facts. |
| 2. Same-identity multiple delivery | **CONFIRMED** | Changed identities are separated, but an exact request replay and an exact duplicate completion are deliberately idempotent and diagnostically indistinguishable from a single delivery. |
| 3. Accepted-state absence | **EXCLUDED** | `gate success + completed item + accepted absent` is not reachable through the production gate implementation. |
| 4. Diagnostic discrimination | **CONFIRMED** | All seven requested failures produce distinct final reasons, distinct `final_subcause` values, and distinct sealed diagnostics that survive exact readback. |
| 5. Overlapping failures | **CONFIRMED** | `final_subcause` is precedence-selected while the tested coexisting facts remain retained. No required causal-order field was demonstrated. |
| 6. Exception and teardown durability | **CONFIRMED** | Pre-result and propagation exceptions terminalize to bounded durable families; zero-byte terminal append and pre-persistence teardown leave a valid but observationally ambiguous OPEN state; anchor failure fails closed as a journal/anchor mismatch. |
| 7. A2-A7 writer boundary | **CONFIRMED** | A1 and A2-A6 share terminal construction, journal append, anchor append, and readback. A7 has no checkpoint writer; it consumes the completed durable readback for admission. |

These current-code determinations do not reconstruct missing Proof 002 facts.
Whether any current-taxonomy replay or lifecycle detail occurred in Proof 002
is **UNRESOLVABLE** from the protected artifacts. The historical Outcome B is
unchanged.

### 1. Attempt-count timing

Current dispatch at `field_notes_adapter.py:940-950` recognizes the proposal
route only when params is already an object and its `tool` is the exact Field
Note tool. Within that route, `field_notes_adapter.py:545-673` performs these
steps in this exact order:

1. Read the outer request ID.
2. Parse the already-object params with `_require_object()`.
3. Parse `callId` and `arguments`.
4. Validate the request-ID type at lines 559-567; an invalid request ID returns
   before call-identity counting.
5. Retain the request identity for a valid request ID.
6. Add a non-empty string `callId` to the distinct call-ID set at lines
   581-585. Missing, empty, or non-string `callId` is only marked malformed.
7. Check request-ID binding and the complete request shape at lines 586-632.
8. Invoke the gate at lines 655-660 only after shape acceptance.
9. Observe and validate completion later at lines 876-936.
10. After the underlying run returns, compute
    `all_proposals_completed` and construct the diagnostic at lines 952-968.

The responder contains a defensive non-object check at lines 547-555, but the
production dispatch guard prevents a non-object params value from reaching
that responder. It falls to the base dynamic-tool parser, which raises before
current A1 proposal-diagnostic construction; the controller/capture path then
terminalizes the pre-result family as `A1_RUN_FAILED`. It is not proof of a
zero-count proposal diagnostic. The two zero-count cases below do traverse the
production proposal route.

`_proposal_final_subcause()` checks distinct call count zero before malformed
shape at lines 691-699. Deterministic current-main inputs prove the consequence:

| Input | Count | Retained facts | Final result | Classification |
|---|---:|---|---|---|
| Proposal request with the correct tool and arguments but no `callId` | 0 | `request_shape_valid=false`, `malformed_observed=true`, `protocol_identity_failure=true`, phase `dynamic_tool_call`, item start observed | `A1_PROPOSAL_MISSING`; diagnostic `15e7b3ecf1c02ac6aae909c09861798fa8ed1ed3dfa66242d82e106222b6b746` | **CONFIRMED** |
| Otherwise valid proposal request whose outer request ID is boolean `true` | 0 | the same malformed/shape/protocol facts, item start observed | `A1_PROPOSAL_MISSING`; diagnostic `11ab482d5eecf508ed0af9aa4d0ce1948cb05ff29dc574dbc3a91bbe67dbfe93` | **CONFIRMED** |
| Valid non-empty `callId`, then an unexpected params key | 1 | malformed and request-shape-invalid facts | `A1_PROPOSAL_REQUEST_SHAPE_INVALID` | **CONFIRMED** control |

Therefore a production-reachable malformed proposal envelope can be
misclassified as missing. The diagnostic facts expose the contradiction, but
the final reason remains wrong. This is a current A1 taxonomy defect.

The same high-level ordering existed historically: Proof 002's historical
`A1_PROPOSAL_INVALID` required one distinct non-empty call identity after the
historical zero-count check. The current defect therefore does not add
zero-identity malformed requests to Proof 002's surviving family and does not
change Outcome B.

### 2. Same-identity multiple delivery

Current state uses sets for distinct call IDs, request identities, argument
identities, and completed item IDs. Saved responses are replayed for an exact
request identity. The resulting behaviors are:

| Delivery | Current behavior | Diagnostic separation | Classification |
|---|---|---|---|
| Exact request replay: same request ID, call ID, and arguments | Re-sends the saved response; gate runs once; accepted result remains valid | None from a singleton. The complete diagnostic and its SHA-256 equal the one-delivery baseline | **CONFIRMED** |
| Same call ID with changed arguments | A replayed start and matching changed request latch `inconsistent_replay`; final is `A1_PROPOSAL_INCONSISTENT_REPLAY`. A changed request that no longer matches its started item is instead request-shape invalid | Both malformed variants are separated from exact replay; the coherent changed replay has `inconsistent_replay=true` | **CONFIRMED** |
| Repeated request ID with a changed call ID | The second distinct call ID is counted; request binding mismatch is latched | Final is `A1_PROPOSAL_DUPLICATE`; diagnostic also retains `proposal_call_count=2`, `request_identity_mismatch=true`, `response_identity_mismatch=true`, and protocol failure | **CONFIRMED** |
| Exact duplicate completion delivery | The completed-item set remains unchanged and the run succeeds. A changed duplicate completion instead latches status, response, or protocol failure | Exact delivery has no separation from a singleton; changed delivery is separated. The exact duplicate's complete diagnostic and SHA-256 equal the one-completion baseline | **CONFIRMED** |

Thus the taxonomy separates both changed-identity cases. It intentionally does
not retain delivery multiplicity for exact idempotent request replay or exact
duplicate completion. That is a remaining forensic observability gap, but the
tests demonstrate no control failure or incorrect terminal decision from it.
Whether an exact replay or duplicate completion happened in Proof 002 is
**UNRESOLVABLE**, not evidence for a historical cause.

### 3. Accepted-state absence

`FieldNoteProposalGate.propose()` at current `field_notes_model.py:474-505`
sets `self.accepted = compile_draft(...)` before returning
`(True, "proposal_accepted")`. Every caught schema exception first resets
`accepted` to `None` and returns failure. The adapter response success is the
gate boolean, and completion expectation is derived from that saved response.

Consequently this conjunction is **EXCLUDED** in production current code:

```text
gate_response_success = true
+ proposal item validly completed
+ accepted_proposal_present = false
```

The historical implementation had the same invariant. An invariant-breaking
gate stub can reach `A1_PROPOSAL_ACCEPTED_STATE_MISSING`, but it is not evidence
of production reachability and is not promoted into the Proof 002 candidate
family.

### Offline discrimination results

The seven required cases were each run independently on current main. All used
one non-empty call ID and one request identity. The fields common to every
diagnostic were:

```text
schema: decision-os.field-note-a1-proposal-diagnostic.v0.1
proposal_call_count: 1
call_identity_sha256:
  359100513a0d50c2b2dffed714e0d9898959c67dd5416e7398f355dc4bf216a3
request_identity_sha256:
  f0be939e8378151881dbf396d4956a72ecbae787ecad90158c83d02ce4442685
item_start_observed: true
request_identity_mismatch: false
direct_write_identity: null
```

The valid-arguments identity was
`c725a7448f5e3d7e6e15c85390f183e07cd3f06a9b5716a09ff5a59776e7b854`;
the schema-rejected arguments identity was
`27833264cba5330ab9f1a28d2279e23563a1c380df07c9c2dc970cc4c05368e3`.
Together with the common fields above, this table records every retained
diagnostic field:

| Case | Shape / malformed | Gate invoked; code; success; accepted | Completion; observed / expected; all completed | Response mismatch / inconsistent replay | Protocol failure / phase | Final reason and `final_subcause` | Diagnostic SHA-256 |
|---|---|---|---|---|---|---|---|
| Request shape invalid | `false / true` | `false; null; null; false` | `true; completed / failed; false` | `false / false` | `true / dynamic_tool_call` | `A1_PROPOSAL_REQUEST_SHAPE_INVALID` | `90da806ccfcd059bd75fee4bdb38ec074425dd331b8b75fdcf2a5d7b167b6d87` |
| Schema rejected | `true / false` | `true; proposal_schema_invalid; false; false` | `true; failed / failed; true` | `false / false` | `false / null` | `A1_PROPOSAL_SCHEMA_REJECTED` | `d7f05aae6e060d21f9648be3c74e3bb04ab25f7db50201c43562696d6c5dfb59` |
| Item not completed | `true / false` | `true; proposal_accepted; true; true` | `false; null / null; false` | `false / false` | `false / null` | `A1_PROPOSAL_ITEM_NOT_COMPLETED` | `935c1386c172ad3d3c099e633bad71a06066a029b878b5ce8d9875f2b8c5d39f` |
| Item status mismatch | `true / false` | `true; proposal_accepted; true; true` | `true; failed / completed; false` | `false / false` | `true / dynamic_tool_call` | `A1_PROPOSAL_ITEM_STATUS_MISMATCH` | `c05ffd2e2b13c3c0b7c016de257a99c9fc4b778b4e9420ddd80d4d1369d35c00` |
| Response identity mismatch | `true / false` | `true; proposal_accepted; true; true` | `true; completed / completed; false` | `true / false` | `true / dynamic_tool_call` | `A1_PROPOSAL_RESPONSE_IDENTITY_MISMATCH` | `a23d347cdd37f865d713165a33a821b4eaeafbbafb007a560dd763e5bdb0aac9` |
| Inconsistent replay | `false / true` | `true; proposal_accepted; true; true` | `true; failed / completed; true` | `false / true` | `true / dynamic_tool_call` | `A1_PROPOSAL_INCONSISTENT_REPLAY` | `b8106aad25a0c9f73777f3a23a30178577c00454b807ab1279177a8b126b863e` |
| Protocol identity failure | `true / false` | `true; proposal_accepted; true; true` | `true; completed / null; false` | `false / false` | `true / dynamic_tool_call` | `A1_PROPOSAL_PROTOCOL_IDENTITY_FAILURE` | `db17355b5dcb0ba1079286291c24c130e509063008fdafaebb66f72919964a2f` |

For every row, terminal persistence and typed readback produced:

```text
state: FAILED
failure_boundary: A1_CAPTURE
failure_reason: exact final_subcause above
journal_record_count: 2
anchor_record_count: 2
trace_event_count: 0
durable_readback_verified: true
read-back diagnostic: byte-canonical object equality with the adapter diagnostic
```

No two required cases have the same final reason, `final_subcause`, diagnostic
SHA-256, or full diagnostic object. Indistinguishability among the seven cases
is therefore **EXCLUDED** on current main.

### 5. Overlapping failures

Two deterministic overlaps were injected:

| Simultaneously true facts | Selected `final_subcause` | Retained non-selected facts | Durable result |
|---|---|---|---|
| Gate schema rejection plus completion status `completed` when `failed` was expected | `A1_PROPOSAL_ITEM_STATUS_MISMATCH` | `gate_response_code=proposal_schema_invalid`, gate failure, accepted absent, observed/expected statuses, protocol failure | Exact diagnostic survives in a two-record failed journal and two-record anchor |
| Same-call changed-argument replay plus request-shape failure | `A1_PROPOSAL_INCONSISTENT_REPLAY` | `request_shape_valid=false`, malformed, accepted gate result, item statuses, protocol failure | Exact diagnostic survives in a two-record failed journal and two-record anchor |

All relevant tested facts remain retained. `final_subcause` is a precedence
selection, not a claim that the other facts did not occur. In the first input,
the retained schema gate result identifies the first meaningful rejection even
though status mismatch has higher final precedence. In the second input, the
known changed replay explains the later shape failure. The aggregate diagnostic
does not timestamp events, but these tests did not produce two opposite causal
orders with an identical diagnostic and different needed decisions. Causal
ordering would be forensically useful, not required by the demonstrated
control behavior; no ordering field is proposed.

### 6. Exception and teardown durability

Fault injection produced the following exact durable states:

| Injection | Raised surface | Durable state after removing the fault | Observational result | Classification |
|---|---|---|---|---|
| Adapter exception before a Run result or proposal diagnostic exists | Bridge error `A1_RUN_FAILED` | `FAILED / A1_CAPTURE / A1_RUN_FAILED`; journal 2, anchor 2, durable true, no diagnostic | Exact run-failure family retained; lower exception detail is intentionally absent | **CONFIRMED** |
| Controller diagnostic accessor raises during capture propagation | Bridge error `A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE` | `FAILED / A1_CAPTURE / A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE`; journal 2, anchor 2, durable true, no diagnostic | Exact bounded propagation family retained | **CONFIRMED** |
| First `os.write` of A1 terminal append raises before writing bytes | Raw injected `OSError` | Prior valid `OPEN / A1_CAPTURE`; physical and projected journal 1, anchor 1, durable true, no terminal reason or diagnostic | Observationally ambiguous after teardown: no durable distinction between not-yet-terminal and failed-to-persist terminal | **CONFIRMED** |
| First `os.write` of A2 terminal append raises before writing bytes | Raw injected `OSError` | Prior valid `OPEN / A2_RECONNECT`; physical and projected journal 3, anchor 3, one A1 trace event, durable true | Same ambiguity at a non-A1 stage, proving shared writer behavior | **CONFIRMED** |
| A1 journal terminal record and diagnostic fsync, then anchor write raises | Raw injected `OSError` | Physical journal 2 with diagnostic, physical anchor 1; typed readback `FAILED / RUNTIME_ENFORCEMENT / CREATOR_LIVE_DURABLE_JOURNAL_ANCHOR_MISMATCH`, durable false and fail-closed projected counts 0 | Integrity failure is unambiguous; the unanchored intended terminal semantic is not admissible | **CONFIRMED** |
| Proposal completes and controller retains `A1_PROPOSAL_SCHEMA_REJECTED`, then teardown is injected before `record_stage_failure` persists | Injected teardown error | Prior valid `OPEN / A1_CAPTURE`; physical and projected journal 1, anchor 1, durable true, no diagnostic | After process loss, the attempted failure is observationally indistinguishable from an attempt that never terminalized | **CONFIRMED** |

The zero-byte append and pre-persistence teardown windows are real
observability limits. The anchor-write case correctly fails closed rather than
trusting journal bytes that lack a matching anchor generation. These tests do
not demonstrate that the shared append algorithm corrupts an already admitted
state, nor do they establish a bounded way to persist a terminal fact when the
same persistence medium refuses the write. They therefore do not, by
themselves, authorize a shared A2-A7 writer repair.

### 7. A1-only and shared-writer boundary

Current `_STAGES` contains A1 through A6. The exact boundary is:

| Facility | A1 | A2-A6 | A7 |
|---|---:|---:|---:|
| Proposal diagnostic construction and precedence | Yes | No | No |
| Controller/capture diagnostic propagation | Yes | No | No |
| Terminal `ATTEMPT_FAILED` construction through `_terminal_failure()` | Yes | Yes | No A7 stage writer |
| Journal append and fsync through `_append()` | Yes | Yes | No direct A7 append |
| Anchor append and fsync through `_append()` | Yes | Yes | No direct A7 append |
| Typed durable readback | Yes | Yes | Yes, as admission input |

`_terminal_failure()` constructs the shared terminal payload at current
`field_notes_creator_live.py:1899-1950`; `_append()` performs the common journal
then anchor writes at lines 1813-1897; `_emit()` uses the same append path for
A1-A6 and writes `TRACE_COMPLETED` after A6 at lines 1972-2022. A7 admission is
the `matches_admission()` check over a complete, durable readback at lines
1100-1131. It does not own another checkpoint append.

The A2 fault injection reached a genuine `A2_RECONNECT` state with one retained
A1 trace event before exercising the same zero-byte terminal append. This
confirms the shared writer failure mode. It does not show an A2-A7 semantic or
contract defect. No A2-A7 code change is requested.

### Confirmed concerns

- malformed proposal deliveries can be final-classified as missing because
  call count zero precedes retained request-shape facts;
- exact request replay and exact duplicate completion are not separately
  counted for forensics;
- overlapping failure facts are aggregate-retained while one final subcause is
  precedence-selected; and
- terminal append and teardown-before-persistence can leave the prior valid
  OPEN record as the only durable truth.

### Excluded concerns

- production gate success with completed item and missing accepted state;
- collision or loss of discrimination among the seven requested current-main
  proposal failure cases;
- loss of coexisting facts in either injected overlap;
- need for a causal-order field based on the tested overlaps; and
- need to change A2-A7 semantics because of the A1 attempt-count defect.

### Remaining observability gaps

1. The diagnostic cannot distinguish a singleton from an exact idempotent
   request replay or exact duplicate completion.
2. Aggregate overlap fields carry no event timestamps. The current tests do
   not establish a decision ambiguity that requires adding order fields.
3. A process loss before the first terminal journal byte is written leaves only
   the earlier OPEN state. This is shared by A1-A6 terminal recording.
4. An anchor-write failure makes the unanchored journal tail inadmissible; the
   typed readback retains the integrity-failure family, not the intended lower
   terminal cause.
5. None of these current observations fills Proof 002's missing historical
   diagnostic. Its exact lower cause remains **UNRESOLVABLE** within Outcome B.

### Concrete current defect and bounded repair recommendation

One current implementation defect is **CONFIRMED** independently of Proof 002:
a proposal request that is observably malformed before acquiring a valid call
identity can be labeled `A1_PROPOSAL_MISSING`, even though
`request_shape_valid=false`, `malformed_observed=true`, and proposal-phase
protocol failure are retained.

A current-code repair is actually required for accurate A1 taxonomy, but it is
not authorized in PR #84. The bounded future repair proposal is:

```text
Defect:
  Zero distinct valid call IDs has unconditional precedence over an observed
  malformed proposal request.

Affected production file:
  decision_os/companion/field_notes_adapter.py

Affected test file:
  tests/test_field_notes_lite.py

Required tests:
  - no proposal request remains A1_PROPOSAL_MISSING;
  - missing/empty/non-string callId on an observed proposal request becomes
    A1_PROPOSAL_REQUEST_SHAPE_INVALID with the existing retained cofacts;
  - invalid outer request identity on an otherwise recognizable proposal
    request becomes A1_PROPOSAL_REQUEST_SHAPE_INVALID;
  - valid shape, schema rejection, duplicate distinct IDs, inconsistent replay,
    completion mismatch, protocol failure, and durable roundtrip remain exact;
  - non-proposal failure precedence remains unchanged.

Expected behavior:
  "missing" means no recognizable proposal request was delivered. An observed
  malformed proposal request is classified by its retained malformed/shape
  facts even when no valid call identity can be counted.

Rollback:
  Revert only the future A1 precedence predicate and its focused tests if any
  existing failure-family invariant regresses. No artifact migration is needed
  because the existing diagnostic schema already retains the required facts.

A2-A7 proof of no change:
  The predicate and facts live entirely in the A1 adapter. Controller, capture
  bridge, shared terminal writer, journal schema, anchor schema, typed readback,
  A2-A6 checkpoints, TRACE_COMPLETED, and A7 admission need no change.
```

The shared zero-write and teardown gaps are recorded as failure-mode limits,
not folded into this bounded repair. A separate shared-writer change would
require an independently demonstrated contract defect and separate authority.

### Exact reconciliation claim boundary

- Original result remains **B — CAUSE FAMILY NARROWED**.
- Proof 002 remains `FAILED / A1_CAPTURE / A1_PROPOSAL_INVALID`.
- The current malformed-as-missing defect is proven on current code; it is not
  claimed as Proof 002's historical cause.
- PR #82 removed the historical missing-diagnostic defect, but it did not remove
  the newly confirmed attempt-count precedence defect.
- The seven requested current failure families are mutually discriminated and
  durably round-trip under successful persistence.
- Exact benign replay and duplicate completion delivery counts are not retained.
- Terminal write refusal and teardown before persistence can leave only an OPEN
  durable state; anchor failure instead fails closed as an integrity mismatch.
- A current repair is required only for the A1 taxonomy defect and is **NOT
  AUTHORIZED** until 13-31 independently reviews this diagnosis.
- No implementation, Note, Run 2, live attempt, model invocation, journal
  mutation, anchor mutation, or evidence rewrite occurred in this
  reconciliation.
- Third live attempt remains **BLOCK / NOT AUTHORIZED**.

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
The bounded historical diagnosis remains complete at Outcome B. Adversarial
reconciliation proves one current A1 taxonomy defect, but no repair or third
attempt is authorized before independent 13-31 review.

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
One diagnosis artifact records the verified historical evidence and Outcome B,
the current deterministic adversarial reconciliation, and one bounded but
unauthorized A1 repair requirement.
```
