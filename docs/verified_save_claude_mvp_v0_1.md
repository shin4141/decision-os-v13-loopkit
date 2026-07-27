# Claude-first Verified Save MVP v0.1

## Product Objective

Verified Save records one local proof-of-use event when a coding agent reuses a
human-selected repository default in a later Run and passes a Wrapper-owned
checkpoint.

The visible result is simple: the coding agent asks the human one fewer repeated
question.

Claude Agent SDK is the first adapter. The protocol, event chain, counters, and
Receipt remain agent-agnostic.

## Install

From a local checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[claude]'
```

The Claude extra is optional and pinned:

```text
claude-agent-sdk==0.2.123
bundled Claude Code CLI: 2.1.215
```

The existing `decision-os` entry point is unchanged. Acceleration uses the
separate `decision-os-accelerate` entry point.

## Supported Decision Types

The fixed core enum is:

- `ADD_TESTS`
- `CREATE_FILE`
- `MODIFY_FILE`
- `DELETE_OR_RENAME`
- `ADD_DEPENDENCY`

The Claude v0.1 adapter verifies only mechanically typed `CREATE_FILE` and
`MODIFY_FILE` decisions:

- Claude `Edit` maps to `MODIFY_FILE`.
- Claude `Write` maps to `CREATE_FILE` when the normalized target did not exist
  before the request.
- Claude `Write` maps to `MODIFY_FILE` when the normalized target already
  existed.

Bash mutation, NotebookEdit, rename, delete, dependency intent, test intent,
semantic similarity, and prose classification are unsupported.

## Exact Verified Save Definition

A Verified Save exists only when all of the following are true:

1. A human explicitly selected `Use for this repository`.
2. A different `run_id` is active.
3. A structured `DECISION_CHECK` occurred.
4. The same mechanically derived `decision_key` reappeared.
5. The stored Repository Default is active.
6. `default.created_run_id != current run_id`.
7. The stored and matched `rule_hash` values are identical.
8. The second human interrupt was actually skipped.
9. A Wrapper-owned checkpoint passed.
10. No related override occurred before the checkpoint.
11. This is the first verified repository × decision pair.

The decision key is:

```text
dk:v1|<hashed repository_id>|<decision_type>|<normalized_scope>
```

The rule hash uses canonical JSON containing only:

```json
{
  "decision": "allow",
  "decision_type": "<fixed enum>",
  "normalized_scope": "<Git-root-relative path>",
  "protocol_version": "decision-os.acceleration.v0.1"
}
```

Prompt text, model identity, display questions, timestamps, and Run IDs never
enter the rule hash.

## Human Choice

Edit and Write are not auto-approved. The SDK callback displays:

```text
Your coding agent needs one default.

May it <create|modify> <normalized scope>?

[1] Allow once
[2] Use for this repository
[3] Deny
```

Only an explicit `2` creates `HUMAN_DEFAULT_CREATED`.

Invalid input, EOF, callback failure, unavailable stdin, or option `3` denies
the request. Option `1`, timeout, same-Run reuse, and absence of a question do
not create a Verified Save or increment a reuse counter.

## Run Boundary

Each `decision-os-accelerate run` invocation creates a new Wrapper `run_id` and
one fresh Claude SDK query.

The adapter sets:

- `continue_conversation=False`;
- no `resume` session;
- filesystem settings sources to `[]`;
- skills to `[]`;
- strict MCP configuration;
- `Read` as the only auto-approved tool;
- Edit and Write through `can_use_tool`;
- permission mode `default`.

The demo exposes only Read and Edit. It never enables Bash or a dangerous
permission-bypass mode.

## Checkpoint

The Wrapper owns checkpoint classification.

For this two-query MVP, a checkpoint passes only after the matched Default was
applied and the SDK emitted a non-error `ResultMessage` with subtype `success`.

Authentication errors, billing errors, API errors, cancellation, timeouts,
decode failures, process failures, a missing result, and error results remain
`PENDING`. Agent prose is not checkpoint evidence.

`CHECKPOINT_PENDING` is the one documented internal v0.1 event used to preserve
an abnormal terminal candidate without promoting it.

## Counters

The counters have different meanings:

- `verified_saves` is the number of unique repository × decision pairs that
  first reached `VERIFIED_SAVE`.
- `verified_reuses` is the total number of valid cross-Run uses that passed a
  checkpoint, including the first use that created each Verified Save.

Therefore:

- `VERIFIED_SAVE` increments both counters.
- `VERIFIED_REUSE` increments only `verified_reuses`.

All estimates use `verified_reuses`. Estimates are never unlock currency.

## Local Storage

State is local to the target Git repository:

```text
<git-common-dir>/decision-os/acceleration/v0.1/events.jsonl
<git-common-dir>/decision-os/acceleration/v0.1/config.json
```

`events.jsonl` is append-only and hash-chained with canonical JSON. The full
chain is verified before a Default is applied, a pending candidate is promoted,
counters are printed, or a Receipt is generated.

Chain corruption blocks reuse. The implementation does not truncate, repair,
or guess through invalid state.

The v0.1 store is single-writer only. Concurrent agent Runs against the same
store are unsupported and must be serialized by the caller.

## Privacy Boundary

The local event log contains mechanical protocol metadata, including the local
normalized scope. It does not contain:

- prompts or conversation bodies;
- code or file content;
- credentials;
- raw remote URLs;
- raw repository names.

Repository identity is hashed before storage. The outward Receipt uses a hashed
receipt identity and does not print normalized file paths, repository names,
raw remotes, prompts, or session identifiers.

No telemetry, server submission, OAuth, or external state service is used.

## Commands

Run one fresh Claude query:

```bash
decision-os-accelerate run \
  --adapter claude \
  --prompt-file examples/verified_save_demo/run_1.txt \
  --minutes-per-reuse 7.5 \
  --hourly-value-jpy 5000 \
  --tokens-per-reuse 9467 \
  /path/to/repository
```

Run the same mechanical decision in a separate invocation with a second prompt:

```bash
decision-os-accelerate run \
  --adapter claude \
  --prompt-file examples/verified_save_demo/run_2.txt \
  /path/to/repository
```

Print the current Receipt:

```bash
decision-os-accelerate receipt /path/to/repository
```

Revoke one active Default:

```bash
decision-os-accelerate revoke \
  --decision-key '<local decision key>' \
  /path/to/repository
```

Revocation after a checkpoint preserves the historical Verified Save and Reuse.
It prevents future application of the inactive Default.

## Live Demo

The fixed demo prompts are:

- [Run 1](../examples/verified_save_demo/run_1.txt)
- [Run 2](../examples/verified_save_demo/run_2.txt)

Authenticate Claude first:

```bash
claude auth login
claude auth status
```

Then run:

```bash
decision-os-accelerate demo \
  --adapter claude \
  --tokens-per-reuse 9467
```

The command creates a disposable Git repository and an existing file, starts
two fresh Claude queries, and requires one explicit option-2 selection in Run 1.
Run 2 must reach the same normalized Edit scope without another human
interrupt. A sanitized Receipt is copied outside the disposable repository
before that repository is cleaned.

Deterministic fixtures cannot produce the live-proof classification or demo
GIF.

## Acceleration Receipt

Hard metrics and estimates are separated:

```text
VERIFIED

1 Save
1 Verified Reuse

ESTIMATED RECOVERED

7.5 minutes
¥625
9,467 tokens
```

The compact formula is:

```text
verified_reuses
× configured estimated minutes per reuse
× configured hourly value
× configured tokens per reuse
```

Minutes default to `7.5` per reuse and hourly value defaults to `¥5,000`.
Tokens remain `UNKNOWN` until explicitly configured. Changing estimate settings
does not rewrite or add Verified Save or Reuse events.

## Claim Boundary

Verified Save is a locally recorded proof-of-use event, not third-party
certification.

The Receipt may describe a local estimated result. It does not establish a
universal productivity result, measured percentage improvement, incident
prevention, or third-party verification.

## Rollback and State Removal

To stop future reuse of one Default, use `decision-os-accelerate revoke`.

For a full local reset:

1. Stop all acceleration Runs for the repository.
2. Resolve the exact Git common directory with
   `git rev-parse --git-common-dir`.
3. Preserve a backup if historical evidence is required.
4. Remove only its exact
   `decision-os/acceleration/v0.1/` child directory.

Full state removal is intentionally not automatic. It removes local event-chain
history and cannot be reconstructed from the outward Receipt.

Code rollback is a normal history-preserving revert of the implementation
commit. It does not silently delete repository-local acceleration state.

## Known Unsupported Cases

- same-Run Verified Save;
- concurrent writers;
- non-Git targets;
- repository-escaping or glob scopes;
- unsupported or changed Claude tool schemas;
- Bash-based file mutation;
- multi-file operations;
- rename and delete;
- semantic decision matching;
- automatic defaults;
- session resume;
- unsupported normal/abnormal result contracts;
- a live claim without two fresh authenticated SDK Runs and explicit human
  option 2.

## Deterministic Tests Versus Live Proof

The deterministic adapter validates protocol transitions without network,
Claude credentials, paid calls, or human input. It covers Save/Reuse
classification, abnormal terminals, overrides, revocation, supersession,
same-Run exclusion, corruption, unsupported scope, and Receipt math.

The live proof separately requires the pinned official SDK, Claude
authentication, two fresh queries, explicit human option 2, one skipped
interrupt, and a normal Wrapper checkpoint.

The current evidence classification is recorded in
[Validation Run 001](../validation/verified_save_claude_mvp_run_001.md).
