# Field Note 057: External Repo Transfer Packet Minimum Input Contract

Date: 2026-06-15

## Purpose

This note records the minimum input contract required before V13 may create an External Repo Transfer Packet.

It uses:

- `field_notes/047_external_repo_transfer_packet.md`
- `field_notes/055_lane_recall_non_self_referential_task_proof.md`
- `field_notes/056_external_task_transfer_packet_decision_proof.md`

This is an input-contract note only.

It does not create the actual packet.

## Why the Contract Is Needed

Field Note 047 defined the External Repo Transfer Packet.

Field Note 055 showed that lane recall can route an external-work event toward transfer-packet consideration without touching an external repo.

Field Note 056 showed that a medium-or-larger external task shape may justify packet creation, but only as a bounded control step.

The missing rule is the minimum input required before packet creation itself may proceed.

Without that input contract, V13 could turn a vague external-task request into a packet too early, creating control bloat or implying permission to touch an external repo.

## Minimum Input Contract

Before V13 may create an External Repo Transfer Packet, the following inputs should be supplied or explicitly marked unknown.

Unknown critical inputs should force HOLD or CAP.

### 1. Repo Identity

Required:

- repo name
- local path or URL
- whether the repo is owned by Shin or external

Why:

The packet must know which repo it governs.

If the repo identity is missing, V13 must not create a repo-specific packet.

Default when missing:

```text
HOLD
```

### 2. Task Purpose

Required:

- what change or review is being considered
- why the task exists

Why:

The packet must preserve the task's reason, not just its proposed actions.

If purpose is vague, the packet may encode momentum instead of owner intent.

Default when missing:

```text
HOLD
```

### 3. Task Size Estimate

Required:

- tiny / small / medium / large
- whether more than one file or module may be touched

Why:

Transfer packets are not for tiny one-off checks.

They become useful when work is medium-or-larger, repeated, handed off, or likely to cross files/modules.

Default when missing:

```text
CAP
```

CAP limit:

```text
Classify task size only; do not create the packet or touch the repo.
```

### 4. Allowed Touch Surface

Required:

- files or directories that may be inspected
- files or directories that may be changed only with explicit authorization

Why:

External repo work becomes risky when inspection, planning, and modification blur together.

The packet must separate read permission from write permission.

Default when missing:

```text
HOLD
```

### 5. Do-Not-Touch Surface

Required:

- protected files
- config
- secrets
- release files
- production paths
- public surfaces
- any repo-specific owner constraints

Why:

The packet is a boundary object.

It must name the surfaces that future agents must not casually touch.

Default when missing:

```text
CAP
```

CAP limit:

```text
Create only a draft boundary list from explicit owner input; do not infer safe write surfaces.
```

### 6. Validation Expectation

Required:

- test/check commands if known
- validation evidence source if commands are unknown

Why:

External work without validation creates future recovery debt.

Unknown validation should force HOLD or CAP.

Default when missing:

```text
HOLD or CAP
```

Use HOLD if no validation path can be named.

Use CAP if one bounded read-only inspection can identify existing validation commands.

### 7. Rollback Expectation

Required:

- branch, commit, patch, or revert path if known
- expected rollback owner if rollback is not automated

Why:

Medium external work should not proceed without a way back.

Unknown rollback should force HOLD or CAP.

Default when missing:

```text
HOLD or CAP
```

Use HOLD if rollback is required but unknown.

Use CAP if one bounded read-only check can identify the branch/commit state.

### 8. Handoff Need

Required:

- whether another agent or session may need to continue
- what future agent must read first
- what evidence must survive the current chat

Why:

Transfer packets are justified by restartability and handoff value.

If no handoff or revisit is expected, a packet may be unnecessary.

Default when missing:

```text
CAP
```

CAP limit:

```text
Ask whether the task is expected to be revisited or handed off before creating the packet.
```

### 9. Known Dangerous Loops

Required:

- broad refactor
- dependency update
- test weakening
- silent formatting churn
- public/release change
- repo-specific loops that have caused prior trouble

Why:

The packet should prevent known loop hazards from becoming repeated damage.

Default when missing:

```text
CAP
```

CAP limit:

```text
List likely dangerous loops from the task shape, but mark them provisional until owner or repo evidence confirms them.
```

### 10. Gate Tendency

Required:

- GO / HOLD / CAP / BLOCK tendency for packet creation
- reason for the gate
- what the gate does and does not authorize

Rule:

- GO only if purpose, touch surface, validation, and rollback are clear.
- CAP if bounded but incomplete.
- HOLD if task purpose or authorization is unclear.
- BLOCK if the task requires unauthorized external repo modification.

Why:

The packet decision must not silently authorize external implementation.

GO for packet creation is not GO for repo modification.

## Missing Input Defaults

Missing input defaults:

| Missing input | Default gate | Reason |
| --- | --- | --- |
| Repo identity | HOLD | No repo-specific packet can be created without a repo. |
| Task purpose | HOLD | Purpose protects owner intent. |
| Task size | CAP | One bounded classification can recover this. |
| Allowed touch surface | HOLD | Write/read boundaries must not be inferred. |
| Do-not-touch surface | CAP | A draft boundary can be made only from explicit input. |
| Validation expectation | HOLD or CAP | Unknown validation must not be ignored. |
| Rollback expectation | HOLD or CAP | Unknown rollback must not be ignored. |
| Handoff need | CAP | Clarify expected reuse before adding packet weight. |
| Dangerous loops | CAP | Record provisional risks without claiming certainty. |
| Gate tendency | HOLD | The packet cannot proceed without an explicit gate. |

## When Packet Creation Itself Should HOLD

Packet creation should HOLD when:

- repo identity is missing
- task purpose is unclear
- owner authorization is missing
- allowed touch surface is unclear
- validation is required but no validation path is known
- rollback is required but no rollback path is known
- the request conflates packet creation with external repo modification
- the packet would become a substitute for owner decision

HOLD means:

```text
Do not create the packet yet; recover the missing contract input first.
```

## When Packet Creation May GO

Packet creation may GO when:

- repo identity is explicit
- task purpose is explicit
- task is medium-or-larger or otherwise handoff/revisit worthy
- allowed touch surface is explicit
- do-not-touch surface is explicit enough to protect the repo
- validation expectation is known or honestly marked as a packet gap
- rollback expectation is known or honestly marked as a packet gap
- packet creation is authorized as a control artifact only
- external repo modification remains explicitly unauthorized

GO means:

```text
Create the transfer packet only.
```

It does not mean:

```text
Modify the external repo.
Copy AGENTS.md.
Implement the external task.
Create automation.
Promote the packet rule to AGENTS.md.
```

## What Must Not Happen Before the Contract Is Satisfied

Before the input contract is satisfied, do not:

- modify any external repo
- create the actual transfer packet
- infer owner approval
- copy AGENTS.md into the external repo
- edit external repo instruction surfaces
- touch schemas, tests, config, secrets, env, deploy, CI, release, or public surfaces
- create automation, hooks, MCP, pluginization, or integration files
- rewrite README or public positioning surfaces
- promote lane recall or transfer-packet rules into AGENTS.md
- claim public readiness

The contract prevents packet creation from becoming hidden implementation.

## Boundary

This is an input-contract note only.

Do not create the actual transfer packet yet.

Do not modify any external repo.

Do not modify AGENTS.md.

Do not modify AGENTS.ja.md.

Do not modify README.md.

Do not modify CLAUDE.md.

Do not modify docs, schemas, examples, prompts, or USE_CASES.

Do not implement automation, hooks, MCP, pluginization, or external repo changes.

Do not promote anything to canonical yet.

Do not claim public readiness.

## V13 Signal

Signal:
🟢 BLUE / TRANSFER-PACKET-INPUT-CONTRACT-DEFINED
+
🟢 BLUE / MISSING-INPUT-DEFAULTS-RECORDED
+
🟢 BLUE / PACKET-GO-DOES-NOT-MEAN-REPO-GO
+
🟢 BLUE / EXTERNAL-REPO-SURFACE-PROTECTED
+
🟡 YELLOW / PACKET-NOT-CREATED-YET
+
🟡 YELLOW / DO-NOT-PROMOTE-TO-AGENTS-YET
+
🟡 YELLOW / NO-EXTERNAL-REPO-MODIFICATION
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The minimum input contract is recorded, but packet creation, external repo modification, canonical promotion, automation, and public-readiness claims remain unauthorized.

Next Loop Command:
Use this input contract when a concrete external repo task is supplied; create no transfer packet until required inputs are explicit.
