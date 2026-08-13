# F-01 Slice 4A — partial-host recovery preparation

**As-of:** 2026-08-13 JST

**Gate:** `HOLD — INDEPENDENT ROLLBACK REVIEW`

**Authority:** preparation and non-privileged fixtures only

**Privileged interaction budget:** `1` for a later separately authorized run

No privileged command was executed during this recovery-preparation pass.

## Exact stop diagnosis

The original provisioner issued a new `dscl` process for every record and
attribute write. Its fixed order was:

1. create and fill the Codex private group;
2. create the Codex user;
3. write `RealName`, `UniqueID`, `PrimaryGroupID`, and `GeneratedUID`;
4. write `NFSHomeDirectory`; then
5. write `UserShell`, password marker, and `IsHidden`.

The post-failure record contained every field through `GeneratedUID` and did
not contain `NFSHomeDirectory`, `UserShell`, or `IsHidden`. The failed command
is therefore fixed by sequence and readback as:

```text
/usr/bin/dscl . -create /Users/_decisionos_codex NFSHomeDirectory /var/empty
```

It returned process exit `40`, so `_checked` raised and the sequential
transaction stopped before issuing any later mutation. Directory Service
defines `eDSPermissionError = -14120`, and `(-(-14120)) mod 256 = 40`; that is
the bounded error classification consistent with the observed process result.
The same exact attribute command succeeded later when run alone, so its
executable path, syntax, record path, attribute name, and value were not
intrinsically invalid.

The exact control-flow root cause is therefore proved: the NFS-home `dscl`
process returned nonzero and the fail-closed wrapper terminated the transaction.
The underlying Directory Service status and daemon reason remain `UNKNOWN`:
exit `40` alone is not a unique encoding of the original negative DS status,
the wrapper discarded `dscl` stderr, and privileged unified-log access is
outside this recovery Gate. The implementation defects are proved: it had no
read-after-write visibility barrier between fresh `dscl` processes, discarded
the diagnostic, and incorrectly treated a password marker as login-disable
proof. These are corrected without retrying mutations.

## Accepted rollback identity

Only these two records are rollback targets:

| Record | Name | Numeric identity | GeneratedUID | RealName |
| --- | --- | --- | --- | --- |
| User | `_decisionos_codex` | UID `510`, primary GID `510` | `D6515614-B56A-4943-AA41-18D17DE9F899` | `Decision OS Codex execution principal` |
| Group | `_decisionos_codex` | GID `510` | `1F200679-B0A2-4D13-A86F-6492F9C4B66F` | `Decision OS Codex execution principal` |

Before deletion, the rollback requires:

- exact equality of all table fields;
- UID 510 and GID 510 each resolve only to the named target;
- no unrelated authentication authority or private-group member;
- Guardian and Broker user/group records remain absent; and
- all DecisionOS/F01PrincipalSeparation host-state paths remain absent.

The target user is read and rebound a second time immediately before its
name-addressed deletion. After that deletion, the target group is likewise
read and rebound immediately before its deletion. Held principals and the
host-state paths are rechecked before each mutation. This narrows each
deletion to the observed identity and refuses a name/GUID/ID substitution.

The only mutation allowlist is:

```text
/usr/bin/dscl . -delete /Users/_decisionos_codex
/usr/bin/dscl . -delete /Groups/_decisionos_codex
```

After user deletion, absence and UID release are polled read-only. The surviving
group's name/GID/GUID/RealName and unique GID binding are then checked again
before group deletion. After group deletion, absence and GID release are polled
read-only. Any mismatch or failure stops at `HOLD` without mutation or
authorization retry. No unrelated record is mutated.

## Prepared rollback artifact

Repository source:

`scripts/macos_f01_rollback_partial_codex.py`

Read-only execution copy:

`/private/tmp/decision-os-f01-slice4a-rollback-714d07da0fa26da6/rollback.py`

Both files have SHA-256:

```text
714d07da0fa26da673ad1c5c72428cc032ad8803024c4a345313f82e2705886d
```

The staged directory is owner `501`, group `0`, mode `0500`. The staged file is
a regular, one-link file owned by UID `501`, GID `0`, mode `0444`. The proposed
loader opens it with `O_NOFOLLOW`, reads it once, validates directory and file
metadata plus the SHA-256, and executes those same in-memory bytes. A mismatch
exits before the rollback entrypoint.

## Exact later one-shot command — not executed

The following is the complete rollback-only authorization command prepared
for independent review. It is one `osascript` process and therefore at most one
administrator interaction. Neither this command nor its rollback payload was
executed in this preparation pass.

```sh
/usr/bin/osascript -e "set payload to \"import hashlib,os,stat,sys;p='/private/tmp/decision-os-f01-slice4a-rollback-714d07da0fa26da6/rollback.py';q='/private/tmp/decision-os-f01-slice4a-rollback-714d07da0fa26da6';d=os.stat(q,follow_symlinks=False);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);s=os.fstat(fd);f=os.fdopen(fd,'rb',closefd=True);b=f.read();f.close();ok=stat.S_ISDIR(d.st_mode) and d.st_uid==501 and d.st_gid==0 and stat.S_IMODE(d.st_mode)==0o500 and stat.S_ISREG(s.st_mode) and s.st_uid==501 and s.st_gid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o444 and len(b)==s.st_size and hashlib.sha256(b).hexdigest()=='714d07da0fa26da673ad1c5c72428cc032ad8803024c4a345313f82e2705886d';ok or sys.exit('rollback script identity mismatch');sys.argv=[p,'rollback','--confirm','rollback-only-observed-partial-codex-uid-gid-510'];g={'__name__':'__main__','__file__':p};exec(compile(b,p,'exec'),g,g)\"" -e 'do shell script ("/usr/bin/python3 -I -S -c " & quoted form of payload) with administrator privileges'
```

Only the shell parse and an unprivileged hash-loader `--help` path were tested.
The authorization mechanism and rollback operation were not invoked.

## Corrected future provision design

The future transaction is repository-ready but not host-qualified or
authorized:

- fixed root-owned tools are `/usr/bin/dscl`, `/usr/bin/id`,
  `/usr/bin/pwpolicy`, `/usr/bin/python3`, `/usr/bin/sudo`, `/bin/test`,
  `/usr/bin/touch`, and `/usr/bin/false`;
- the review-snapshot entrypoint is preflighted as
  `/usr/bin/python3 -I -S decision_os/companion/principal_separation.py`; the
  standalone module does not import the broader Companion package;
- `dscl . -create`, `dscl . -read`, and `dscl . -search` syntax is pinned;
- every mutation is issued once and followed by up to 20 read-only readbacks at
  0.1-second intervals;
- explicit login denial uses `pwpolicy -u <account> disableuser` once and
  requires `pwpolicy -u <account> authentication-allowed` to report denial;
- `dsAttrTypeNative:IsHidden` readback is normalized and verified;
- only `eDSRecordNotFound` is accepted as record absence;
- private primary groups require no redundant `dseditgroup` membership write;
- stderr is retained in bounded failure diagnostics; and
- every failure is `HOLD`, with no mutation retry and no authorization wrapper.

The full corrected Directory Service and filesystem transaction has been
executed only against mocks. Guardian and Broker have not been provisioned.

## Preparation verification

- focused principal-separation plus rollback fixtures: `53` tests passed;
- rollback fixtures under macOS `/usr/bin/python3` 3.9: `18` tests passed;
- corrected provision fault injection covers every one of its `39` successful
  Directory Service/password-policy mutation positions and proves one call at
  the injected failure;
- executable path metadata and `pwpolicy` help syntax were checked read-only on
  this host;
- the plan entrypoint passed under the exact macOS system Python 3.9 runtime;
- staged and repository rollback hashes match; and
- the proposed shell command passed `zsh -n` parsing without execution;
- non-network Broker/Companion regression: `531` tests passed, `2` skipped;
- full repository attempt: `1741` tests ran, with `14` skips, `43` loopback
  bind errors (`PermissionError: [Errno 1] Operation not permitted`), and `3`
  sandboxed browser-process failures (exit `-6`). No broader sandbox or
  authorization retry was requested.

`F-01 remains OPEN`
