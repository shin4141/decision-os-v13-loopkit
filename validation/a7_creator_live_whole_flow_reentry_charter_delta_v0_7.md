# V13 Creator-Live Whole-Flow Re-entry Charter Delta v0.7

Status: `AUTHORIZED — implementation and non-live qualification only`

## Purpose

This Forward-only Delta authorizes a version-gated Creator-Live proof v0.3
implementation that durably preserves content-free Run 2 output identity and
A3 compiler audit identity before A3 can produce a checkpoint or terminal
failure. It also authorizes terminal/restart projection from durable typed
records, a read-only backward projection of Cycle 005, and removal of the
terminal Cycle 005 Start affordance.

It does not authorize a model invocation, task transmission, another proof
opening, Cycle 005 continuation or replacement, Cycle 006 design, release, or
publication.

## Authority and Fixed History

| Authority | Identity |
| --- | --- |
| Parent Charter | `validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md` |
| Parent Charter SHA-256 | `84e65d12e7b7dd2c86204273c7dc96c16689580e3148f9a0beb2993fd7ee0585` |
| Delta v0.6 | `validation/a7_creator_live_whole_flow_reentry_charter_delta_v0_6.md` |
| Delta v0.6 SHA-256 | `3c5aeeebba29ea7c59fa559cbde9d5cb10b171e0c24778c9ba9ce9930f7180b1` |
| Implementation authorization observed at | `2026-08-05T12:28:00Z` |
| Starting revision | `bbfa49ba48254758a8b6429b2eb88d141954eac8` |

Cycle 005 remains permanently:

```text
FAILED / A3_REUSE / A3_EXACT_STRUCTURE_MISSING
```

Its fixed identities are:

| Field | Identity |
| --- | --- |
| Launch binding | `e03a8f05be5a30e0af0e20ff983a0c89f675cb02376562f339e8899311e60bb1` |
| Proof attempt | `proof_a7_creator_live_cycle_005_e03a8f05be5a30e0af0e20ff983a0c89f675cb02376562f339e8899311e60bb1` |
| Journal-file SHA-256 | `1de2e998804f5fb694707846b7deb0dc9d8b5f9cfc6027ad0210ddc270029322` |
| Anchor-file SHA-256 | `e246757a7ba98849a6b4a694ababf473dc1a98baf1fc1ce0ea7daa3a6e7e8610` |
| Typed-readback SHA-256 | `481be90dc8751bda3d7b00714f5a0c650230dffa8974a1332881ce42c127710f` |

No Cycle 005 proof byte, historical Note, prior Charter, maturity record, or
other historical proof may be rewritten, migrated, normalized, regenerated,
re-anchored, retried, resumed, replaced, or deleted.

## Starting-State Gate

Before implementation work, the executing agent verified:

| Gate | Verified value |
| --- | --- |
| Selected repository | `/Users/sn/Documents/v13/decision-os-v13-loopkit` |
| Branch | `main` |
| Local main / origin/main | `bbfa49ba48254758a8b6429b2eb88d141954eac8` / exact equality |
| Ahead / behind | `0 / 0` |
| Tracked worktree and index | clean |
| Git operation | none active |
| Cycle 005 journal-file SHA-256 | exact fixed identity |
| Cycle 005 anchor-file SHA-256 | exact fixed identity |
| Cycle 005 typed-readback SHA-256 | exact fixed identity |

Pre-existing untracked files are preserved. Any mismatch in this gate requires
`HOLD`; it does not authorize cleanup, repair, or discard.

## Version-Gated Durable Schema

New attempts may use only these new schemas and filenames:

```text
decision-os.field-note-creator-live-proof-journal.v0.3
decision-os.field-note-creator-live-proof-record.v0.3
decision-os.field-note-creator-live-proof-anchor.v0.3
decision-os.field-note-creator-live-proof-readback.v0.3
creator-live-proof-v0.3.jsonl
creator-live-proof-v0.3.anchor.jsonl
```

The v0.1 and v0.2 schemas, parsers, record ordering, anchor semantics, typed
readback bodies, and readback hashes are frozen. v0.3 records are admitted only
under the v0.3 record schema. No old record may be rewritten into v0.3.

### Terminal projection binding

For v0.3 only, `ATTEMPT_OPENED` contains one typed, content-free
`terminal_projection_binding` with exactly:

```text
schema
launch_binding_sha256
contract_identity:
  profile
  title
  source_byte_count
  source_sha256
  wrapper_sha256
  interpretation_sha256
ordinary_contract_execution_authority
guided_intake_freeze_authority
implementation_authorization_observed_at
run_1_task:
  byte_count
  sha256
run_2_task:
  byte_count
  sha256
historical_boundary:
  cycle_key
  state
  failure_boundary
  failure_code
retry_count
replacement_count
```

Revision, runtime, Cycle authorization, and proof-attempt identity remain owned
by their existing typed fields. The complete P0 binding is not persisted.

### Run 2 output identity

The journal record kind `RUN_2_OUTPUT_IDENTITY_RECORDED` has payload schema:

```text
decision-os.field-note-creator-live-run-2-output-identity.v0.1
```

It contains exactly:

```text
schema
proof_attempt_id
run_id
task_byte_count
task_sha256
transmission_ordinal
normal_terminal
turn_status
runtime_status
failure_diagnostic_absent
final_output_byte_count
final_output_sha256
output_artifact:
  schema
  artifact_id
  proof_attempt_id
  run_id
  transmission_ordinal
  media_type
  byte_count
  sha256
a3_compiler_branch
```

Its fixed values are:

```text
transmission_ordinal = 2
normal_terminal = true
turn_status = completed
runtime_status = NORMAL_TERMINAL
failure_diagnostic_absent = true
media_type = text/plain; charset=utf-8
a3_compiler_branch =
  EXACT_UTF8_NON_WHOLE_UNIQUE_SOURCE_UNIQUE_OUTPUT
```

It binds the proof and Run identities; Run 2 task byte count and SHA-256;
verified normal-terminal facts; final-output byte count and SHA-256; a canonical
output-artifact identity; and the exact compiler branch.

```text
EXACT_UTF8_NON_WHOLE_UNIQUE_SOURCE_UNIQUE_OUTPUT
```

The artifact identity is the SHA-256 of canonical JSON over its schema,
proof-attempt ID, Run ID, transmission ordinal, media type, byte count, and
SHA-256. It contains no output bytes or text.

### A3 compiler audit identity

The journal record kind `A3_COMPILER_AUDIT_RECORDED` has payload schema:

```text
decision-os.field-note-creator-live-a3-compiler-audit.v0.1
```

It contains exactly:

```text
schema
proof_attempt_id
run_id
output_artifact_id
compiler_version
compiler_branch
source_note_byte_count
source_note_sha256
output_byte_count
output_sha256
eligible_candidate_count
rejection_counts:
  below_minimum_byte_length
  whole_note_range
  non_unique_source_occurrence
  absent_output_occurrence
  multiple_output_occurrences
longest_candidate_byte_count
winning_candidate_count
selected_source_start_byte
selected_source_end_byte
selected_output_start_byte
selected_output_end_byte
terminal_a3_code
audit_sha256
```

The exact compiler version is:

```text
decision-os.creator-live-a3-exact-output-artifact-compiler.v0.1
```

All four offsets are populated only for exactly one winner. They are otherwise
null. The terminal code is null for one winner,
`A3_EXACT_STRUCTURE_MISSING` for no eligible winner, and
`A3_EXACT_STRUCTURE_AMBIGUOUS` for an ambiguous winner set.

## Mandatory Ordering

The runtime must enforce:

```text
open v0.3 attempt with terminal projection binding
→ journal fsync
→ anchor append and fsync
→ directory fsync
→ exact typed readback
→ Run 2 verified normal terminal
→ construct content-free output identity
→ journal/anchor/directory fsync
→ exact typed readback
→ enter A3 from that durable identity only
→ run the unchanged compiler in memory
→ construct content-free compiler audit
→ journal/anchor/directory fsync
→ exact typed readback and identity cross-check
→ cross-check against durable Run 2 output and durable Note identities
→ A3 checkpoint or exact terminal A3 failure
→ discard transient Note and output bytes when no longer required
```

A process restart never resumes model transport or compilation. An interrupted
open attempt remains `OPEN_UNRESUMABLE`. A torn journal or anchor append remains
`INTEGRITY_FAILURE`. Neither state grants repair, retry, or replacement.

## Frozen A3 Predicate

This Delta changes evidence persistence only. A3 remains exact UTF-8 byte
matching over a range with at least 32 non-whitespace bytes, not the whole
Note, occurring exactly once in the source and exactly once in output. It
admits no normalization, trimming-based equivalence, fuzzy matching, semantic
substitution, usefulness inference, or authority inference.

## Terminal Projection and Privacy

After proof storage is occupied, the UI obtains its terminal projection only
from version-appropriate durable typed readback. The public projection is an
explicit allowlist containing only:

- exact revision;
- Contract identity;
- ordinary Contract execution authority;
- Guided Intake freeze authority;
- runtime tuple;
- Run 1 and Run 2 task byte counts and SHA-256 values;
- Cycle and implementation authorization timestamps;
- historical boundary;
- launch binding and proof-attempt ID;
- runtime-issued `proof_as_of`;
- journal-file, anchor-file, and typed-readback SHA-256 values;
- terminal stage and exact failure code;
- retry and replacement counts;
- output-artifact identity;
- compiler identity and result.

It must not expose task bodies, Note contents or paths, model-output text,
hidden approvals, arbitrary repository paths, arbitrary journal fields, the
complete P0 binding, or protected-history listings.

Unknown fields, invalid hashes, negative counts, inconsistent offsets,
unexpected record ordering, or mismatched artifact identities fail closed.

Cycle 005 projects only fields durably present in v0.2:

| Field | Exact projection |
| --- | --- |
| Exact revision | `bbfa49ba48254758a8b6429b2eb88d141954eac8` |
| Contract identity | `NOT_DURABLY_PERSISTED` |
| Ordinary Contract authority | `NOT_DURABLY_PERSISTED` |
| Guided Intake freeze authority | `NOT_DURABLY_PERSISTED` |
| Runtime | `chatgpt / gpt-5.6-sol / ultra / priority / CLI 0.146.0-alpha.3.1` |
| Run 1 byte count | `NOT_DURABLY_PERSISTED` |
| Run 1 SHA-256 | `e377fb2f9e003f3f04e8d1b10d2aef96347416d86f78305102d4671519ed3417` |
| Run 2 byte count | `NOT_DURABLY_PERSISTED` |
| Run 2 SHA-256 | `NOT_DURABLY_PERSISTED` |
| Cycle authorization | `2026-08-05T06:22:00Z` |
| Implementation authorization | `NOT_DURABLY_PERSISTED` |
| Historical boundary | `NOT_DURABLY_PERSISTED` |
| Launch binding | derived only from validated durable proof-attempt grammar |
| Proof-attempt ID | `proof_a7_creator_live_cycle_005_e03a8f05be5a30e0af0e20ff983a0c89f675cb02376562f339e8899311e60bb1` |
| Runtime `proof_as_of` | `2026-08-05T11:24:40.255812Z` |
| Journal-file SHA-256 | `1de2e998804f5fb694707846b7deb0dc9d8b5f9cfc6027ad0210ddc270029322` |
| Anchor-file SHA-256 | `e246757a7ba98849a6b4a694ababf473dc1a98baf1fc1ce0ea7daa3a6e7e8610` |
| Typed-readback SHA-256 | `481be90dc8751bda3d7b00714f5a0c650230dffa8974a1332881ce42c127710f` |
| Retry / replacement counts | `NOT_DURABLY_PERSISTED` |
| Terminal state | `FAILED / A3_REUSE / A3_EXACT_STRUCTURE_MISSING` |

Current constants and contemporary state are not substitutes for historical
persistence. The terminal stage is read from `failure_boundary`, not transient
coordinator state.

When storage is occupied, the actionable `Start Cycle 005` control is absent
and is replaced with:

```text
TERMINAL — NO RETRY OR REPLACEMENT
```

The backend `409 / CYCLE_005_ATTEMPT_EXISTS` guard remains authoritative.
Keyboard and click submission paths are disabled or removed after
terminalization and cannot issue a Start POST.

## Authorized Surface

Production:

- `decision_os/companion/field_notes_creator_live.py`
- `decision_os/companion/field_notes_controller.py`
- `decision_os/companion/field_notes_creator_live_entrypoint.py`
- `decision_os/companion/static/index.html`
- `decision_os/companion/static/app.js`

Tests:

- `tests/test_field_notes_creator_live.py`
- `tests/test_field_notes_creator_live_reconnect.py`
- `tests/test_field_notes_creator_live_entrypoint.py`
- `tests/test_companion_server.py`

Forward-only authority:

- `validation/a7_creator_live_whole_flow_reentry_charter_delta_v0_7.md`

No other production file is authorized by this Delta.

The Delta does not authorize changing ordinary Contract authority semantics,
the A1 task, the A2 task, or the A3 predicate.

## Qualification and Closure

Qualification uses fixtures and fakes only. It includes focused source and
installed-product suites, frozen v0.1/v0.2 compatibility, Cycle 005 exact hash
checks, crash boundaries, strict A3 cases, projection/privacy behavior, full
default discovery, JavaScript syntax, Python compilation, `git diff --check`,
canonical build/install, source/installed product-tree equality, installed
process replay, and process qualification.

After independent review and forward merge, the unchanged exact Contract must
be Forward-only fixed to the exact implementation merge. Source, installed
runtime, Contract fixation, and running process must agree. Exact-final-merge
P0 is non-live and must not open proof storage or invoke a model.

Closure stops after exact-final-merge P0. It does not authorize another Cycle.

## Stop Conditions

Implementation returns `HOLD` or `BLOCK` rather than expanding scope if:

- starting state or Cycle 005 hashes differ;
- v0.2 typed-readback identity would change;
- compatibility requires rewriting old proof records;
- A3 would require weakening or other predicate change;
- raw task, Note, or output text would need persistence;
- a non-allowlisted production file must change;
- ordinary Contract authority semantics must change;
- Contract refix cannot bind the exact merge;
- source/installed equality or process qualification fails;
- model invocation, task transmission, proof opening, or historical mutation
  appears necessary.

## Rollback

This rollback authority applies only before any future proof opening. Before
merge, abandon the unmerged implementation. After merge, use a normal forward
revert commit, rebuild and reinstall from the exact revert revision,
Forward-only refix the unchanged Contract, and re-establish source/installed
equality and process qualification.

Installed backups may provide temporary recovery, but rollback is incomplete
until source, installed runtime, Contract fixation, and running process agree.
Cycle 005 and every historical proof remain byte-for-byte unchanged.

If any future proof artifact already exists, preserve it; rollback no longer
authorizes deleting or replacing that artifact, and separate disposition is
required.

## Remaining Separate Question

No future Cycle identity, authorization, task pair, or preregistered basis for
future A3 admissibility is established by this Delta.
