# V13 Runner Distribution Surface v0.1

## Status

```text
Implementation:
PASS / COMPLETE / MERGED / AVAILABLE ON MAIN

Canonical starting main:
f4df2a726bd632ae54b2ac1069640a772cfb6fac

Packaging source ref:
e1212a795413e0146c52b2c9aa51356897c62846

Implementation head:
205be5766be05d079cc2aa3627b1685cec2500bd

PR #14:
PASS / MERGED / COMPLETE

Implementation merge:
f9b83d5bde850829e232653df811790fbd3daff9

Runner:
V13 RUNNER V0.2 / UNCHANGED

Package publication:
NONE

Release:
NONE

Tag:
NONE

Telemetry:
NONE

Remote scan:
NONE
```

This surface lets a person who has not cloned the V13 repository execute the
unchanged Runner v0.2 against a local Git repository. It does not publish a
package, scan a remote repository, upload a report, contact an owner, or make
an adoption recommendation.

## Five-minute path

Prerequisites:

- `uv` is already available;
- a local Python satisfying the package contract `>=3.10` is already
  available;
- the target is a local Git repository.

Validated command:

```sh
uvx --isolated --no-config --no-env-file --no-python-downloads \
  --from "git+https://github.com/shin4141/decision-os-v13-loopkit@e1212a795413e0146c52b2c9aa51356897c62846" \
  decision-os scan --format text .
```

Deterministic JSON:

```sh
uvx --isolated --no-config --no-env-file --no-python-downloads \
  --from "git+https://github.com/shin4141/decision-os-v13-loopkit@e1212a795413e0146c52b2c9aa51356897c62846" \
  decision-os scan --format json .
```

The equivalent explicit spelling was also verified:

```sh
uv tool run --isolated --no-config --no-env-file --no-python-downloads \
  --from "git+https://github.com/shin4141/decision-os-v13-loopkit@e1212a795413e0146c52b2c9aa51356897c62846" \
  decision-os scan --format text .
```

`--isolated` prevents reuse of an already installed tool. `--no-config` and
`--no-env-file` keep target-local or user configuration from changing the
transport contract. `--no-python-downloads` requires an already available
compatible Python instead of adding a Python acquisition path. Quiet mode is
intentionally absent: a cold run's transport identity remains visible on
stderr.

The exact 40-character Git ref is immutable and is the source identity used by
the command. The cold validation log named that full ref while building the
distribution, and the cached checkout resolved to the same full commit. An
invalid 40-character ref returned exit 1, emitted no Runner output, and did
not fall back to another revision.

## Transport and scan boundary

Distribution transport:

- may contact GitHub to fetch the exact Git source;
- may contact the Python package index for `flit_core==3.12.0`;
- may populate uv's local cache;
- may write transport progress to stderr.

Runner scan:

- makes no Git network call;
- sends no repository content;
- uses no telemetry;
- contacts no external service;
- performs no target-worktree or target-Git-directory write;
- writes deterministic Runner output to stdout.

The bounded claim is therefore:

> The tool transport requires network access on a cold run. After launch, the
> repository scan itself is local, read-only, and sends no repository content.

The validation target contained a unique file-body sentinel. That sentinel
was absent from cold transport stderr, warm stderr, Runner stdout, and every
parity execution. The Runner package contains no runtime dependency and no
network client. This is bounded evidence for the stated execution path, not a
general packet-level attestation of every host environment.

## Package identity

```text
Distribution name:
decision-os-v13-loopkit

Distribution version:
0.2.0

Import package:
decision_os

Console command:
decision-os

Entry point:
decision_os.cli:main

Requires-Python:
>=3.10

Runtime dependencies:
none

Build backend:
flit_core==3.12.0

License:
MIT
```

The wheel contained the existing seven `decision_os` Python files plus
distribution metadata and the license. The source distribution additionally
contained the README and `pyproject.toml`. No `decision_os/**` file, existing
Runner test, fixture, schema, recommendation rule, or exit-code definition was
changed.

Temporary build artifacts:

```text
Wheel SHA-256:
75edaee45cd365b42e5556d0cb6724dfcdefe9be1cf0aaa6854d85f35635dab0

Source distribution SHA-256:
285c75c68c47c18bb158b1fbbd0d116b5b8f164bfe9455a1944720a0df47caa0
```

These artifacts were validation inputs only. They were not published,
released, tagged, or committed.

## Transport Tool Identity Guard receipt

The Guard completed before branch creation or repository modification.

```text
Guard:
PASS

uv:
0.11.32

uv version output:
uv 0.11.32 (3010295ae 2026-07-23 aarch64-apple-darwin)

uvx version output:
uvx 0.11.32 (3010295ae 2026-07-23 aarch64-apple-darwin)

Official release:
https://github.com/astral-sh/uv/releases/tag/0.11.32

Official artifact:
uv-aarch64-apple-darwin.tar.gz

Artifact SHA-256:
ed336d0ba49db8ef89b2b41fffa372ce63bd032f22a56f001c265891aec32829

uv executable SHA-256:
3736babdf838efb1c04ca690dd6ff3458a23cdf98e0e08b1f721eac4779e272d

uvx executable SHA-256:
572d4d5281ba5b20b9c94ea53fac1b2b9c19287931091b44e8693dc65780cb3d

Private fixed Guard receipt SHA-256:
73a1aa69cc110223c9ffe26f65e5605f872e9732fda712760dc7d84ba5d20968

Host:
macOS 26.2 build 25C56 / arm64
```

The Guard receipt recorded the exact executable paths inside one mode-0700
dedicated temporary root. The same executable identities and the same
dedicated `UV_CACHE_DIR` were used for cold and warm validation. There was no
global installation, shell-profile change, system-wide PATH change, system
package-manager action, authentication, telemetry, or dependency on an
existing user uv cache.

## Validation receipt

Environment:

```text
Validated platform:
macOS 26.2 build 25C56 / arm64

Validated Python:
3.14.3

Other macOS versions:
NOT TESTED

Linux:
NOT TESTED

Windows:
NOT TESTED

Other Python versions:
NOT TESTED IN THIS RUN
```

Unit suite:

```text
73 OF 73 / PASS
```

Cold and warm exact-ref execution:

```text
Cold-cache exit:
0

Warm-cache exit:
0

Cold-cache text stdout SHA-256:
0f1044c6a7eb3295d768409f6c69c114059af117550127e353ecea0162bdcf57

Warm-cache text stdout SHA-256:
0f1044c6a7eb3295d768409f6c69c114059af117550127e353ecea0162bdcf57

Cold-cache stderr:
exact-ref build and one-package install transport only

Cold-cache stderr SHA-256:
84bd0b4fd468ce4d95bcbb441cbf1adfb276a8b820115b0fb342b83bfba5cbd9

Warm-cache stderr:
empty
```

The cold run executed from outside the V13 checkout, in a target path
containing spaces and containing a decoy `decision_os` package that would fail
if imported. The exact-ref command returned the expected Runner result, so the
decoy was not imported.

Four-surface parity:

| Case | Expected exit | Result |
| --- | ---: | --- |
| ordinary repository / JSON | 0 | byte-identical stdout; stderr empty |
| ordinary repository / text | 0 | byte-identical stdout; stderr empty |
| complete V13 fixture / check | 0 | byte-identical stdout; stderr empty |
| non-Git directory / check | 3 | byte-identical stdout; stderr empty |
| missing-closure V13 fixture / check | 4 | byte-identical stdout; stderr empty |
| contradictory V13 fixture / check | 5 | byte-identical stdout; stderr empty |
| invalid usage | 2 | byte-identical stdout; stderr empty |

The four surfaces were:

1. repository-local `bin/decision-os`;
2. `python3 -m decision_os`;
3. a temporary wheel-installed console entry point;
4. exact-ref `uvx` execution from the dedicated warm cache in offline mode.

The explicit `uv tool run` spelling produced the same text bytes and exit 0.
The ordinary JSON SHA-256 was
`cdf0da919f62baf97be32250208366c927b199f231b5ff7f0ddeeb24a480ed33`;
the ordinary text SHA-256 was
`0f1044c6a7eb3295d768409f6c69c114059af117550127e353ecea0162bdcf57`.

No-write proof:

```text
Ordinary target worktree digest:
ce0169a98d8eb72bcfd881c0ca3d9bedac7b27477fa6a5114d13a37a441d5732

Ordinary target Git-directory digest:
4754d8c367b1e0e7576016136a50b00be60e69688d69e84041b600d3cbf7438d

Complete fixture worktree digest:
293e7be1ecebea475586f763a2a0925b0226eaaf23a3a77a513d04b553840ca1

Missing-closure fixture worktree digest:
b09df9f87b05a93bf9053d36463229ea24828f67ae8dff56f8bac2227b2599dc

Contradictory fixture worktree digest:
9b1f58b8239841bb5f1d226d7d73b9e46cd1fc94483de0a28b2f8af242ce2410

Source worktree digest:
aff89c930967c0d01de6be8ec5d469537dcabff98f6d3f08a0919b5305d4c0cc

Opening versus closing comparison:
IDENTICAL FOR ALL WORKTREES, GIT DIRECTORIES, HEADS, BRANCHES, AND STATUSES
```

## Cache removal

The verified complete cleanup command is:

```sh
uv cache clean
```

It removes the entire uv cache, including data used by unrelated uv-managed
tools. `uv cache clean decision-os-v13-loopkit` removed package cache entries
in the validation copy but retained the Git-source checkout, so this receipt
does not claim that selective command fully removes all transport data. A user
who requires isolated cleanup can instead set a dedicated `UV_CACHE_DIR` for
the run and remove that dedicated directory afterward.

## Correction and rollback boundary

One of the two authorized pre-merge correction cycles was used. The initial
candidate `flit_core==4.0.0` was unavailable from the public package index;
the repository-local package metadata and its test were corrected to the
available pinned `flit_core==3.12.0`. No Runner source or behavior changed.

The predefined rollback is a history-preserving revert of the eventual
implementation merge, followed only by the reserved closure surfaces if
rollback is required. No reset, release deletion, tag deletion, package-index
action, source behavior repair, or authority expansion is permitted.

## Integration and authority closure

```text
Run:
COMPLETE / 2 OF 2 OPERATIONAL LOOPS CLOSED

Activation:
CONSUMED / CLOSED

Authority Envelope:
V13 RUNNER DISTRIBUTION SURFACE V0.1 / CONSUMED / CLOSED

Authority Window:
V13 RUNNER DISTRIBUTION SURFACE V0.1 / EXHAUSTED

Remaining authorized loops:
0

Pre-merge corrections:
1 OF 2 USED / REMAINING CORRECTION AUTHORITY EXHAUSTED WITH RUN CLOSURE

Approved implementation head:
205be5766be05d079cc2aa3627b1685cec2500bd

PR:
#14 / MERGED

History-preserving merge:
f9b83d5bde850829e232653df811790fbd3daff9

Rollback Identity:
STARTING MAIN f4df2a726bd632ae54b2ac1069640a772cfb6fac / IMPLEMENTATION MERGE f9b83d5bde850829e232653df811790fbd3daff9 / HISTORY-PRESERVING REVERT ONLY

Rollback execution:
NOT EXECUTED

Receipt:
docs/v13_runner_distribution_surface_v0_1.md / GUARD + BUILD + EXACT-REF + PARITY + NO-WRITE PASS

Closure-Only Tail:
docs/v13_runner_distribution_surface_v0_1.md + docs/current_signal.md + handoff/current_codex_handoff.md / CONSUMED BY ENCLOSING COMMIT

Current Gate:
HOLD — DISTRIBUTION SURFACE V0.1 CLOSED / NO NEXT AUTHORIZED ACTION

Active Branch:
none

Codex Next Authorized Action:
none
```

The merge preserved both implementation commits and merged the reviewed head
without squash. The enclosing documentation-only commit supplies the
closure-tail transport identity. It grants no additional correction, branch,
PR, scan, package publication, release, tag, CI, telemetry, outreach,
Revenue, runtime, or v0.3 authority.

Completion Line:

V13 Runner Distribution Surface v0.1は、固定uv identityとexact Git refで
cold/warm transport、四経路のbyte/exit parity、no-write、no-content-returnを
実証し、Runner v0.2を変更せずmainへ統合してauthorityを閉じた。
