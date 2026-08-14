# F-01 Slice 4A — exact privileged-snapshot evidence repair

**As-of:** 2026-08-14 JST

**Base:** `3102145a9705b015565e63112fa1fbcc282fb872`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT P1 REVIEW`

**Authority:** unprivileged forward-only evidence/fixture repair, fixture
testing, production-artifact rebuild, and read-only qualification

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

Every identity-bearing and held-surface invariant matched. Raw
observer-context differences included both the user Password presentation and
the `accountPolicyData` bytes:

```text
EUID 501: dsAttrTypeStandard:Password = ["********"]
EUID 0:   dsAttrTypeStandard:Password absent

EUID 501 accountPolicyData creationTime = 1786621421.5785599
EUID 0   accountPolicyData creationTime = 1786621425.7855999
```

Password was the only raw difference that violated the then-current validator
and caused the rollback HOLD. The accepted validator had incorrectly treated
that presentation marker as a stable principal-identity invariant.
`accountPolicyData` creationTime is not an identity-bearing invariant under the
existing safe-policy contract. This P1 evidence repair changes no validator
logic and authorizes no widening of that account-policy contract.

This remains a forward-only correction; it does not rewrite, reinterpret, or
remove the historical failed-execution evidence.

## Minimal repaired contract

The preceding P repair changed only the user Password-marker rule. This P1
repair changes no validation contract. The user Password attribute remains
recorded in the normalized snapshot but is not identity-bearing. Exactly two
observations remain accepted:

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
- the exact privileged `accountPolicyData` base64 is:

  ```text
  PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y3JlYXRpb25UaW1lPC9rZXk+Cgk8cmVhbD4xNzg2NjIxNDI1Ljc4NTU5OTk8L3JlYWw+CjwvZGljdD4KPC9wbGlzdD4K
  ```

- those base64 bytes decode to the captured root plist with exact textual
  value `creationTime=1786621425.7855999` (246 bytes; SHA-256
  `4dee49878c19674db70c41879de42f96817d781b15c28eefcdb2ec6c19a2511a`);
  and
- every remaining user/group, binding, held-principal, node, and path field is
  inherited from the exact accepted fixture.

`exact_privileged_snapshot_account_policy_bytes_embedded` proves that the
complete fixture contains that exact base64 payload.
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

The native modeled/adversarial suite is `41/41`, including explicit PASS cases
for both observer shapes and zero-delete HOLD cases for wrong, multi-value,
credential-like, and malformed user Password observations.

## Rebuilt production mutation identity

P1 source SHA-256 change:

```text
a050e3c45b0df6bc8bdbb38d4c4b528bd6b77624c938d25e7ad04be1b7b9907e
->
28f6728199e09a2e459eb1d0237e8d16ddb688e57b70c08050a45bcfabde32bf
```

P1 production binary SHA-256 result:

```text
0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802
->
0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802
```

The P1 edit is entirely inside `F01_TESTING`. Two clean optimized builds in
separate directories, using the exact production output basename, were
byte-identical to one another and to the already-staged production mutator.
Compiler and binary evidence remains:

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

The unchanged staged production binary ran once as EUID 501 outside the app
sandbox after the P1 fixture edit. It returned process exit 3:

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

## Unchanged one-shot identities

The P1 repair did not regenerate or modify the one-shot chain. The staged
mutator remains:

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

The wrapper, loader, command, staged path, staged bytes, and staged filesystem
identity are unchanged. The one-shot architecture remains one possible future
administrator authorization, no retry or fallback, hash/inode/metadata
validation, exact opened-byte copying into a root-private directory, one child
launch, exact output preservation, and no post-rollback provisioning or ACL
path.

The command remains the exact sole line in:

```text
scripts/macos_f01_opendirectory_one_shot_command.txt
```

The command was not executed. No authorization path was invoked.

## Verification

- native modeled/adversarial cases: `41/41` passed;
- production artifact/surface tests under Homebrew Python: `7/7` passed;
- production artifact/surface tests under macOS Python 3.9: `7/7` passed;
- focused wrapper/loader/stage tests under Homebrew Python: `21/21` passed;
- focused wrapper/loader/stage tests under macOS Python 3.9: `21/21` passed;
- two exact-basename optimized builds: byte-identical to each other and the
  unchanged staged mutator;
- one unprivileged live read-only run: exact current-state match, zero mutation;
- production signature, architecture, dependency, symbol, and forbidden
  surface checks remain covered by the byte-identical artifact and focused
  tests; and
- privileged prompt count: `0`.

## Completion state

**V12 State:** `PASS` for bounded 13-153P1 exact privileged-snapshot evidence
repair only. This is not rollback execution or Slice 4A completion.

**V13 Next Loop Gate:**
`HOLD — INDEPENDENT P1 REVIEW`

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
