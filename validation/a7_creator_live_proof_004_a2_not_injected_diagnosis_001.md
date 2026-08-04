# V13 A7 Creator-Live Proof 004 — A2 Not-Injected Diagnosis 001

## Diagnosis Identity

```text
Layer:
V13 — Creator-Live Whole-Flow
Post-terminal A2 exact-lineage reconnect diagnosis

Repository:
shin4141/decision-os-v13-loopkit

Execution repository HEAD:
fd9ce80f7a1d2199400eacf280075e40ada686fa

Implementation baseline:
83ea1d95df8cfe3f7eb041b85c50fcdc56058692

Product-code tree:
c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5

Proof attempt:
proof_a7_creator_live_004_862c2f5cfdf7b134

Run 1:
run_a7_creator_live_004_1_9535f704b6586ff3

Run 2:
run_a7_creator_live_004_2_2da9c32b7fd99674

Required classification:
A — EXACT-LINEAGE PINNING GAP ESTABLISHED
```

This is a diagnosis-only record. It does not retry, continue, reopen, replace,
repair, or reinterpret Cycle 003. The permanent historical result remains:

```text
FAILED / A2_RECONNECT / A2_NOT_INJECTED
A1 established
A2 not established
```

No product/runtime model was invoked during this diagnosis. No proof identity,
Run, Note, journal, anchor, installation, restart, or production/test change
was created.

## Evidence Inventory

### Protected Cycle 003 evidence

The protected local artifacts were read without editing, moving, staging,
normalizing, or rewriting them.

| Evidence | Exact identity or result |
| --- | --- |
| Saved Note ID | `fn_e502adfcd48485897f1b79e8e59565b0` |
| Saved Note path | `.decision-os/field-notes/2026-08-04-bind-product-code-baseline-and-ws4unkvwfe.md` |
| Saved Note SHA-256 | `dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446` |
| Saved Note bytes | `3657` |
| Saved metadata SHA-256 | `be5f5bdc5846f59533da446e4945e02d53872cee19a8ce6d0202f96c40d78dd2` |
| Saved metadata bytes | `884` |
| A1 capture receipt | `b0cee7313574dbb57402296ad6a5fc719a36f7beafeaac2544fd292d0fa6996f` |
| Run 2 reconnect receipt | `59966b1045ba4999a874ce0781bd8c3cc2950970d78f3997463ad1bd7a852dbb` |
| Final journal | `af0906977646897fa6bb279f512372998404974a5b581070fe5e1e94f9fd4c4a` |
| Final anchor | `349b3298379f88cd2ea62f454c486ac857bc71e16614b7e8de4906e802b80331` |
| Typed readback | `3fb00c2c12ca9ccb83ae88a2b1ed7ddec9c0aa7de3028148169599aaef6e440f` |

The typed readback was independently recomputed from the protected journal and
anchor using the exact implementation. It verifies four journal records, four
anchor records, one A1 trace event, durable readback, the exact captured Note,
the exact A1 commit, the exact Run 2 identity, and the terminal A2 failure.

The final anchor chain binds the final journal byte length `7066`, record count
`4`, record-chain head
`0c87904ee46a396f3863d647d40f9ba92e98e4da958acd8f8570ba4ddb68fdb7`,
and exact final journal SHA-256 above. The anchor carries journal identity, not
a separate semantic projection of the Note.

### Exact Run 2 receipt

The bounded execution result retained:

```text
run_id: run_a7_creator_live_004_2_2da9c32b7fd99674
state: NO_MATCH
failure_reason: none
metadata_entries_seen: 2
metadata_candidate_files_seen: 1
metadata_files_valid: 1
metadata_bytes_read: 884
selected_field_note_path: none
selected_field_note_id: none
selected_metadata_sha256: none
selected_full_note_sha256: none
full_note_bytes_read: 0
full_notes_injected: 0
ordinary_distinct_paths_consumed: 4
```

Its canonical identity is the reconnect receipt SHA-256 above. The counters
show that the saved Note was present and metadata-valid in the Cycle 003
execution worktree. They do not indicate an absent, malformed, or cross-
repository Note. The selector did not perform the full-body read because the
valid metadata candidate failed relevance admission first.

### Exact code and execution transcript

The inspected application paths at execution HEAD were:

- `decision_os/companion/field_notes_model.py`
- `decision_os/companion/field_notes_creator_live_capture.py`
- `decision_os/companion/field_notes_creator_live.py`
- `decision_os/companion/field_notes_controller.py`
- `decision_os/companion/field_notes_adapter.py`
- `decision_os/companion/field_notes_reconnect.py`
- `decision_os/acceleration/codex_adapter.py`

The `decision_os` tree is byte-identical between the implementation baseline
and execution HEAD. The later commits between them add qualification and
Charter controls, not a reconnect-path product change.

The canonical Cycle 003 execution transcript survives locally. Its Run 2
dispatch loads the durable attempt, assigns `before.captured_note` to `note`,
reads the exact bytes at `note.note_path`, verifies the exact Run 2 identity,
constructs `FieldNotesCodexAdapter` without any A2 target or A2 mode, runs the
fixed task, and only then passes the previously loaded `note` and `note_bytes`
to `runtime.record_a2_reconnect(...)`. This transcript is operational
forensic evidence; the protected journal and anchor remain the terminal proof
authority.

## A1 Identity Reach

### Exact identity tuple

The following tuple was durably available before Run 2 execution:

```text
Note ID:
fn_e502adfcd48485897f1b79e8e59565b0

Note relative path:
.decision-os/field-notes/2026-08-04-bind-product-code-baseline-and-ws4unkvwfe.md

Full Note SHA-256:
dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446

Metadata SHA-256:
be5f5bdc5846f59533da446e4945e02d53872cee19a8ce6d0202f96c40d78dd2

Byte count:
3657

Source Run 1:
run_a7_creator_live_004_1_9535f704b6586ff3

Proof attempt:
proof_a7_creator_live_004_862c2f5cfdf7b134

Repository:
repo:v1:b788ba7065dd3b7f687ab07ce4d36b06d62794233c6f61877086c549ad7e7bc6
at fd9ce80f7a1d2199400eacf280075e40ada686fa

Runtime:
gpt-5.6-sol / ultra / priority / Codex CLI 0.146.0-alpha.3.1 /
ChatGPT account

Draft created:
2026-08-04T22:23:00Z

Save As-of:
2026-08-04T22:23:20.614898Z
```

The metadata digest is an exact deterministic derivation from the first `884`
protected Note bytes using the production metadata boundary. It was not a
separately carried A1 field and, because selection returned `NO_MATCH`, the Run
2 receipt left `selected_metadata_sha256` null.

### Boundary-by-boundary reach

`Explicit` means the boundary object or durable record carries the value.
`Derivable` means exact protected bytes carry enough data to reproduce it, but
the field is not explicitly retained there. `Context` means the value is
available to the controlling A1/runtime context but is not a field of that
particular object.

| Boundary | Note ID / path / full SHA | Metadata SHA | Bytes | Run 1 | Proof | Repository / runtime | Save As-of |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Accepted proposal / compiled `FieldNoteDraft` | Explicit | Derivable from `markdown` | Explicit as `len(markdown)` | Explicit | Context | Context | Absent |
| Saved Note | Explicit in metadata/path; full SHA from exact bytes | Derivable | Explicit from exact bytes | Explicit in metadata | Context | Context | Absent |
| A1 capture commit receipt | Explicit | Derivable from bound Note bytes | Explicit | Explicit | Explicit | Explicit | Explicit |
| Journal A1 checkpoint | Explicit in `note` and `capture_commit` | Derivable from bound Note bytes | Explicit | Explicit | Explicit | Explicit | Explicit |
| Anchor generation 1 | Bound through exact journal SHA/count/head | Bound through protected journal and Note, not projected | Bound through journal | Bound through journal | Explicit attempt ID | Bound through journal | Bound through journal |
| Typed readback after A1 | Explicit in `captured_note` and commit | Derivable from bound Note bytes | Explicit | Explicit | Explicit | Explicit | Explicit in commit |
| `open_run_2` input | Run 2 identity does not carry Note; pre-call readback does | Pre-call derivation available | Pre-call readback explicit | Pre-call readback explicit | Explicit in Run 2 | Explicit in Run 2 | Pre-call readback explicit |
| `RUN_2_OPENED` readback | Still explicit in retained `captured_note` and commit | Still derivable | Explicit | Explicit | Explicit | Explicit | Explicit in retained commit |

The code path supports this reach:

1. `FieldNoteProposalGate.propose()` stores the compiled draft in
   `accepted` (`field_notes_model.py:501-538`).
2. The A1 bridge obtains that exact draft, saves it once, performs exact byte
   readback, issues the capture commit, records A1, and verifies durable closure
   (`field_notes_creator_live_capture.py:293-388`).
3. `record_a1_capture()` binds the Note, byte count, and full capture commit in
   the A1 checkpoint (`field_notes_creator_live.py:2083-2167`).
4. Journal projection retains them as `captured_note`,
   `captured_note_byte_count`, and `a1_capture_commit`
   (`field_notes_creator_live.py:1299-1355`).
5. `open_run_2()` reads and validates that state before appending only the Run
   2 identity (`field_notes_creator_live.py:2025-2081`). Its returned readback
   still retains the A1 tuple.

### Reach result

**The exact expected Note identity was available when Run 2 was opened and was
again loaded immediately before adapter construction.** It was not lost at
proposal acceptance, save, A1 commit, journal append, anchor binding, typed
readback, or Run 2 opening.

## Run 2 Reconnect Call Graph

### Actual Cycle 003 path

| Step | Caller → callee | Exact material passed | Mode and identity consequence | Durable evidence |
| --- | --- | --- | --- | --- |
| A1 completion | A1 bridge → `runtime.record_a1_capture(draft, capture_commit, expected_task_sha256, actual_runtime_identity, observed_at)` | Exact draft, Note identity, bytes/count, Run 1, proof, repository, runtime, As-of | Creator-live A1 | A1 checkpoint and anchor generation 1 |
| Run 2 opening | Cycle orchestrator → `runtime.open_run_2(run_2)` | Run 2 ID, proof ID, repository, runtime, start time | Creator-live stage guard; exact captured Note remains in readback but is not an argument | `RUN_2_OPENED` and anchor generation 2 |
| Pre-dispatch readback | Cycle orchestrator → `runtime.read_back()` | None; returns exact A1 tuple and Run 2 | Creator-live identity is available | Verified typed readback in memory |
| Run 2 construction | Cycle orchestrator → `AccelerationEngine(repo)` and `FieldNotesCodexAdapter(engine, input_func, stdout, approval_provider, lifecycle_sink)` | Repository only at engine construction; **no expected Note ID/path/SHA, source Run 1, or proof ID** | No A2 bridge; no A2 controller start; adapter has only its default null A1-capture provider | None |
| Prompt assignment | Cycle orchestrator → `adapter.run(exact_run_2_task)` | Exact prompt SHA `688203fd91c880cb4c9e32619219e9e660160b31fded0ae630ae2a401ea6cdcf` | Ordinary adapter mode | None |
| Run reset | `FieldNotesCodexAdapter.run` → base `CodexAdapter.run` → overridden `_reset_run` | Base obtains exact Run 2 ID from `engine.new_run_id`; override reads prompt and null A1 capture config | Ordinary reconnect selected because prompt is a string and A1 capture is null | None |
| Selector call | Adapter `_reset_run` → `prepare_field_note_reconnect(repository, prompt, run_id)` | **Only repository, exact Run 2 prompt, and Run 2 ID** | Generic relevance mode; expected Cycle 003 Note identity is omitted | In-memory `FieldNoteReconnectPlan(NO_MATCH)` |
| Developer instructions | Adapter `_developer_instructions()` | Ordinary instructions; `plan.envelope` is null | No Note block in `thread/start` developer instructions | None |
| Injection transition | Adapter `_start_thread()` | Marks `injected()` only when an envelope exists | Condition false; zero injected Notes | None |
| Finalization | Adapter `run()` → `plan.finalized(normal_terminal, ordinary_paths=4)` | Normal-terminal result and four later ordinary read paths | `NO_MATCH` remains `NO_MATCH` regardless of later abnormal terminal status | Exact reconnect receipt returned in Run result |
| A2 admission | Cycle orchestrator → `runtime.record_a2_reconnect(receipt, note=expected_note, note_bytes=expected_bytes)` | The exact expected Note reappears only **after** selection and Run completion | Exact Note bytes first pass `_require_exact_note`; `state=NO_MATCH` and count `0` then fail the A2 injection predicate | `ATTEMPT_FAILED / A2_RECONNECT / A2_NOT_INJECTED` and anchor generation 3 |

The decisive production predicate in `field_notes_adapter.py:368-377` is:

```python
if isinstance(prompt, str) and self._creator_live_a1_capture is None:
    self._reconnect_plan = prepare_field_note_reconnect(
        self.engine.store.repository,
        prompt,
        self._run_id,
    )
```

There is no Creator-Live A2 config, provider, controller start method, or
exact-target selector in the inspected code. The only creator-live adapter
configuration is `FieldNoteCreatorLiveA1CaptureConfig`.

The decisive A2 admission predicate in
`field_notes_creator_live.py:2208-2213` is:

```python
receipt.state not in {"INJECTED", "ACTIVATION_UNKNOWN"}
or receipt.full_notes_injected != 1
or receipt.failure_reason is not None
```

It correctly rejects the ordinary selector's `NO_MATCH`. The gap is before
that correct admission guard: no production path pins the A1 identity into
Run 2 reconnect selection.

### Exact loss boundary

The expected Note identity was held in local variables `note` and `note_bytes`
before the adapter was created. The adapter constructor accepted no A2 target,
and `_reset_run()` recomputed a generic plan from only repository, prompt, and
Run 2 ID. The identity was therefore **omitted at the Run 2 adapter/selector
boundary**, not destroyed or made unavailable earlier.

## Exact Model-Free Reproduction

### Fixed inputs

```text
Saved Note SHA-256:
dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446

Run 2 task SHA-256:
688203fd91c880cb4c9e32619219e9e660160b31fded0ae630ae2a401ea6cdcf

Run 2 task bytes:
856

Production token count:
131

Relevance threshold:
4
```

The production `NFKC` + `casefold` + alphanumeric tokenizer produced this
exact sequence:

```text
use the exact reconnected field note from run 1 to evaluate this proposed
execution decision a documentation only execution charter was merged after
product code baseline x the installed runtime matches code baseline x
repository main later moved to commit y after the charter merge because the
runtime code did not change execution may proceed without recording y or
requalifying the repository return a bounded verdict demonstrate use of one
exact structure from the reconnected note through rule trace or output artifact
the evidence must identify the exact note exact bounded structure exact run 2
and how that structure affected the verdict generic similarity correct task
output or an unsupported statement that the note was useful is insufficient do
not propose another field note do not write or modify repository files
```

### Note eligibility

The exact Note independently passes:

| Check | Result |
| --- | --- |
| Canonical filename/date/short-ID identity | PASS |
| Canonical metadata JSON and exact key/value schema | PASS |
| Metadata SHA-256 over exact `884` bytes | `be5f5bdc5846f59533da446e4945e02d53872cee19a8ce6d0202f96c40d78dd2` |
| Compiled Markdown validation | PASS |
| Full UTF-8, marker, heading, body-section, and slug validation | PASS |
| Full-body validation error | `none` |
| Full Note SHA-256 over exact `3657` bytes | `dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446` |
| Metadata source Run | `run_a7_creator_live_004_1_9535f704b6586ff3` |

This excludes classification C. The Note was available, inside the selected
repository, metadata-valid, and independently full-body-valid.

### Stored relevance fields

```text
Task family:
charter-governed execution identity qualification

Path prefixes:
validation/
field_notes/

Exclude terms:
historical proof reconstruction
runtime modification authorization
release authorization
```

`task_family` is validated metadata but contributes zero to `_score()`.
`path_prefixes` contribute only when the prompt contains a valid repository
path inside single-backtick inline code.

### Trigger and exclusion matrix

| Stored term | Production tokens | Exact contiguous prompt match |
| --- | --- | --- |
| `implementation baseline` | `implementation baseline` | no |
| `execution repository HEAD` | `execution repository head` | no |
| `merged execution Charter` | `merged execution charter` | no; the prompt has `execution charter was merged` in the reverse order |
| `runtime build identity` | `runtime build identity` | no |
| `bounded requalification` | `bounded requalification` | no; `requalifying` is a different token |
| `Charter delta` | `charter delta` | no |
| exclude: `historical proof reconstruction` | same | no |
| exclude: `runtime modification authorization` | same | no |
| exclude: `release authorization` | same | no |

The prompt has zero inline-code path values. Therefore neither `validation/`
nor `field_notes/` matches an explicit path.

### Exact score

Production scoring at `field_notes_reconnect.py:617-643` is:

```text
trigger_matches = 0
trigger contribution = min(0, 3) * 2 = 0
explicit-path match = false
explicit-path contribution = 0
exclude match = false

final score = 0
RELEVANCE_THRESHOLD = 4
0 < 4
result = NO_MATCH
```

Direct deterministic invocation of the exact implementation reproduces
`NO_MATCH`, null selection fields, no envelope, zero full-body bytes read, and
zero injected Notes. No prompt or Note byte was changed.

### Candidate inventory and Field Note 125

At Cycle 003 execution time the receipt proves:

```text
direct directory entries: 2
direct Markdown candidates: 1
metadata-valid Markdown candidates: 1
```

The second direct entry was the `proofs` directory. The one Markdown candidate
was the Cycle 003 Note. Therefore there was **no other valid reconnect
candidate and no alternate candidate score** in the execution worktree.

After evidence-preserving copy-back, the canonical working directory also
contains an older local Note,
`.decision-os/field-notes/2026-08-03-topmost-canonical-state-restart-guard-lcmwhjvkpf.md`.
It was not in the isolated Cycle 003 execution worktree. A current read-only
comparison gives that Note score `0` as well and still returns `NO_MATCH`; it
cannot change the historical result.

Tracked `field_notes/125_execution_context_proof_selection.md` was not a
candidate. `prepare_field_note_reconnect()` scans only direct Markdown files
under `.decision-os/field-notes`. The Run 2 receipt records four ordinary
repository paths consumed after the no-envelope thread started. The Run result
records Field Note 125 and its validation as ordinary read evidence. Field Note
125 was therefore reached later through ordinary repository reading, not
selected or injected by reconnect.

The later unsupported dynamic-tool behavior made the Run result abnormal, but
it did not cause the selection failure. The reconnect plan was already
`NO_MATCH` before `thread/start`, and `NO_MATCH` remains unchanged whether the
turn later ends normally or abnormally.

## Contract Comparison

### Ordinary Field Notes reconnect

The ordinary contract is implemented by `prepare_field_note_reconnect()`:

- scan direct local Note metadata safely;
- reject excluded scope;
- calculate prompt trigger and explicit-path relevance;
- select at most one candidate at or above threshold;
- allow `NO_MATCH` without a failure reason when no candidate qualifies; and
- inject only when a selected full Note passes safe full-body validation.

For an ordinary task, the Cycle 003 score `0` and `NO_MATCH` are correct.
Changing ordinary fuzzy/relevance behavior is neither required nor justified
by this diagnosis.

### Creator-Live Whole-Flow A2 reconnect

The Creator-Live A2 contract is exact-lineage, not relevance-based:

- the A1 checkpoint already determines one Note ID, path, full SHA, byte count,
  source Run 1, proof, repository, runtime, and As-of;
- Run 2 must receive that exact Note or a precise exact-identity rejection;
- a lower relevance score cannot authorize an alternate Note or cancel the
  already fixed target; and
- A2 admission requires exactly one injected Note matching A1.

`record_a2_reconnect()` correctly enforces the last point after a receipt
exists. The acquisition path incorrectly uses the ordinary selector before
that point. A generic `NO_MATCH` silently substitutes for exact-lineage target
selection and the runtime can discover the mismatch only after Run 2 has
already executed.

**The current implementation conflates the two acquisition contracts.** It
does not conflate their final admission result: the A2 runtime correctly
terminalizes the generic receipt as `A2_NOT_INJECTED`.

## Root-Cause Classification

```text
A — EXACT-LINEAGE PINNING GAP ESTABLISHED
```

This is A because all of the following are exact:

1. the captured A1 Note identity survived save, commit, journal, anchor,
   readback, and Run 2 opening;
2. Cycle 003 loaded that exact identity and its exact bytes immediately before
   adapter construction;
3. no A2 target was supplied to the adapter;
4. the production selector received only repository, prompt, and Run 2 ID;
5. the only valid candidate scored `0` against threshold `4` and returned the
   exact retained `NO_MATCH` receipt; and
6. the A2 admission guard converted that receipt to the permanent
   `A2_NOT_INJECTED` terminal.

This is not B because the identity was not lost earlier; its omission boundary
is the exact adapter/selector call. It is not C because the saved Note validates
independently and was counted metadata-valid by the actual receipt. It is not D
because both the value-transfer boundary and the exact relevance predicate are
bounded by surviving evidence and deterministic reproduction.

## Narrowest Future Repair Boundary

Repair is not implemented or authorized by this artifact. A separately
authorized repair should preserve the ordinary selector unchanged and add one
explicit Creator-Live A2 exact-target lane.

### Required target and flow

Introduce one immutable Creator-Live A2 reconnect target issued from verified
durable readback after `open_run_2`, containing at minimum:

- expected Note ID;
- expected Note relative path;
- expected full Note SHA-256;
- expected source Run 1 ID;
- expected proof-attempt ID;
- exact source repository identity and commit; and
- exact Run 2 ID.

The exact lane should:

1. validate the repository and target binding before any Run 2 model
   invocation;
2. resolve only the expected direct path under `.decision-os/field-notes`;
3. reuse the existing descriptor-based directory, metadata, full-note,
   containment, symlink, race, size, UTF-8, marker, filename, and compiled-Note
   controls;
4. compare metadata Note ID and source Run 1, full Note path/SHA/bytes, proof,
   repository, and Run 2 to the issued target;
5. bypass `_score()` only for this explicit Creator-Live target;
6. never scan or select an alternate Note on exact-target failure;
7. return a precise missing, changed, invalid, cross-repository, cross-Run,
   cross-proof, or SHA-mismatch failure;
8. inject exactly one validated Note envelope and retain exact selected
   path/ID/metadata SHA/full SHA/count in the receipt; and
9. pass that receipt through the existing `record_a2_reconnect()` exact Note
   and Run 2 checks so the durable A1 + A2 trace proves the complete lineage.

An exact-target failure must terminalize A2 before the Run 2 turn starts and
must leave A3–A7 unopened. Ordinary reconnect must continue to allow relevance
`NO_MATCH`.

### Anticipated production files

The narrow production surface is:

- `decision_os/companion/field_notes_reconnect.py` — add a separate exact-
  target preparation function that reuses the safe readers and leaves
  `prepare_field_note_reconnect()` unchanged;
- `decision_os/companion/field_notes_adapter.py` — accept one typed A2 target
  provider, select exact mode only when that target is present, and fail before
  `thread/start` when exact preparation fails;
- `decision_os/companion/field_notes_controller.py` — add a mutually exclusive
  Creator-Live A2 start/configuration path and propagate the exact receipt;
- `decision_os/companion/field_notes_creator_live_reconnect.py` — new bounded
  bridge from durable A1/Run 2 readback to controller dispatch and existing A2
  admission.

No change is anticipated in:

- `decision_os/companion/field_notes_creator_live.py`; its current exact Note,
  Run 2, receipt-state, injected-count, and selected-identity guards are already
  correct;
- journal, anchor, or typed readback schemas;
- ordinary reconnect scoring or thresholds;
- A1 capture; or
- A3–A7 logic.

If implementation proves that an existing receipt cannot carry a precise
exact-target failure without weakening its invariants, that schema question
must be returned for a separately bounded delta rather than silently widening
this repair. This diagnosis does not authorize such a change.

### Anticipated focused test files

- `tests/test_field_notes_reconnect.py`
- `tests/test_field_notes_lite.py`
- `tests/test_companion_controller.py`
- `tests/test_field_notes_creator_live.py`
- `tests/test_field_notes_creator_live_reconnect.py` — new focused bridge tests

Required tests should prove exact success, no relevance-score dependency in
exact mode, ordinary selection unchanged, no alternate selection, and precise
fail-closed results for missing, changed, invalid, cross-repository, cross-Run,
cross-proof, and SHA-mismatched targets. They must also prove zero Run 2 model
invocation on pre-thread exact-target failure, exact injected receipt fields,
durable A2 admission on success, and no A3–A7 opening on failure.

Rollback is one revert of the separately authorized bounded repair while the
live-proof gate remains blocked. No historical artifact, ordinary selector,
or A3–A7 schema would require migration.

## Claim Boundary

This diagnosis establishes only why Cycle 003's saved Note was not selected
and injected:

```text
The exact A1 Note identity existed and remained available.
Cycle 003 did not pass it to reconnect selection.
The ordinary selector scored the valid Note 0 below threshold 4.
The resulting NO_MATCH receipt correctly failed A2 as A2_NOT_INJECTED.
```

It does not claim:

- Cycle 003 success, continuation eligibility, retry eligibility, or repair;
- A2, A3, A4, A5, A6, or A7 establishment;
- that Field Note 125 was reconnected;
- that the later Run 2 output or verdict is valid reuse evidence;
- model, portability, cross-model, cross-repository, Warehouse, release, or
  publication eligibility; or
- authority to implement the proposed repair or begin another live cycle.

Historical boundaries remain:

| Historical cycle or proof | Unchanged result and identity |
| --- | --- |
| Proof 001 | Permanent FAIL — direct-write A1 path violation; protected identity `UNAVAILABLE` |
| Proof 002 | Permanent FAIL; historical diagnosis `B — Cause family narrowed`; journal `8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c`; anchor `3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c` |
| Proof 003 | Permanent FAIL; journal `d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1`; anchor `0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc`; typed readback `e50e77ce318befcd24bf6057c02aeb15d56aedff76f8600983bc41bc4b313e2b` |
| Cycle 002 | `BLOCK — volatile P0, before P1 identity creation`; no proof identity or Run |

None is reopened, reinterpreted, retried, replaced, or modified here.

## Gates and Completion

```text
Diagnosis:
PASS — A — EXACT-LINEAGE PINNING GAP ESTABLISHED

Repair Gate:
BLOCK

Live Proof Gate:
BLOCK

Retry count:
0

Replacement count:
0

Product/runtime model invocations during diagnosis:
0
```

One exact A2 failure classification and one bounded future repair boundary are
recorded without changing Cycle 003 or implementation.
