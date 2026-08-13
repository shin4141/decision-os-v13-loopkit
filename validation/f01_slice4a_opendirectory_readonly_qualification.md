# F-01 Slice 4A — OpenDirectory read-only qualification

**As-of:** 2026-08-14 JST

**Base:** `575cfa32ab2d6c137ebf6797cc5f52fb30e4f5d1`

**Gate:** `HOLD — INDEPENDENT OPENDIRECTORY HELPER REVIEW`

**Authority:** unprivileged read-only construction and qualification only

No administrator authorization, Directory Service mutation, principal
provisioning or deletion, password-policy mutation, ACL change, protected
repository permission change, or main merge occurred in this run.

## Helper boundary

The standalone helper is Objective-C with ARC and links directly to Apple's
Foundation and OpenDirectory frameworks. It has no repository import or runtime
dependency. It opens `/Local/Default` by fixed name, queries fixed record types
and names, reads the complete exposed attribute surface, and separately queries
UID 510, GID 510, held-principal names, and the three held host-state paths.

`ODQuery` is capped at two results. Zero, two, or more logical matches therefore
fail the exact-one check. Numeric and held-principal result names are sorted.
Attribute keys are emitted with sorted JSON keys and multi-valued attributes are
sorted by their canonical JSON representation. OpenDirectory failures retain
their native error domain, code, localized details, and canonicalized
`userInfo` in a `HOLD_FRAMEWORK_READ_ERROR` report.

The accepted identity contract is not widened by framework metadata. The
helper records and validates framework record name/type and node location. It
also records the local daemon version, inert password markers, and the raw
base64 `accountPolicyData`; only a numeric `creationTime` policy key is accepted.
Any other user or group attribute or account-policy key fails closed.

## Mutation is structurally unavailable

- `PRIVILEGED_EXECUTION_AUTHORIZED` is a translation-unit constant set to
  `NO` and is emitted as `false` in every report.
- Defining `F01_MUTATION_ENABLED` is a preprocessing hard error.
- The ordinary binary accepts no arguments. Any argument exits 64 with
  `HOLD_RUNTIME_INPUT_REJECTED`.
- It reads no environment variable, stdin, config file, repository file,
  network input, or dynamic plugin and invokes no shell command.
- Its disabled deletion request discards the supplied operation without
  invoking it. The native fixture proves zero mutation calls.
- The optimized ordinary binary contains no record-delete selector or
  authorization/shell mutation symbol or string.
- EUID 0 fails qualification; the live runs were EUID 501.

Any future delete-capable implementation requires a distinct source and binary
identity plus separate review and authorization. This artifact has no hidden
runtime enablement switch.

## Build and artifact identity

Repository source:

`scripts/macos_f01_opendirectory_readonly.m`

Source SHA-256:

```text
0b12fdebf944b01645733c9b7aaf1cbfa97397e82b6ebfbe80a6d823120adaa6
```

Compiler:

```text
Apple clang version 21.0.0 (clang-2100.1.1.101)
Target: arm64-apple-darwin25.6.0
Thread model: posix
InstalledDir: /Library/Developer/CommandLineTools/usr/bin
```

Unprivileged reproducible build command, with a caller-selected private module
cache and output path:

```sh
/usr/bin/clang -fobjc-arc -Wall -Wextra -Werror -O2 -fmodules-cache-path=<module-cache> -framework Foundation -framework OpenDirectory scripts/macos_f01_opendirectory_readonly.m -o <output>
```

Two clean invocations produced the same binary SHA-256:

```text
9423cf2db3145be636db9108a49eeed3e8f271cdd3b3723b8f5208c799c6e93c
```

Read-only qualification artifact:

```text
/private/tmp/decision-os-f01-slice4a-od-readonly-0b12fdebf944/macos_f01_opendirectory_readonly
```

Artifact metadata:

```text
directory: mode 0500, UID 501, GID 0
binary: regular file, mode 0555, UID 501, GID 0, 74784 bytes
format: Mach-O 64-bit executable arm64
signature: valid ad-hoc linker signature; no TeamIdentifier
CDHash: 84d38dc06826fe480f10e36c3b712316acd2fe33
```

Dynamic dependencies are only Foundation, OpenDirectory, `libobjc`,
`libSystem`, and CoreFoundation. `codesign --verify --strict` passed. Clang's
static analyzer completed with no diagnostic.

## Exact real-host read-only result

The hash-bound staged artifact ran twice as EUID 501. Both invocations exited
0 and produced the same 2,523-byte output, byte for byte:

```json
{"issues":[],"mutation_attempted":false,"privileged_execution_authorized":false,"schema":"decision-os-f01-slice4a-opendirectory-readonly-v0.1","snapshot":{"execution":{"effective_uid":501,"mutation_attempted":false,"privileged_execution_authorized":false},"held_principals":{"broker_group":[],"broker_user":[],"guardian_group":[],"guardian_user":[]},"host_state_paths_present":{"/Library/Application Support/DecisionOS":false,"/Library/Application Support/DecisionOS/F01PrincipalSeparation":false,"/Library/Application Support/DecisionOS/F01PrincipalSeparation/v1":false},"node":{"requested":"/Local/Default","resolved":"/Local/Default"},"numeric_bindings":{"gid_510_record_names":["_decisionos_codex"],"uid_510_record_names":["_decisionos_codex"]},"records":{"group":{"attributes":{"dsAttrTypeNative:record_daemon_version":["9670000"],"dsAttrTypeStandard:AppleMetaNodeLocation":["/Local/Default"],"dsAttrTypeStandard:GeneratedUID":["1F200679-B0A2-4D13-A86F-6492F9C4B66F"],"dsAttrTypeStandard:Password":["*"],"dsAttrTypeStandard:PrimaryGroupID":["510"],"dsAttrTypeStandard:RealName":["Decision OS Codex execution principal"],"dsAttrTypeStandard:RecordName":["_decisionos_codex"],"dsAttrTypeStandard:RecordType":["dsRecTypeStandard:Groups"]},"framework_record_name":"_decisionos_codex","framework_record_type":"dsRecTypeStandard:Groups","match_count":1,"normalization_errors":[]},"user":{"attributes":{"dsAttrTypeNative:accountPolicyData":[{"data_base64":"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y3JlYXRpb25UaW1lPC9rZXk+Cgk8cmVhbD4xNzg2NjIxNDIxLjU3ODU1OTk8L3JlYWw+CjwvZGljdD4KPC9wbGlzdD4K"}],"dsAttrTypeNative:record_daemon_version":["9670000"],"dsAttrTypeStandard:AppleMetaNodeLocation":["/Local/Default"],"dsAttrTypeStandard:GeneratedUID":["D6515614-B56A-4943-AA41-18D17DE9F899"],"dsAttrTypeStandard:NFSHomeDirectory":["/var/empty"],"dsAttrTypeStandard:Password":["********"],"dsAttrTypeStandard:PrimaryGroupID":["510"],"dsAttrTypeStandard:RealName":["Decision OS Codex execution principal"],"dsAttrTypeStandard:RecordName":["_decisionos_codex"],"dsAttrTypeStandard:RecordType":["dsRecTypeStandard:Users"],"dsAttrTypeStandard:UniqueID":["510"]},"framework_record_name":"_decisionos_codex","framework_record_type":"dsRecTypeStandard:Users","match_count":1,"normalization_errors":[]}}},"status":"PASS_CURRENT_HOST_STATE_MATCH"}
```

This proves the exact accepted user and group identity fields, required
attribute absences, unique UID/GID bindings, Guardian/Broker absence, held
host-state-tree absence, explicit `/Local/Default` resolution, and zero
mutation attempt. The same observation before and after final hardening was
identical, so the current principal and held host-state surfaces remained
unchanged.

## Verification

- native adversarial and canonicalization fixtures: `32/32` passed;
- Python compile/surface tests: `5/5` passed;
- focused helper, rollback, principal-separation, and Broker Slice 1/2/3
  regression: `243/243` passed;
- full repository discovery: `1,754` tests were exercised. In the app sandbox,
  `43` loopback-bind cases errored and `3` Chrome cases failed because the
  sandbox denied the required local process/socket operations. The exact
  affected classes were rerun unprivileged outside that sandbox: `59` tests
  ran, `58` passed, and `1` pre-existing proof-storage case skipped. Combined
  evidence accounts for the full suite as `1,740` passes and `14` skips with no
  unresolved test failure;
- two independent optimized builds were byte-identical;
- two final real-host observations were byte-identical;
- code-signature verification, dependency inspection, undefined-symbol scan,
  string scan, compile-time mutation-gate rejection, and static analysis
  passed; and
- privileged prompt count: `0`.

No `osascript`, `sudo`, `dscl`, `sysadminctl`, `dseditgroup`, or `pwpolicy`
command was invoked. No OpenDirectory write API was called.

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
