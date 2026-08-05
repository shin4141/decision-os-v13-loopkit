# V13 Creator-Live Cycle 004 — A1 Chronology Authority Diagnosis 001

## Diagnosis Identity

```text
Layer:
V13 — Creator-Live Whole-Flow
Post-terminal A1 chronology authority diagnosis

Repository:
shin4141/decision-os-v13-loopkit

Exact base:
8e8a97956a39b7ca90bf099023cf1126a934ec35

Cycle:
Creator-Live Whole-Flow Re-entry Cycle 004

Proof attempt:
proof_a7_creator_live_005_1f0c0263566af0a8

Permanent result:
FAILED / A1_CAPTURE / A1_CAPTURE_CHRONOLOGY_INVALID

Classification:
B — DURABLE PROOF-AS-OF SCHEMA GAP
```

This record is diagnosis-only. It does not retry, reopen, continue, replace,
repair, or reinterpret Cycle 004. It introduces no production or test change,
does not invoke a product/runtime model, and does not authorize another live
cycle.

## Protected Cycle 004 Boundary

The following local evidence was read without editing, moving, normalizing,
reconstructing, or rewriting it.

| Evidence | Exact identity or result |
| --- | --- |
| Proof attempt | `proof_a7_creator_live_005_1f0c0263566af0a8` |
| Run 1 | `run_a7_creator_live_005_1_f4e81804b24bd653` |
| Run 2 | Not created |
| Saved Note ID | `fn_575e4a7630fbe3020af3f7c1f85e5b9b` |
| Saved Note SHA-256 | `e3f49d578dd525c0a8c8ffdf90374c50ab00167e684fbdae991d7d2d24ff9cdd` |
| Journal SHA-256 | `5e329626cc9b23fa800ddf53fc2a5ff637a38da58442d1e1c01d7eee00a27f6b` |
| Anchor SHA-256 | `c434ff5e4e38b45bd8f8d497fb51d11bcc5ad050d8e29ed2025b514e0bb9a4d0` |
| Typed readback SHA-256 | `e3a6a44d0c9b3fe51d6f469d62f355defdcf44e70cfd02332ef38501c628b2c2` |
| Durable state | `FAILED / A1_CAPTURE / A1_CAPTURE_CHRONOLOGY_INVALID` |
| Durable repair classification | `TIMESTAMP_CHANGE` |
| Checkpoint count | `0` |
| Journal / anchor record counts | `2 / 2` |

The A1 model, proposal, schema, gate, completion, save, and exact Note readback
paths succeeded. The failure occurred when the runtime tried to admit the saved
draft as the first durable A1 checkpoint.

## Exact Contradiction

The durable and saved evidence retains:

```text
authorization observation / attempt proof_as_of:
2026-08-05T01:06:00Z

Run 1 start:
2026-08-05T01:13:51.199055Z

draft creation:
2026-08-05T01:14:45Z
```

Production requires:

```text
run_1_started_at
<= draft_created_at
<= save_as_of
<= observed_at
<= proof_as_of
```

The draft alone is eight minutes and forty-five seconds after the immutable
`proof_as_of`. Therefore no value of the later save or observation instants
could satisfy the predicate. This proves
`ORCHESTRATION_TIMESTAMP_AUTHORITY_MISMATCH` without requiring the lower
in-memory save timestamp to survive.

## Existing Contract Map

### Attempt construction

`FieldNoteWholeFlowAttempt` requires `proof_as_of` at construction. It has no
`authorization_observed_at`, no runtime-issued `attempt_opened_at`, and no
separate terminal cutoff. Its `as_dict()` output includes the caller-supplied
`proof_as_of` as part of the attempt identity.

### Attempt opening and journal authority

`FieldNoteCreatorLiveProofRuntime.open_attempt()` requires the typed attempt
before Run 1 dispatch. It writes `attempt.as_dict()` into the initial
`ATTEMPT_OPENED` record under an exclusive-create, append-only journal. The
runtime does not issue a new Proof As-of at opening and cannot defer that field
until evidence exists.

`_static_identity()` reconstructs the same attempt only from the first journal
record. Every subsequent readback therefore inherits the opening value.

### A1 checkpoint admission

`_a1_capture_chronology_is_valid()` parses the five instants and requires:

```python
run_time <= draft_time <= save_time <= observed_time <= proof_time
```

`record_a1_capture()` obtains a truthful checkpoint observation from the
runtime clock, but compares it to `self._static.attempt.proof_as_of`, which was
already fixed before Run 1. It cannot issue a post-observation cutoff.

### Later trace and A7 verification

The same opening value remains authoritative beyond A1:

- every typed trace event must be no later than the receipt `proof_as_of`;
- A6 review must be no later than the attempt `proof_as_of`;
- `_receipt()` copies `bundle.attempt.proof_as_of` into
  `FieldNoteWholeFlowProofReceipt`;
- creator-live PASS validation compares A1 save and observation against that
  receipt field;
- `verify_field_note_whole_flow()` rejects a Proof As-of preceding A6 and any
  trace observation after it;
- portable-candidate output is derived from the same verified receipt.

No current journal, readback, receipt, or verification surface provides an
independently issued terminal Proof As-of.

## Classification Decision

### A — ORCHESTRATOR BINDING GAP: excluded

Classification A requires the existing durable schema to accept a truthful
Proof As-of issued after evidence observation. It does not.

The caller must supply `proof_as_of` before `open_attempt()`, and the attempt
must be open before the A1 bridge will dispatch Run 1. Supplying a value after
A1 observation is therefore unavailable. Supplying a value that happens to be
later would be a guessed future timestamp, not a post-observation authority.

Moving only the caller binding cannot fix this while preserving both the
append-only attempt identity and the existing chronology invariant.

### B — DURABLE PROOF-AS-OF SCHEMA GAP: established

The immutable attempt conflates three distinct authorities:

1. the Decision Owner's authorization observation;
2. the runtime's attempt-opening observation; and
3. the terminal evidence cutoff after the last admitted observation.

Only one caller-supplied field exists, and it is fixed before all three runtime
events can be known. The contradiction is structural and deterministically
reproducible from current code plus protected Cycle 004 evidence.

### C — CAUSE NOT BOUNDED: excluded

The exact predicate, timestamp ordering, append-only write point, and later
receipt propagation all survive. No missing lower cause prevents
classification.

## Narrowest Required Schema Delta

A separately authorized schema task must represent three non-substitutable
instants:

| Authority | Required owner | Required timing |
| --- | --- | --- |
| `authorization_observed_at` | Decision Owner / authorized caller evidence | At or before attempt opening |
| `attempt_opened_at` | Creator-live runtime clock | Issued while durably opening the attempt, before Run 1 |
| terminal `proof_as_of` | Creator-live runtime terminalization clock | Issued only after the final admitted observation or terminal failure |

The terminal Proof As-of must not be caller-supplied at attempt opening. The
runtime must make guessed future values unavailable rather than merely reject
some guesses.

The chronology must remain strong, split into truthful phase predicates:

```text
authorization_observed_at
<= attempt_opened_at
<= run_1_started_at
<= draft_created_at
<= save_as_of
<= A1 observed_at

last admitted observed_at
<= terminal proof_as_of
```

For a pre-checkpoint failure, terminalization still needs a runtime-issued
terminal cutoff bound to the failure record. No timestamp may be rewritten
after terminalization.

## Affected Durable Surfaces

The narrow schema delta requires explicit review of:

1. `decision_os/companion/field_notes_whole_flow.py`
   - attempt identity and serialization;
   - proof receipt identity and serialization;
   - PASS chronology and proof-trace validation;
   - A6 / Proof-As-of ordering;
   - portable candidate derivation from the receipt.
2. `decision_os/companion/field_notes_creator_live.py`
   - `ATTEMPT_OPENED` payload and journal schema;
   - runtime issuance of `attempt_opened_at`;
   - A1 chronology admission without a guessed terminal cutoff;
   - `ATTEMPT_FAILED` and `TRACE_COMPLETED` terminal Proof-As-of issuance;
   - static identity parsing, typed readback projection, and schema identity;
   - append-only and anchor readback verification.
3. `decision_os/companion/field_notes_creator_live_capture.py`
   - A1 preflight binding to authorization/opening authority;
   - production clock ownership at save and checkpoint observation.
4. Focused creator-live, capture, and Whole-Flow tests.
   - no A2 selection, A3 maturity, ordinary reconnect, or product/runtime
     behavior change is justified by this diagnosis.

The anchor algorithm can continue to bind exact journal bytes, counts, and
chain heads, but its protected identity necessarily changes for a new attempt
whose journal schema changes. Historical v0.1 artifacts must remain readable
and immutable.

## Required Test-First Gate for the Schema Task

Before production changes, the separately authorized schema task must add a
model-free vertical test proving:

1. authorization before Run 1 is valid authorization evidence;
2. authorization time cannot populate terminal Proof As-of;
3. a realistic startup delay does not doom A1;
4. `Run <= draft <= save <= A1 observation` remains enforced;
5. terminal Proof As-of cannot precede the last observation;
6. callers cannot supply a guessed future terminal cutoff;
7. terminal timestamp mutation and post-failure continuation remain rejected;
8. Cycle 004 protected hashes remain exact;
9. zero product/runtime model invocation is sufficient.

This diagnosis does not add that test because classification B explicitly
requires a diagnosis-only Draft PR with no production or test change.

## Repair and Live Gates

```text
Schema implementation:
HOLD — not authorized in this task

Cycle 004:
PERMANENT FAILED — no retry, reopen, continuation, replacement, or rewrite

New live cycle:
BLOCK

Product/runtime model invocations during diagnosis:
0
```

## Claim Boundary

This diagnosis establishes only that the current immutable v0.1 attempt cannot
truthfully carry a terminal Proof As-of issued after later evidence. It does
not establish a new schema, prove a future live cycle, change the meaning of
any historical attempt, or authorize installation, restart, release,
publication, or live execution.

One truthful authorization-to-Proof-As-of contract requires a separately
authorized durable schema delta; no future time was fabricated and Cycle 004
remains unchanged.
