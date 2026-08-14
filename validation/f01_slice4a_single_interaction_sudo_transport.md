# F-01 Slice 4A — single-interaction sudo recovery transport

**As-of:** 2026-08-14 JST

**Base:** `4b866a7a926866ff4f7481685bbd92fd76e069c5`

**Branch:** `codex/13-153-rollback-review`

**Gate:** `HOLD — INDEPENDENT SINGLE-INTERACTION SUDO REVIEW`

**Authority:** unprivileged, forward-only authentication-input transport
repair only. No rollback execution authority.

No real `sudo`, `osascript`, administrator authorization, root execution,
OpenDirectory mutation, principal deletion/provisioning, ACL change, or
sole-writer work occurred. Real sudo invocation count and privileged prompt
count are both `0`.

## S2 correction

The accepted S1 command starts one fixed `/usr/bin/sudo` process, but a single
sudo process can consume more than one password attempt under host sudoers
policy. S1 therefore did not structurally enforce the DecisionOS human
interaction budget. S2 preserves S1 as historical preparation evidence and
adds a forward-only credential feeder and command; it does not rewrite the S1
artifact.

The S2 execution ancestry is:

```text
independently launched Terminal
-> fixed Apple Python 3.9 interpreter
-> exact embedded unprivileged feeder
-> /usr/bin/sudo -S -p '' --
-> fixed Apple Python 3.9 interpreter
-> exact accepted loader
-> exact accepted wrapper
-> exact accepted mutator
```

## New artifacts

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `scripts/macos_f01_opendirectory_sudo_once_feeder.py` | `5659eb30493fa36ff6be61047549471b2d5c7faa4b456a9f954bdaf5a3c0938e` | 6883 |
| `scripts/macos_f01_opendirectory_sudo_once_command.txt` | `1877dfe9dd088a5d84fafd7febb0719e1f3bf96df4b0f4d3b2b5e1a6ec8cb8c8` | 5480 |

The one-line command uses the fixed interpreter path with `-I -S -c` and
contains the exact feeder bytes as a compressed base64 payload. Decoding that
payload produces the repository feeder byte-for-byte. The feeder contains the
accepted loader payload, whose decoded SHA-256 remains
`5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1`.

The feeder accepts no runtime arguments or mutation target. Its fixed sudo
argument vector is exactly:

```text
/usr/bin/sudo
-S
-p
<empty prompt string>
--
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9
-I
-S
-c
<exact accepted loader bootstrap>
```

There is one process-construction call, one sudo argument vector, no loop, no
recursive invocation, and no authorization fallback.

## One-human-input contract

The production feeder has these fixed invariants:

```text
PRIVILEGED_HUMAN_INTERACTION_BUDGET = 1
SUDO_INVOCATION_BUDGET = 1
AUTHORIZATION_RETRY_ALLOWED = False
```

It calls `getpass` through one call site exactly once. A credential containing
an embedded carriage return or newline is rejected before sudo launch. For an
accepted value it constructs exactly one credential line, passes that value
only as the `input` to one `Popen.communicate` call, and `communicate` closes
the sudo stdin pipe after that input. A later sudo password read therefore
receives EOF. It cannot trigger another `getpass` call, even if host sudoers
would otherwise permit multiple password tries.

The fixed `-p ''` suppresses sudo's own password prompt. Cancellation or EOF
at the single `getpass` call stops before sudo. An authentication failure or a
request for another password receives no second human input and exits HOLD.
This bound does not depend on the host `passwd_tries` value.

The feeder promotes Python's `GetPassWarning` to an exception. If echo-safe
credential entry is unavailable, it therefore stops before getpass can use
its echoing fallback and before sudo launch.

## Credential handling

The password is never put into argv, environment variables, shell history,
repository or Desktop bytes, files, JSON reports, logs, stdout, or stderr. The
sudo argv and environment are fixed before the read. The feeder does not open
or write a file and emits no report of its own. It relays only the fixed
child's stdout and stderr bytes.

The password exists transiently as immutable language/runtime objects in the
unprivileged feeder and as the one line supplied to sudo's stdin pipe. Local
references are dropped after communication, but Python cannot provide
cryptographic zeroization guarantees for immutable string or bytes objects.
No stronger erasure claim is made.

## Exact result preservation and HOLD behavior

The feeder captures and then writes the sudo child's stdout and stderr bytes
unchanged. It exits success only when all of these are true:

1. sudo returned exit code `0`;
2. stdout is one exact canonical JSON object;
3. `status` is exactly
   `ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW`; and
4. `completed_mutations` is exactly
   `["user_deleted", "group_deleted"]`.

Every other result exits with the fixed outer HOLD code `3`. This includes
credential EOF/cancellation, sudo launch failure, sudo authentication failure,
nonzero sudo exit, malformed or non-canonical output, handled child HOLD, and
partial or substituted completion. Authentication failure remains an outer
authentication-transport HOLD; S2 does not relabel it as a mutation failure.

## Preserved SSV trust contract and chain

The accepted SSV trust contract is unchanged:

```text
SUDO_CONTENT_SHA256 = NOT_USER_READABLE / NOT REQUIRED UNDER SSV TRUST CONTRACT
```

Read-only tests still require `/usr/bin/sudo` to be the exact regular,
root:wheel, mode `04511`, device `16777234`, inode
`1152921500312572853`, one-link, 1575952-byte executable on the sealed,
read-only APFS system volume, with no writable or redirected path component.
This exception remains limited to the Apple SSV-hosted sudo executable.

| Preserved artifact | SHA-256 |
| --- | --- |
| historical S1 command | `de3e767904080373237f2d0372f058add7d0b5db0270f8e0795d7280c72f4af4` |
| loader | `5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1` |
| wrapper | `faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9` |
| mutation source | `28f6728199e09a2e459eb1d0237e8d16ddb688e57b70c08050a45bcfabde32bf` |
| production/staged mutator | `0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802` |

The staged directory, wrapper, and mutator retain their reviewed
device/inode/UID/GID/mode/link-count/size identities. No reviewed chain or SSV
contract artifact changed.

## Desktop operation surface

The final unprivileged convenience copy is:

```text
/Users/sn/Desktop/DecisionOS_OpenDirectory_Rollback_SUDO_ONCE_Command.txt
```

Its SHA-256 is
`1877dfe9dd088a5d84fafd7febb0719e1f3bf96df4b0f4d3b2b5e1a6ec8cb8c8`.
Direct comparison against the repository command is byte-identical `PASS`;
both are 5480 bytes and retain the final newline. The Desktop file was not
opened or executed.

## Unprivileged verification

- S2 single-input transport tests under Homebrew Python: `9/9` passed;
- S2 single-input transport tests under macOS Python 3.9: `9/9` passed;
- exact helper embedding and accepted loader-byte comparison: passed;
- one getpass call, one process construction, one line, then EOF: passed;
- wrong-password/additional-read mock and real-pipe fake: one human read and
  EOF: passed;
- argv/environment/output secret-exclusion fixtures: passed;
- exact stream preservation and success/HOLD interpretation fixtures: passed;
- shell parse under `zsh -n` and `sh -n`: passed without execution;
- existing S1 SSV transport tests under both Python runtimes: `5/5` passed;
- existing wrapper/mutation tests under both Python runtimes: `28/28` passed;
- native modeled/adversarial mutation cases in each mutation suite: `41/41`
  passed; and
- `git diff --check`: passed.

No live authorization or mutation path was exercised. Host principal and
DecisionOS Slice 4A state remain unchanged from the accepted current-state
snapshot.

## Completion state

**V12 State:** `PASS` for bounded S2 single-human-input transport preparation
only. This is not rollback execution or Slice 4A completion.

**V13 Next Loop Gate:**
`HOLD — INDEPENDENT SINGLE-INTERACTION SUDO REVIEW`

`F-01 remains OPEN.`

`Slice 4A remains incomplete.`
