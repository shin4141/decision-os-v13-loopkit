# F-01 Slice 4A — OpenDirectory one-shot wrapper preparation

**As-of:** 2026-08-14 JST

**Base:** `76f9ee0fa52e5bed8473308f178e485054484f9c`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT ONE-SHOT WRAPPER REVIEW`

**Authority:** repository implementation, unprivileged fixture testing, fresh
`/private/tmp` staging, and same-user read-only host qualification only

No administrator authorization, root execution, OpenDirectory mutation,
principal deletion/provisioning, or ACL change occurred. The privileged prompt
count for this preparation run is `0`.

## Fixed reviewed identities

The accepted mutation source was not modified. Its SHA-256 remains:

```text
c22849cae2f8610a3f75b349943123283ab549d22d7df6305497872cdf482954
```

The freshly staged mutation binary is:

```text
/private/tmp/decision-os-f01-slice4a-one-shot-2418c8ea235a/macos_f01_opendirectory_mutation
```

Its accepted and observed SHA-256 is:

```text
2418c8ea235a3eebe0890e38ed95932ff6094bf4aaa778e78964bfb9eaa6b4fa
```

The standalone wrapper source is:

```text
scripts/macos_f01_opendirectory_one_shot_wrapper.py
```

The repository source and staged copy are byte-identical at SHA-256:

```text
8b140768b8c639a4317ff1fcd216ee4041d3645ed3cfdc5289bb83e68bd90217
```

The exact future command is the single newline-terminated line in:

```text
scripts/macos_f01_opendirectory_one_shot_command.txt
```

Its SHA-256 is:

```text
e7dccb42a85856e442f5d0a62371375f3d8a60108184a486ae593ed1b7f2ae49
```

That line embeds the zlib-compressed bytes of the reviewable loader source:

```text
scripts/macos_f01_opendirectory_one_shot_loader.py
```

The repository source and decoded command payload are byte-identical: 7,164
bytes with SHA-256:

```text
abe76aed381b01999e828c2122644ff3ad4f01d2c900d445b58eb10641254236
```

The command file, compressed payload, and wrapper contain no credential,
secret, repository import, dynamic request input, or mutation fallback.

## Staged metadata binding

All numeric values below are fixed into the loader or wrapper and were
re-read after the directory was sealed:

| Object | Device | Inode | UID | GID | Mode | Links | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| staged directory | `16777234` | `123705528` | `501` | `0` | `0500` | `4` observed | `128` observed |
| staged wrapper | `16777234` | `123706512` | `501` | `0` | `0444` | `1` | `21377` |
| staged mutator | `16777234` | `123705533` | `501` | `0` | `0555` | `1` | `94704` |

The loader binds the exact directory path, device/inode, UID/GID, and mode. It
opens the wrapper relative to the opened directory with `O_NOFOLLOW`, requires
a regular one-link file and exact metadata, hashes the opened bytes, repeats
`fstat`, and proves the pathname still names the opened inode. It then compiles
those exact in-memory bytes. It does not execute the wrapper by a second source
pathname read.

The wrapper independently repeats the same class of checks for the fixed
mutator identity. It reads and hashes the opened mutator descriptor, copies
those same bytes into a newly created effective-root-owned `0700` directory,
creates a one-link `0500` executable, and reopens/re-hashes/rebinds that private
copy immediately before its one direct child launch. The child is launched
with no shell, an empty environment, fixed `/` working directory, closed
descriptors, bounded output capture, and a fixed timeout.

## Interpreter identity

The future command uses the resolved interpreter directly rather than the
mutable `xcode-select` shim route:

```text
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9
```

Observed identity:

- Python `3.9.6` built by Apple Clang `21.0.0`;
- regular universal Mach-O (`x86_64`, `arm64`);
- device `16777234`, inode `113376340`;
- UID `0`, GID `0`, mode `0755`, link count `1`, size `102352`;
- SHA-256
  `bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e`;
- code-signing identifier `com.apple.python3`; and
- TeamIdentifier `59GAB85EFG`.

The loader requires its `sys.executable` to equal that exact path, then opens
the interpreter path with `O_NOFOLLOW`, validates all listed file metadata,
hashes it, repeats `fstat`, and rebinds the pathname before reading the wrapper.
The installed signature is structurally present, but `codesign --verify
--strict` reports `CSSMERR_TP_NOT_TRUSTED`; this report therefore relies on the
fixed root-owned file identity and SHA rather than claiming trust-chain
verification.

## One-interaction and result contract

The command contains exactly:

- one `/usr/bin/osascript` process;
- one `do shell script ... with administrator privileges` clause; and
- one fixed Python loader invocation.

It contains no loop, second authorization request, retry, repair path, or
fallback to `dscl`, `sysadminctl`, `dseditgroup`, `pwpolicy`, another binary,
or provisioning. Cancellation or denial terminates that sole `osascript`
invocation. Any loader/wrapper/artifact mismatch returns or terminates at
`HOLD`; there is no second invocation.

The wrapper executes the mutation child at most once. It preserves the exact
child stdout and stderr as base64, the exact exit code, parsed canonical child
report (including native OpenDirectory errors and final snapshot), and any
reported `completed_mutations`. Top-level success is possible only when all of
these are exact:

```text
exit_code = 0
status = ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW
completed_mutations = ["user_deleted", "group_deleted"]
```

Every other result remains `HOLD`. Even that exact success ends the one-shot
session; the wrapper contains no provisioning or ACL path.

## Unavoidable check-to-exec residual

This macOS host exposes neither `fexecve(2)` nor `execveat(2)` for a true
descriptor-bound Mach-O launch. A direct unprivileged qualification attempt to
execute the reviewed Mach-O through `/dev/fd/<fd>` failed with `EACCES`.

The narrow implementation therefore executes the validated private pathname
after its final inode check. The private path is inside a newly random,
effective-root-owned `0700` directory, so the staged UID 501 principal and
other non-root principals cannot traverse or replace it. A root-equivalent
actor could still replace the private pathname between the final check and the
kernel's path lookup. The wrapper does not claim protection against an already
compromised root authority, and it does not claim fd-bound execution.

The initial interpreter launch also necessarily trusts the fixed root-owned
Command Line Tools runtime and OS loader before the loader can self-hash the
interpreter. Root/OS modification of that runtime is outside this wrapper's
non-root substitution threat boundary.

## Qualification evidence

- focused wrapper, loader, substitution, output, no-retry, and no-fallback
  suite under Homebrew Python: `20/20` passed;
- the same focused suite under macOS `/usr/bin/python3` 3.9: `20/20` passed;
- combined wrapper/mutation/read-only/rollback/principal-separation and Broker
  Slice 1/2/3 regression: `269/269` passed;
- exact staged wrapper direct run as UID `501`: canonical
  `HOLD_WRAPPER_PRIVILEGE_REQUIRED`, zero execution attempts, zero
  authorization requests, and zero prompts;
- exact embedded loader direct run unprivileged: canonical
  `HOLD_LOADER_PRIVILEGE_REQUIRED`, zero mutation execution attempts, zero
  authorization requests, and zero prompts;
- loader opened and hashed the exact interpreter and staged wrapper during the
  focused qualification without invoking the wrapper as root;
- exact command has one line, its compressed payload decodes byte-for-byte to
  the qualified loader, `zsh -n` passed, and `osacompile` accepted the exact
  AppleScript source without executing it; and
- repository/stage hashes and every pinned metadata tuple were re-read after
  sealing.

The app-sandboxed OpenDirectory probe failed closed at node open with native
error `com.apple.OpenDirectory` code `10002` and zero mutation. One subsequent
same-user, EUID `501`, read-only run outside the app sandbox returned the
expected canonical `HOLD_PRIVILEGE_REQUIRED` current-state snapshot. This was
not root or administrator execution and displayed no administrator prompt.

That final read-only snapshot exactly retains:

- `_decisionos_codex` user UID/primary GID `510`, user GUID
  `D6515614-B56A-4943-AA41-18D17DE9F899`, exact RealName, and
  `NFSHomeDirectory=/var/empty`;
- required user absence of `UserShell`, `IsHidden`, and
  `AuthenticationAuthority`;
- `_decisionos_codex` group GID `510`, group GUID
  `1F200679-B0A2-4D13-A86F-6492F9C4B66F`, and exact RealName;
- required group absence of `GroupMembership` and `GroupMembers`;
- unique UID/GID 510 bindings to `_decisionos_codex`;
- Guardian and Broker user/group absence; and
- absence of `/Library/Application Support/DecisionOS` and both Slice 4A
  descendants.

The result also reports `mutation_attempted=false`,
`completed_mutations=[]`, `provisioning_performed=false`,
`protected_repository_acl_changed=false`, and `privileged_prompt_count=0`.
Host state therefore matches the accepted pre-preparation anchor.

## Completion state

**V12 State:** `PASS` for bounded 13-153X preparation only. The repository
artifacts, fresh stage, identities, tests, restart evidence, and residual are
recorded. This is not a rollback execution PASS and not Slice 4A completion.

**V13 Next Loop Gate:** `HOLD — INDEPENDENT ONE-SHOT WRAPPER REVIEW`

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
