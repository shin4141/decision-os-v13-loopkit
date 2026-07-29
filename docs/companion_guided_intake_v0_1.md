# Companion Guided Intake v0.1

Guided Intake is an isolated card in the private Decision OS Companion. It
preserves one exact raw request, accepts a manually produced Pro JSON draft,
validates the declared boundary, records one bounded user confirmation when
needed, freezes an immutable interpretation, and can copy that frozen boundary
to Manual Bridge.

> **INTERPRETATION ONLY — NO EXECUTION AUTHORITY**
>
> This intake does not start a Runner, authorize a Builder, approve a file
> change, grant merge permission, or authorize publication or release.

## Product route

```text
Raw Request Capture
→ Original Request Fixation
→ Copy for Pro
→ Manual Pro Draft Import
→ Deterministic Boundary Validation
→ User Confirmation / HOLD
→ Intake Freeze
→ Optional Copy to Manual Bridge
```

The route never calls Pro, Codex, `/api/run`,
`CompanionController.start_run()`, the Codex adapter, or the acceleration
approval engine.

## Exact Original Request identity

Identity begins with the Unicode string returned by server-side JSON decoding.
The product does not trim it or normalize Unicode, whitespace, or line
endings. The exact string is encoded as UTF-8 and limited to 65,536 bytes.

Each capture records:

- request UUID;
- SHA-256 over exact UTF-8 bytes;
- byte size;
- UTC capture time;
- `COMPANION_GUIDED_INTAKE_TEXTAREA` source label;
- UTF-8 encoding;
- no-normalization policy;
- Forward-only supersession identity.

A correction is Forward-only. It must name the current
`supersedes_request_id`; it creates a new request ID and SHA-256 and leaves the
prior exact bytes and identity in history. It does not edit or relabel the
prior capture. The new request becomes active and invalidates the prior active
draft, interpretation, Copy-for-Pro prompt, and transfer receipt. Any older
freeze remains historical but is no longer eligible for transfer.

Private runtime data is stored under:

```text
<git-common-dir>/decision-os/guided-intake-v0.1/
```

Directories are mode `0700` and files are mode `0600` where supported. Raw
request text is not written to the worktree, event log, outward receipt,
browser storage, URL, or server log.

## Visible field contract

The card keeps the source and generated fields separate:

```text
Original Request       fixed exact source
Objective              generated interpretation
Completion Line        generated interpretation
Do Not Touch           generated interpretation
UNKNOWN                generated interpretation
```

`Evidence Needed` is metadata inside an UNKNOWN entry, not a fifth generated
field.

## Manual Pro draft

`Copy for Pro` produces a prompt bound to the full Original Request SHA-256.
The user obtains the result outside Companion and imports one strict JSON
object with schema:

```text
guided-intake-draft-v0.1
```

The parser rejects malformed JSON, duplicate keys, unsupported top-level
fields, a replacement `original_request`, a source SHA mismatch, invalid
types, invalid provenance, and any authority claim other than `NONE`.

### Exact provenance rules

Provenance is typed and validated rather than inferred from polished prose:

- Every Objective atom has a unique ID and at least one support record.
- `ORIGINAL_REQUEST_QUOTE` support contains exactly `kind`, `quote`, and a
  positive one-based `occurrence`. The exact occurrence must exist in the
  captured request. Companion resolves it to UTF-8 byte start/end offsets and
  a SHA-256 of the exact quote.
- `USER_CONFIRMATION` support contains exactly `kind` and `event_id`. The
  event must be a recorded confirmation for the active request. The normalized
  support records the event ID and SHA-256 of its exact answer.
- Objective text without supporting token overlap is classified
  `SUBSTITUTED`. Unsupported risk terms or unsupported clauses are classified
  `EXPANDED`. Neither status can freeze.
- A `USER_EXPLICIT` Do Not Touch item requires exact Original Request quote
  support whose protected surface overlaps the item. A
  `USER_CONFIRMED_CANDIDATE` requires a matching recorded confirmation and
  answer support.
- An `INFERRED_SAFETY_CANDIDATE` remains visibly inferred and cannot be
  attributed to the user without Forward-only confirmation.
- UNKNOWN provenance keeps its typed basis and any related exact request
  quotes. An imported UNKNOWN must be `OPEN`; a model assertion cannot import
  it as resolved.

Missing, mistyped, nonexistent, or mismatched support fails closed as:

```text
HOLD — FIELD PROVENANCE INCOMPLETE
```

A model assertion, producer label, confidence statement, hash, or receipt is
not a substitute for source or confirmation provenance.

## Deterministic validation

Objective fidelity uses these statuses:

```text
PRESERVED
NARROWED WITH EXPLICIT USER APPROVAL
EXPANDED
SUBSTITUTED
UNKNOWN
```

Only the first two can freeze.

Completion Line uses:

```text
TESTABLE
PARTIALLY TESTABLE
SUBJECTIVE
MISSING
UNKNOWN
```

`TESTABLE` requires a bounded observable, pass condition, and evidence source.

Do Not Touch distinguishes:

```text
USER_EXPLICIT
REPOSITORY_INVARIANT
INFERRED_SAFETY_CANDIDATE
USER_CONFIRMED_CANDIDATE
```

An inferred safety candidate is never attributed to the user.

The product also enforces these four repository invariants as a separate
`REPOSITORY_INVARIANT` basis:

- `DNT-REPO-1`: “Guided Intake grants no execution authority.”
- `DNT-REPO-2`: “No Guided Intake action may start the Runner.”
- `DNT-REPO-3`: “All repository surfaces outside a separately authorized Builder scope remain protected.”
- `DNT-REPO-4`: “Stage 1 and Stage 2 behavior must remain unchanged unless the accepted design explicitly permits an additive extension.”

If a draft supplies one of these IDs, its text must match exactly and it must
not claim user support. Missing invariants are added deterministically. They
remain repository facts, never user statements.

UNKNOWN supports:

```text
USER_STATED_UNKNOWN
MODEL_DETECTED_MISSING_FACT
CONFLICTING_EVIDENCE
UNVERIFIED_ASSUMPTION_CANDIDATE
FUTURE_OBSERVATION
```

A material open UNKNOWN with execution effect blocks freeze. A non-material
UNKNOWN may remain visible only with `effect_on_execution: NONE`.

## Gate and confirmation

The structural gate is one of:

```text
CLEAR ENOUGH TO FREEZE
NEEDS USER CONFIRMATION
HOLD — OBJECTIVE UNKNOWN
HOLD — COMPLETION LINE UNKNOWN
HOLD — DO NOT TOUCH UNKNOWN
HOLD — MATERIAL UNKNOWN UNRESOLVED
```

Unsupported expansion or substitution fails as an Objective fidelity HOLD.
Authority inflation is blocked.

At most one field-specific question is active at a time. A confirmation
records the exact question, exact answer, Forward-only field delta, resolved
UNKNOWN identities, time, and event identity. It confirms represented intent
only. It grants no execution authority.

Confirmation does not rewrite the imported draft or an earlier UNKNOWN entry.
It appends a content-addressed confirmation receipt and a hash-linked event.
Each resolved entry moves from `OPEN` to `RESOLVED_FORWARD_ONLY` and names the
confirmation event as its evidence. Confirmation history remains scoped to
the captured request and is available to later draft validation.

Only `CLEAR ENOUGH TO FREEZE` can freeze.

## Freeze and transfer

Freeze writes canonical UTF-8 JSON with stable key order and a SHA-256 over
the exact artifact bytes. It includes source identity, generated fields,
resolved quote ranges, confirmations, UNKNOWN history, field statuses,
authority boundary, selected local repository commit, and the prior event
chain head.

The frozen artifact authority state is exactly:

```text
IMMUTABLE_INTERPRETATION_ONLY
```

This state means only that the identified interpretation is immutable. It does
not authorize execution, a Builder, file changes, transfer, merge,
publication, or release.

A frozen artifact cannot be edited or recreated in place. Re-freezing the same
active request, draft, and interpretation is rejected. A request, draft,
confirmation, or boundary correction creates a new freeze with a new identity,
`supersedes_freeze_id`, and an explicit Forward-only supersession reason. The
old artifact and its receipt remain readable; it is marked superseded and
cannot transfer. Old request captures, drafts, confirmations, UNKNOWN
transitions, freezes, and events are retained rather than overwritten.

### Freeze receipt audit hook

A successful freeze exposes `freeze_id`, `frozen_at`, and the full frozen
artifact SHA-256 in the Companion snapshot. The private hash-linked
`INTAKE_FROZEN` event records:

- `IMMUTABLE_INTERPRETATION_ONLY`;
- freeze ID and frozen Intake SHA-256;
- Original Request SHA-256;
- repository As-of commit;
- superseded freeze ID, when present.

The canonical frozen artifact independently binds the request identity, active
draft SHA-256, generated boundary, confirmations, UNKNOWN history, Evidence
Packet identity, repository identity, and pre-freeze event-chain head. These
are audit hooks for identity and immutability, not authority claims.

Immediately before Manual Bridge transfer, Guided Intake verifies:

- the freeze is the latest effective freeze;
- the Original Request is current and not superseded;
- the selected local repository `HEAD` still matches the frozen As-of commit;
- the active draft and interpretation still match the freeze;
- no later confirmation conflicts with the freeze;
- the request and freeze blobs are present, hash-valid, non-purged, and
  non-corrupt.

Failure closes as:

```text
HOLD — INTAKE AS-OF STALE
```

Transfer sends exact Objective, Completion Line, Do Not Touch, UNKNOWN,
Original Request SHA-256, frozen Intake SHA-256, repository As-of identity,
Evidence Packet identity, and the `INTERPRETATION_ARTIFACT_ONLY` boundary.
Pre- and post-transfer canonical field hashes must match. Manual Bridge keeps
its existing thirteen handoff fields and conditionally appends a
`Guided Intake Boundary` block. Legacy Stage 2 sessions and handoff bytes are
unchanged.

Manual Bridge remains:

```text
HOLD — SEPARATE BUILDER AUTHORITY REQUIRED
```

Transfer is `ARTIFACT_TRANSFER_ONLY`; it starts no Runner, Codex adapter,
approval engine, handoff acceptance run, branch, or Builder.

### Transfer receipt audit hook

The transfer receipt authority state is exactly:

```text
ARTIFACT_TRANSFER_ONLY
```

The receipt records the Bridge session ID, canonical hashes for Objective,
Completion Line, Do Not Touch, UNKNOWN, and the authority boundary, the
Original Request SHA-256, frozen Intake SHA-256, transfer time, and:

```text
TRANSFERRED WITHOUT EXECUTION
```

Guided Intake accepts the receipt only after Manual Bridge returns the same
field-hash map. A private hash-linked
`INTAKE_TRANSFERRED_TO_MANUAL_BRIDGE` event records the receipt authority
state, Bridge session ID, field hashes, and freeze SHA-256. The receipt proves
only that the identified artifact boundary was transferred without detected
field alteration. It does not approve, accept, execute, or grant authority
over the transferred instructions.

## Local API

All endpoints use the existing private loopback session, same-origin, and CSRF
controls.

```text
GET  /api/guided-intake/state
POST /api/guided-intake/capture
POST /api/guided-intake/copy
POST /api/guided-intake/import-draft
POST /api/guided-intake/confirm
POST /api/guided-intake/freeze
POST /api/guided-intake/transfer-to-bridge
```

Every successful mutation returns the complete Companion snapshot. Guided
Intake errors are panel-local; corrupt intake state does not turn the Runner
into an intake recovery path.

## UI disclosure

The Guided Intake card keeps its claim boundary visible at all lifecycle
states:

```text
INTERPRETATION ONLY — NO EXECUTION AUTHORITY
```

The accompanying explanation states that the intake does not start a Runner,
authorize a Builder, approve a file change, or grant merge, publication, or
release authority. The UI renders the exact Original Request and its identity
separately from Objective, Completion Line, Do Not Touch, and UNKNOWN. It also
shows Objective fidelity, Completion testability, the current gate, the one
active confirmation question, the freeze identity, the transfer receipt, and
panel-local HOLD or corruption errors.

Freeze is available only for a current `CLEAR ENOUGH TO FREEZE`
interpretation with no active question. Transfer is available only for the
latest current freeze and is disabled after a transfer receipt exists. Button
labels say “Freeze Guided Intake” and “Copy Frozen Intake to Manual Bridge”;
neither wording implies execution or approval. All imported and generated text
is rendered as inert text, not executable HTML.

## Ambiguous demonstration

The repository fixtures preserve this Original Request:

```text
Add a Guided Intake box to the Companion so I can paste an unclear task
and get it ready for the next agent. Don’t break the current Runner.
```

Before confirmation, completion is UNKNOWN, current Runner behavior remains an
explicit Do Not Touch item, and the gate is `NEEDS USER CONFIRMATION`. The
product does not silently choose between:

- a frozen Guided Intake artifact; or
- a frozen artifact also copied into Manual Bridge.

The explicit fixture answer selects the first interpretation. Only then does
the Completion Line become testable and the gate become
`CLEAR ENOUGH TO FREEZE`.

## Claim boundary

Guided Intake structures and preserves a request boundary. It does not prove
hidden intent, automatic correctness, general safety, product generality,
execution readiness, Builder approval, merge approval, publication approval,
or release approval. Freeze and transfer receipts are evidence of the
identified local lifecycle events only. They are not certifications and do
not convert interpretation, immutability, or artifact transfer into execution
authority.
