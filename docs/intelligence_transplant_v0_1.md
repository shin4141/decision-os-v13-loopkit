# Intelligence Transplant Loop v0.1

## Status and authority boundary

Intelligence Transplant is the Stage 5, manual-transport path for turning one
observed failure into a bounded control asset and then testing that asset on
one separate, similar lower Run.

The v0.1 authority mode is fixed:

```text
Structural Validation: PASS | FAIL
Authority Provenance: MANUAL OWNER ATTESTED
Cryptographic Provenance: NOT ESTABLISHED
Generalized transplant: NOT ESTABLISHED
```

The Decision Owner is Shin. A valid record proves that the supplied object has
the required shape, exact hashes, dependency bindings, timestamps, manual
receipts, and event-chain position. It does not authenticate the real-world
operator, establish external identity, prove that no hidden input existed, or
establish federated provenance.

The browser session protects the loopback HTTP surface. It is not identity
proof. The UI therefore always displays:

```text
Local manual authority receipt — not cryptographic identity proof
```

Stage 5 never invokes a model, starts the Codex adapter, assigns a Role, merges,
releases, or starts Formal Run 001.

## Evidence states

Execution status, delta maturity, lifecycle, and CAP are separate dimensions.

| Effective records | Delta state | Gate |
|---|---|---|
| Charter only | `NONE` | Charter gate; execution is `NOT_ESTABLISHED` |
| E1 only | `NONE` | `HOLD` for independent audit |
| E1 + E2 `REJECT` | `REJECTED` | `BLOCK` for that lineage |
| E1 + E2 `SURVIVE`/`REVISE`, without E3 | `NONE` | `HOLD` |
| Valid E1 + E2 + E3 | `CANDIDATE` | `GO` only with separate implementation authority |
| Valid current E4 | `IMPLEMENTED` | `GO` only for a pre-frozen lower-Run trial |
| Valid current E5 | `REUSED` | `HOLD`; generalization is not established |
| A current dependency is revoked or rolled back | `REVOKED` | `HOLD` |
| An effective CAP exists | unchanged | `CAP` overlay |

One verified similar lower Run establishes only the first `REUSED` state.
Generalized transplant remains `NOT ESTABLISHED`.

## Record model

The executable validator and reducer are in
`decision_os/intelligence_transplant.py`. The corresponding JSON Schema is
`schema/v13_intelligence_transplant.schema.json`.

Every record:

- uses the `decision-os.intelligence-transplant.v0.1` schema version;
- has one stable `object_id`, `object_type`, and `run_id`;
- has a timezone-aware effective timestamp;
- carries a lowercase SHA-256 `content_hash`;
- computes that hash from canonical JSON after blanking its own hash fields;
- uses exact `{object_id, content_hash}` references;
- rejects unknown fields, duplicate JSON keys, non-finite numbers, object ID
  reuse, stale hashes, cycles, cross-Run substitution, and old-hash replay.

Receipt-, manifest-, and charter-specific hash fields equal `content_hash`.
Transport-byte SHA-256 is separate from the structured object hash.

### Manual seat assignment

Before a role begins, a `SEAT_ASSIGNMENT_RECEIPT` fixes:

- `run_id`;
- seat and assignee context identity;
- assignment scope;
- allowed and prohibited inputs;
- effective as-of time;
- Decision Owner attestation;
- exact receipt hash.

This is a manual governance receipt, not authentication. Discovery, Audit,
Acceptance, Implementation, lower-Run execution, and Evaluation use distinct
seat bindings where their evidence requires them.

### E1 — discovery

E1 binds the charter failure family and predicate, Discovery seat and context,
observed failure, proposed mechanism, strongest falsifier, discovery claims,
and evidence anchors. E1 alone never creates a candidate.

After an E2 `REJECT`, E1 novelty is compared through a canonical semantic
signature over conservative lexical inventories for the fixed discovery
claim, observed failure, mechanism, and strongest falsifier. Unicode
compatibility forms, case, whitespace, punctuation, control or invisible
characters, the combining grapheme joiner, variation selectors, anchor
ordering, and word or list ordering do not create a materially new lineage by
themselves.

### E2 — independent audit

Before E2, an `AUDIT_INPUT_MANIFEST` freezes the current E1 ID/hash, allowed
inputs, prohibited inputs, and Audit context. E2 also requires:

- a distinct Audit seat and active context from Discovery;
- the immutable current E1 target;
- a strongest counterexample;
- `SURVIVE`, `REVISE`, or `REJECT`;
- an `AUDIT_COMPLETION_RECEIPT`.

Changing only a role label inside the same active context is invalid. The same
model in a genuinely fresh, separately assigned context is permitted.

### E3 — accepted discovery

E3 binds the exact current E1 and E2. `REJECT` cannot advance. `SURVIVE`
preserves the accepted E1 claims. `REVISE` requires a one-to-one application
for every required audit delta. Accepted and excluded claims, implementation
requirements and scope, and forbidden overclaims are explicit.

`GENERALIZED_TRANSPLANT_NOT_ESTABLISHED` is mandatory.

### E4 — implementation binding

E4 binds the current E3 to one concrete `test`, `guard`, `rule`, `schema`, or
`validator`. It records:

- repository base, opening, bound, and closing HEAD identities;
- changed paths, Git blobs, SHA-256 values, and asset version;
- a one-to-one mapping from every accepted claim through required control
  behavior, concrete asset, and behavioral activation verification;
- complete consumption of every E3 implementation requirement through required
  control behavior, a concrete asset, and behavioral verification;
- complete binding of every E3 implementation-scope path to a declared changed
  artifact;
- focused and regression results;
- a rollback path.

File existence, a commit, or a passing suite without behavioral activation is
not sufficient. Behavioral verification is limited to an adversarial behavior
test, runtime interception trace, or controlled contrast; activation evidence
is separately limited to a runtime trace, adversarial trigger trace, or
controlled contrast. Every path changed by the bound Git range must be
declared—an E4 cannot hide an unrelated change in the same commit range.

### E5 — separate lower Run

Before the lower Run begins, `LOWER_RUN_TRIAL_MANIFEST` freezes the new task,
source task, failure family and predicate, allowed and prohibited inputs,
active E4 asset identity/version/hash, repository HEAD, lower runtime context,
and owner attestation.

The active asset must be one of the assets actually used by an E4 claim
binding; presence only in `changed_artifacts` is insufficient. The manifest,
completion receipt, activation trace, and E5 fix the same asset identity,
version, and hash.

The allowed input manifest is exact and ordered: new-task bytes, repository
HEAD, active asset identity/version/hash, and the minimum execution boundary.
No additional input class is accepted.

After the Run, `LOWER_RUN_COMPLETION_RECEIPT` records actual inputs, activation
trace, causal proof mode, result, human-rescue state, evaluator context and
receipt, event sequence, and completion time.

The new task must differ from the source task while preserving the fixed
failure family and predicate. Upper-conversation content, hidden reasoning,
accepted answers, and owner corrections are forbidden inputs.

The lower runtime context is distinct from the Discovery, Audit, and
Implementation contexts. Its Seat Assignment, trial manifest, and completion
receipt must bind the same lower context identity.

The only causal proof modes are:

- `INTERCEPTION_TRACE`: the active asset demonstrably intercepts or detects the
  fixed failure predicate;
- `CONTROLLED_CONTRAST`: all other conditions are fixed, the asset-off/old
  condition exhibits the failure, and the asset-on/new condition intercepts or
  prevents it.

Asset presence, asset loading, a passing suite, or an accidentally correct
answer is insufficient. `human_rescue` equal to `PRESENT` or `INTERRUPTED`
cannot support E5.

An interception trace uses a structured interception point whose mode is
`PRE_ACTION_CONTROL_INTERCEPTION` or `FAILURE_PREDICATE_PREVENTION`, and whose
observed effect must exactly match the completion and E5 result. A controlled
contrast fixes task bytes, repository HEAD, runtime context, and input
manifest; `ACTIVE_ASSET_ENABLED` is the only changed condition.

## Forward-only lifecycle and controls

A replacement names the exact current object ID/hash in `supersedes`. The old
object becomes `FORWARD_ONLY_REPLACED`; downstream evidence does not
automatically inherit the replacement.

- Replacing E3 returns the lineage to `CANDIDATE` until a new E4 exists.
- Replacing E4 requires a new E5.
- An E2 `REJECT` requires a materially new E1 and new lineage.
- Revoking E5 requires an exact forward supersession plus a new pre-frozen
  lower-Run manifest and a new completion receipt with materially different
  task/input/result evidence before `REUSED` can return. Relabeling object,
  trial, task, context, reference, or timestamp identities is insufficient.
- Revoked or superseded lower-Run manifests and completion receipts cannot be
  reused by a detached E5.

CAP, CAP release, revoke, and rollback use `MANUAL_CONTROL_RECEIPT`. Every
effective control fixes the action, target ID/hash, reason, timestamp, Decision
Owner attestation, and receipt hash.

A CAP preserves the maturity that existed at `capped_from`. Later transport is
allowed, but it cannot promote effective maturity until a valid release.
Expiry is not release; it changes the gate to `HOLD`. A release binds the exact
CAP and its release evidence.

A revocation makes a current dependency non-effective. A rollback must target
the exact current E4 and bind the post-rollback repository identity and changed
artifacts. It revokes that E4 and its downstream E5. Reintroduction requires a
new forward-only E4; materializing an old maturity snapshot is forbidden.

Each rollback artifact declares `post_rollback_state` as `PRESENT` or
`DELETED`. Present artifacts bind the post-rollback Git blob and SHA-256;
deleted artifacts require both identities to be null. The store verifies the
complete forward Git diff from the target E4 HEAD to the post-rollback HEAD,
including every original E4 artifact path.

## Private storage

Stage 5 uses an additive repository-private namespace:

```text
<git-common-dir>/decision-os/intelligence-transplant/v0.1/
  events.ndjson
  event-head.json
  publication-state.json  # transient IN_PROGRESS / persistent INVALID marker
  charters/sha256/<content_hash>.json
  evidence/sha256/<content_hash>.json
  manifests/sha256/<content_hash>.json
  transport/sha256/<exact_payload_sha256>.bin
  transport/sha256/<receipt_sha256>.receipt.json
```

Directories are owner-only `0700`; files are `0600`. Symlinks and paths outside
the Git common directory are rejected. A process lock and file lock serialize
append operations. Store file I/O walks owner-only directories with anchored
directory descriptors and refuses intermediate or final symlinks. The event
chain is verified from genesis on every read and the integrity head detects
truncation. Event IDs derive from record content hashes and event time is bound
to the record `as_of`; wrapper rewrites cannot choose new IDs or timestamps.
Structured blobs and exact transport bytes are rehashed before use.

Maturity is always reduced from the verified event chain. No writable maturity
field is an authority source. Corruption fails closed and does not silently
restore an older state.

Raw Git evidence commands disable replacement-object interpretation, sanitize
the ambient Git environment and global/system config, and fix diff behavior.
Replace refs, legacy grafts, alternate object stores, identity-sensitive
local/worktree configuration, and a non-SHA-1 object format fail closed. E4
and rollback commit/tree/blob bindings are reverified from raw Git evidence on
every event-chain read.

Append performs opening and closing repository-HEAD checks. The final check,
event append, and event-head update run under a fail-closed publication state.
A post-publication HEAD check clears that state only when the expected HEAD is
still current; drift or interruption leaves an explicit unreadable publication
state. Every atomic marker, event-head, immutable blob, and receipt replacement,
and marker deletion, fsyncs its parent directory. Reopening after a crash with
an uncleared marker fails closed. E4 additionally verifies commit ancestry, Git
blobs, and artifact hashes against its bound HEAD. A drifted repository cannot
publish a readable event.

Each manual-transport event also embeds a hashed transport receipt containing
the mode, source label, declared and observed exact-byte hashes,
context-evidence reference, and as-of time. The receipt is event-chain
metadata, not part of the evidence object's content identity.

## Guided Intake and Manual Bridge boundaries

The Guided Intake adapter is read-only. It exposes only the latest current,
fully verified freeze identity, completion line, and repository HEAD for
charter construction. A charter freeze is not evidence of execution.

The Manual Bridge Stage 5 transport builder is session-independent. It fixes
exact bytes, source label, mode, declared hash, context-evidence reference, and
as-of time. It performs transport only. It does not adopt evidence, issue an
audit verdict, or promote maturity.

The legacy six-role order, Golden manifest bytes, and Structural Replay
semantics remain unchanged. Stage 5 records are never inserted into a legacy
Bridge session.

## Companion HTTP and UI

All Stage 5 routes use the existing loopback session, Origin, CSRF, request
size, and CSP boundaries:

```text
POST /api/intelligence-transplant/charter/freeze
POST /api/intelligence-transplant/manifest/freeze
POST /api/intelligence-transplant/evidence/attach
POST /api/intelligence-transplant/receipt/attach
POST /api/intelligence-transplant/control/record
```

Manual transport routes accept one exact payload as pasted UTF-8 text or
base64 byte-exact input. The declared SHA-256 must match the exact payload.
Route category and object type must agree.

The Companion `run` response is a typed union. Legacy clients may treat a
missing `run_type` as `bounded_task`; the current server emits it explicitly.
Stage 5 operations return `run_type: intelligence_transplant` and never enter
the bounded-task adapter path. When the typed Run is Stage 5, both the
top-level `run` and `intelligence_transplant` panel are derived from the same
fresh verified projection. The private Run cache is synchronized to that same
projection and is not an independent maturity or Gate authority.

The Stage 5 UI is read-only. It shows Delta State, Gate, missing evidence, next
one action, prohibited next actions, evidence identities, lifecycle, and
lineage. It provides no Role-assignment, model-invocation, or next-loop action.
All untrusted values are rendered with `textContent`.

## Product rollback

To remove the Stage 5 product surface, revert the complete additive Stage 5
change set, including its bounded-repair commit. Do not delete or rewrite the
private Stage 5 store. Older Companion versions ignore the unknown directory.
A later reintroduction rebuilds the projection from the verified event chain.

If store integrity fails, reads and writes stop in `BLOCKED_CORRUPT`. Recovery
requires a separately designed repair that preserves event and blob identity;
silent fallback to a last-known-good projection is prohibited.

## Known limitations

- Manual owner attestation is not cryptographic identity.
- External context separation and hidden-input absence are not
  cryptographically proven.
- No organizational or federated provenance is established.
- The local event chain is a structural, repository-private integrity check,
  not an externally witnessed append-only ledger. A coordinated process with
  the same OS identity and full write access remains outside this v0.1 trust
  boundary.
- One valid similar lower Run does not establish generalization.
- No external model invocation or Formal Run 001 is part of v0.1.
