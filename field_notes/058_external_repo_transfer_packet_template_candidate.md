# Field Note 058: External Repo Transfer Packet Template Candidate

Date: 2026-06-15

## Purpose

This note records a reusable candidate template for an External Repo Transfer Packet.

It uses:

- `field_notes/047_external_repo_transfer_packet.md`
- `field_notes/056_external_task_transfer_packet_decision_proof.md`
- `field_notes/057_external_repo_transfer_packet_minimum_input_contract.md`

This is a template candidate only.

It is not an actual transfer packet for a real repo.

## Template Status

Status:

```text
candidate
```

The template exists to test whether the External Repo Transfer Packet concept can be made reusable without becoming implementation, automation, or canonical AGENTS.md routing.

It should not move into docs or AGENTS.md until it has been used on at least one concrete external repo task and shown to reduce restart risk without creating control bloat.

## Candidate Template

````md
# External Repo Transfer Packet: <target repo / task>

Packet Status:
<draft / active / superseded>

## 1. Packet Identity

Packet date:
<YYYY-MM-DD>

Source V13 repo:
<path or URL to V13 control-room repo>

Target repo name/path/URL:
<repo name>
<local path or URL>

Repo ownership:
<owned by Shin / external / unknown>

Packet owner:
<owner name or role>

Intended future agent/session:
<who or what should use this packet next>

## 2. Task Purpose

Task summary:
<one short summary>

Why this task exists:
<owner goal / problem / trigger>

Intended outcome:
<what should be true after the task>

Non-goals:
- <what must not be done>
- <what is explicitly out of scope>

## 3. Current Known State

Repo status if known:
<clean / dirty / behind / unknown>

Branch / commit if known:
<branch and commit>

Working tree status if known:
<status summary>

Known constraints:
- <constraint>
- <constraint>

Unknowns:
- <unknown>
- <unknown>

## 4. Allowed Touch Surface

Allowed for inspection:
- <file or directory>
- <file or directory>

Allowed for edits only with explicit authorization:
- <file or directory>
- <file or directory>

Notes:
<read/write distinction or owner condition>

## 5. Do-Not-Touch Surface

Do not touch:
- secrets
- production/release files
- public surfaces
- configs
- unrelated modules
- tests that would weaken validation
- <repo-specific protected surface>

Any change to these surfaces requires explicit owner approval before work begins.

## 6. Validation Plan

Known commands:
```text
<command>
<command>
```

Manual checks if needed:
- <manual check>
- <manual check>

Unknown validation handling:
<HOLD / CAP condition if validation is unknown>

Evidence required before continuing:
- <evidence>
- <evidence>

## 7. Rollback Plan

Known rollback path:
<branch / revert / patch / restore path>

Fallback if rollback is unknown:
<HOLD / CAP condition>

Rollback owner:
<owner / future agent / unknown>

Do not proceed to implementation if rollback is required but unknown.

## 8. Dangerous Loops

Watch for:
- broad refactor
- dependency update
- test weakening
- silent formatting churn
- scope creep
- public/release modification
- <repo-specific loop risk>

Loop gate:
<GO / CAP / HOLD / BLOCK conditions for repeated work>

## 9. Gate Conditions

GO:
<conditions under which the future agent may proceed>

CAP:
<bounded action and concrete limit>

HOLD:
<missing input, owner decision, validation, rollback, or authority issue>

BLOCK:
<forbidden surface, unsafe task, unauthorized modification, or hidden-assumption risk>

Important:
GO for this packet does not authorize unrelated repo modification.

## 10. Handoff Requirements

Future agent must read first:
- <file / note / task description>
- <file / note / task description>

Evidence required before continuing:
- <evidence>
- <evidence>

After work, report:
- what changed
- what was verified
- what was not touched
- remaining risk
- exact next action

Restart condition:
<what makes the task restartable after interruption>

## 11. Packet Boundary

This packet is a control surface, not implementation approval.

Packet creation does not authorize repo modification.

Packet use must stay bounded to the stated task.

Do not use this packet to:
- copy AGENTS.md into the repo
- broaden the task
- create automation
- change public/release surfaces
- weaken tests
- promote V13 rules into canonical repo instructions
- claim the repo is safe or complete without evidence
````

## How This Template Uses Field Note 047

Field Note 047 defined the transfer packet as a control capsule for medium-or-larger external repo work.

This template preserves that idea by making the packet:

- repo-specific
- task-specific
- bounded
- restartable
- explicit about validation and rollback
- explicit about what must not be touched

The template is not meant to be a second repo handbook.

It is meant to preserve the control delta that would otherwise die with the chat.

## How This Template Uses Field Note 056

Field Note 056 showed that packet creation may be CAP even when external repo modification is not authorized.

This template preserves that distinction:

- creating the packet is a possible control step
- modifying the external repo remains a separate decision
- GO for packet creation is not GO for implementation
- external repo files stay protected until authorization is explicit

## How This Template Uses Field Note 057

Field Note 057 defined the minimum input contract.

This template turns that contract into fillable sections:

- repo identity
- task purpose
- current known state
- allowed touch surface
- do-not-touch surface
- validation expectation
- rollback expectation
- handoff need
- dangerous loops
- gate tendency

If these sections cannot be filled enough to protect the repo, packet creation should HOLD or CAP.

## Evidence Needed Before Docs or AGENTS Promotion

Evidence needed before this template could move toward docs or AGENTS.md:

- one actual external repo task where the template is filled from explicit inputs
- one actual external repo task where the template is rejected as unnecessary
- evidence that the template reduces restart risk or prevents a concrete mistake
- evidence that the template does not become default overhead for small tasks
- evidence that a future agent can use the packet without reading the whole field-note chain
- compact wording or routing that would not bloat AGENTS.md
- confirmation that packet use does not imply AGENTS.md copying or repo invasion

Current evidence:

```text
insufficient for promotion
```

## Why README / AGENTS Promotion Is Still HOLD

README promotion is HOLD because:

- public value is not proven
- no real external packet has been used yet
- the template may still be too heavy for ordinary readers
- the public entry path should not imply automatic external repo governance

AGENTS.md promotion is HOLD because:

- this is still a candidate template
- no compact canonical trigger has been tested
- field-note-level evidence is not yet enough
- premature routing could make AGENTS.md heavier
- packet creation must not become default behavior

The template may be reused in future field notes or concrete tasks, but it is not canonical.

## Boundary

This is a template candidate only.

Do not create an actual transfer packet for a real repo.

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
🟢 BLUE / TRANSFER-PACKET-TEMPLATE-CANDIDATE-RECORDED
+
🟢 BLUE / INPUT-CONTRACT-TURNED-INTO-FILLABLE-SHAPE
+
🟢 BLUE / PACKET-GO-NOT-REPO-GO-PRESERVED
+
🟢 BLUE / EXTERNAL-REPO-SURFACE-PROTECTED
+
🟡 YELLOW / TEMPLATE-CANDIDATE-ONLY
+
🟡 YELLOW / NO-REAL-PACKET-CREATED
+
🟡 YELLOW / DO-NOT-PROMOTE-TO-AGENTS-YET
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The transfer packet candidate template is recorded as a bounded field-note artifact, but it has not been used on a real external repo task and must not be promoted or treated as implementation.

Next Loop Command:
Use the candidate template only when a concrete external repo task satisfies the minimum input contract; otherwise keep packet creation HOLD or CAP.
