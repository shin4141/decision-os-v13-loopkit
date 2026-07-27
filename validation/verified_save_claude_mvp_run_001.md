# Verified Save Claude MVP — Validation Run 001

## Receipt Identity

```text
Packet:
V13-VERIFIED-SAVE-CLAUDE-MVP-001

Scope Amendment:
V13-VERIFIED-SAVE-CLAUDE-MVP-001-A1

Starting main:
3c9142692dfe60785a033b91ad7b6e5226712a93

Branch:
feat/verified-save-claude-mvp-v0-1

Validation date:
2026-07-27
```

## Classification

```text
LIVE_PROOF:
DELAY

DETERMINISTIC_ENGINE:
PASS

CLAUDE_ADAPTER:
PASS

DEMO_GIF:
NOT_CREATED
```

`CLAUDE_ADAPTER=PASS` means the pinned SDK API, permission options, typed tool
mapping, normal/error ResultMessage boundary, lazy optional import, and
fail-closed callback behavior passed implementation and deterministic adapter
tests.

It does not mean a live two-Run Verified Save occurred.

## Starting-State Receipt

The amended preflight passed before implementation:

- GitHub repository identity:
  `https://github.com/shin4141/decision-os-v13-loopkit`;
- local `main`, `origin/main`, fetched `main`, and remote `main`:
  `3c9142692dfe60785a033b91ad7b6e5226712a93`;
- implementation branch:
  `feat/verified-save-claude-mvp-v0-1`;
- implementation branch starting HEAD:
  `3c9142692dfe60785a033b91ad7b6e5226712a93`;
- remote implementation branch:
  absent before implementation;
- worktree and index:
  clean;
- GitHub CLI account:
  authenticated as repository owner;
- A1 added only
  `tests/test_decision_os_distribution.py` to the update allowlist.

The existing local branch was reused without recreation, reset, deletion, or
switching.

## Validated SDK Identity

The current official package was inspected from its PyPI wheel and sdist before
adapter implementation:

```text
Package:
claude-agent-sdk

Version:
0.2.123

Wheel:
claude_agent_sdk-0.2.123-py3-none-macosx_11_0_arm64.whl

Wheel SHA-256:
e333c7edd50dde407b366b1124370e18767fb366d3c5389440891e7417d3c1ca

Bundled Claude Code CLI:
2.1.215 (Claude Code)
```

The inspected API contract included:

- `ClaudeAgentOptions`;
- `can_use_tool(tool_name, input_data, context)`;
- `ToolPermissionContext.tool_use_id`;
- `PermissionResultAllow`;
- `PermissionResultDeny`;
- `ResultMessage.subtype`;
- `ResultMessage.is_error`;
- `ResultMessage.api_error_status`;
- Edit and Write `file_path` input;
- async-iterable streaming mode required for `can_use_tool`.

The committed optional dependency is pinned exactly to
`claude-agent-sdk==0.2.123`. The core package retains zero mandatory runtime
dependencies.

## Deterministic Engine Result

```text
Acceleration-specific tests:
25 / 25 PASS

Network:
not required

Claude credentials:
not required

Human input:
not required
```

The deterministic test boundary covered:

- canonical decision key and rule-hash reproducibility;
- hashed repository identity;
- exact path normalization;
- duplicate separator and `..` normalization;
- repository escape rejection;
- glob rejection;
- directory rejection;
- outside-root symlink rejection;
- append-only event hashing;
- previous-hash verification;
- chain-corruption fail-closed behavior;
- explicit option-2 Default creation;
- Allow-once exclusion;
- invalid/EOF/timeout-style exclusion;
- same-Run exclusion;
- cross-Run match;
- interrupt-skipped event;
- normal Wrapper checkpoint;
- abnormal terminal PENDING;
- first `VERIFIED_SAVE`;
- repeated `VERIFIED_REUSE`;
- pre-checkpoint override rejection;
- post-checkpoint revocation preservation;
- Default supersession preservation;
- separate Save and Reuse counters;
- estimate-setting independence;
- Receipt formula;
- token estimate UNKNOWN by default;
- outward Receipt privacy;
- missing optional extra behavior;
- unsupported Claude tool rejection;
- unsupported Claude input schema rejection;
- Write create/modify mapping from pre-request existence;
- isolated Claude settings and permission configuration.

## Full Regression

```text
Baseline before implementation:
166 / 166 PASS

Final full suite:
191 / 191 PASS

Protected v0.1 blobs and modes:
14 / 14 PASS

git diff --check:
PASS
```

The existing `decision-os` console mapping remains unchanged. The amended
distribution contract verifies the complete two-entry `project.scripts`
mapping rather than weakening the assertion to membership checks.

## Package and Entry-Point Validation

The final source built successfully with the pinned Flit backend:

```text
Wheel:
decision_os_v13_loopkit-0.2.0-py3-none-any.whl

Wheel SHA-256:
396e0c588fb8fe0db2d3ece3dd34523fa2bd2a12ddb640cc88556e1d2a069164
```

An isolated environment without the Claude extra passed:

```text
Core import:
PASS

claude_agent_sdk present:
no

decision-os-accelerate --help:
PASS / exit 0

decision-os-accelerate run without extra:
DELAY / nonzero / no traceback
```

An isolated environment with the Claude extra passed:

```text
decision_os import:
PASS

claude_agent_sdk version:
0.2.123

bundled Claude Code identity:
2.1.215 (Claude Code)

console entry-point import:
PASS
```

No package was published.

## Event-Chain and Privacy Result

The local state root is mechanically derived as:

```text
<git-common-dir>/decision-os/acceleration/v0.1/
```

The required state files are:

```text
events.jsonl
config.json
```

The implementation verifies the complete canonical JSON hash chain before
Default application, candidate promotion, counter reporting, and Receipt
generation.

Tests verified that outward Receipts contain no raw repository name, raw remote,
working path, or normalized target filename. The event model has no fields for
prompt text, conversation body, code body, file content, credentials, raw
repository name, or raw remote URL.

No telemetry or server submission was added.

## Live Proof Attempt

One bounded attempt used the installed official SDK and the bundled CLI in a
disposable Git repository.

Observed result:

```text
Run 1 normal terminal:
no

Human option-2 callback reached:
no

Repository Default created:
no

Run 2 started:
no

Verified Save:
no

Verified Reuse:
no
```

The bundled Claude CLI authentication check returned:

```text
loggedIn:
false

authMethod:
none

apiProvider:
firstParty
```

This is a recoverable authentication prerequisite, so the correct
classification is `LIVE_PROOF=DELAY`, not FAIL or PASS.

Exact re-entry condition:

```text
claude auth login
claude auth status

Required status:
loggedIn=true
```

Then run from an interactive terminal:

```bash
decision-os-accelerate demo \
  --adapter claude \
  --tokens-per-reuse 9467
```

The human must explicitly select option `2` in Run 1. No agent, fixture, timeout,
or automatic input may substitute for that selection.

## Receipt Example

The deterministic, privacy-safe rendering contract passed with:

```text
VERIFIED

1 Save
1 Verified Reuse

ESTIMATED RECOVERED

7.5 minutes
¥625
9,467 tokens

Calculated from:
1 verified reuse × 7.5 estimated minutes per reuse × ¥5,000 per hour
1 verified reuse × 9,467 configured tokens per reuse
```

This is deterministic engine evidence, not a live Proof-of-Use claim.

The renderer also includes:

```text
Verified Save is a locally recorded proof-of-use event, not third-party
certification.
```

## GIF Result

```text
DEMO_GIF:
NOT_CREATED
```

A GIF is conditional on a passing real live proof. No fabricated fixture visual
was substituted, so dimensions, duration, frame count, renderer identity,
source receipt identity, and GIF hash are not applicable.

## Exact File Boundary

The authorized boundary is 18 files:

### Create

1. `decision_os/acceleration/__init__.py`
2. `decision_os/acceleration/model.py`
3. `decision_os/acceleration/store.py`
4. `decision_os/acceleration/engine.py`
5. `decision_os/acceleration/claude_adapter.py`
6. `decision_os/acceleration/cli.py`
7. `tests/test_acceleration_engine.py`
8. `tests/test_acceleration_store.py`
9. `tests/test_acceleration_cli.py`
10. `tests/test_acceleration_claude_adapter.py`
11. `examples/verified_save_demo/run_1.txt`
12. `examples/verified_save_demo/run_2.txt`
13. `docs/verified_save_claude_mvp_v0_1.md`
14. `validation/verified_save_claude_mvp_run_001.md`

### Update

1. `pyproject.toml`
2. `tests/test_decision_os_distribution.py`
3. `docs/current_signal.md`
4. `handoff/current_codex_handoff.md`

The conditional GIF path was not created.

`README.md`, `AGENTS.md`, existing Runner source, release/version, tag, OAuth,
server, telemetry, pricing, public claim, and adjacent adapter surfaces remain
untouched.

## Git and Draft PR State

This section is completed only from actual post-push evidence in the closure
commit.

```text
Implementation commit:
PENDING INITIAL COMMIT

Closure commit:
PENDING CLOSURE COMMIT

Remote branch:
PENDING INITIAL PUSH

Draft PR:
PENDING CREATION

Merge:
NOT AUTHORIZED / NOT PERFORMED
```

These are explicit current facts at this validation stage, not planned-success
claims.
