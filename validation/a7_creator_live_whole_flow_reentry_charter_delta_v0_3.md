# V13 — Creator-Live Whole-Flow Re-entry Charter Delta v0.3

## Purpose

This forward-only Delta records the model-free repair of the volatile P0
Companion process-identity guard. It adds one reusable qualification helper
and its focused tests. It changes no Companion production file or installed
runtime.

This Delta does not reopen, retry, replace, continue, repair into success, or
reclassify Creator-Live Whole-Flow Re-entry Cycle 002 or any historical proof.

## Parent Authority

| Authority | Identity |
| --- | --- |
| Parent Charter | `validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md` |
| Parent Charter SHA-256 | `84e65d12e7b7dd2c86204273c7dc96c16689580e3148f9a0beb2993fd7ee0585` |
| Delta v0.1 SHA-256 | `d34bf2f00de56b0869cc341ce0db65c2fa147ca8a824a81ccd2bde1a8cfe47fa` |
| Delta v0.2 SHA-256 | `da6347ee71512ab135ac0c418a7e6487adf243b0adaae89ee72f17774404ddc5` |
| Delta v0.2 merge | `b63e3fa9af13007c66a3fcf32ab162c0c9384082` |

The repair branch was created from that exact Delta v0.2 merge while
`origin/main` resolved to the same commit.

## Cycle 002 Permanent Boundary

Creator-Live Whole-Flow Re-entry Cycle 002 remains:

```text
BLOCK — volatile P0, before P1 identity creation
```

Its exact boundary remains:

- no proof-attempt identity;
- no product/runtime model invocation;
- no Run 1 or Run 2;
- no Field Note;
- no proof journal or anchor;
- retry count zero;
- replacement count zero;
- no interpretation as proof failure or proof success.

This control repair applies only to future model-free P0 qualification.

## Exact Harness Diagnosis

### Surviving source

The failed guard was not repository-owned. It was an inline, thread-local
Python preflight authored for Cycle 002. No standalone temporary or tracked
harness file contained it. The exact relevant logic survives in the canonical
Codex thread record:

```python
ps = subprocess.run(['ps', '-ef'], text=True, capture_output=True, check=False)
require(ps.returncode == 0, 6, 'PROCESS_INSPECTION_FAILED')
require(
    'Decision OS Companion.app/Contents/MacOS/applet' in ps.stdout,
    6,
    'APP_PROCESS_MISSING',
)
require(
    'Decision OS Companion/runtime/run.py' in ps.stdout,
    6,
    'RUNTIME_PROCESS_MISSING',
)
```

The same inline preflight separately opened a TCP connection to
`127.0.0.1:64203` and required an unauthenticated `/api/state` request to
return `401`.

### Origin of the stale expectation

The `runtime/run.py` expectation originated only in that thread-local inline
check. Repository-wide inspection found no `runtime/run.py` launcher
requirement. No Parent Charter, Delta, build record, source file, or protected
proof authorized it.

The canonical launcher and build establish instead:

```text
<authorized Python binary> -m decision_os.companion
```

Specifically:

- `macos/DecisionOSCompanion.applescript` constructs the module launch with
  bounded `PYTHONPATH` and picker-script environment values;
- `scripts/build_companion_app.sh` renders and compiles that AppleScript;
- the build copies the `decision_os` package and canonical AppleScript source
  into the installed runtime;
- the build creates no `runtime/run.py` launcher.

### Evidence the old guard did and did not examine

| Evidence | Old guard |
| --- | --- |
| Full process listing | Read as one raw string |
| Applet presence | Raw substring only |
| Runtime process command | Raw `runtime/run.py` substring only |
| Tokenized argv | Not examined |
| Listener existence | Checked separately |
| Listener-owning PID | Not examined |
| Process existence for listener owner | Not examined |
| Executable identity | Not examined |
| Canonical module identity | Not examined |
| Runtime-root product identity | Checked earlier, but not bound to the listener owner |
| Applet/process ancestry | Not examined |
| Competing listener owners | Not examined |

The healthy canonical process was classified as missing because its actual
argv contained `-m decision_os.companion` and did not contain the stale raw
substring `Decision OS Companion/runtime/run.py`. The check mapped that false
Boolean directly to `RUNTIME_PROCESS_MISSING`; it had no command-mismatch
branch.

### Classification

```text
P0_RUNTIME_PROCESS_EXPECTATION_STALE
```

This is narrower than an unavailable-source conclusion because the exact
thread-local predicate survives and the canonical launcher/build sources
directly contradict it.

## Durable Process Qualification Control

The new reusable helper is:

```text
scripts/qualify_companion_process.py
```

Helper SHA-256 at validation:

```text
77837c301495ddc6c49854223d015328c40b45add77bde4b380ebb2425373e61
```

The helper requires explicit bounded inputs for:

- installed runtime root;
- authorized repository root;
- expected product-tree SHA-256;
- expected Python executable;
- listener host and port;
- expected module;
- optional expected applet executable.

It does not hard-code a PID or listener port. It accepts only the canonical
host `127.0.0.1` and module `decision_os.companion`.

### Process evidence chain

The control independently establishes:

1. installed runtime-root existence and safety;
2. exact installed `decision_os` product-tree identity;
3. byte equality between installed and authorized AppleScript source;
4. canonical module invocation in the authorized launcher source;
5. active listener existence;
6. one exact listener-owning PID;
7. process existence for that PID;
8. process executable identity against the expected Python's OS executable;
9. tokenized argv identity;
10. exact `-m decision_os.companion` module execution;
11. optional exact applet parentage.

A healthy listener without the process binding does not pass. A matching
command that does not own the listener does not pass. Raw substring similarity
does not pass. A present wrong process receives a mismatch code rather than a
missing-process code.

The helper does not claim that argv proves imported module bytes. Final PASS
requires both the listener-owning process identity and the separately computed
installed product-tree/launcher binding.

### Machine-readable taxonomy

The helper emits bounded canonical JSON with schema:

```text
decision-os.companion-process-qualification.v0.1
```

Its fail-closed result taxonomy includes:

```text
PASS
RUNTIME_LISTENER_MISSING
RUNTIME_LISTENER_MULTIPLE_OWNERS
RUNTIME_PROCESS_MISSING
RUNTIME_PROCESS_EXECUTABLE_MISMATCH
RUNTIME_PROCESS_COMMAND_MISMATCH
RUNTIME_PROCESS_MODULE_MISMATCH
RUNTIME_PROCESS_PARENT_AMBIGUOUS
RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE
RUNTIME_ROOT_MISSING
RUNTIME_PRODUCT_TREE_MISMATCH
RUNTIME_LAUNCHER_SOURCE_MISMATCH
RUNTIME_LAUNCHER_MODULE_MISMATCH
```

No broad environment or unrelated process data is emitted.

## Focused Test Control

The focused test file is:

```text
tests/test_companion_process_qualification.py
```

Test-file SHA-256 at validation:

```text
e4cd993551a47337f2c0066ad3ffada5d549086bf93f05a7472326a87f1181a5
```

The deterministic matrix proves:

- canonical expected Python plus `-m decision_os.companion` passes;
- no `runtime/run.py` launcher is required;
- another module is `RUNTIME_PROCESS_MODULE_MISMATCH`;
- another Python executable is
  `RUNTIME_PROCESS_EXECUTABLE_MISMATCH`;
- a listener owner with no surviving process is
  `RUNTIME_PROCESS_MISSING`;
- a matching non-owner cannot satisfy the listener binding;
- multiple listener owners fail closed;
- raw substring spoofing is `RUNTIME_PROCESS_COMMAND_MISMATCH`;
- malformed evidence is `RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE`;
- installed-tree mismatch blocks PASS;
- installed-launcher mismatch blocks PASS;
- absent listener and ambiguous applet parentage retain distinct codes;
- a launcher missing the canonical module blocks PASS.

The two explicit live-integration cases prove against the current installation:

- T12: the current canonical installed process passes without restart;
- T13: the authenticated surface remains protected and an unauthenticated
  request returns `401`.

## Current Installed Replay

The helper's bounded current replay returned:

```json
{"details":{"applet_parent_verified":true,"installed_launcher_sha256":"7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538","installed_product_tree":"c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5","listener_host":"127.0.0.1","listener_owner_pid":17368,"listener_port":64203,"module":"decision_os.companion"},"passed":true,"result":"PASS","schema":"decision-os.companion-process-qualification.v0.1"}
```

The observed PID and port are replay observations only. They are not embedded
as helper defaults or future authority.

## Product Boundary

| Product identity | Value |
| --- | --- |
| Implementation baseline | `83ea1d95df8cfe3f7eb041b85c50fcdc56058692` |
| Authorized product-code tree | `c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5` |
| Installed product-code tree | `c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5` |
| Installed launcher-source SHA-256 | `7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538` |
| Normalized app manifest | `0fb7c3414c45fe38215b484ccd775a7f0e5f5542e9b201fbba740e7e4c4780a3` |

No production file changed. No Companion build, installation, restart, or
runtime trust configuration change occurred.

## Validation

| Validation | Result |
| --- | --- |
| Focused helper suite with current installed replay | PASS — 16 tests |
| Current helper CLI replay | PASS |
| Current authenticated boundary / unauthenticated request | PASS — `401` |
| Relevant validation-tool suite | PASS — 7 tests |
| Full default discovery outside sandbox confinement | PASS — 1,154 tests, two declared live-integration skips |
| Python source compilation | PASS — 90 sources |
| Product-code tree unchanged | PASS — `c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5` |
| Historical protected identities | PASS |

The first confined full-discovery invocation could not bind ephemeral localhost
test servers and could not start its headless Chrome probes. It returned 29
`PermissionError` server-bind errors and two confined Chrome failures. The
identical full discovery was therefore rerun with the required local test
permissions and passed. No dependency, code, test, product, or runtime change
was made between those invocations.

## Historical Evidence

Proof 001 remains:

```text
Permanent FAIL — direct-write A1 path violation
Protected identity: UNAVAILABLE
```

Protected surviving identities remain:

| Evidence | SHA-256 |
| --- | --- |
| Proof 002 journal | `8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c` |
| Proof 002 anchor | `3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c` |
| Proof 003 journal | `d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1` |
| Proof 003 anchor | `0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc` |
| Proof 003 canonical typed readback | `e50e77ce318befcd24bf6057c02aeb15d56aedff76f8600983bc41bc4b313e2b` |

No historical evidence was rewritten, staged, moved, repaired, or
reinterpreted.

## Future Execution Authority

Future execution repository HEAD is:

```text
Exact merge commit of this Delta v0.3 PR, resolved only after merge.
```

The branch head and Draft PR are not live execution authority. Merge alone
creates no live authority.

After merge, a future cycle requires all of the following:

1. rerun final model-free P0 using the durable helper;
2. bind the exact Delta v0.3 merge commit;
3. obtain a new, explicit Shin live authorization.

No later repository commit may be substituted without another bounded
requalification or forward-only Charter delta.

## Claim Boundary

This Delta claims only that the stale thread-local process expectation was
diagnosed, a durable model-free listener-owner/process/runtime qualification
control was added, and the current installed canonical Companion passed that
control without restart.

It does not claim:

- Cycle 002 success or eligibility for continuation;
- creator-live proof success;
- model-facing protocol acceptance;
- portability or cross-model/cross-repository equivalence;
- Warehouse eligibility;
- release or publication authority;
- `PROMOTABLE` status.

Zero product/runtime model invocations occurred. No proof-attempt identity,
Run, Note, proof journal, or proof anchor was created.

## Gates

Process guard repair:

```text
PASS
```

Delta v0.3:

```text
HOLD — independent review and merge required
```

Live Proof Gate:

```text
BLOCK
```

Warehouse / Release Gate:

```text
BLOCK
```
