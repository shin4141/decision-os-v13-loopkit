# Companion Manual Bridge v0.1

## Purpose and claim boundary

Companion Manual Bridge v0.1 is a bounded, local artifact bridge inside the
existing private Decision OS Companion. It turns a manually transferred Pro
workflow into an inspectable artifact chain:

```text
Copy for Pro
→ exact artifact import
→ identity fixation
→ Execution Handoff generation
→ Build Receipt / Pro Audit / Reusable Delta import
→ Bridge Receipt and Golden manifest generation
→ structural Replay
```

The Bridge records artifact identity and structure. It does not call a model,
start Codex, approve a change, mutate the selected repository worktree, grant
authority, or turn an imported claim into PASS.

Golden means a frozen comparison source only. It does not mean correct,
approved, certified, authorized, or PASS. Replay proves only the deterministic
structural comparison defined below.

## Storage and the working-tree no-write boundary

Bridge state is private, repository-local state under the selected
repository's Git common directory:

```text
.git/decision-os/manual-bridge/v0.1/
  events.jsonl
  artifacts/sha256/<artifact_sha256>.bin
  imports/<import_event_id>.json
  sessions/<session_id>/session.json
  outputs/<session_id>/copy_for_pro.md
  outputs/<session_id>/execution_handoff.md
  outputs/<session_id>/bridge_receipt.md
  outputs/<session_id>/golden_manifest.json
  outputs/<session_id>/replay_result.json
```

For linked worktrees, `.git` above means the resolved Git common directory,
not a guessed `<worktree>/.git` directory.

The Bridge's “no repository file write” rule means:

- Bridge endpoints may append and fix private evidence beneath the Git common
  directory;
- Bridge endpoints do not create, modify, rename, or delete files in the
  selected working tree;
- Bridge endpoints do not stage, commit, reset, merge, rebase, or update refs;
- generated output remains private Bridge state until a separately authorized
  Builder copies exact bytes into an allowed working-tree path;
- a Builder's separately authorized Golden-file creation is not a Bridge
  authority grant or an automatic Bridge action.

Bridge state is separate from `AccelerationStore`, its event identity,
Repository Defaults, and the Verified Save/Reuse Receipt. Corrupt Bridge state
blocks Bridge reads and appends for the affected repository without
reinterpreting or migrating Acceleration state.

## Exact bytes, request limits, and import modes

The decoded artifact payload limit is:

```text
1 MiB = 1,048,576 bytes
```

The complete JSON request-envelope limit for Bridge endpoints is:

```text
2 MiB = 2,097,152 bytes
```

The larger envelope limit permits one 1 MiB artifact to be transported as
base64 with bounded metadata. Exceeding either limit fails closed. Limits are
checked before artifact persistence.

`BYTE_EXACT_FILE_IMPORT` accepts base64 transport, decodes it once, and hashes
the resulting bytes before Unicode decoding, newline conversion, trimming,
Markdown parsing, field extraction, or display escaping. Its identity is the
decoded file bytes, not the base64 spelling.

`PASTE_CAPTURE` encodes the exact captured browser string as UTF-8 and hashes
those captured bytes. It makes no claim that the captured payload is
byte-identical to an external file and is not eligible for Golden fixation.

Consequently:

- LF and CRLF payloads are different artifacts;
- adding or removing a trailing newline changes identity;
- a declared SHA-256 mismatch rejects the import;
- the source path or label is metadata and is not identity proof;
- the current Codex runtime identity is never substituted for an imported Pro
  model identity.

## Canonical JSON and generated-byte contracts

All canonical Bridge JSON uses:

```text
encoding: UTF-8 without BOM
key order: lexicographically sorted
separators: "," and ":" with no insignificant whitespace
Unicode: emitted directly; no normalization
numbers: finite JSON numbers only; NaN and Infinity are rejected
file ending: exactly one LF
```

In Python terms, the canonical object form is equivalent to:

```python
json.dumps(
    value,
    allow_nan=False,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
)
```

Pretty-printed JSON shown in the browser is presentation only and is not a
hash preimage.

Every `events.jsonl` line is one canonical JSON object followed by LF. An event
hash is SHA-256 over the canonical event object without `event_hash`.
`previous_event_hash` binds the prior verified event, starting from a fixed
64-zero genesis value. Reads verify the entire chain before later appends.
The materialized session also anchors the verified chain head and event count.
Repository-scoped file locking serializes mutations across processes; lock
waits are bounded, and a busy or corrupt Bridge remains a panel-local failure
so the existing Runner and approval surface remain available.

Generated Markdown uses UTF-8, LF newlines, no BOM, no trailing spaces, and
exactly one final LF. The same frozen inputs produce the same generated bytes.
Import-event time, output-freeze time, UUIDs, and final output byte hashes are
fixed in external identity records rather than injected into deterministic
content.

An artifact cannot contain its own final byte hash without a self-reference.
An Execution Handoff therefore carries an explicit external-fixation
placeholder; the freeze record and later Build Receipt carry the actual
SHA-256. A receipt ID likewise excludes its own `receipt_id` from the canonical
preimage and includes referenced import-event IDs in a fixed ordered array.

## Artifact envelope

An imported document may contain one normative fenced JSON object, or the user
may provide the same fields as explicit import metadata. The operationally
selected role is supplied separately by the user before payload acceptance.
The document's declared or embedded role is evidence only.

The v0.1 envelope uses these stable fields:

```text
schema
task_id
protocol_run_id
artifact_role
selected_role
declared_role
source_path_or_label
model_identity.value
model_identity.basis
model_identity.verification_state
role_identity
artifact_authored_at
imported_at
as_of_commit
evidence_packet_identity
artifact_content_hash
import_event_id
authority_state
objective
completion_line
do_not_touch
current_gate
authority_boundary
required_next_actor
findings
human_execution_cost
reusable_delta
unknowns
```

`artifact_content_hash`, `imported_at`, and `import_event_id` may be
`TO_BE_FIXED_AT_IMPORT` in source material. The accepted import record replaces
those markers with system-fixed values; it does not rewrite the immutable
source bytes.

## Role and authority separation

The fixed artifact-role family is:

```text
EVIDENCE_PACKET
PRO_DESIGN
EXECUTION_HANDOFF
BUILD_RECEIPT
PRO_AUDIT
REUSABLE_DELTA_RECORD
GOLDEN_MANIFEST
REPLAY_RESULT
BRIDGE_RECEIPT
FORWARD_ONLY_DELTA
```

Users may import only:

```text
EVIDENCE_PACKET
PRO_DESIGN
BUILD_RECEIPT
PRO_AUDIT
REUSABLE_DELTA_RECORD
```

The Bridge generates the remaining roles.

| Role | Permitted meaning | Does not imply |
|---|---|---|
| Evidence Packet | frozen evidence input | design or execution authority |
| Pro Design | design input | build, merge, publication, or PASS |
| Execution Handoff | instruction artifact | authority grant |
| Build Receipt | execution evidence | independent audit or Product PASS |
| Pro Audit | independent judgment | implementation or merge authority |
| Reusable Delta | future-use candidate | automatic Canon update |
| Golden manifest | frozen comparison index | correctness or certification |
| Replay result | structural comparison | Protocol or Product PASS |
| Bridge Receipt | local artifact and observation chain | third-party certification |

Identity never grants authority. A hash, model name, role label, timestamp,
commit, source label, Golden state, or Replay result is never consumed as file
approval, execution permission, merge authority, or publication authority.

Pro Design and Pro Audit require different selected roles and different import
event IDs. A Build Receipt cannot satisfy the Audit role. The same bytes cannot
be assigned two selected roles in one session. Structured authority exceeding
the selected role moves the Bridge to `BLOCKED_AUTHORITY_INFLATION`.
Every imported Design, Build Receipt, Audit, and Reusable Delta also binds the
fixed Evidence Packet commit, blob, and SHA-256. A mismatch remains held and
cannot become effective.

## Result separation

The Bridge retains three independent result objects:

```text
Protocol Result:
Did the manual protocol execute correctly?

Product Result:
Did Companion Manual Bridge v0.1 satisfy the bounded design?

Replay Result:
Did the Bridge preserve the Golden structure?
```

Every pairwise non-implication flag is true. No result update changes another
result, and the UI must not collapse them into one badge.

During the Builder stage the visible defaults are:

```text
Protocol Result: IN PROGRESS / NOT FINAL
Product Result: BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED
Replay Result: NOT YET PERFORMED
```

## Session lifecycle

The bounded lifecycle vocabulary is:

```text
BOUNDARY_INCOMPLETE
COPY_READY
DESIGN_IMPORTED
HANDOFF_GENERATED
HANDOFF_FROZEN
BUILD_RECEIPT_IMPORTED
AUDIT_IMPORTED
DELTA_IMPORTED
GOLDEN_INCOMPLETE
GOLDEN_ELIGIBLE
GOLDEN_FROZEN
REPLAY_ELIGIBLE
REPLAY_RECORDED
BLOCKED_CORRUPT
BLOCKED_AUTHORITY_INFLATION
```

A session begins with frozen task, protocol, objective, Completion Line, Do Not
Touch, Gate, Authority Boundary, As-of commit, required-next-actor, and
Evidence Packet identity fields. Missing required values keep the boundary
incomplete.

The usual successful sequence is:

1. create a complete boundary;
2. generate deterministic Copy for Pro;
3. import and freeze one valid Pro Design;
4. generate and freeze an instruction-only Execution Handoff;
5. import one Build Receipt;
6. import one independent Pro Audit;
7. import one Reusable Delta Record;
8. generate and freeze the Bridge Receipt and Golden manifest;
9. become Replay-eligible only after all six Golden roles are fixed;
10. compare one candidate and record a Replay result.

Frozen artifacts are never edited in place. Correction creates new bytes, a
new hash, a new event, `supersedes_import_event_id`, a reason, and a
Forward-only Delta linkage. A second distinct artifact for a role never
silently replaces the current effective identity. Once the Golden manifest is
frozen, a correction remains held until a separate Forward-only manifest
version can preserve the historical frozen entry.

## Local HTTP API

All routes are loopback-only. `GET /api/state` returns the ordinary Companion
snapshot plus `manual_bridge`. Every state-changing route below requires the
private session cookie, exact same Origin, and CSRF token.

| Method and path | Request object | Effect |
|---|---|---|
| `POST /api/bridge/session` | `{"boundary": {...}}` | freeze one session boundary |
| `POST /api/bridge/copy` | `{}` | generate Copy for Pro |
| `POST /api/bridge/import` | role, mode, source, one payload form, optional metadata/hash/supersession | capture and validate exact payload bytes |
| `POST /api/bridge/handoff/generate` | `{}` | generate an instruction-only Execution Handoff |
| `POST /api/bridge/output/freeze` | `{"role": "<generated role>"}` | externally fix generated bytes and identity |
| `POST /api/bridge/receipt/generate` | `{}` | generate the separate Bridge Receipt |
| `POST /api/bridge/manifest/generate` | `{}` | generate the six-role Golden manifest |
| `POST /api/bridge/replay` | `{"baseline": {...}, "candidate": {...}}` | perform typed structural comparison |
| `POST /api/bridge/observation` | field, value, unit, method, optional notes | record one bounded burden observation |

For file import, the sole payload field is `payload_base64` and mode is
`BYTE_EXACT_FILE_IMPORT`. For paste import, the sole payload field is
`payload_text` and mode is `PASTE_CAPTURE`. Supplying both, neither, an unknown
mode, or a non-object metadata value is invalid.

None of these routes calls the Codex adapter or the existing exact-file
approval route.

## Execution Handoff

The generated Markdown preserves the thirteen repository-native fields:

```text
Target Layer
Repo Root
Current State
Current Gate
Active Branch
Next Authorized Action
Completion Line
Missing Closure
Next Owner
What the Receiving AI Now Owns
First One Action
Do Not Continue Boundary
What must not be returned to the Decision Owner
```

It also carries Task ID, Protocol Run ID, Evidence Packet identity, Pro Design
hash/model/role/time, external Handoff-hash fixation, and authority state.

The generated default is:

```text
Current Gate: HOLD — SEPARATE BUILDER AUTHORITY REQUIRED
Authority state: INSTRUCTION_ARTIFACT_ONLY
```

Generation and freeze are blocked when a required field is missing, a role
conflicts, identity does not match, UNKNOWN has been smoothed away, store
integrity fails, or authority is inflated.

## Golden manifest

The manifest always contains these six entries in this order:

1. `EVIDENCE_PACKET`
2. `PRO_DESIGN`
3. `EXECUTION_HANDOFF`
4. `BUILD_RECEIPT`
5. `PRO_AUDIT`
6. `REUSABLE_DELTA_RECORD`

Each entry records role, state, source, SHA-256, Git/fixation identity when
known, import event, model and role identity, authored/import time, As-of
commit, authority, result boundary, UNKNOWNs, and supersession.

A not-yet-produced role remains visible as:

```json
{
  "artifact_role": "PRO_AUDIT",
  "state": "MISSING",
  "artifact_sha256": "UNKNOWN",
  "import_event_id": "UNKNOWN",
  "reason": "NOT_YET_PRODUCED"
}
```

Replay eligibility requires all six entries to have one effective frozen
artifact, a frozen manifest, and no unresolved collision, hash mismatch,
corruption, or authority inflation. Eligibility changes no Protocol or Product
result.

The repository Golden manifest for V13-PMR-002 is reserved for the later
Golden owner. Builder-stage product tests may use fixture manifests and the
private generated manifest; they do not create the reserved repository file.

## Structural Replay

Replay accepts top-level `task_id`, `protocol_run_id`, and a `fields` object.
Live Replay also requires `manifest_identity` on both baseline and candidate
to equal the exact frozen Golden-manifest SHA-256, plus one bounded
`candidate_id`. The result records a system-computed SHA-256 for the complete
candidate object. A complete manifest deterministically projects typed atoms
from its effective structured imports, embeds that baseline, and records its
SHA-256. Freezing the manifest therefore commits the six sources and the exact
baseline; a caller cannot substitute another baseline at Replay time.
Baseline and candidate task/protocol identities must match the manifest, and
every live atom's `source_artifact_hash` must identify one of that manifest's
six frozen artifacts. Source locations are bounded single-line values. The
pure structural comparator remains usable for fixtures without changing
lifecycle state.

The fixed field IDs are:

```text
task_id
objective
completion_line
do_not_touch
current_gate
authority_boundary
as_of_identity
model_identity
role_identity
time_anchor
required_next_actor
findings
human_execution_cost
reusable_delta
unknowns
```

Every field contains an `atoms` array. Each structural atom has:

```json
{
  "atom_id": "CL-001",
  "value": "bounded value",
  "source_artifact_hash": "sha256",
  "source_location": "$.completion_line"
}
```

Each field receives exactly one primary status:

```text
PRESERVED
ALTERED
MISSING
SUBSTITUTED
AUTHORITY-INFLATED
NOT APPLICABLE
UNKNOWN
```

Replay is deterministic and uses no LLM, embedding, semantic similarity, or
fluent-prose score. A paraphrase without the required atoms is `MISSING`. A
different source, actor, role, or time presented in place of the baseline is
`SUBSTITUTED`. Increased authority is `AUTHORITY-INFLATED`. `NOT APPLICABLE`
requires an explicit baseline reason. UNKNOWN remains UNKNOWN unless an
explicit Forward-only Delta resolves it. Candidate atom identities must be
complete and unique. Extra atoms alter a fixed field; only findings or reusable
deltas carrying explicit Forward-only linkage may be recorded as additions
without rewriting the preserved baseline atoms.

Replay PASS requires every required field to be `PRESERVED` or an
evidence-backed `NOT APPLICABLE`, with no unresolved baseline UNKNOWN and no
altered, missing, substituted, or authority-inflated field.

## UNKNOWN and observations

`UNKNOWN` is an explicit unresolved state. It is not equivalent to an empty
string, `null`, false, zero, `N/A`, or PASS. Missing imported model or authored
time remains UNKNOWN; import time does not replace authored time.

Every burden observation records:

```text
value_or_unknown
unit
method
source_event_ids
recorded_at
basis
confidence
notes
```

Pre-product events that the Bridge could not observe remain:

```text
UNKNOWN — PRE-BRIDGE MANUAL EVENT NOT SYSTEM-OBSERVED
```

Existing Verified Save estimates are not measured Golden cost and are never
copied into the Bridge burden sheet as observations.

The optional Framework Lens fields are trace metadata only. They do not gate
imports, choose models, route agents, grant authority, or affect Product PASS.

## Security and fail-closed behavior

The Bridge inherits the Companion's loopback bind, one-time bootstrap,
HttpOnly SameSite cookie, exact Host and Origin checks, CSRF validation,
no-store responses, CSP, static allowlist, and JSON `<`, `>`, and `&` escaping.

Imported names and prose are rendered with text nodes, never executable HTML.
Raw imported prose is not placed into `innerHTML`, evaluated, followed as an
instruction, or copied into an authority field.

The client rejects files larger than 1 MiB before calling `arrayBuffer()`.
Disconnect and repository changes clear unsent role, file, paste, metadata,
Replay, and boundary drafts before controls can be re-enabled.

State access is restricted to the selected repository's resolved Git common
directory. Path traversal, symlink escape, malformed base64, non-object JSON,
oversized content, event-chain mismatch, content-addressed blob mismatch, and
post-freeze output alteration fail closed with bounded errors.

## Non-goals

v0.1 does not provide:

- model invocation, model selection, or model routing;
- automatic Builder start or automatic handoff acceptance;
- a public service, SaaS surface, or network listener;
- general workflow orchestration, Guided Intake, Multi-Agent Roles, or
  Orchestra behavior;
- semantic or LLM-based Replay;
- AccelerationStore migration or Verified Save Receipt extension;
- automatic file approval, merge, publication, release, or Canon promotion;
- independent audit generated by the Builder;
- automatic burden-reduction claims;
- Stage 3–5 behavior, pricing, market claims, or public release work.
