# F-01 Slice 4A — OpenDirectory mutation artifact construction

**As-of:** 2026-08-14 JST

**Base:** `11e12d23c767b2c5a324c3e9a969256355e26a5a`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT MUTATION ARTIFACT REVIEW`

**Authority:** construction, fixture-only mutation modeling, and unprivileged
real-host read qualification

No administrator authorization or real mutation occurred. The production
binary was run only as EUID 501.

## Separate artifact identity

The mutation-capable source is a separate Objective-C + ARC translation unit:

`scripts/macos_f01_opendirectory_mutation.m`

It does not modify, include, or runtime-import the accepted read-only helper.
The accepted read-only source remains byte-identical at SHA-256:

```text
0b12fdebf944b01645733c9b7aaf1cbfa97397e82b6ebfbe80a6d823120adaa6
```

The mutation source SHA-256 is:

```text
c22849cae2f8610a3f75b349943123283ab549d22d7df6305497872cdf482954
```

The fixed production binary SHA-256 is:

```text
2418c8ea235a3eebe0890e38ed95932ff6094bf4aaa778e78964bfb9eaa6b4fa
```

The staged read-only execution artifact is:

```text
/private/tmp/decision-os-f01-slice4a-od-mutation-c22849cae2f8/macos_f01_opendirectory_mutation
```

## Fixed authority and identity contract

The binary accepts no arguments and reads no authority, node, operation,
record name, ID, GUID, path, or capability from environment variables, stdin,
configuration, repository files, network input, or plugins. Any argument exits
64 with `HOLD_RUNTIME_INPUT_REJECTED` before the OpenDirectory backend is
created.

All of these values are compiled into the source:

- node `/Local/Default`;
- principal `_decisionos_codex`;
- user UID and primary GID `510`;
- user GUID `D6515614-B56A-4943-AA41-18D17DE9F899`;
- group GID `510`;
- group GUID `1F200679-B0A2-4D13-A86F-6492F9C4B66F`;
- RealName `Decision OS Codex execution principal`;
- NFS home `/var/empty`;
- required absence of `UserShell`, `IsHidden`,
  `AuthenticationAuthority`, `GroupMembership`, and `GroupMembers`;
- Guardian and Broker user/group absence; and
- the three absent DecisionOS host-state paths.

The helper also requires the reviewed framework record type, node location,
and inert password-marker observations. It records local daemon metadata and
raw base64 `accountPolicyData`; only a numeric `creationTime` policy key is
allowed. Any other attribute or policy key fails closed without widening the
accepted identity contract.

The only runtime authority boundary is `geteuid() == 0`. There is no switch or
API that changes EUID. EUID other than zero performs one full exact-state
observation and returns `HOLD_PRIVILEGE_REQUIRED` before either deletion method
is called. The embedded privileged-interaction budget is one and authorization
retry is always false; the binary itself contains no authorization mechanism.

## Production transaction and failure semantics

The production backend opens `/Local/Default` directly with OpenDirectory and
uses `-[ODRecord deleteRecordAndReturnError:]` for the two intended deletes.
It invokes no shell or command-line account-management tool.

The modeled successful event order is exactly:

```text
observe
rebind_both
delete_user
observe
observe
delete_group
observe
```

`rebind_both` first repeats the complete current-state surface verification,
then queries the fixed user and group records again as its final framework
reads. The exact returned records are retained as the only records eligible
for the immediate user-delete call. After user deletion, the next observation
proves user absence, UID 510 freedom, surviving-group identity, GID binding,
held-principal absence, and held-path absence. The following fresh observation
rebinds the surviving group and re-proves held surfaces before the group-delete
call. The final observation proves both records absent and UID/GID 510 free.

There is no mutation retry:

- user-delete failure reports native `NSError`, leaves
  `completed_mutations=[]`, and never calls group delete;
- any failure after successful user deletion reports
  `completed_mutations=["user_deleted"]` and stops before group delete unless
  the fresh exact group gate passes;
- group-delete failure reports native `NSError`, retains only
  `completed_mutations=["user_deleted"]`, and does not retry; and
- success requires exactly
  `completed_mutations=["user_deleted","group_deleted"]` plus final absence
  and numeric-ID-release proof.

## Build and binary surface

Compiler:

```text
Apple clang version 21.0.0 (clang-2100.1.1.101)
Target: arm64-apple-darwin25.6.0
Thread model: posix
InstalledDir: /Library/Developer/CommandLineTools/usr/bin
```

Reproducible production command, with caller-selected private module cache and
output path:

```sh
/usr/bin/clang -fobjc-arc -Wall -Wextra -Werror -O2 -fmodules-cache-path=<module-cache> -framework Foundation -framework OpenDirectory scripts/macos_f01_opendirectory_mutation.m -o <output>/macos_f01_opendirectory_mutation
```

Two clean same-name builds in separate directories produced the same binary
SHA-256. The staged artifact metadata is:

```text
directory: mode 0500, UID 501, GID 0
binary: regular file, mode 0555, UID 501, GID 0, 94704 bytes
format: Mach-O 64-bit executable arm64
signature: valid ad-hoc linker signature; no TeamIdentifier
CDHash: a50484cbbd7f0e8b3fc4005e6e76c89809945452
```

Direct dependencies are only Foundation, OpenDirectory, `libobjc`,
`libSystem`, and CoreFoundation. The optimized production binary contains the
`deleteRecordAndReturnError:` selector and OpenDirectory record/query symbols.
Source and binary inspection found no `osascript`, `sudo`, `dscl`,
`sysadminctl`, `dseditgroup`, `pwpolicy`, Authorization Services, shell
execution, network transport, or request-controlled configuration path.
`codesign --verify --strict` and Clang static analysis passed.

## Exact unprivileged host result

The exact SHA-bound production binary was run twice after a separate read-only
check proved the execution identity was UID 501. Both invocations exited 3 and
produced the same 2,687-byte canonical output byte for byte:

```json
{"authorization_retry_allowed":false,"completed_mutations":[],"effective_uid":501,"gate":"HOLD","issues":[],"mutation_attempted":false,"phase":"unprivileged_read_qualification","privileged_execution_authorized":false,"privileged_interaction_budget":1,"privileged_prompt_count":0,"protected_repository_acl_changed":false,"provisioning_performed":false,"schema":"decision-os-f01-slice4a-opendirectory-mutation-v0.1","snapshot":{"held_principals":{"broker_group":[],"broker_user":[],"guardian_group":[],"guardian_user":[]},"host_state_paths_present":{"/Library/Application Support/DecisionOS":false,"/Library/Application Support/DecisionOS/F01PrincipalSeparation":false,"/Library/Application Support/DecisionOS/F01PrincipalSeparation/v1":false},"node":{"requested":"/Local/Default","resolved":"/Local/Default"},"numeric_bindings":{"gid_510_record_names":["_decisionos_codex"],"uid_510_record_names":["_decisionos_codex"]},"records":{"group":{"attributes":{"dsAttrTypeNative:record_daemon_version":["9670000"],"dsAttrTypeStandard:AppleMetaNodeLocation":["/Local/Default"],"dsAttrTypeStandard:GeneratedUID":["1F200679-B0A2-4D13-A86F-6492F9C4B66F"],"dsAttrTypeStandard:Password":["*"],"dsAttrTypeStandard:PrimaryGroupID":["510"],"dsAttrTypeStandard:RealName":["Decision OS Codex execution principal"],"dsAttrTypeStandard:RecordName":["_decisionos_codex"],"dsAttrTypeStandard:RecordType":["dsRecTypeStandard:Groups"]},"framework_record_name":"_decisionos_codex","framework_record_type":"dsRecTypeStandard:Groups","match_count":1,"normalization_errors":[]},"user":{"attributes":{"dsAttrTypeNative:accountPolicyData":[{"data_base64":"PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBsZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAiPgo8ZGljdD4KCTxrZXk+Y3JlYXRpb25UaW1lPC9rZXk+Cgk8cmVhbD4xNzg2NjIxNDIxLjU3ODU1OTk8L3JlYWw+CjwvZGljdD4KPC9wbGlzdD4K"}],"dsAttrTypeNative:record_daemon_version":["9670000"],"dsAttrTypeStandard:AppleMetaNodeLocation":["/Local/Default"],"dsAttrTypeStandard:GeneratedUID":["D6515614-B56A-4943-AA41-18D17DE9F899"],"dsAttrTypeStandard:NFSHomeDirectory":["/var/empty"],"dsAttrTypeStandard:Password":["********"],"dsAttrTypeStandard:PrimaryGroupID":["510"],"dsAttrTypeStandard:RealName":["Decision OS Codex execution principal"],"dsAttrTypeStandard:RecordName":["_decisionos_codex"],"dsAttrTypeStandard:RecordType":["dsRecTypeStandard:Users"],"dsAttrTypeStandard:UniqueID":["510"]},"framework_record_name":"_decisionos_codex","framework_record_type":"dsRecTypeStandard:Users","match_count":1,"normalization_errors":[]}}},"status":"HOLD_PRIVILEGE_REQUIRED"}
```

This is an exact match to the accepted current state. It proves the EUID gate,
zero mutation attempts, an empty completion list, Guardian/Broker absence,
held-path absence, and unchanged user/group and UID/GID bindings.

## Verification

- native modeled transaction and adversarial cases: `31/31` passed;
- repository production-build/surface tests: `6/6` passed;
- combined mutation/read-only/rollback/principal-separation and Broker Slice
  1/2/3 regression: `249/249` passed;
- independent optimized production builds: byte-identical;
- final unprivileged real-host runs: byte-identical;
- static analysis, code-signature verification, architecture/dependency review,
  undefined-symbol review, and source/binary forbidden-surface review passed;
- privileged prompt count: `0`; and
- real OpenDirectory mutation calls: `0`.

No `osascript`, `sudo`, `dscl`, `sysadminctl`, `dseditgroup`, or `pwpolicy`
command was invoked. No principal was deleted or provisioned. No ACL or
protected-repository permission was changed. The current host-state observation
before and after construction is unchanged.

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
