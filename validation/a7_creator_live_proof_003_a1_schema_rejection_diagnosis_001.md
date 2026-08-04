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

Under SHA-256 collision resistance and the bounded log-row binding, equality of
the last two values supports canonical identity equivalence between the
recovered object and the argument identity observed by the adapter. It
conditionally excludes a value-changing transport mutation on the single
Proof 003 proposal path. The aggregate is not an injective encoding of ordered
or repeated argument collections; the exact limitation is enumerated below.

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
| Transport mutation/transformation | CONDITIONALLY EXCLUDED | Recovered object recomputes the protected aggregate under SHA-256 collision resistance and the bounded log binding; aggregation is not injective over ordered multisets. |
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

A bounded subcause can be retained without storing any proposal value. Static
reach audit separates two codes:

```text
LEVEL_3_TRUST_NOT_CONFIGURED
LEVEL_3_TRUST_CLASS_MISMATCH
```

The first means active runtime trust does not make Level 3 available. The
second means an otherwise Level-3-capable asserted configuration disagrees
with the emitted classes. Proof 003 is the first case. The existing payload-
free `gate_response_code` can retain the exact distinction while the existing
`A1_PROPOSAL_GATE_REJECTED` final subcause identifies the common terminal
family. No proposal payload, free text, or diagnostic-schema change is needed.

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
- Model argument defect excluded; transport mutation conditionally excluded
  under SHA-256 collision resistance and the bounded log-row binding.

Proposed bounded repair:
- Align dynamic advertised schema with active trusted configuration.
- Return and durably retain LEVEL_3_TRUST_NOT_CONFIGURED separately from
  LEVEL_3_TRUST_CLASS_MISMATCH, without payload.
- A1-only; A2–A7 unchanged.

Fixed policy after review:
- Option A: UNKNOWN / UNKNOWN is fail-closed for Level 3 and Level 3 is not
  advertised.
- No trust inference from runtime identity or proposal content is permitted.
- Repair remains subject to separate authorization.
```

Claude was not contacted during the original diagnosis. Its subsequent
adversarial review is reconciled below without another model invocation in
this static audit.

## Claude Adversarial Review Reconciliation

Claude returned `PARTIAL AGREEMENT`. The complete production reach audit
confirms the historical Outcome A and Case 2 attribution, and accepts the
following refinements:

- the advertised/admitted mismatch and the terminal-code category error are
  co-equal defects;
- `UNKNOWN / UNKNOWN` is fail-closed for Level 3 under fixed Option A;
- transport mutation is only **CONDITIONALLY** excluded, not unconditionally;
- unavailable trust and emitted-versus-configured disagreement require
  separate payload-free gate codes; and
- schema parity must be derived from active configuration at the model-facing
  tool construction point, not inferred from runtime identity and not checked
  only by a separate startup assertion.

The audit excludes a broader current production ingress for trust classes and
excludes a systemic terminal-code defect. `proposal_schema_invalid` has one
emission site. Its currently reachable non-trust branches are input validation
or compiler-admission predicates; the false category is the Level 3 trust
predicate caught by the same `TypeError`/`ValueError` umbrella. Internal Run
identity and generated-time compiler predicates could also be mislabeled by
the catch if their invariants were broken, but the production adapter makes
those paths unreachable.

Result:

```text
A — REPAIR BOUNDARY FIXED
```

No repair is implemented or authorized by this reconciliation.

## Trust-Class Reach Enumeration

Static search at PR #88 head `4c2d888349de941c180eb6496efca9915e2415fe`
finds every production occurrence in exactly three files. Every row below is
production source; non-default callers are identified separately where they
exist only in tests.

| File and exact occurrence | Symbol and role | Caller → callee | `UNKNOWN` behavior and reach |
| --- | --- | --- | --- |
| `field_notes_controller.py:57` | `_field_notes_adapter_factory()` source keyword-only default/read | controller-bound `partial` → adapter constructor | Defaults to `UNKNOWN`; pass-through only. |
| `field_notes_controller.py:58` | Same factory, target default/read | controller-bound `partial` → adapter constructor | Defaults to `UNKNOWN`; pass-through only. |
| `field_notes_controller.py:67` | Source keyword and value pass-through | factory → `FieldNotesCodexAdapter.__init__()` | No transformation at this call. |
| `field_notes_controller.py:68` | Target keyword and value pass-through | factory → `FieldNotesCodexAdapter.__init__()` | No transformation at this call. |
| `field_notes_controller.py:130-131` | Controller constructor local write; `kwargs.pop()` read/default; normalization by `configured_model_class()` | any Python constructor caller → controller | Only in-process constructor ingress; missing value becomes `UNKNOWN`; invalid value raises before a Run. |
| `field_notes_controller.py:133-134` | Same controller constructor target write/read/default/normalization | any Python constructor caller → controller | Same behavior for target. |
| `field_notes_controller.py:139` | Source keyword and local value captured in `functools.partial` | controller constructor → `_field_notes_adapter_factory()` | Retained in controller memory for adapters created during that process. |
| `field_notes_controller.py:140` | Target keyword and local value captured in `functools.partial` | controller constructor → `_field_notes_adapter_factory()` | Retained in controller memory for adapters created during that process. |
| `field_notes_adapter.py:311` | `FieldNotesCodexAdapter.__init__()` source keyword-only default/read | factory or direct in-process caller → adapter | Defaults to `UNKNOWN`. |
| `field_notes_adapter.py:312` | Adapter target default/read | factory or direct in-process caller → adapter | Defaults to `UNKNOWN`. |
| `field_notes_adapter.py:320-321` | Adapter source attribute write plus constructor-argument read/normalization | adapter constructor → `configured_model_class()` | Validated member of `stronger`, `lower-cost`, `UNKNOWN`. |
| `field_notes_adapter.py:323-324` | Adapter target attribute write plus constructor-argument read/normalization | adapter constructor → `configured_model_class()` | Same. |
| `field_notes_adapter.py:346` | Source keyword and attribute read passed into a fresh gate | `FieldNotesCodexAdapter._reset_run()` → `FieldNoteProposalGate.__init__()` | Same in-memory value used for each adapter Run reset. |
| `field_notes_adapter.py:347` | Target keyword and attribute read passed into a fresh gate | adapter reset → gate constructor | Same. |
| `field_notes_model.py:461` | `FieldNoteProposalGate.__init__()` source default/read | adapter or direct in-process caller → gate | Defaults to `UNKNOWN`. |
| `field_notes_model.py:462` | Gate target default/read | adapter or direct in-process caller → gate | Defaults to `UNKNOWN`. |
| `field_notes_model.py:465-466` | Gate source attribute write plus argument read/normalization | gate constructor → `configured_model_class()` | Invalid value fails construction. |
| `field_notes_model.py:468-469` | Gate target attribute write plus argument read/normalization | gate constructor → `configured_model_class()` | Invalid value fails construction. |
| `field_notes_model.py:485` | Level 3 source-configuration comparison | `propose()` trust guard | `UNKNOWN != stronger`; fail-closed and first short-circuit for the shipped path. |
| `field_notes_model.py:486` | Level 3 target-configuration comparison | `propose()` trust guard | Evaluated only if source is `stronger`; `UNKNOWN != lower-cost` is fail-closed. |
| `field_notes_model.py:487` | Emitted source versus configured source comparison | `propose()` trust guard | Current shipped defaults short-circuit before this C branch. |
| `field_notes_model.py:488` | Emitted target versus configured target comparison | `propose()` trust guard | Current shipped defaults short-circuit before this D branch. |
| `field_notes_model.py:493` | Configured source read overwrites proposal source in a copy | gate → `compile_draft()` | For Levels 1–2, `UNKNOWN` is deliberately admitted and compiled; for Level 3 this line is unreachable under `UNKNOWN`. |
| `field_notes_model.py:496` | Configured target read overwrites proposal target in a copy | gate → `compile_draft()` | Same. |

Reach determinations:

- The sole shipped launcher, `decision_os/companion/__main__.py:37-40`, supplies
  neither value. **No production launcher supplies non-default values.**
- The authenticated server exposes repository, Run, approval, save, and skip
  operations, but no trust-class field or configuration route. **No production
  server/API path supplies non-default values.**
- The values are captured only in the controller's in-memory adapter-factory
  partial. A new adapter receives them for each Run in that controller process.
  Reconnect changes developer instructions and Note context, not trust. Restart
  recreates the launcher defaults, so the values do not persist durably across
  process restart.
- Proposal `source_model_class` and `target_model_class` values are compared to
  and then replaced by the configured values; they never write the configured
  values. **No model output influences trust configuration.**
- `CodexRuntimeIdentity` verifies model, effort, tier, CLI version, and account
  type, but none of those fields is read by the trust constructors or gate.
  **No runtime identity field influences trust configuration.**
- C/D (`source_class != configured source` / `target_class != configured
  target`) are not reachable through today's shipped launcher or HTTP API.
  They are reachable only through direct in-process non-default construction,
  currently exercised by tests such as `tests/test_field_notes_lite.py:262-275`.
- `UNKNOWN` is fail-closed specifically for Level 3. Levels 1 and 2 remain
  available and compile with trusted classes overwritten to `UNKNOWN`.

The name `trusted_*` overstates the evidence source: the value is a validated
constructor assertion with no provenance, As-of, owner, revocation, runtime-
identity binding, or durable configuration record. Renaming it to `asserted_*`
would be semantically clearer, but would touch all three production interfaces
and many focused tests without being required to repair advertised/admitted
parity or terminal classification. The rename therefore exceeds the narrowest
safe A1 repair. Any future Option B configuration should revisit the name as
part of its separately authorized provenance design.

## Tool-Schema Reach Enumeration

| Surface | Construction, mutation, send, cache, or reuse behavior |
| --- | --- |
| `field_notes_model.py:61-142` | Defines the only `FIELD_NOTE_TOOL_SPEC` object and its only `inputSchema`. It is a module-resident static base object. |
| `field_notes_adapter.py:17-24` | Imports the object and related gate symbols. No copy or mutation occurs at import. |
| `field_notes_adapter.py:395-430` | `_start_thread()` builds each `thread/start` request and sends `copy.deepcopy(FIELD_NOTE_TOOL_SPEC)` as the second `dynamicTools` element. This is the sole production model-facing send. |
| `field_notes_adapter.py:331-379` | `_reset_run()` constructs the active gate from adapter trust values. It does not construct or mutate the tool schema. |
| Reconnect path | `_reconnect_plan` can prepend a reconnect envelope to developer instructions, but `_start_thread()` sends the same fresh deep copy. Trust and schema are neither retained in the reconnect receipt nor altered by reconnect. |
| Run/restart boundary | The module constant is reused as the deep-copy source across Runs in one process; each `thread/start` receives a fresh copy. No production transport cache, persisted schema, or mutation site exists. Restart reloads the same code constant. |

Static search finds no assignment into `FIELD_NOTE_TOOL_SPEC`, no subscript
mutation, and no other copy or send. The separate `inputSchema` in
`decision_os/acceleration/codex_adapter.py` belongs to the read-only repository
tool, not the Field Note proposal tool.

The narrowest parity point is the Field Notes adapter's construction of the
fresh proposal-tool copy immediately before `thread/start`, because that object
already has the same active trust values used to construct the gate. A shared
pure Level 3 availability predicate in `field_notes_model.py` can drive both
gate admission and the derived copy:

- if the active asserted pair is not exactly `stronger / lower-cost`, derive a
  schema whose `value_level` enum is only `[1, 2]`;
- if it is exactly `stronger / lower-cost`, Level 3 may remain advertised, with
  the existing Level 3 source/target cross-field relation expressed in the
  schema; and
- never rewrite or silently downgrade a Level 3 proposal to Level 2.

This is derivation from active configuration, not a second startup assertion.
It does not infer trust from model name, provider, reasoning effort, service
tier, proposal contents, or model self-description.

## `proposal_schema_invalid` Call-Site Enumeration

There is exactly one production emission and one production interpretation:

- `field_notes_model.py:502-504` catches all gate/compiler `TypeError` and
  `ValueError` and emits `(False, "proposal_schema_invalid")`;
- `field_notes_adapter.py:717-721` maps that code to
  `A1_PROPOSAL_SCHEMA_REJECTED` before the generic failed-gate mapping at
  lines 722-726.

The one catch covers these originating predicates:

| Originating predicate | Fault family | Production reach | Semantic assessment |
| --- | --- | --- | --- |
| `propose():479-482`: emitted source or target not in `MODEL_CLASSES` | Schema | Reachable if the runtime delivers arguments outside the advertised enum | Correct at current umbrella granularity. |
| `propose():484-486`: Level 3 active configuration is not the required `stronger / lower-cost` pair | Configuration / trust policy | **Reachable today; Proof 003 took this path with `UNKNOWN / UNKNOWN`** | **Incorrect category**: unavailable trust is not proposal-schema invalidity. |
| `propose():487-488`: Level 3 emitted class differs from an active Level-3-capable pair | Trust policy | Not through today's launcher/API; reachable by direct non-default in-process construction | **Incorrect category** when reachable: disagreement is gate policy, not schema. |
| `compile_draft():326-335`: exact top-level keys | Schema | Reachable | Correct. |
| `compile_draft():336` plus `_bounded_string()` / `_structured_text()`: title type, bounds, nonblank, NUL, line, metadata marker, and Markdown structure | Schema / compiler admission | Reachable | Correct as invalid proposal content; more specific observability is optional, not required by this repair. |
| `compile_draft():337-339`: exact integer and Level enum | Schema | Reachable | Correct. |
| `compile_draft():340-347`: model-class enum and Level 3 relation | Schema | Unreachable through the gate because configured valid values overwrite emitted values after the earlier guard | Correct for direct compiler use; not a current gate terminal source. |
| `compile_draft():348-353`: trigger list shape, count, item bounds, uniqueness | Schema | Reachable | Correct. |
| `compile_draft():354-373`: scope object, exact keys, bounded unique lists | Schema / compiler admission | Reachable | Correct. |
| `compile_draft():374-380`: body object, exact keys, bounded structured text | Schema / compiler admission | Reachable | Correct. |
| `compile_draft():381-382`: missing source Run ID | Lifecycle / configuration | Unreachable: base reset generates a non-empty Run ID and creator-live capture supplies a validated non-empty Run ID | The umbrella would be incorrect if the invariant broke, but it is not a production-reachable proposal cause. |
| `compile_draft():383-391`: invalid or naive creation time | Lifecycle / configuration | Unreachable through the gate: the compiler generates `_utc_timestamp()` and the gate supplies no caller timestamp | Same unreachable-category caveat. |
| `compile_draft():420-421`: metadata exceeds 8 KiB | Compiler admission | Reachable from bounded but large proposal data | Semantically acceptable as rejected proposal content at the existing umbrella level. |
| `compile_draft():427-430` and `validate_compiled_markdown()`: Note exceeds 64 KiB or compiled structure is invalid | Compiler admission | Size is reachable; constructed-structure invariants are fail-closed compiler safeguards | Semantically acceptable for input-caused size failure; an invariant failure would indicate an internal compiler defect, but no such production input path is known. |

The emitter therefore collapses many distinct validation predicates and one
disjoint trust/configuration family. Collapse alone is not a category error:
the reachable schema and compiler-admission rows all mean the proposal cannot
be compiled under the bounded candidate contract. The Level 3 trust rows do
not. After those rows receive separate gate codes, the remaining umbrella is
semantically coherent. No protocol branch reaches this emitter: request shape,
identity, replay, item completion, and lifecycle protocol failures are handled
in the adapter before or after gate invocation with their own diagnostics.

Conclusion: terminal-code miscategorization is isolated to the Level 3 trust
path, not systemic across the currently reachable proposal gate. The two trust
subcases are distinct codes within one bounded policy family, so the result is
not Outcome C.

## Argument Identity Construction

`CodexAdapter._arguments_identity()` at
`decision_os/acceleration/codex_adapter.py:1681-1691`:

1. accepts one Python argument dictionary;
2. serializes it with `json.dumps(..., allow_nan=False, ensure_ascii=False,
   separators=(",", ":"), sort_keys=True)`;
3. encodes the resulting JSON as UTF-8; and
4. returns the lowercase SHA-256 hex digest.

Dictionary-key insertion order is removed recursively by `sort_keys=True`.
List order and scalar JSON representation are retained. Unicode is not
normalized. The function is a collision-resistant digest, not an injective
encoding.

During creator-live capture, the adapter adds per-argument digests to
`_capture_argument_identities`, a Python `set`, at the valid request and item
observation paths (`field_notes_adapter.py:635-639` and `870-873`).
`_identity_set_sha256()` at lines 675-681 sorts the distinct digest strings,
serializes the sorted list with canonical JSON, and SHA-256 hashes those bytes.
Consequences:

- collection order is intentionally lost;
- multiplicity is intentionally lost;
- `[A, B]` and `[B, A]` share an aggregate without any cryptographic
  collision; and
- `[A]` and `[A, A]` share an aggregate without any cryptographic collision.

For two different **sets of distinct canonical per-argument digests** to share
the protected aggregate would require an inner or outer SHA-256 collision.
Proof 003 additionally retains one distinct valid call ID, no inconsistent
replay, valid request shape, and one gate invocation. Those facts plus the
singleton recomputation support the historical binding, but neither the set
aggregation nor SHA-256 proves mathematical injectivity.

Transport-mutation exclusion is therefore:

```text
CONDITIONAL
```

It is conditional on the bounded operational log-row binding, execution of the
inspected production identity path, and SHA-256 collision resistance. It
supports exclusion of a value-changing mutation for Proof 003; it does not
recover ordering or multiplicity for a general proposal collection.

## Diagnostic Reach

The payload-free durability chain is:

1. `FieldNoteProposalGate.propose()` returns `(success, code)` to
   `_respond_field_note_tool_call()`.
2. `field_notes_adapter.py:655-660` stores `gate_response_code` and success;
   lines 683-750 select `final_subcause`; lines 752-804 construct and hash
   `FieldNoteA1ProposalDiagnostic`; and lines 995-1034 place it in the typed
   `FieldNoteCodexRunResult`.
3. `field_notes_controller.py:369-425` round-trips the diagnostic through
   `from_dict()`, reconciles completion failure with `final_subcause`, and
   lines 460-467 store it in controller completion state. Lines 538-562 return
   another digest-verified copy.
4. `field_notes_creator_live_capture.py:270-290` verifies the copy, selects its
   `final_subcause`, and calls `_terminal()`; lines 95-106 forward it to
   `record_stage_failure()`.
5. `field_notes_creator_live.py:1908-1950` verifies diagnostic/reason binding
   and appends an `ATTEMPT_FAILED` journal record containing the full payload-
   free diagnostic plus `diagnostic_sha256`.
6. `_append()` at lines 1813-1897 fsyncs the journal, then appends and fsyncs an
   anchor that commits journal byte length, count, chain head, and SHA-256. The
   anchor does not duplicate diagnostic fields; it cryptographically commits
   the journal bytes containing them.
7. Readback at lines 1388-1474 parses the diagnostic with `from_dict()`, checks
   its digest and equality between `failure_reason` and `final_subcause`, then
   lines 1508-1535 construct `FieldNoteCreatorLiveTraceReadback`. Its typed
   `a1_proposal_diagnostic` field and `as_dict()` retain both
   `gate_response_code` and `final_subcause`.

Current `proposal_schema_invalid` follows this chain as:

```text
gate_response_code = proposal_schema_invalid
final_subcause = A1_PROPOSAL_SCHEMA_REJECTED
failure_reason = A1_PROPOSAL_SCHEMA_REJECTED
```

The narrowest future payload-free representation is:

| Gate fact | `gate_response_code` | Existing `final_subcause` |
| --- | --- | --- |
| Level 3 unavailable because active trust is not Level-3-capable | `level_3_trust_not_configured` | `A1_PROPOSAL_GATE_REJECTED` |
| Level-3-capable active trust disagrees with emitted classes | `level_3_trust_class_mismatch` | `A1_PROPOSAL_GATE_REJECTED` |

`gate_response_code` already accepts any non-empty bounded string up to 128
characters, and `A1_PROPOSAL_GATE_REJECTED` already belongs to the diagnostic
subcause enum. Both exact codes therefore survive controller propagation,
journal append, anchor commitment, and typed durable readback without proposal
payload, free text, diagnostic-schema change, journal-schema change, anchor-
schema change, or typed-readback-schema change.

## Revised Repair Boundary

The complete audit fixes the narrowest later repair at two A1 production files:

- `decision_os/companion/field_notes_model.py`
  - define one shared pure Level 3 availability predicate;
  - derive a Field Note tool-spec copy from the active configured pair;
  - under Option A, remove Level 3 from the advertised enum when the pair is
    not exactly `stronger / lower-cost`;
  - when Level 3 is available, advertise its source/target cross-field rule;
  - split trust-not-configured from emitted/configured mismatch before the
    compiler catch; and
  - retain `proposal_schema_invalid` for actual validation/compiler-admission
    failures.
- `decision_os/companion/field_notes_adapter.py`
  - use the derived fresh tool spec at the sole `thread/start` send point; and
  - let the two new false gate codes map through the existing generic
    `A1_PROPOSAL_GATE_REJECTED` branch while retaining their exact diagnostic
    `gate_response_code`.

`field_notes_controller.py` requires no change: its default already expresses
Option A, its pass-through is complete, and no production configuration ingress
is authorized. No launcher, server, reconnect, runtime-identity, diagnostic
schema, journal, anchor, typed-readback, A2–A7, README, Charter, proof, or
settlement change belongs in the repair.

Mechanically required tests are bounded to focused A1 surfaces:

- unknown/unknown advertises only Levels 1 and 2;
- exact stronger/lower-cost advertises Level 3 with its exact class relation;
- default Level 3 defense-in-depth rejection returns
  `level_3_trust_not_configured`;
- configured-versus-emitted disagreement returns
  `level_3_trust_class_mismatch`;
- genuine proposal validation still returns `proposal_schema_invalid` and
  `A1_PROPOSAL_SCHEMA_REJECTED`;
- both trust codes retain `A1_PROPOSAL_GATE_REJECTED` plus the exact payload-
  free `gate_response_code` through journal, anchor, and typed readback;
- one-shot, direct-write, malformed-request, replay, item, protocol, and
  established non-proposal precedence remain unchanged; and
- no Note or Run 2 occurs on either repaired rejection path.

The rename to `asserted_source_model_class` / `asserted_target_model_class` is
not required in this bounded repair. Rollback is one revert of the two-file A1
change and its focused tests. No implementation begins without separate Shin
authorization.

## Revised Claim Boundary

- Historical Outcome A and Case 2 remain unchanged.
- Proof 003 remains permanently `FAILED / A1_CAPTURE /
  A1_PROPOSAL_SCHEMA_REJECTED`; the historical terminal code is not rewritten.
- The audit establishes two co-equal current defects: Level 3 was advertised
  while unavailable under active Option A configuration, and that trust-policy
  rejection was categorized as proposal-schema invalid.
- The terminal-code category error is proven only for the Level 3 trust path.
  No systemic current production category error is claimed.
- Transport mutation is conditionally excluded under the explicit hash and log
  assumptions above; injectivity, order recovery, and multiplicity recovery are
  not claimed.
- Current production has no non-default trust ingress. A direct Python
  constructor can supply values in process, but that is not the shipped launcher
  or authenticated server API.
- `trusted_*` is an overstated name for constructor-supplied assertions, but a
  rename is outside the narrow repair.
- Option B, trust inference, auto-downgrade, repair implementation, another live
  proof, retry, replacement, Note, Run 2, release, and publication remain out of
  scope and unauthorized.

## Final Repair Gate

```text
Static audit result:
A — REPAIR BOUNDARY FIXED

Proof 003:
PERMANENT FAIL

PR #88:
DRAFT

Repair Gate:
BLOCK — separate Shin authorization required

Live Proof Gate:
BLOCK
```

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

Static reach audit:
COMPLETE — A / repair boundary fixed

Proof 003:
PERMANENT FAIL

PR #88:
DRAFT

Live Proof Gate:
BLOCK

Repair Gate:
BLOCK — separate Shin authorization required
```
