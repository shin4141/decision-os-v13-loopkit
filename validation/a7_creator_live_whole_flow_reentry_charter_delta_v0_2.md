# V13 Creator-Live Whole-Flow Re-entry Charter Delta v0.2

Status: `HOLD — independent review and merge required`

This is a forward-only delta. It records the model-free qualification of the
merged PR #89 implementation and its canonically installed Companion build. It
does not reopen, retry, replace, repair, or reclassify any historical proof.
It creates no authority for live execution.

## Parent Authority

Parent Charter:

`validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md`

Parent Charter SHA-256:

`84e65d12e7b7dd2c86204273c7dc96c16689580e3148f9a0beb2993fd7ee0585`

Prior forward-only Delta:

`validation/a7_creator_live_whole_flow_reentry_charter_delta_v0_1.md`

Prior Delta SHA-256:

`d34bf2f00de56b0869cc341ce0db65c2fa147ca8a824a81ccd2bde1a8cfe47fa`

This v0.2 delta advances only the forward implementation, installation, and
future execution-identity boundary stated below. Every other Parent Charter
and Delta v0.1 restriction remains binding.

## Forward-Only Implementation Identity

Diagnosis merge:

`0bb89d64c81b56e80f9cf9fd35dfdcf222a3f03d`

A1 repair merge and implementation baseline:

`83ea1d95df8cfe3f7eb041b85c50fcdc56058692`

PR #89 repair head:

`891fe9e367cea24b211551a83cfc2fa4c3406fdd`

Authorized source product-code tree:

`c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5`

Installed product-code tree:

`c1861df13861e562d82f95b36ba087e6bdb6da44d6faec53690f53303c8755a5`

The product-code tree is the SHA-256 of the sorted canonical manifest of every
regular file below `decision_os`, excluding `__pycache__` directories and
`*.pyc` files. Each manifest row is the file SHA-256 plus repository-relative
path, using the same method that reproduces the previously authorized installed
tree `6da32a98d9a9f3b733c4536faecf8698dfde64e99629f2c1e9dac1cdc04818e9`.

Relevant implementation source identities:

| File | SHA-256 |
| --- | --- |
| `decision_os/companion/field_notes_model.py` | `fbdd9a0edfb31a44e1e12856a7703ced999550fd005cf5c140add8d7b21f9fbb` |
| `decision_os/companion/field_notes_adapter.py` | `d0f2f91dc04e80a75ce0b5723fbba86ffe5637182aa9371b2c414929de4c3862` |
| `decision_os/companion/field_notes_creator_live.py` | `41263cb2f0d491f9e13a4c586a8260113ff2b8ac08e63d2bd5c6885555e2c86b` |
| `decision_os/companion/field_notes_creator_live_capture.py` | `28229fe2832c7b87ad95d24c0d40ca4686d556bcf7545b19238d5990df8b0cea` |
| `decision_os/companion/field_notes_controller.py` | `fcdbf15ae458edc1b990dbef184bd3f44f4fb57e753238c652f16fb0f69985d6` |
| `decision_os/companion/controller.py` | `539a13344e37b47fdd8562ae447dc254e33840b14a8322f555c2671b17489f1a` |
| `decision_os/companion/field_notes_server.py` | `564ab25bfb5daaae379d28f0481255c4c4b0d4d693b722d95707405d1c6f82af` |
| `macos/DecisionOSCompanion.applescript` | `7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538` |

## Canonical Product Manifest

The 51-file product manifest is:

```text
decision_os/__init__.py
decision_os/__main__.py
decision_os/acceleration/__init__.py
decision_os/acceleration/claude_adapter.py
decision_os/acceleration/cli.py
decision_os/acceleration/codex_adapter.py
decision_os/acceleration/engine.py
decision_os/acceleration/model.py
decision_os/acceleration/store.py
decision_os/audit_delivery.py
decision_os/audit_delivery_text.py
decision_os/audit_gate.py
decision_os/audit_gate_text.py
decision_os/audit_link.py
decision_os/audit_link_text.py
decision_os/checks.py
decision_os/cli.py
decision_os/companion/__init__.py
decision_os/companion/__main__.py
decision_os/companion/controller.py
decision_os/companion/field_notes_adapter.py
decision_os/companion/field_notes_controller.py
decision_os/companion/field_notes_creator_live.py
decision_os/companion/field_notes_creator_live_capture.py
decision_os/companion/field_notes_maturity_commit.py
decision_os/companion/field_notes_maturity_ledger.py
decision_os/companion/field_notes_maturity_review.py
decision_os/companion/field_notes_model.py
decision_os/companion/field_notes_reconnect.py
decision_os/companion/field_notes_reuse.py
decision_os/companion/field_notes_server.py
decision_os/companion/field_notes_whole_flow.py
decision_os/companion/guided_intake.py
decision_os/companion/intelligence_transplant.py
decision_os/companion/manual_bridge.py
decision_os/companion/ordinary_user_path.py
decision_os/companion/server.py
decision_os/companion/static/app.css
decision_os/companion/static/app.js
decision_os/companion/static/field_notes.css
decision_os/companion/static/field_notes.js
decision_os/companion/static/index.html
decision_os/handoff_acceptance.py
decision_os/intake.py
decision_os/intake_text.py
decision_os/intelligence_transplant.py
decision_os/public_claim_guard.py
decision_os/role_contract.py
decision_os/scan.py
decision_os/scan_text.py
decision_os/state.py
```

## Fixed Repair Behavior

The qualified and installed implementation is bounded Option A:

- the shipped model-facing Field Note schema advertises exactly value levels
  `[1, 2]` under both `UNKNOWN / UNKNOWN` and `stronger / lower-cost`;
- Level 3 is not advertised or made model-visible;
- `UNKNOWN` remains fail-closed;
- Option B is deferred and is not authorized;
- the input-schema root contains none of `oneOf`, `anyOf`, `allOf`, `enum`,
  `const`, or `not`;
- every emitted Field Note tool spec and input schema is a fresh object;
- `FIELD_NOTE_TOOL_SPEC` is not mutated;
- Level 3 defense-in-depth rejects unavailable trust as
  `level_3_trust_not_configured`;
- Level 3 defense-in-depth rejects configured-versus-emitted disagreement as
  `level_3_trust_class_mismatch`;
- neither trust rejection enters `compile_draft()`;
- both trust-policy codes map to `A1_PROPOSAL_GATE_REJECTED`;
- genuine proposal/compiler invalidity remains `proposal_schema_invalid` and
  maps to `A1_PROPOSAL_SCHEMA_REJECTED`; and
- one-shot consumption, no-Note, and no-Run-2 behavior remains fail-closed.

Trust policy and schema/compiler terminal codes remain separate. No
model-facing Level 3 advertised/admitted parity is claimed.

## Source Qualification

Qualification ran model-free in a clean detached temporary worktree at exact
HEAD and `origin/main`
`83ea1d95df8cfe3f7eb041b85c50fcdc56058692`. No untracked source entered the
build. PR #89's exact changed-file boundary was:

```text
decision_os/companion/field_notes_adapter.py
decision_os/companion/field_notes_model.py
tests/test_field_notes_creator_live_capture.py
tests/test_field_notes_lite.py
```

Results:

| Qualification | Result |
| --- | --- |
| Exact PR #89 repair tests | PASS — 19 tests |
| `tests/test_field_notes_lite.py` | PASS — 45 tests |
| `tests/test_field_notes_creator_live.py` | PASS — 79 tests |
| `tests/test_field_notes_creator_live_capture.py` | PASS — 21 tests |
| Focused A1 / creator-live qualification | PASS — included in the exact and full A1 sets above |
| A2-A7 focused regression | PASS — 296 tests, 3 declared skips |
| Companion controller/server regression | PASS — 62 tests |
| Full default discovery | PASS — 1,138 tests, 3 declared skips, 398.255 seconds |
| Python compilation | PASS — 87 source files |
| `git diff --check` | PASS |
| Final source tracked worktree/index | clean |

No product/runtime model was invoked by any qualification.

## Backup, Build, Install, and Restart

Pre-install installed product-code tree:

`6da32a98d9a9f3b733c4536faecf8698dfde64e99629f2c1e9dac1cdc04818e9`

Exactly these product files differed from the authorized source before install:

```text
decision_os/companion/field_notes_adapter.py
decision_os/companion/field_notes_model.py
```

The normalized app-bundle manifest SHA-256, computed from sorted regular-file
hash rows relative to the app-bundle root, was unchanged across install:

`0fb7c3414c45fe38215b484ccd775a7f0e5f5542e9b201fbba740e7e4c4780a3`

Explicit pre-install backups:

```text
/Users/sn/Applications/Decision OS Companion.app.pre-pr89-backup.20260805T003429+0900
/Users/sn/Library/Application Support/Decision OS Companion/runtime.pre-pr89-backup.20260805T003429+0900
```

The explicit runtime backup reproduces the pre-install product tree exactly,
and the explicit app backup reproduces the normalized app manifest exactly.

The canonical installer also retained its normal rollback copies:

```text
/Users/sn/Applications/Decision OS Companion.app.backup.20260805003508
/Users/sn/Library/Application Support/Decision OS Companion/runtime.backup.20260805003508
```

The only build/install procedure used was:

`./scripts/build_companion_app.sh`

It ran from the clean exact-merge worktree. No individual source file was
manually copied or substituted. The installed `decision_os` tree has no diff
from the authorized source tree, and the installed launcher source is
byte-identical to the authorized launcher source.

The old applet/runtime processes and loopback listener were stopped before the
new app was launched. The installed app restarted normally as a new applet and
Python runtime, exposed a new loopback listener, opened the authenticated
Companion root, and returned `401` to an unauthenticated request. No task was
started.

## Installed Model-Free Qualification

The installed module origin was verified below:

`/Users/sn/Library/Application Support/Decision OS Companion/runtime/decision_os/__init__.py`

The exact 19-test repair set and the machine-identity/wire-settings test were
rerun against the installed tree with only local fake transports. Both passed.
Deterministic installed replays established:

| Case | Gate result | A1 result | Compiler entered | Note saved | Run 2 |
| --- | --- | --- | --- | --- | --- |
| Default Level 3 trust | `level_3_trust_not_configured` | `A1_PROPOSAL_GATE_REJECTED` | no | no | blocked |
| Configured/emitted class mismatch | `level_3_trust_class_mismatch` | `A1_PROPOSAL_GATE_REJECTED` | no | no | blocked |
| Genuine invalid proposal | `proposal_schema_invalid` | `A1_PROPOSAL_SCHEMA_REJECTED` | not applicable | no | blocked |

Installed schema inspection returned `[1, 2]` for both qualified trust inputs,
an empty intersection with the prohibited root keywords, fresh independent
tool-spec/schema objects, and an unchanged base tool spec.

No stale PR #82, PR #85, or pre-PR #89 product file remains: the complete
installed product tree is exactly equal to the authorized source tree.

The exact future runtime configuration remains statically identifiable without
invocation:

| Field | Fixed identity |
| --- | --- |
| Account | ChatGPT (`chatgpt`) |
| Provider | `openai` |
| Model | `gpt-5.6-sol` |
| Reasoning effort | `ultra` |
| Service tier | `priority` |
| Codex CLI/app-server | `0.146.0-alpha.3.1` |
| Sandbox | `read-only` |
| Approval/reviewer | `on-request` / `user` |
| Thread | fresh and ephemeral |
| Working directory | canonical selected repository |
| Model-affecting plugins, MCP servers, shell, hooks, apps, multi-agent | disabled |

This identity was inspected and replayed with a fake transport only. The
bundled Codex executable was not started.

## Historical Proof Boundary

Proof 001 remains:

`Permanent FAIL — direct-write A1 path violation`

Its protected identity status remains:

`UNAVAILABLE`

Proof 002 remains permanently failed. Its protected identities remain:

| Evidence | SHA-256 |
| --- | --- |
| Journal | `8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c` |
| Anchor | `3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c` |

Proof 003 remains permanently failed. Its protected identities remain:

| Evidence | SHA-256 |
| --- | --- |
| Journal | `d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1` |
| Anchor | `0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc` |
| Canonical typed readback | `e50e77ce318befcd24bf6057c02aeb15d56aedff76f8600983bc41bc4b313e2b` |

The identities were verified before and after installation. The protected
artifacts were not rewritten, staged, moved, deleted, reconstructed, or
repaired. PR #89 is a forward-only control repair, not proof success. No retry,
reopening, replacement, or evidence repair occurred.

## Future Execution Identity

Future execution repository HEAD:

`Exact merge commit of this Delta v0.2 PR, resolved only after merge.`

After this delta PR exists, no live execution may use
`83ea1d95df8cfe3f7eb041b85c50fcdc56058692` directly as execution authority.
No later commit may be substituted without a new bounded requalification or a
separately reviewed Charter delta.

After this delta is merged, a fresh model-free P0 qualification must bind its
exact merge commit. Only after that qualification passes may Shin provide a new
and explicit live authorization.

This task created no proof-attempt identity. It made zero product/runtime model
invocations and created no Run or Note.

## Gates

Installed repair qualification:

`PASS`

Charter Delta v0.2:

`HOLD — independent review and merge required`

Live Proof Gate:

`BLOCK`

Warehouse / Release Gate:

`BLOCK`

No proof-attempt identity exists. No model invocation occurred. No Run or Note
exists from this qualification.

## Claim Boundary

This delta claims only that the exact PR #89 source tree was model-free
qualified, canonically built, installed, restarted, and model-free qualified in
the bounded environment recorded above. It does not claim live model protocol
acceptance, creator-live proof success, Level 3 availability, portability,
cross-model equivalence, cross-repository equivalence, Warehouse eligibility,
release readiness, publication authority, or `PROMOTABLE` status.
