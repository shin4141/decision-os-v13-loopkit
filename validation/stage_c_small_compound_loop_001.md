# Stage C Small Compound Loop 001

## Identity

```text
Stage:
C — Small Compound Loop

Starting canonical main:
a920a796c01f0e448037a8e0390f10861b641df0

Focused branch:
codex/stage-c-small-compound-loop

Automatic continuation limit:
2

Hard total Run cap:
3

Run 4:
STRUCTURALLY ABSENT

Stage D:
NOT AUTHORIZED / NOT STARTED
```

## Real Goal

```text
Establish the exact accepted Stage A proof, accepted Stage B proof, and the
fixed Roadmap v0.3 Stage C three-Run boundary through three distinct read-only
actions.
```

The Goal was fixed before Run 1. The three actions were distinct and jointly
necessary: Stage A establishes the Supervisor predecessor, Stage B establishes
the one-continuation predecessor, and Roadmap v0.3 establishes the authorized
Stage C outcome and cap boundary. No single read establishes that complete
lineage.

The proof used the production `CompanionController`, Stage B atomic
continuation store, Receipt delta path, Supervisor, causal Task constructor,
integrity validator, and reconnect loader. The Worker adapter performed actual
local repository reads and returned content-free path, byte-count, SHA-256, and
repository-identity evidence. It was deliberately a deterministic local reader:
no repository file content was transmitted to an external model and no file was
modified.

```text
Repository identity:
a920a796c01f0e448037a8e0390f10861b641df0

Worker execution lane:
local-deterministic-repository-reader / local / no external transmission

File-change approval requested:
NO

Tracked or untracked repository mutation during proof:
NONE — pre-proof and post-proof git status were byte-for-byte identical
```

## Run 1

```text
Task:
Read only validation/stage_a_supervisor_judgment_001.md and establish its exact
accepted Stage A PASS identity.

Run ID:
57b1bfdc-10dd-4b42-b4e8-41f4027feee9

Terminal:
NORMAL_TERMINAL / completed normally

Read evidence:
validation/stage_a_supervisor_judgment_001.md
5732 bytes
SHA-256 a9b65437ea94b624ede85b2dfdb2f4f93d5a81a3bb17a5829d8f6c13a35ba77f
repository identity a920a796c01f0e448037a8e0390f10861b641df0

File actions:
none

Receipt delta:
0 Verified Saves / 0 Verified Reuses / 0 estimated value

Persisted Run 1 evidence SHA-256:
38a294e67a51066af1815b72bea58f11f133616fec2bcd3de519a25b03785a31
```

Run 1 residue:

```text
Newly established:
STAGE-A-PASS

Still open:
STAGE-B-PASS
STAGE-C-BOUNDARY

Residue SHA-256:
98bc3ccdebe5febd01d38bf090037abb9a08d6fb5d47f6f025d703ec952e6b1c
```

Supervisor 1 independently consumed Run 1 and returned:

```text
GO / AI-OWNED

Consumed Run:
57b1bfdc-10dd-4b42-b4e8-41f4027feee9

Judgment SHA-256:
e065500ecf2ddfa8d7c81444cd047892ae703b07004719a4872222960351f96a

Next bounded action:
Establish STAGE-B-PASS from
validation/stage_b_one_automatic_continuation_001.md.
```

## Automatically Constructed Task 2

Task 2 was absent before Run 1. The controller constructed it only after the
Run 1 result, Receipt delta, cumulative residue, and Supervisor 1 judgment were
persisted and read back.

```text
Original Goal SHA-256:
4b94ec9d1ce971352ed0fac74729e4bfe9be3804fb2ad46244753e4a0b725169

Source Run ID:
57b1bfdc-10dd-4b42-b4e8-41f4027feee9

Source evidence SHA-256:
38a294e67a51066af1815b72bea58f11f133616fec2bcd3de519a25b03785a31

Source judgment SHA-256:
e065500ecf2ddfa8d7c81444cd047892ae703b07004719a4872222960351f96a

Selected requirement:
STAGE-B-PASS

Task 2 SHA-256:
0f804cbe44e24862de3ea97b059cd38f74eae07f8937cce0d6b7d8ff9e789d8b
```

## Run 2

```text
Run ID:
5ace2dfe-d7ca-46fe-aa43-12fffd2f0412

Terminal:
NORMAL_TERMINAL / completed normally

Read evidence:
validation/stage_b_one_automatic_continuation_001.md
8150 bytes
SHA-256 35e3a28b4d6488e210f065646e43a4f0d2c99ece5e5bbf17186ea359f22f6fb8
repository identity a920a796c01f0e448037a8e0390f10861b641df0

File actions:
none

Receipt delta:
0 Verified Saves / 0 Verified Reuses / 0 estimated value

Persisted Run 2 evidence SHA-256:
72e3ee9d41d825b777fafe68168e86d788e48c7e828ef982c5e09ea3d90b8929
```

Run 2 residue increased the established state rather than replaying Run 1:

```text
Cumulatively established:
STAGE-A-PASS
STAGE-B-PASS

New in Run 2:
STAGE-B-PASS

Still open:
STAGE-C-BOUNDARY

Residue SHA-256:
fd30db4c8b9675fa732cfb585760ce8da0bdfdd700d149b04d9f2a365135cbc7
```

Supervisor 2 independently consumed Run 2. Run 3 did not inherit Run 2's
authority automatically.

```text
GO / AI-OWNED

Consumed Run:
5ace2dfe-d7ca-46fe-aa43-12fffd2f0412

Judgment SHA-256:
ed6932cac6c1d7ce50cb16b86f20a7180d6cc38e91cf56bf3ee9c1a947016782

Next bounded action:
Establish STAGE-C-BOUNDARY from docs/companion_product_roadmap_v0_3.md.
```

## Automatically Constructed Task 3

Task 3 was absent before Run 2. It was constructed only from the newly
persisted Run 2 state and is not Task 2 with a changed label.

```text
Original Goal SHA-256:
4b94ec9d1ce971352ed0fac74729e4bfe9be3804fb2ad46244753e4a0b725169

Immediate source Run ID:
5ace2dfe-d7ca-46fe-aa43-12fffd2f0412

Immediate source evidence SHA-256:
72e3ee9d41d825b777fafe68168e86d788e48c7e828ef982c5e09ea3d90b8929

Immediate source judgment SHA-256:
ed6932cac6c1d7ce50cb16b86f20a7180d6cc38e91cf56bf3ee9c1a947016782

Selected requirement:
STAGE-C-BOUNDARY

Task 3 SHA-256:
36bcecf09c87ba8853c1ccf849fb28f32b84b700d4a85f44ef15fb44f1be0b6e
```

Task 3's source is Run 2, not Run 1. Its selected path, expected identity,
requirement, source Run, source evidence, source judgment, task body, and task
SHA all differ from Task 2 where the causal state differs.

## Run 3 and Terminal Residue

```text
Run ID:
b2120b10-ba90-4fbb-80b9-f1aeadbc4b1f

Terminal:
NORMAL_TERMINAL / completed normally

Read evidence:
docs/companion_product_roadmap_v0_3.md
10360 bytes
SHA-256 c3283a70e12d509419b0b314cf026fa59676564332913fa5c1c38abeacf73f3d
repository identity a920a796c01f0e448037a8e0390f10861b641df0

File actions:
none

Receipt delta:
0 Verified Saves / 0 Verified Reuses / 0 estimated value

Persisted Run 3 evidence SHA-256:
d5d0c07a8c58f66cb063d8fb9bae7438b2bb50bf81606f69a837f5a52a5e53fd
```

Terminal residue:

```text
Cumulatively established:
STAGE-A-PASS
STAGE-B-PASS
STAGE-C-BOUNDARY

New in Run 3:
STAGE-C-BOUNDARY

Remaining requirements:
none

Residue SHA-256:
9e538c14e2fa90a20802442cc2de1750b6a15c66fbe6acbc401e24fa4c8755f4
```

Supervisor 3 independently consumed Run 3 and closed the Goal:

```text
HOLD / STOP — the Goal is complete; another Run is unnecessary

Consumed Run:
b2120b10-ba90-4fbb-80b9-f1aeadbc4b1f

Judgment SHA-256:
a2ce9ae6a7bba60992d0f97380e617e27bf43a181771d3e940a942b90940c0e4

Canonical Stage C outcome:
COMPLETE
```

The final Supervisor gate is `HOLD / STOP` because another Worker Run is not
admissible after completion. The Stage C terminal outcome is `COMPLETE` because
all predeclared completion requirements are established. These two fields have
different roles and are intentionally not collapsed.

## Persisted Causal Record and Restart

```text
Chain ID:
74e7ae5174ac73e2f295e3a4e2866cb3

Terminal chain state:
TERMINAL / COMPLETE

Worker Runs dispatched:
3

Automatic continuations started / limit:
2 / 2

Total Run cap:
3

Run 4 dispatches:
0

Self-authenticating record SHA-256:
58b926ae5b75317466df53329cafa2cf700137b5a7b0638f03e6f79662d9cafa

Exact serialized record file SHA-256:
d6d5efe0e0130761afdf2c28ecc7c6aa1d1f44a48af72215ba98c8ee1f01f8df

Record permissions:
0600

Fresh-controller reconnect:
TERMINAL / COMPLETE / 3 Runs / 2 automatic continuations /
record SHA-256 58b926ae5b75317466df53329cafa2cf700137b5a7b0638f03e6f79662d9cafa

Reconnect-triggered Worker Runs:
0
```

The record contains the immutable Goal and authority envelope, three sanitized
Run results, Receipt deltas, three cumulative residues, three Supervisor
judgments, both causally constructed Tasks, fixed counters, the terminal
outcome, and its self-hash. Raw Worker messages are represented only by byte
count and SHA-256.

## Governance and Integrity Proofs

- Three-Run GO path: one Goal was submitted once; only Supervisor 1 and
  Supervisor 2 `GO / AI-OWNED` judgments permitted Runs 2 and 3.
- Early completion: focused proofs complete at Run 1 or Run 2 and leave the
  unused continuation budget undispatched.
- Per-Run supervision: each persisted Run has one consuming judgment; Run 3
  requires the persisted Supervisor 2 GO.
- Hard cap and no Run 4: dispatch is an explicit fixed `(1, 2, 3)` structure,
  continuation count is restricted to `0..2`, Run 3 always terminates, and an
  unchanged Goal cannot reset or renew its persisted cap.
- Non-GO preservation: abnormal evidence, execution failure, Human Seat,
  HOLD, CAP, BLOCK, and evidence-recovery cases terminate before another
  dispatch.
- Authority preservation: Tasks carry the unchanged Goal, single allowed path,
  Protected Objects, ownership, public exposure, and cost/cap boundaries.
- Causal integrity: deterministic reconstruction validates Task 2 from Run 1
  and Task 3 from Run 2, including evidence, residue, judgment, and Goal hashes.
- Tamper resistance: rehashed changes to Task 2, Task 3, source Run, or source
  evidence fail closed as `BLOCKED_CORRUPT`.
- Replay resistance: a validly rehashed stale `RUN_3_ACTIVE` record reconnects
  without dispatch and blocks a second chain; terminal reconnect is also
  dispatch-free.
- Restartability: COMPLETE, governed-stop, cap-exhausted, execution-failure,
  and corrupt states preserve an inspectable terminal or recovery view.
- Human Seat: the Stage A return contract is reused unchanged; a proved
  authority failure terminates as `HUMAN SEAT REQUIRED` with the preserved
  completed work and no later Run.

## Claim and Authority Boundary

- Stage C is a fixed maximum-three extension of the Stage B causal mechanism,
  not a parallel engine or arbitrary-N recursion.
- The proof establishes real local repository I/O and causal control behavior;
  it makes no claim that an external model saw or interpreted repository file
  content.
- The canonical current Gate changed from the active Stage C build `GO` to the
  completed Stage C `HOLD`. Its one-line CLI expectation and corresponding
  protected blob identity are co-updated as one valid Forward-only closure
  delta; test structure and production scan behavior are unchanged.
- The numeric cap cannot be increased, silently reset, or renewed for the
  unchanged Goal. A later cap change requires a separate Forward-only decision.
- Stage D leave-the-desk dogfood is not implemented or started.
- No Canon modification, release, publication, signing, notarization,
  deployment, or paid-tier behavior is added.

## Verification

```text
Focused Stage C compound loop:
PASS — 10 tests

Stage A / Stage B / controller / process / server-client regression:
PASS — 80 tests / 2 expected skips, plus 38 server-client tests

Canonical-state and handoff regression:
PASS — 132 tests after the one Chrome probe used normal GUI permissions

Full repository regression:
PASS — 1440 tests / 15 expected environment skips from a clean detached
worktree

Repository validation:
python -B -m decision_os check . — PASS

Patch hygiene:
git diff --check — PASS
```

## Completion Line

One fixed Goal entered once. Three meaningful, causally connected repository
reads established increasing state; both automatic Tasks were constructed from
the immediately preceding persisted Run and independent Supervisor judgment;
the third judgment closed the Goal; no user translated a Receipt; no Run 4
path or cap renewal exists; and a fresh controller reloaded the exact terminal
record without another dispatch.

```text
Stage C Completion Line:
PASS

Remaining Missing Closure:
Stage D — Leave-the-Desk Dogfood (NOT AUTHORIZED)

Stage D Authorized:
NO

Release Authority:
NONE

Publication Authority:
NONE
```
