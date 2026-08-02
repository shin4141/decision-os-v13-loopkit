# Companion Repository Read Recovery 001

Date: 2026-08-02 JST

Branch: `codex/13-67-companion-repository-read-recovery`

Canonical base: `85546d82aa09bd49a0dc469ff4b1008e8add47ff`

## Integrity Before Diagnosis

- Local `main` exactly matched the canonical base.
- The tracked worktree and index were clean.
- The only untracked repository file was the protected manual probe.
- Protected probe SHA-256:
  `f68b3a1f47136782cbb5ade4c4686724c2b877eaaffe52bdb81aa72ae19c6344`.
- The installed runtime source matched the canonical checkout byte for byte,
  excluding generated Python cache files.
- Installed bundled executable version: `0.146.0-alpha.3.1`.

The installed app was inspected but was not replaced or restarted. No new live
model task was started.

## Captured Live Request and Receipt

The failed live turn used:

- thread: `019fc147-2f85-78f1-a077-ccd4a7888438`;
- turn: `019fc147-3022-78e3-ad11-0bfc683ebaaa`;
- call: `exec-66413325-bcb1-43fd-969b-c410a3f51ec3`;
- JSON-RPC request id: integer `0`;
- tool: `read_repository_text_file`;
- arguments:
  `{"path":"validation/companion_thread_start_recovery_001.md"}`.

The local structured app-server log retained the model's exact composed call:

```text
const r = await tools.read_repository_text_file({path:"validation/companion_thread_start_recovery_001.md"}); text(r);
```

The effective bounded request was:

```json
{
  "id": 0,
  "method": "item/tool/call",
  "params": {
    "arguments": {
      "path": "validation/companion_thread_start_recovery_001.md"
    },
    "callId": "exec-66413325-bcb1-43fd-969b-c410a3f51ec3",
    "threadId": "019fc147-2f85-78f1-a077-ccd4a7888438",
    "tool": "read_repository_text_file",
    "turnId": "019fc147-3022-78e3-ad11-0bfc683ebaaa"
  }
}
```

The exact wire distinction between an absent `namespace` field and an explicit
JSON `null` was not retained and is `UNKNOWN`. Its effective parsed value was
`None`; otherwise the adapter would have returned a failed response instead of
the captured successful response.

The installed Companion receipt recorded:

- read status: `succeeded`;
- path: `validation/companion_thread_start_recovery_001.md`;
- byte count: `6961`;
- SHA-256:
  `49bfe1977a5d8ac9e719b1fdd18631f7ade9d8b0fff550258760178d9d777471`;
- repository identity: `85546d82aa09bd49a0dc469ff4b1008e8add47ff`;
- Codex turn: completed;
- Approval: not started;
- file change: not established.

The source file in the canonical checkout has the same byte count and SHA-256.
The structured log retained Companion's JSON-RPC success response for request
`0`, followed by app-server `DynamicToolResponse`, `item/completed`, and tool
completion. It did not retain repository source content in this record.

## Exact Failure Point

The read path completed all of these gates successfully:

1. dynamic request identity and exact argument shape;
2. path normalization and traversal rejection;
3. exact started-item, thread, turn, call, tool, and argument binding;
4. canonical repository and regular-file binding;
5. 131,072-byte maximum and stable file identity checks;
6. strict UTF-8 decoding;
7. stable Git `HEAD` verification;
8. typed response construction and successful JSON-RPC response send.

Failure occurred later in dynamic `item/completed` validation. The adapter
required request `0` to appear in `_resolved_read_requests`. Before this repair,
that set was populated only by `serverRequest/resolved` notifications.

The captured app-server process emitted 78 outgoing events during the live
interval and zero `serverRequest/resolved` notifications. The installed schema
defines that notification separately from the dynamic-tool response. The
app-server protocol documents the dynamic-tool sequence as:

```text
item/started -> item/tool/call -> client response -> item/completed
```

It does not include `serverRequest/resolved`; that notification belongs to
pending approval and input-request lifecycles. The protocol reference is the
[official app-server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md#dynamic-tool-calls-experimental).

The successful read was therefore rejected as an unresolved request at
`dynamic_tool_call`, producing `CodexRuntimeIdentityError`. The controller then
projected the bounded repository-read failure, kept Approval unstarted, and did
not establish a file change.

## Causal Replay

A deterministic fake-transport replay used the captured thread, turn, call,
request id, exact relative path, exact 6,961 source bytes, exact source hash,
successful dynamic response, and no `serverRequest/resolved` notification. It
did not start a model task.

| Replay | Single condition | Result | Read | Approval / write |
|---|---|---|---|---|
| Original | Response does not mark request resolved | `ABNORMAL_TERMINAL`, `CodexRuntimeIdentityError`, phase `dynamic_tool_call` | succeeded | none / none |
| Minimal change | Mark request resolved immediately after its response is sent | `NORMAL_TERMINAL` | succeeded and completion accepted | none / none |
| Restored | Restore original response handling | Same failure as original | succeeded | none / none |

The replay repository remained byte-identical in every case.

## Established Root Cause

`ROOT_CAUSE = DYNAMIC_TOOL_RESPONSE_RESOLUTION_MISMATCH`

The adapter treated `serverRequest/resolved` as mandatory completion evidence
for a dynamic tool request. App-server resolves this request type with the
client's JSON-RPC response and proceeds directly to `item/completed`; it does
not emit that notification. The adapter consequently rejected a successful,
correctly bound bounded read after the filesystem operation and response had
already succeeded.

No other explanation is established. In particular, path rejection, wrong
item binding, file size, encoding, filesystem access, repository drift,
response failure, model failure, Approval, and file mutation are contradicted
by the captured successful response and receipt. The namespace wire-presence
detail remains `UNKNOWN` and is non-causal.

## Smallest Repair

After `_send_read_response` successfully sends a response for a valid string or
integer request id, it records that id as resolved. A later legacy
`serverRequest/resolved` notification remains harmless and idempotent.

No repository/path/item check was removed. The repair does not weaken the
read-only sandbox, network restriction, human Approval, one-file mutation
boundary, read-before-write requirement, unsupported-tool fail-closed behavior,
runtime identity verification, or private-path and source-content redaction.

## Regression Coverage

The new live-shape regression uses the captured ids and exact path, intentionally
omits `serverRequest/resolved`, and verifies a normal completed bounded read,
one successful read receipt, no Approval, no file action, no repository event,
and unchanged source bytes.

Existing adapter coverage retains rejection for malformed request shapes,
forged or changed request identity, a second or wrong-item read, absolute and
parent traversal, `.git` access, missing and non-regular files, symlink escape,
invalid UTF-8, a 131,073-byte file, repository/file identity drift, unsupported
tools, and mutation before a valid bound read. Controller coverage retains
sanitized public failure projection and forged-diagnostic downgrade behavior.

## Qualification Status

- Focused adapter tests: PASS — 57 tests in 12.667 seconds.
- Companion controller tests: PASS — 27 tests in 13.715 seconds.
- Companion server/client/headless tests: PASS — 35 tests in 65.787
  seconds.
- Full repository suite: PASS — 693 tests in 365.306 seconds.
- `git diff --check`: PASS.
- Protected probe recheck: PASS — SHA-256 remained
  `f68b3a1f47136782cbb5ade4c4686724c2b877eaaffe52bdb81aa72ae19c6344`.

The installed Companion was not changed. A next live task remains blocked until
the repair is independently reviewed, merged, installed, and runtime identity
is verified under separate authorization.
