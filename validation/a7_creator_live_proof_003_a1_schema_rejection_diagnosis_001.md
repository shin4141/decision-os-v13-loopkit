# V13 A7 Creator-Live Proof 003 — A1 Schema-Rejection Diagnosis 001

## Diagnosis Identity

```text
Layer:
V13 — Creator-Live Whole-Flow Re-entry Cycle 001
Post-terminal A1 schema-rejection diagnosis

Repository:
shin4141/decision-os-v13-loopkit

Execution repository HEAD:
1489dcd5acd039032aa36f0d20c393815290c452

Implementation baseline:
03a39f82f832f1655d1f25fc8ae982d606c7729d

Product-code tree:
6da32a98d9a9f3b733c4536faecf8698dfde64e99629f2c1e9dac1cdc04818e9

Proof attempt:
proof_a7_creator_live_003_94a0d625f4d155f5

Run 1:
run_a7_creator_live_003_1_41c7c943066498ad

Required classification:
A — EXACT SCHEMA PREDICATE ESTABLISHED
```

This is a diagnosis-only record. It does not reopen Proof 003, repair its
proposal, authorize another attempt, or change its permanent terminal result.
No product/runtime model was invoked during this diagnosis.

## Protected Proof 003 State

Proof 003 remains durably terminal:

```text
State: FAILED
Boundary: A1_CAPTURE
Reason: A1_PROPOSAL_SCHEMA_REJECTED
Repair action: NONE
Trace events: 0
Captured Note: none
Run 2: none
```

Protected identities at diagnosis entry:

| Evidence | SHA-256 |
| --- | --- |
| Proposal diagnostic | `b0334cb3209e4a65cc7040472c82557787792c1b6c74dc78716a5c3c049f584b` |
| Journal | `d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1` |
| Anchor | `0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc` |
| Typed readback | `e50e77ce318befcd24bf6057c02aeb15d56aedff76f8600983bc41bc4b313e2b` |

Typed durable readback verifies two journal records, two anchor records, the
terminal state above, and the exact payload-free diagnostic. The diagnostic
retains one valid request shape, one proposal call, gate invocation, response
code `proposal_schema_invalid`, completed item status `failed`, no accepted
proposal, and no replay, request/response identity, or protocol-identity
failure.

## Surviving Proposal Evidence

### Exact argument recovery

The complete proposal does not survive in the protected journal or anchor.
It does survive in the bounded local Codex app-server log for the exact
ephemeral Run 1 thread:

```text
Log database:
/Users/sn/.codex/logs_2.sqlite

Thread:
019fcc91-6601-7350-b9f9-72d808a0af06

Turn:
019fcc91-6702-72f3-9c42-9704bd763e1b

Proposal log row:
104612485 at 2026-08-04 20:39:16 +09:00

Gate-response log row:
104612488 at 2026-08-04 20:39:16 +09:00
```

Row `104612485` contains the model-emitted
`propose_field_note_candidate` object. Row `104612488` contains the rejected
response `proposal_schema_invalid`. The log database is mutable operational
state, not a protected proof artifact. Its recovered arguments are nevertheless
cryptographically cross-bound to the protected diagnostic:

| Identity | SHA-256 |
| --- | --- |
| Exact emitted JS object bytes in row `104612485` | `ae808507fd9aea482b34ed3c636d241978eb2e91ae6e964935ca9a1b2bded8e6` |
| Canonical argument object used by `_arguments_identity()` | `754bc9015163c737ca6bb854cd8441d3fedb0a2bc69a4dfacd48ba1496950ebf` |
| One-element canonical identity-set aggregation | `e9129e12b78ca365aabd500392bcac7392eb0c5be0a361f2d4f5c122a270db27` |
| Protected diagnostic `arguments_identity_sha256` | `e9129e12b78ca365aabd500392bcac7392eb0c5be0a361f2d4f5c122a270db27` |

The equality of the last two values proves that the recovered log object and
the single argument object observed by the production adapter are identical
under the production identity construction. It excludes transport mutation or
an argument transformation between the logged model call and the adapter's
gate input.

### Minimum structural facts

The complete proposal is not reproduced here because the exact cause requires
only bounded structural facts and three values.

```text
Canonical argument JSON bytes: 4259

Exact top-level keys:
body
scope
source_model_class
target_model_class
title
trigger_terms
value_level

Top-level types:
body=dict
scope=dict
source_model_class=str
target_model_class=str
title=str
trigger_terms=list
value_level=int

Exact relevant values:
value_level=3
source_model_class=stronger
target_model_class=lower-cost
```

Other bounded facts are: title length 52; six unique trigger terms; exact
scope keys `task_family`, `path_prefixes`, and `exclude_terms`; three path
prefixes; three exclude terms; and the exact eight required body keys. All
body fields are non-empty. No unrelated Note content or Charter content is
needed for the diagnosis.

The bounded search found no equivalent payload in the Proof 003 directory,
installed Companion application-support storage, registered repository
worktrees, `/Users/sn/Library/Logs/com.openai.codex`, or bounded temporary
execution receipts. The production transport drains stderr into a bounded
failure category and retains no independent request-envelope file. The exited
controller/adapter process retained no inspectable in-memory state. The app-
server log row is therefore the sole surviving exact payload source.

## Advertised Tool Schema

`FIELD_NOTE_TOOL_SPEC["inputSchema"]` is defined in
`decision_os/companion/field_notes_model.py:61`. Its canonical identity at the
authorized code tree is:

```text
Canonical inputSchema bytes: 1575
SHA-256: eb5c13ca38c82b0cf5eeca3ead9469c6f2971cdc038d9b061d98bd47715288e4
```

A deterministic schema walk checked required keys, additional properties,
JSON types, enums, string bounds, list bounds, and uniqueness. The recovered
proposal passes every advertised predicate:

| Advertised predicate | Result |
| --- | --- |
| Exact top-level object and required keys | PASS |
| No additional top-level, scope, or body keys | PASS |
| Title string length 1–120 | PASS — 52 |
| Integer `value_level` in 1, 2, 3 | PASS — 3 |
| Model-class enum values | PASS — `stronger`, `lower-cost` |
| Trigger list count, uniqueness, and item lengths | PASS — 6 |
| Scope keys, types, counts, uniqueness, and lengths | PASS |
| Eight required non-empty body strings | PASS |

The schema advertises Level 3 and the emitted class pair, but contains no
predicate relating those values to the gate's runtime-only trusted source and
target model-class configuration. The model was not shown that the active
gate was configured `UNKNOWN` / `UNKNOWN`.

## Actual Gate and Compiler Constraints

### Gate configuration and first failing predicate

The normal controller construction defaults both trusted classes to `UNKNOWN`
at `decision_os/companion/field_notes_controller.py:130-135` and passes them to
the adapter. The adapter and `FieldNoteProposalGate` preserve those values.

The exact gate predicate at
`decision_os/companion/field_notes_model.py:483-490` is:

```python
value_level == 3 and (
    trusted_source_model_class != "stronger"
    or trusted_target_model_class != "lower-cost"
    or source_class != trusted_source_model_class
    or target_class != trusted_target_model_class
)
```

For Proof 003 it evaluates as:

```text
value_level: 3
emitted source / target: stronger / lower-cost
trusted source / target: UNKNOWN / UNKNOWN
predicate: true
raised condition: Level 3 trusted model classes do not match.
```

`FieldNoteProposalGate.propose()` catches that `ValueError` together with all
other gate and compiler `TypeError`/`ValueError` cases and returns only
`proposal_schema_invalid` at lines 502-504. This is the first and exact
historical failing predicate.

The proposal-attempt state was fresh when the single call entered the gate.
The diagnostic proves one call and excludes the already-consumed attempt path.

### Compiler comparison

`compile_draft()` starts at
`decision_os/companion/field_notes_model.py:319`. Direct deterministic replay
of the unmodified recovered proposal succeeds. That independently excludes
every compiler family for this exact payload:

| Compiler predicate family | Proof 003 replay |
| --- | --- |
| Exact top-level keys | PASS |
| Title bounds and one-line rule | PASS |
| `value_level` exact integer and enum | PASS |
| Model-class enums | PASS |
| Level 3 `stronger` → `lower-cost` relation | PASS |
| Trigger list type, count, uniqueness, lengths | PASS |
| Exact scope keys and bounded lists | PASS |
| Exact eight body keys and non-empty values | PASS |
| NUL, metadata-marker, heading, fence, rule, and HTML prohibitions | PASS |
| Metadata size | PASS — 881 bytes of 8192 maximum |
| Compiled Markdown size | PASS — 4646 bytes of 65536 maximum |
| Compiled metadata, heading, order, and UTF-8 integrity | PASS |

The deterministic compiler replay fixed only the generated identity and
timestamp inputs. Those inputs occur after the proven gate predicate and do
not affect it. No file was written and the compiled counterfactual was not
promoted into proof evidence.

## Offline Replay

The implementation-baseline and execution-HEAD `decision_os` Git tree objects
are both `796ff78d59e9596f58dc8e4a74c04b87d0f765ac`; there is no product-code
delta between them. Replay therefore exercised the exact authorized
implementation behavior.

| Replay | Input/configuration | Result |
| --- | --- | --- |
| Advertised schema | Unmodified recovered proposal | PASS |
| Direct compiler | Unmodified recovered proposal | PASS |
| Production gate | Unmodified proposal; trusted `UNKNOWN` / `UNKNOWN` | `(False, proposal_schema_invalid)` |
| Compiler-entry observation | Same production gate replay | `compile_draft()` call count `0` |
| Trusted-config counterfactual | Unmodified proposal; trusted `stronger` / `lower-cost` | `(True, proposal_accepted)` |
| Minimum payload counterfactual | Only `value_level: 3 → 2`; trusted `UNKNOWN` / `UNKNOWN` | `(True, proposal_accepted)` |

Both counterfactuals are model-free causal tests only. Neither edits,
resubmits, repairs, or reclassifies Proof 003. In particular, lowering the
value level would change the proposed meaning and is not a repair
recommendation.

## Exact or Bounded Failing Predicate

```text
A — EXACT SCHEMA PREDICATE ESTABLISHED
```

The single proposal was valid under the advertised tool schema and valid when
passed directly to `compile_draft()`. It was rejected before compiler entry
because its advertised-valid Level 3 classification required a runtime trusted
configuration of `stronger` / `lower-cost`, while the production controller
had configured the gate as `UNKNOWN` / `UNKNOWN`.

This conclusion is exact, not a family inference: the recovered object is
cryptographically cross-bound to the protected diagnostic; the precise gate
configuration is fixed by the production path; the exact predicate evaluates
true; the production gate reproduces the same umbrella response; and compiler
entry is not reached.

## Model vs Contract Attribution

This is **Case 2 — advertised-schema / actual-admission contract mismatch**.

| Candidate attribution | Determination | Basis |
| --- | --- | --- |
| Model-emitted argument defect | EXCLUDED | Exact arguments pass the advertised schema and direct compiler. |
| Advertised tool-schema insufficiency | PROVEN | Runtime trusted-class admission is absent from the shown schema. |
| Hidden compile constraint | EXCLUDED as this cause | The compiler accepts the exact proposal. |
| Hidden gate constraint | PROVEN | The Level 3 trusted-class predicate rejects before compiler entry. |
| Trusted runtime model-class constraint | PROVEN | Active trusted classes were `UNKNOWN` / `UNKNOWN`. |
| Transport mutation/transformation | EXCLUDED | Recovered object recomputes the protected aggregate argument identity. |
| Missing schema-level observability | PROVEN | Protected evidence retained only `proposal_schema_invalid`. |

The model selected exactly the Level 3 class pair permitted by the advertised
schema and independently required by the compiler. It is therefore incorrect
to attribute the rejection to model violation of a shown constraint.

## Observability Gap

The diagnostic correctly retained lifecycle and identity facts without
retaining payload, but `proposal_schema_invalid` conflates the exact trusted-
class rejection with every gate and compiler `TypeError`/`ValueError`.
Without the operational app-server row, the protected Proof 003 artifacts alone
could not distinguish these predicates.

A bounded subcause can be retained without storing any proposal value. For
this path, the most accurate code is:

```text
LEVEL_3_TRUSTED_CLASS_MISMATCH
```

If the taxonomy must use the coarser proposed family, it maps to
`LEVEL_3_CLASS_MISMATCH`, but the trusted-runtime qualifier should be retained
to avoid implying that the emitted `stronger` / `lower-cost` pair was invalid.
The existing payload-free `gate_response_code` can carry a stable bounded code,
so this exact cause need not require proposal retention. Compiler exceptions
can likewise be mapped at their point of origin to bounded codes such as
`TITLE_INVALID`, `TRIGGER_TERMS_INVALID`, `BODY_FIELD_INVALID`,
`METADATA_SIZE_EXCEEDED`, or `COMPILED_MARKDOWN_INVALID`.

## Potential Repair Boundary

No repair is implemented or authorized here. A later separately authorized
repair should address both admission contract and observability:

1. make the advertised proposal schema/configuration consistent with the
   actual trusted source/target classes used by the gate;
2. do not advertise an admissible Level 3 path when the active controller's
   trusted configuration makes every Level 3 proposal impossible;
3. preserve the Level 3 cross-field rule and one-shot gate;
4. return a bounded trusted-class gate code instead of
   `proposal_schema_invalid` for this predicate; and
5. retain that code through the existing payload-free A1 diagnostic and
   durable readback.

Potential production surface is bounded to the A1 proposal contract and gate:

- `decision_os/companion/field_notes_model.py`
- `decision_os/companion/field_notes_adapter.py`
- `decision_os/companion/field_notes_controller.py` only if explicit trusted
  configuration must be supplied rather than schema-specialized
- focused A1 proposal tests

Required tests should prove advertised/admitted parity for each trusted-class
configuration, exact acceptance of a configured Level 3 proposal, explicit
rejection of an unavailable Level 3 path, payload-free durable subcause
retention, one-shot behavior, and unchanged direct-write and malformed-request
precedence.

A2–A7 need no behavior or schema change: the defect occurs before A1 compiler
entry and Proof 003 emitted zero trace events. Any repair must stop at A1 and
must not change the creator-live journal, anchor, maturity, A7 admission, or
historical proof artifacts. Rollback is one bounded revert of the later A1
contract/gate change. No further live attempt is authorized by this diagnosis.

## Claude Review Packet

```text
Known facts:
- Proof 003 is permanently FAILED / A1_CAPTURE /
  A1_PROPOSAL_SCHEMA_REJECTED.
- One well-shaped proposal call reached the gate and completed as failed.
- No Note, Run 2, or A2–A7 evidence exists.

Exact emitted proposal identity:
- App-server log row 104612485, thread
  019fcc91-6601-7350-b9f9-72d808a0af06.
- Canonical argument object SHA-256:
  754bc9015163c737ca6bb854cd8441d3fedb0a2bc69a4dfacd48ba1496950ebf.
- Protected aggregate argument identity recomputes exactly to:
  e9129e12b78ca365aabd500392bcac7392eb0c5be0a361f2d4f5c122a270db27.

Advertised-schema result:
- PASS.
- Relevant emitted values: Level 3, stronger, lower-cost.

Actual compiler result:
- Direct compile PASS; metadata 881 bytes; Note 4646 bytes.
- Production gate invokes compiler zero times.

Exact failing predicate:
- Gate trusted classes UNKNOWN / UNKNOWN do not satisfy the hidden Level 3
  trusted-class predicate.
- Production replay returns proposal_schema_invalid.

Minimal counterfactual:
- Changing only value_level 3 to 2 makes the default gate accept.
- Keeping the payload exact and configuring trusted stronger / lower-cost also
  makes the gate accept.
- Neither counterfactual is proof evidence or a repair.

Proposed attribution:
- Case 2 advertised-schema / actual-admission contract mismatch.
- Model argument defect and transport mutation excluded.

Proposed bounded repair:
- Align dynamic advertised schema with active trusted configuration.
- Return and durably retain LEVEL_3_TRUSTED_CLASS_MISMATCH without payload.
- A1-only; A2–A7 unchanged.

Uncertainties:
- Product policy must decide whether creator-live Level 3 should configure
  trusted stronger/lower-cost or should be unavailable when trust is UNKNOWN.
- Repair design and taxonomy naming remain subject to 13-31 and Claude review.
```

This packet is prepared only for later review. Claude was not contacted in
this task.

## Claim Boundary

- Proof 003 remains permanent `FAILED / A1_CAPTURE /
  A1_PROPOSAL_SCHEMA_REJECTED`.
- Outcome A identifies the lower rejection predicate; it does not turn any
  Proof 003 output or counterfactual into proof evidence.
- The emitted proposal was not edited, resubmitted, or saved.
- No Note, Run 2, A2–A7 checkpoint, Whole-Flow Proof Receipt, or Portable
  Candidate Warehouse Manifest exists for Proof 003.
- Proof 001 and Proof 002 remain unchanged.
- No model invocation, new proof identity, retry, replacement, repair,
  installation, restart, release, publication, or Warehouse action occurred
  during this diagnosis.
- The operational app-server log is supporting forensic evidence, not a
  protected proof artifact and not permission to rewrite the protected record.

## Current Gate

```text
Diagnosis:
COMPLETE — A / exact trusted-class gate predicate established

Proof 003:
PERMANENT FAIL

Live Proof Gate:
BLOCK

Repair Gate:
BLOCK pending 13-31 independent review, Claude adversarial consultation, and
separate repair authorization
```
