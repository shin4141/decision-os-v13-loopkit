# V13 Creator-Live Whole-Flow Re-entry Charter Delta v0.4

Status: `HOLD — independent review and merge required`

## Purpose

This Forward-only Delta records the canonical build, installation, and
model-free qualification of the merged PR #93 Creator-Live A2 exact-lineage
reconnect repair. It advances only the future implementation, installed-product,
and execution-identity boundary stated below.

It does not reopen, retry, replace, continue, repair into success, reinterpret,
or reclassify Cycle 003 or any earlier proof. It creates no live execution
authority.

## Parent Authority

| Authority | Identity |
| --- | --- |
| Parent Charter | `validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md` |
| Parent Charter SHA-256 | `84e65d12e7b7dd2c86204273c7dc96c16689580e3148f9a0beb2993fd7ee0585` |
| Delta v0.1 SHA-256 | `d34bf2f00de56b0869cc341ce0db65c2fa147ca8a824a81ccd2bde1a8cfe47fa` |
| Delta v0.2 SHA-256 | `da6347ee71512ab135ac0c418a7e6487adf243b0adaae89ee72f17774404ddc5` |
| Delta v0.3 SHA-256 | `8a221220281e100ca0fc0d42efccc530902250da04a32138ee0fbc5415e5f45c` |
| Delta v0.3 merge | `fd9ce80f7a1d2199400eacf280075e40ada686fa` |
| Proof 004 diagnosis merge | `c54bc464d9613f1ddb23553949c67336260a9236` |
| A2 repair merge / implementation baseline | `524214a923a8fb1c7d76f5b0ed083a8db0641692` |
| PR #93 repair head | `082bf7ac31c053ad780451160d4b3567569f335f` |
| PR #93 base | `c54bc464d9613f1ddb23553949c67336260a9236` |

Qualification fetched `origin` without merge or rebase. `origin/main`, the
detached source worktree HEAD, and the implementation baseline all resolved
exactly to `524214a923a8fb1c7d76f5b0ed083a8db0641692`. The source worktree was
clean before qualification and contained no untracked build input.

## Historical Boundary

Cycle 003 remains permanently:

```text
FAILED / A2_RECONNECT / A2_NOT_INJECTED
```

Its proof-attempt identity remains:

```text
proof_a7_creator_live_004_862c2f5cfdf7b134
```

Cycle 003 established A1. It did not establish A2. A3 through A7 were not
opened. The repair and this Delta do not reopen, retry, replace, continue, or
alter Cycle 003.

Protected Cycle 003 identities remained exact before and after installation:

| Evidence | SHA-256 |
| --- | --- |
| Captured Field Note | `dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446` |
| Proof journal | `af0906977646897fa6bb279f512372998404974a5b581070fe5e1e94f9fd4c4a` |
| Proof anchor | `349b3298379f88cd2ea62f454c486ac857bc71e16614b7e8de4906e802b80331` |
| Canonical typed readback | `3fb00c2c12ca9ccb83ae88a2b1ed7ddec9c0aa7de3028148169599aaef6e440f` |

Proofs 001 through 003 and Cycle 002 remain closed and unchanged. Proof 001's
protected identity remains `UNAVAILABLE`. Other surviving protected identities
remain:

| Evidence | SHA-256 |
| --- | --- |
| Proof 002 journal | `8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c` |
| Proof 002 anchor | `3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c` |
| Proof 003 journal | `d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1` |
| Proof 003 anchor | `0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc` |
| Proof 003 canonical typed readback | `e50e77ce318befcd24bf6057c02aeb15d56aedff76f8600983bc41bc4b313e2b` |

All three surviving proof runtimes read back durably terminal as `FAILED`; no
Creator-Live proof attempt was `OPEN`. No protected evidence was edited,
normalized, moved, staged, reconstructed, or rewritten.

## Exact Diagnosis

The independently reviewed diagnosis classification remains:

```text
A — EXACT-LINEAGE PINNING GAP ESTABLISHED
```

The exact A1 Field Note existed and was durably readable. Run 2 adapter
construction did not receive that exact A1 Note identity. The ordinary
relevance reconnect lane then evaluated the Note at score zero and correctly
returned `NO_MATCH`; Cycle 003 terminalized as
`FAILED / A2_RECONNECT / A2_NOT_INJECTED`.

This diagnosis is not a claim that the later repair succeeded live.

## Exact Repair Boundary

PR #93 changed exactly:

```text
decision_os/companion/field_notes_adapter.py
decision_os/companion/field_notes_controller.py
decision_os/companion/field_notes_creator_live_reconnect.py
decision_os/companion/field_notes_reconnect.py
tests/test_field_notes_creator_live_reconnect.py
```

The four changed or added production files have these exact source identities:

| File | SHA-256 |
| --- | --- |
| `decision_os/companion/field_notes_adapter.py` | `d3d043e41c96cf8629fdd297b65c8868f20324912f1a9f3732419b6ba714ee0a` |
| `decision_os/companion/field_notes_controller.py` | `5014014fac0cb38a4ee485d123ac28b8145d6a22e9f8e8415186d87046ddf15e` |
| `decision_os/companion/field_notes_creator_live_reconnect.py` | `f6c8eb17117289fdb7dc3e21004f025fde2ee06f785ea1c2edb12e94af5ece46` |
| `decision_os/companion/field_notes_reconnect.py` | `7aef1a3d6e72d6d85a8dc73ca6972a6db56a34f2955660283d96f6b4188c2a49` |

The qualified repair establishes these model-free controls:

- ordinary reconnect remains relevance-based and unchanged;
- score-zero ordinary input remains `NO_MATCH`;
- ordinary `_score()` and `prepare_field_note_reconnect()` are byte-for-byte
  function-source identical to the previous implementation baseline;
- Creator-Live A2 uses an immutable exact-lineage target issued only from
  verified durable readback after Run 2 opening;
- the target binds proof, Run 1, Run 2, Note ID, exact path, full SHA-256, byte
  count, repository, commit, and runtime identity;
- exact preparation occurs before transport and thread construction;
- exact failure constructs no transport and invokes no model;
- no alternate Note scan, relevance score, or fallback is allowed;
- exact success injects one and only one Note envelope;
- existing `record_a2_reconnect()` durable admission is reused;
- missing, changed, invalid, symlinked, cross-proof, cross-Run,
  cross-repository, cross-commit, path, ID, SHA, byte-count, and read-race
  mismatches fail closed at A2;
- A1 and Creator-Live A2 modes are mutually exclusive; and
- exact failure leaves A3 through A7 unopened.

No journal, anchor, typed-readback, A7-admission, A1-capture, diagnostic,
ordinary-threshold, or durable proof schema changed.

## New Product Boundary

| Product identity | Value |
| --- | --- |
| Implementation baseline | `524214a923a8fb1c7d76f5b0ed083a8db0641692` |
| Source product-code tree | `3caeb6eddc4f302832d9b85e1b85a28da602a36ccdb7b1b156d5e540c6d26107` |
| Installed product-code tree | `3caeb6eddc4f302832d9b85e1b85a28da602a36ccdb7b1b156d5e540c6d26107` |
| Source product file count | `52` |
| Installed/source byte equivalence | `PASS` |
| Normalized app-bundle manifest | `0fb7c3414c45fe38215b484ccd775a7f0e5f5542e9b201fbba740e7e4c4780a3` |
| Installed canonical launcher-source SHA-256 | `7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538` |
| Installed applet executable SHA-256 | `00307012dac37c6cb090ad1cb0e3423900ed63c5599accb41e56180d60f7c4c5` |
| Durable process-helper SHA-256 | `77837c301495ddc6c49854223d015328c40b45add77bde4b380ebb2425373e61` |
| Expected Python launcher | `/opt/homebrew/bin/python3` |

The product-code tree is the SHA-256 of canonical rows for every regular file
under `decision_os`, excluding `__pycache__` and `*.pyc`, rejecting symlinks,
and sorting repository-relative UTF-8 paths. Each row is the file SHA-256,
two spaces, its path relative to the product root, and a newline.

The normalized app manifest is the SHA-256 of the same sorted regular-file
hash rows relative to the app-bundle root, with each relative path prefixed by
`./`. The eight-file manifest retained the prior authorized identity.

## Canonical Build, Installation, and Runtime

The pre-install installed product tree exactly matched its declared prior
identity:

```text
c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5
```

The only build and installation command was:

```text
./scripts/build_companion_app.sh
```

It ran from the clean exact-merge worktree. No product file was manually
copied or substituted. The canonical installer retained these rollback copies:

```text
/Users/sn/Applications/Decision OS Companion.app.backup.20260805085837
/Users/sn/Library/Application Support/Decision OS Companion/runtime.backup.20260805085837
```

The runtime backup reproduces the prior product tree exactly, and the app
backup reproduces the prior normalized app manifest exactly. Older backups
were not deleted.

After canonical relaunch, the bounded observed runtime identity was:

| Runtime evidence | Observation |
| --- | --- |
| Authenticated root | `PASS` — `Decision OS Companion` loaded at the bounded localhost root |
| Unauthenticated `/api/state` | `401` |
| Listener count | one |
| Listener host/port | `127.0.0.1:53804` |
| Applet PID | `78200` |
| Listener-owning runtime PID | `78212` |
| Runtime argv | exact `<authorized Python> -m decision_os.companion` |
| UI Task / Run | `Not started` / `Not started` |

The PID and port are installation-time observations, not future hard-coded
authority.

The merged durable helper emitted:

```json
{"details":{"applet_parent_verified":true,"installed_launcher_sha256":"7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538","installed_product_tree":"3caeb6eddc4f302832d9b85e1b85a28da602a36ccdb7b1b156d5e540c6d26107","listener_host":"127.0.0.1","listener_owner_pid":78212,"listener_port":53804,"module":"decision_os.companion"},"passed":true,"result":"PASS","schema":"decision-os.companion-process-qualification.v0.1"}
```

This binds the installed tree, installed launcher bytes, exact Python/module
argv, single listener ownership, and applet parent. No runtime trust or model
configuration was altered.

## Model-Free Qualification

All qualification used deterministic temporary repositories, fake transports,
or static/process inspection. No product/runtime model was invoked.

| Qualification | Result |
| --- | --- |
| Pre-install focused A1/A2/ordinary/controller/Creator-Live set | `PASS` — 220 tests, 1 declared local-artifact skip |
| Source exact-lineage plus ordinary reconnect | `PASS` — 48 tests, 1 declared local-artifact skip |
| Installed-package exact-lineage plus ordinary reconnect | `PASS` — the same 48 tests, 1 declared local-artifact skip |
| A2 through A7 focused regression | `PASS` — 351 tests, 2 declared local-artifact skips |
| Exact controller/server suite | `PASS` — 62 tests |
| Full default discovery | `PASS` — 1,166 tests, 5 declared skips, 412.837 seconds |
| Full explicit discovery | `PASS` — 1,166 tests, 5 declared skips, 427.370 seconds |
| Normalized test-ID equality | `PASS` — 1,166 equals 1,166; no one-sided IDs |
| Normalized test-ID SHA-256 | `e6a23ab7415ffef057a7858c4c3e921cc74b7cde09187bc7dfb7c9cad6038992` |
| Python compilation | `PASS` |
| `git diff --check` | `PASS` |

The installed test process imported `decision_os` from:

```text
/Users/sn/Library/Application Support/Decision OS Companion/runtime/decision_os/__init__.py
```

It imported only the unchanged test harness from the clean source worktree;
no source product file was copied over the installed runtime.

The five full-suite skips were explicit rather than silent omissions:

- three tests require local-only protected Creator-Live artifacts that are
  deliberately absent from the clean detached source worktree;
- two live-integration tests require explicit environment enablement for the
  current installed process and unauthenticated endpoint. Their exact controls
  were exercised directly by the durable helper and the bounded `401` probe.

One preliminary controller/server command appended the nonexistent module name
`tests.test_field_notes_server` to the two real repository modules. The 62 real
tests ran, followed by one loader error for that extra name. No product, test,
configuration, installation, or evidence change followed. The exact existing
controller/server invocation was then run and passed all 62 tests. This is
recorded as command-selection evidence, not as a product or suite failure.

## Future Execution Authority

Future execution repository HEAD is:

```text
The exact merge commit of the Delta v0.4 PR, resolved only after merge.
```

The repair merge and this Delta branch head are not live execution authority.
Merge alone creates no live authority. No later repository commit may be used
without a new bounded requalification or a separately reviewed Forward-only
Charter delta.

After merge, future live consideration requires all of the following:

1. a final model-free P0 at the exact Delta v0.4 merge commit;
2. exact installed runtime and fixed task-identity verification;
3. one new explicit Shin live authorization; and
4. a completely new cycle and proof-attempt identity.

Cycle 003 is not eligible for reuse, continuation, retry, reopening, or
replacement.

## Claim Boundary

This Delta claims only that the exact PR #93 implementation was model-free
qualified, canonically built and installed, source/installed byte identity was
established, the installed process passed the durable process helper, and the
exact-lineage A2 controls passed deterministic source and installed-package
qualification.

It does not claim:

- Cycle 003 success;
- A2 live success;
- A3 through A7 success;
- creator-live proof success;
- model-facing protocol acceptance;
- portability or cross-model/cross-repository equivalence;
- Warehouse eligibility or import authority;
- release or publication authority; or
- `PROMOTABLE` status.

No proof-attempt identity, Run, Field Note, proof journal, or proof anchor was
created. Zero product/runtime model invocations occurred.

## Gates

Installed A2 exact-lineage repair qualification:

```text
PASS
```

Charter Delta v0.4:

```text
HOLD — independent review and merge required
```

Live Proof Gate:

```text
BLOCK
```

Warehouse / Release / Publication Gate:

```text
BLOCK
```
