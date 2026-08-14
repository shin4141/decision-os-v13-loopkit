# F-01 Slice 4A — SSV-anchored sudo recovery transport

**As-of:** 2026-08-14 JST

**Base:** `7654b2dc0c96c669845a544684745979aa89dfc8`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT SSV-SUDO TRANSPORT REVIEW`

**Authority:** unprivileged, forward-only transport materialization and
read-only qualification. No rollback execution authority.

No `sudo`, `osascript`, administrator authorization, root execution,
OpenDirectory mutation, principal deletion/provisioning, ACL change, or
sole-writer work occurred. Sudo invocation count and privileged prompt count
are both `0`.

## Forward-only correction of the S HOLD

The preceding S preparation stopped because `/usr/bin/sudo` is intentionally
non-readable to the ordinary user on this host. It is an execute-only setuid
Apple system binary, and ordinary content reads return `EACCES`.

No privileged read was added. This S1 repair does not rewrite the historical S
HOLD evidence. It narrows the recovery-only trust contract to the exact
OS-managed sudo identity on the active macOS Signed System Volume:

```text
SUDO_CONTENT_SHA256 = NOT_USER_READABLE / NOT REQUIRED UNDER SSV TRUST CONTRACT
```

The recovery trust contract delegates sudo content integrity to the active
macOS Signed System Volume and OS execution trust boundary. It does not consume
Human Seat authority merely to obtain a redundant user-space content hash.
This exception applies only to the Apple SSV-hosted `/usr/bin/sudo`; it does
not apply to mutable Data-volume tools or artifacts.

## Exact SSV sudo trust anchor

Read-only host evidence establishes:

| Field | Required and observed value |
| --- | --- |
| Path | `/usr/bin/sudo` |
| Object | regular executable file, not a symlink |
| Device | `16777234` |
| Inode | `1152921500312572853` |
| UID/GID | `0/0` (`root:wheel`) |
| Mode | `04511` (`-r-s--x--x`) |
| Link count | `1` |
| Size | `1575952` bytes |

Every path component (`/`, `/usr`, `/usr/bin`, `/usr/bin/sudo`) is root-owned,
not a symlink, and has no group/other write bit. The containing root mount is:

```text
/dev/disk3s1s1 on / (apfs, sealed, local, read-only, journaled)
```

No user-writable path component, PATH lookup, indirection, or redirection is
part of the transport.

## New outer transport artifact

The historical osascript command remains unchanged. The new forward-only
artifact is:

```text
scripts/macos_f01_opendirectory_sudo_one_shot_command.txt
```

Identity:

```text
SHA-256 = de3e767904080373237f2d0372f058add7d0b5db0270f8e0795d7280c72f4af4
bytes = 3073
lines = 1
final newline = present
```

Its shell token surface is exactly:

```text
/usr/bin/sudo
--
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9
-I
-S
-c
<fixed embedded loader bootstrap>
```

It contains exactly one `/usr/bin/sudo`, zero `osascript`, no retry or
fallback, and no request-controlled path, principal, record type, or operation.
The fixed bootstrap decodes byte-for-byte to the already accepted loader and
executes that loader once. The only transport change is:

```text
old: Terminal -> osascript administrator transport -> fixed Python loader
new: Terminal -> /usr/bin/sudo -> fixed Python loader
```

The unprivileged Desktop convenience copy is:

```text
/Users/sn/Desktop/DecisionOS_OpenDirectory_Rollback_SUDO_Command.txt
```

Its SHA-256 is
`de3e767904080373237f2d0372f058add7d0b5db0270f8e0795d7280c72f4af4`.
Direct byte comparison with the repository command returned `PASS`; both are
3073 bytes and preserve the final newline. The Desktop copy was not opened or
executed.

## Unchanged reviewed chain

| Artifact | SHA-256 |
| --- | --- |
| mutation source | `28f6728199e09a2e459eb1d0237e8d16ddb688e57b70c08050a45bcfabde32bf` |
| production/staged mutator | `0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802` |
| wrapper | `faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9` |
| loader | `5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1` |
| historical osascript command | `75d433390e58e08bbd4ba97c80addbc85814416794f76b51fb57d4d87add4575` |

The staged directory, wrapper, and mutator retain their reviewed
device/inode/UID/GID/mode/link-count/size bindings. The loader still validates
the fixed Apple Python interpreter and staged wrapper. The wrapper still
authenticates the staged mutator, copies its exact bytes to a root-private
execution path, runs one child at most, preserves exact child stdout/stderr and
native error JSON, and has no retry, fallback, provisioning, or ACL path.

## Unprivileged verification

- new SSV-sudo transport tests under Homebrew Python: `5/5` passed;
- new SSV-sudo transport tests under macOS Python 3.9: `5/5` passed;
- existing wrapper/mutation tests under Homebrew Python: `28/28` passed;
- existing wrapper/mutation tests under macOS Python 3.9: `28/28` passed;
- native modeled/adversarial mutation cases exercised by each mutation suite:
  `41/41` passed;
- `zsh -n` and `sh -n` parse checks: passed without execution;
- loader payload decompression and exact-byte comparison: passed;
- forbidden `osascript`, `dscl`, `sysadminctl`, `dseditgroup`, and `pwpolicy`
  transport/fallback checks: passed; and
- malformed/substituted artifact and handled-HOLD fixture coverage remains
  passing in the unchanged wrapper suite.

## Current host state

An EUID-501 read-only run of the unchanged production mutator returned
`HOLD_PRIVILEGE_REQUIRED`, `issues=[]`, `mutation_attempted=false`, and
`completed_mutations=[]`. The accepted Codex user/group identities and unique
UID/GID 510 bindings remain present; Guardian/Broker remain absent; all
DecisionOS Slice 4A host-state paths remain absent. Host state is unchanged.

## Completion state

**V12 State:** `PASS` for bounded 13-153S1 SSV-sudo transport materialization
only. This is not rollback execution or Slice 4A completion.

**V13 Next Loop Gate:**
`HOLD — INDEPENDENT SSV-SUDO TRANSPORT REVIEW`

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
