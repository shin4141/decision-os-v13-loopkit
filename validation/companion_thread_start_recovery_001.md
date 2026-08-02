# Companion `thread/start` Recovery 001

Date: 2026-08-02 JST

Branch: `codex/13-64-companion-thread-start-recovery`

Canonical base: `3b8a0f99c418707d0da53a3c03c0a48b4a1232b7`

## Integrity Before Diagnosis

- `HEAD` exactly matched the canonical base.
- The tracked worktree and index were clean.
- The only untracked repository file was the protected manual probe.
- Protected probe SHA-256:
  `f68b3a1f47136782cbb5ade4c4686724c2b877eaaffe52bdb81aa72ae19c6344`.
- Bundled executable version: `0.146.0-alpha.3.1`.

## Exact Original Boundary

The adapter initialized app-server with:

```json
{"capabilities":{"experimentalApi":false}}
```

It then sent `thread/start` with these top-level fields:

```text
approvalPolicy
approvalsReviewer
config
cwd
developerInstructions
dynamicTools
ephemeral
model
modelProvider
sandbox
serviceTier
```

The bounded settings were:

- approval policy: `on-request`;
- approval reviewer: `user`;
- sandbox: `read-only`;
- dynamic tool: exactly one typed `read_repository_text_file` function;
- model: `gpt-5.6-sol`;
- service tier: `priority`;
- reasoning effort: `ultra`, inside the thread config;
- ephemeral thread: `true`;
- model provider: `openai`;
- current working directory: the selected repository;
- inherited process environment, with Codex state resolved by app-server.

The nested config fields were `features`, `mcp_servers`,
`model_reasoning_effort`, and `plugins`. The feature block disabled `apps`,
`hooks`, `multi_agent`, `remote_plugin`, `shell_tool`, and
`skill_mcp_dependency_install`. MCP servers and plugins were empty. These
boundaries remained unchanged by the repair.

## Installed Protocol Evidence

The exact bundled executable generated both its stable and experimental JSON
Schema bundles. In the stable `ThreadStartParams` schema, `dynamicTools` was
absent. In the experimental schema, `dynamicTools` was present and its declared
function shape matched the adapter request. The same executable accepts the
client capability `experimentalApi` during `initialize`.

This establishes that the typed dynamic tool is an experimental app-server
surface in this installed runtime. Declaring it while explicitly declining the
experimental capability is internally incompatible.

## No-Turn Reproduction

Three of the maximum six permitted `thread/start` probes were used. Every
probe used:

- the exact bundled executable;
- a fresh isolated Git repository;
- a writable isolated Codex state directory;
- the same copied ChatGPT authentication identity;
- the exact adapter startup config and exact `thread/start` request;
- no `turn/start`, model task, Approval, or repository mutation.

| Probe | Single variable | Result | JSON-RPC | Bounded category | Process / transport | Repository |
|---|---|---|---|---|---|---|
| 1 | Original `experimentalApi=false` | Failed | `-32600` | invalid params / capability | clean exit / response received | unchanged |
| 2 | `experimentalApi=true` | Succeeded with a fresh thread identity | none | success | clean exit / response received | unchanged |
| 3 | Restored `experimentalApi=false` | Failed | `-32600` | invalid params / capability | clean exit / response received | unchanged |

The sanitized local app-server reason for probes 1 and 3 was:

```text
thread/start.dynamicTools requires experimentalApi capability
```

Account type remained `chatgpt`, the required model remained present in the
local model catalog, stderr did not contain a protocol, state, permission,
schema, or transport failure, and no transport closure caused the failure.

## Established Root Cause

`ROOT_CAUSE = INITIALIZE_CAPABILITY_MISMATCH`

The adapter declared the experimental `dynamicTools` field at `thread/start`
while its preceding `initialize` request explicitly advertised
`experimentalApi=false`. App-server therefore rejected the request with
JSON-RPC `-32600` before stateful model execution. Changing only that capability
to `true` made the same `thread/start` request succeed; restoring `false`
restored the failure.

The failure was not caused by the typed phase label, repository permissions,
Codex-state writability, process transport, authentication, model identity,
sandbox representation, Approval policy, service tier, or the nested feature
block.

## Forward-Only Repair

The compatibility repair changes only the initialization capability from
`false` to `true`. It does not remove the dynamic read tool or weaken the
read-only sandbox, network restriction, human Approval boundary, one-file
boundary, read-before-write requirement, exact item identity, unsupported-tool
fail-closed handling, or runtime identity checks.

The diagnostic repair retains only canonical bounded values:

- the existing canonical failure code, phase, reason, and action;
- one category from `jsonrpc_method_rejected`, `jsonrpc_invalid_params`,
  `state_or_filesystem`, `transport_or_process`, or `unknown`;
- an exact signed 64-bit JSON-RPC integer code when present;
- one known adapter protocol method when present.

Raw JSON-RPC messages, stderr, credentials, prompts, repository contents,
provider text, and private paths are not stored or projected. App-server error
and stderr text are reduced immediately to bounded categories. Malformed,
lookalike, subclassed, incomplete, or forged diagnostics still rebuild to the
canonical `unknown` diagnostic.

## Regression and Qualification Status

Focused adapter tests: PASS — 54 tests.

Companion controller tests: PASS — 27 tests.

Companion server/client and headless presentation tests: PASS — 35 tests.

Full repository suite: PASS — 690 tests.

Staged `git diff --check`: PASS after the validation record was added.

Post-repair isolated live `thread/start`: PASS.

The post-repair qualification copied the branch `decision_os` runtime into a
temporary runtime root and used a fresh committed Git repository plus a fresh
writable Codex state directory carrying only the same authentication identity.
The staged branch adapter advertised `experimentalApi=true`, received a fresh
thread identity from bundled app-server `0.146.0-alpha.3.1`, retained the exact
read-only request field set, model `gpt-5.6-sol`, service tier `priority`, and
ChatGPT account type, and sent no `turn/start`. The repository `HEAD`, status,
tracked-file hash, and absence of Decision OS acceleration state were unchanged.
App-server was terminated only by the qualifier's bounded close after the
successful response; no transport failure occurred.

The installed Companion app was not replaced.
