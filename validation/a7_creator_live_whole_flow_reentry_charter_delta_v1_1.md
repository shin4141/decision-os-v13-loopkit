# V13 Creator-Live Cycle 006 Forward-Only Runtime Migration Charter Delta v1.1

Status: `AUTHORIZED — bounded Forward-only implementation and Draft PR only`

Current Gate: `HOLD / RUNTIME MIGRATION NOT YET QUALIFIED`

## Purpose and Current Authority

This Delta is the explicit current authority for the smallest Cycle
006-specific Forward-only runtime migration. It authorizes only:

- binding Cycle 006 to the fixed preserved Codex artifact named below;
- adding fail-closed verification before proof opening and task transmission;
- focused fake/fixture tests and non-live static qualification; and
- one Draft PR for review.

It does not authorize merge, Companion build or install, Contract refix,
fresh-process production qualification, exact P0, proof opening, live start,
model invocation, task transmission, Candidate execution, retry, replacement,
publication, release, or external claims.

This Delta is additive after
`validation/a7_creator_live_whole_flow_reentry_charter_delta_v1_0.md`, SHA-256
`9e05844eaed474ee9197245986d1a2fb5a877cbef5e0baa6f53e26952932cd3f`.
Every earlier Creator-Live Charter and Delta remains historical and
byte-immutable.

Field Note 129 is advisory origin evidence only. Its lifecycle remains
`Verification pending` and its Canon promotion remains `HOLD`. It did not
authorize this migration or this Charter change. The bounded 13-91
responsibility transfer and this Delta supply the present implementation
authority.

## Historical Runtime As-of Remains Valid

PR #36 recorded completed creator-owned live evidence under the runtime
observed at that time:

```text
Observed path:
/Applications/ChatGPT.app/Contents/Resources/codex

Observed runtime:
codex-cli 0.146.0-alpha.3.1

Observed execution identity:
gpt-5.6-sol / ultra / priority / codex-cli 0.146.0-alpha.3.1
```

The validation record was introduced by
`9a441bce42abcec1f6385ce9bbe36dfb818d398e` and merged by PR #36 at
`e6e2ba7a1be8612eb781c565c7c2bb9d012b129d`.

That evidence remains valid under its original As-of because it records the
runtime identity observed for those completed Runs. A later change at the same
application path does not retroactively change, invalidate, replace, or
reinterpret the earlier observation. This Delta does not assert that all
historical Codex activity used the new artifact.

## Why the Historical Artifact Cannot Be Recovered

The exact `0.146.0-alpha.3.1` executable is not locally or canonically
recoverable as an artifact. The mutable ChatGPT application path later
reported `0.147.0-alpha.1.2`, and a bounded read-only search found no locally
recoverable executable reporting the earlier version.

No preserved old binary, binary SHA-256, content-addressed custody object,
authoritative package or archive, or exact recovery route was established.
The historical bytes and SHA-256 therefore remain `UNKNOWN`. This is not a
claim about a particular destructive cause or updater. It is a bounded custody
finding: the observation survived as evidence, while the executable did not
survive as a rerunnable fixed object.

The unavailable historical artifact must not be reconstructed, substituted,
or treated as a PATH-resolved future prerequisite.

## New Forward-Only Runtime As-of

The new Cycle 006 runtime identity is fixed Forward-only as follows:

| Field | Exact value |
| --- | --- |
| Migration As-of | `2026-08-07` |
| Artifact custody recorded at | `2026-08-06T15:38:01Z` |
| Codex CLI | `0.147.0-alpha.1.2` |
| Binary SHA-256 | `9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481` |
| Size | `275653216` bytes |
| Mode | `0755` |
| File type | regular executable |
| Symlink | `false` |

Preserved executable:

```text
/Users/sn/Library/Application Support/Decision OS Companion/runtime-artifacts/codex/9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481/codex
```

Recovery receipt:

```text
/Users/sn/Library/Application Support/Decision OS Companion/runtime-artifacts/codex/9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481/recovery-receipt.json
```

The receipt records custody only and did not itself authorize migration, P0,
a model invocation, task transmission, or proof creation. This Delta supplies
the current bounded migration authority.

The preserved content-addressed path is the sole Cycle 006 execution identity.
The mutable ChatGPT application path and PATH lookup are not Cycle 006
identities or fallbacks.

## Fixed Compatibility Assessment

Assessment verdict:

```text
PASS — FORWARD-ONLY MIGRATION QUALIFIABLE
```

The fixed no-turn assessment established protocol-level compatibility for:

- app-server startup and initialize;
- ChatGPT authentication;
- `gpt-5.6-sol` / `ultra` / `priority`;
- `thread/start` schema;
- experimental dynamic typed tools;
- read-only sandbox with model network `false`;
- `on-request` / user approval boundaries;
- fresh ephemeral threads;
- project-document isolation;
- runtime identity projection;
- unsupported-request fail-closed behavior; and
- schema-level terminal lifecycle handling.

No model turn, Candidate task, proof attempt, approval request, or file
mutation occurred during the assessment. The result is bounded to the fixed
Cycle 006 protocol surface; it does not establish broad runtime architecture,
live behavior, exact P0, or Cycle 006 execution.

## Fail-Closed Runtime Binding

Before any future model transmission, the production Cycle 006 route must
verify in this order:

1. the configured path equals the exact preserved path;
2. the path exists;
3. the artifact is a regular executable file;
4. the artifact is not a symlink;
5. the full binary SHA-256 equals the fixed SHA-256;
6. `<preserved-path> --version` exits `0`;
7. stdout is exactly `codex-cli 0.147.0-alpha.1.2` plus its final LF;
8. the adapter launches that exact absolute preserved executable;
9. no PATH fallback is available;
10. no ChatGPT application-path fallback is available; and
11. substitution fails before proof opening or task transmission.

Verification is repeated immediately before the adapter launches the
preserved executable so drift after proof opening still fails before task or
model transmission. The adapter may not discover or select another runtime.

## Protected Semantics Remain Unchanged

This migration changes no Candidate or proof meaning:

- Candidate v0.1 remains byte-immutable and historical;
- Candidate v0.2 identity, source, task pair, tools, Gates, and behavior suite
  remain unchanged;
- A1–A7, generated Witness, and A3 overlay semantics remain unchanged;
- proof schemas and proof identity derivation remain unchanged;
- Cycle 005 terminal evidence remains unchanged;
- the Ordinary User Path Contract and authority meanings remain unchanged;
- the P0 Gate order remains unchanged apart from the fixed runtime artifact
  prerequisite; and
- publication remains unauthorized.

Cycle 006 still permits exactly one future attempt, zero retries, zero
replacements, no resume after interruption, no alternate proof identity, and
no alternate proof root.

## Current Protected State

```text
Cycle 006: UNSTARTED
model invocation: 0
task transmission: 0
retry / replacement: 0 / 0
proof root: ABSENT
exact P0: NOT_RUN
live-start authority: ABSENT
artifact behavior: NOT_RUN
comparison result: NOT_ESTABLISHED
```

Compatibility `PASS` does not promote this state to live `GO`. The
live-start decision remains a separate Human Seat authority held by Shin.

## Rollback Boundary

Before merge, abandon the unmerged implementation. After a later merge but
before proof opening, use a normal Forward revert, rebuild and install the
exact revert, refix the unchanged Contract, and re-establish source/installed
equality and process qualification under separate authority.

Preserve the new custody artifact and receipt as historical evidence. Preserve
all Charter, Candidate, Cycle 005, and proof history. Never delete or rewrite
Cycle 006 proof storage.

Because the historical executable is unavailable, rollback returns Cycle 006
to safe `HOLD / NOT_READY`. It does not recreate a runnable
`0.146.0-alpha.3.1` artifact and does not permit PATH, ChatGPT application-path,
or version downgrade fallback.

If a future proof has opened, this rollback authority no longer applies to the
attempt. The attempt and its storage must remain preserved under the
one-attempt rule.

## Re-evaluation and Stop Conditions

Re-evaluate before any execution if any of these change or become uncertain:

- configured or preserved path;
- existence, regular-file type, executable mode, or symlink state;
- full binary SHA-256;
- version-probe exit status or exact stdout;
- recovery-receipt custody;
- app-server protocol or schema;
- ChatGPT authentication or model entitlement;
- fixed compatibility findings;
- Charter lineage; or
- any Candidate, A1–A7, Witness, proof, one-attempt, or authority invariant.

Return `HOLD` or `BLOCK` on drift or contradiction. Any later runtime version
or artifact requires another additive Forward-only Delta; do not edit this
Delta in place.

## Completion and Stop Boundary

This bounded migration is complete only when the minimum implementation,
v1.1 Delta, fail-closed tests, one full default discovery pass, static checks,
and one Draft PR are present.

Stop at Draft PR review with exact P0 `NOT_RUN`, Cycle 006 `UNSTARTED`, model
invocation and task transmission `0`, retry/replacement `0 / 0`, and proof root
`ABSENT`.

Next actor: `13-34 receiving AI`.
