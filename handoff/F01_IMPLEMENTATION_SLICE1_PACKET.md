# V13 F-01 — Implementation Slice 1

**As-of:** 2026-08-13 JST  
**Decision Owner:** Shin  
**Base:** `9566cc4fa442633a0885fa8d2f1180979b2078ee`  
**Branch:** `codex/f01-broker-control-domain-slice1`  
**Authority:** bounded repository-only implementation. No host deployment, migration, merge, or release authority.

## Human-Seat disposition

Proceed. Do not return routine implementation decisions or cleanup to Shin.

Deployment/Security Package v2 is accepted as the pre-implementation boundary. This Slice authorizes repository-only code and tests; it does **not** authorize macOS users/groups, LaunchDaemon installation, root-owned filesystem changes, ACL changes on Shin's machine, live repository migration, privileged activation, merge to `main`, or release.

## Objective

Implement and falsify the repository-level Broker control-domain substrate required by F-01 before any privileged deployment.

Canonical F-01 behavior to preserve: persisted `RUN_n_ACTIVE` / intermediate compound states remain fail-closed; legacy unfenced records are not retroactively recoverable.

Canonical durability defect to repair in this Slice: `StageBContinuationStore.save()` currently uses temp file + `os.replace()` without file or parent-directory `fsync`.

## Fixed invariants

- Process lifetime is not the authority boundary.
- Authority binds to an authority-domain identity, not an integer generation alone.
- An abandoned domain may remain alive only if it cannot mutate a successor protected identity.
- `UNCERTAIN` is never force-unlocked.
- An uncertain control domain is abandoned, not repaired in place.
- Old recovered Runs never reconnect and receive no continuation refund.
- Repository-resident evidence can constrain/contradict/DELAY/BLOCK but can never create or restore positive mutation authority.
- Initial mutation contract remains one path, `CREATE`/`REPLACE`, full target bytes, expected-prior-hash/CAS; no delete, rename, multi-path, `.git`, symlink/hardlink, directory mutation, arbitrary shell, or model-generated command execution.

## Slice 1 required substrate

Provide, without root privileges or real OS account changes:

1. authority-domain identity;
2. protected-repository identity binding;
3. logical write-principal identity binding;
4. crash-safe control-record persistence;
5. expected-prior-hash / CAS;
6. `ACTIVE / ABANDONED / UNCERTAIN` control-domain states;
7. activation-tuple mismatch fail-closed behavior;
8. reconciliation outcomes `APPLIED / NOT_APPLIED / UNCERTAIN`;
9. no force-unlock transition;
10. tests proving abandoned domains cannot become current authority again.

Logical write-principal identity is data-model-only in Slice 1. Do not create real users/groups.

## Preferred code shape

Keep blast radius small:

- one focused module under `decision_os/companion/` for Broker/control-domain state;
- focused tests under `tests/`;
- smallest durability repair to `decision_os/companion/continuation.py` needed for crash consistency.

Do not broadly rewrite `CompanionController` in Slice 1. Do not implement LaunchDaemon/XPC/ACL/macOS privilege code.

## Durable persistence rule

For every security-bearing control record and `StageBContinuationStore.save()`:

1. write canonical bytes to a fresh temp file;
2. flush userspace buffers;
3. `fsync` the temp file descriptor;
4. atomically publish with replace;
5. `fsync` the parent directory;
6. preserve strict size/schema/hash validation;
7. remove temp files on handled failure;
8. re-read and validate the published record;
9. never report `APPLIED` from an unvalidated write.

If neither exact pre-image nor exact post-image can be proved after a crash prefix, reconcile to `UNCERTAIN` and fail closed.

## Minimum control-record semantics

Bind at least:

- schema/version;
- `authority_domain_id`;
- `repository_id`;
- `protected_repository_identity`;
- `write_principal_identity`;
- authority state (`ACTIVE`, `ABANDONED`, `UNCERTAIN`);
- serializer/journal position or equivalent;
- predecessor/control-record hash where applicable;
- `record_sha256`.

Protected-record generation values are witnesses only. A bare integer generation must never be the sole authority identity.

## CAS / reconciliation

A decision must be bound to authority-domain identity, protected-repository identity, expected prior hash, and expected post hash/full target bytes.

Required outcomes:

- exact post-image present -> `APPLIED`;
- exact prior still present -> `NOT_APPLIED`;
- neither exact pre nor post can be proved -> `UNCERTAIN`;
- authority-domain mismatch -> fail closed before apply;
- repository-identity mismatch -> fail closed before apply;
- `ABANDONED` or `UNCERTAIN` domain -> cannot apply successor mutation.

No timeout-, PID-, liveness-, or narrative-based recovery inference.

## Required tests

At minimum:

- normal durable save validates;
- file fsync precedes replace;
- directory fsync follows replace;
- handled failure does not create authoritative partial state;
- torn/invalid state never becomes PASS/APPLIED;
- fresh domain tuple accepted;
- abandoned/stale domain rejected;
- numeric generation reuse cannot restore an abandoned domain;
- repository identity mismatch rejected;
- write-principal identity mismatch rejected;
- exact prior -> `NOT_APPLIED`;
- exact post -> `APPLIED`;
- neither -> `UNCERTAIN`;
- no force-unlock path;
- no `ABANDONED -> ACTIVE` transition;
- legacy pre-F-01 ACTIVE/intermediate records remain fail-closed;
- relevant full suite passes and F-04 protections do not regress.

## Allowed / forbidden

Allowed: focused Python, tests, directly required fixtures, minimal persistence durability changes.

Forbidden: host/system mutation, root commands, real users/groups, LaunchDaemon, actual ACL changes, live rematerialization, production activation, README/public expansion, unrelated refactors, F-02 changes, F-04 redesign.

If a prohibited action would be required, stop that action and continue only with repository-level simulation/tests.

## Completion report

Before claiming Slice 1 complete, report:

- exact base SHA;
- final branch SHA;
- changed files;
- tests and counts/results;
- whether any fixed invariant or blast-radius boundary was exceeded.

Do not merge to `main`.
Do not treat green tests as F-01 closure.

At Slice 1 completion:

`F-01 remains OPEN`

Next gate:

`HOLD — INDEPENDENT IMPLEMENTATION REVIEW`

Later implementation-gate items remain out of scope: trusted subprocess/git environment, Controller/Broker peer authentication, fd-bound proposal acquisition and production CAS apply, explicit abandoned-Run terminal/accounting representation, real OS-principal separation, TCB installer/promoter, real ACLs, fresh rematerialization/cutover, LaunchDaemon, production break-glass, and live F-01 qualification.
