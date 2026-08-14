# F-01 Slice 4A — observer-dependent Password-marker contract repair

**As-of:** 2026-08-14 JST

**Base:** `7c5c0c849716803e7aa5d9d09fa834291cf71fbc`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT OBSERVER-CONTEXT REPAIR REVIEW`

**Authority:** unprivileged forward-only contract repair, fixture testing,
native artifact rebuild, fresh staging, and same-user read-only host
qualification

No `osascript`, `sudo`, administrator authorization, root execution,
OpenDirectory mutation, principal deletion/provisioning, ACL change, or
sole-writer work occurred. Privileged prompt count is `0`.

## Causal correction

The prior one-shot rollback was not blocked by host identity drift. Its sole
privileged invocation reached the exact reviewed mutation artifact and stopped
before mutation with:

```text
status = HOLD_CURRENT_HOST_STATE_MISMATCH
issue = User non-credential password marker mismatch.
mutation_attempted = false
completed_mutations = []
```

Every identity-bearing and held-surface invariant matched. The only difference
was observer-dependent OpenDirectory presentation:

```text
EUID 501: dsAttrTypeStandard:Password = ["********"]
EUID 0:   dsAttrTypeStandard:Password absent
```

The accepted validator had incorrectly treated that presentation marker as a
stable principal-identity invariant. This commit is a forward-only correction;
it does not rewrite, reinterpret, or remove the historical failed-execution
evidence.

## Minimal repaired contract

Only the user Password-marker rule changed. The user Password attribute is now
recorded in the normalized snapshot but is not identity-bearing. Exactly two
observations are accepted:

- attribute absent; or
- the exact singleton string array `["********"]`.

Every other value, multiple values, a credential-like/unreviewed string, or a
malformed representation fails closed before any modeled delete. The group
Password contract remains the exact singleton `["*"]`.

All other CURRENT_HOST_STATE invariants remain exact and unchanged: record and
framework names/types, user UID and primary GID 510, group GID 510, both GUIDs,
both RealNames, `NFSHomeDirectory=/var/empty`, required absence of `UserShell`,
`IsHidden`, `AuthenticationAuthority`, `GroupMembership`, and `GroupMembers`,
unique UID/GID bindings, Guardian/Broker absence, exact `/Local/Default` node,
the safe account-policy surface, and DecisionOS host-state-tree absence.

## Exact privileged-shaped fixture

The native self-test contains a fixture built from the exact privileged
snapshot returned by the failed one-shot invocation:

- the user Password attribute is absent;
- both record-daemon versions are `9670000`;
- the exact observed `accountPolicyData` base64 is retained; and
- every remaining user/group, binding, held-principal, node, and path field is
  inherited from the exact accepted fixture.

`exact_privileged_snapshot_current_state_validates` passes with zero issues.
The ordering case uses only `F01FixtureBackend`: it observes, rebinds both
records, and reaches the fixture's `deleteBoundUser` seam only after both
validations pass. That seam is configured to return a fixture NSError, so the
case ends at `HOLD_USER_DELETE_FAILED`, `completed_mutations=[]`, with no live
OpenDirectory mutation. Its exact event order is:

```text
observe
rebind_both
delete_user
```

The native modeled/adversarial suite is `40/40`, including explicit PASS cases
for both observer shapes and zero-delete HOLD cases for wrong, multi-value,
credential-like, and malformed user Password observations.

## Rebuilt mutation identity

Old → new source SHA-256:

```text
c22849cae2f8610a3f75b349943123283ab549d22d7df6305497872cdf482954
->
a050e3c45b0df6bc8bdbb38d4c4b528bd6b77624c938d25e7ad04be1b7b9907e
```

Old → new production binary SHA-256:

```text
2418c8ea235a3eebe0890e38ed95932ff6094bf4aaa778e78964bfb9eaa6b4fa
->
0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802
```

Two clean optimized builds in separate directories were byte-identical.
Compiler and binary evidence:

- Apple clang `21.0.0 (clang-2100.1.1.101)`;
- target `arm64-apple-darwin25.6.0`;
- Mach-O 64-bit arm64, 94,704 bytes;
- build copy: UID 501, GID 0, mode `0755`, link count 1;
- valid ad-hoc linker signature, no TeamIdentifier;
- CDHash `b7ca7668a64fdbcc65b8b5feba9c7916ab57174a`;
- direct dependencies remain Foundation, OpenDirectory, CoreFoundation,
  `libobjc`, and `libSystem`; and
- source/binary inspection retains `deleteRecordAndReturnError:` and finds no
  `osascript`, `sudo`, `dscl`, `sysadminctl`, `dseditgroup`, `pwpolicy`,
  Authorization Services, shell execution, or network transport.

Clang static analysis and `codesign --verify --strict` passed.

## Unprivileged live qualification and unchanged host

The exact new production binary ran twice as EUID 501 outside the app sandbox.
Both results were byte-identical canonical JSON and returned process exit 3:

```text
status = HOLD_PRIVILEGE_REQUIRED
issues = []
effective_uid = 501
mutation_attempted = false
completed_mutations = []
privileged_execution_authorized = false
privileged_prompt_count = 0
provisioning_performed = false
protected_repository_acl_changed = false
```

The live snapshot retains the accepted user/group names, GUIDs, UID/GID 510,
RealNames, `NFSHomeDirectory=/var/empty`, required authority-bearing attribute
absences, unique numeric bindings, Guardian/Broker absence, and all three
DecisionOS host-state paths absent. The observed EUID-501 user Password marker
remains the exact singleton `["********"]`; group Password remains `["*"]`.
Host state is unchanged.

## Regenerated one-shot identities

Fresh staged mutator:

```text
/private/tmp/decision-os-f01-slice4a-one-shot-0450739ae668/macos_f01_opendirectory_mutation
```

Staged metadata after sealing:

| Object | Device | Inode | UID | GID | Mode | Links | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| directory | `16777234` | `123725406` | `501` | `0` | `0500` | `4` observed | `128` observed |
| wrapper | `16777234` | `123725636` | `501` | `0` | `0444` | `1` | `21377` |
| mutator | `16777234` | `123725407` | `501` | `0` | `0555` | `1` | `94704` |

Dependent hashes:

```text
wrapper: faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9
loader:  5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1
command: 75d433390e58e08bbd4ba97c80addbc85814416794f76b51fb57d4d87add4575
```

Only their fixed stage/artifact identities changed. The one-shot architecture
is unchanged: one possible future administrator authorization, no retry or
fallback, hash/inode/metadata validation, exact opened-byte copying into a
root-private directory, one child launch, exact output preservation, and no
post-rollback provisioning or ACL path.

The command remains the exact sole line in:

```text
scripts/macos_f01_opendirectory_one_shot_command.txt
```

It passed `zsh -n` and compile-only `osacompile` validation without invocation.
The command was not executed. Direct unprivileged wrapper and loader runs each
returned their expected privilege-required HOLD with zero authorization or
mutation attempts.

## Verification

- native modeled/adversarial cases: `40/40` passed;
- production artifact/surface tests: `7/7` passed;
- focused wrapper/loader/stage tests under Homebrew Python: `21/21` passed;
- focused wrapper/loader/stage tests under macOS Python 3.9: `21/21` passed;
- combined recovery/principal-separation and Broker Slice 1/2/3 regression:
  `271/271` passed;
- two optimized builds: byte-identical;
- two unprivileged live runs: byte-identical and exact current-state match;
- static analysis, signature, architecture, dependency, symbol, and forbidden
  surface checks passed; and
- privileged prompt count: `0`.

## Completion state

**V12 State:** `PASS` for bounded 13-153P observer-context repair only. This is
not rollback execution or Slice 4A completion.

**V13 Next Loop Gate:**
`HOLD — INDEPENDENT OBSERVER-CONTEXT REPAIR REVIEW`

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
