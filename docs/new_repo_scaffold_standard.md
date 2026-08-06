# New Repo Scaffold Standard

## Purpose

A New Repo Capsule is a purpose-adaptive starter kit, not a copy of the V13
dictionary and not a fixed file checklist.

When a new repository or workspace is created, V13 must first establish what
that destination is for. It then transfers the universal operating core and
only the additional V13 guards that the destination makes relevant.

The intended shape is:

```text
Universal Core
+ destination-specific selected guards
+ reconnectable guidance when its trigger can occur
- unrelated V13 knowledge
```

Shortness is not success, and copying all V13 knowledge is not success. A
capsule succeeds when it gives the destination the necessary and sufficient
initial operating knowledge to make its relevant known failures harder to
repeat.

Creating this scaffold does not authorize implementation, outreach, public
posting, pricing, release, scraping, API use, automation, or target selection.

## Required Capsule Flow

Follow this order whenever creating a repository/workspace capsule. Do not
skip the fit decision by treating the universal minimum or the file structure
as the complete capsule.

### 1. Define the Destination and Purpose

Record:

- what the repository/workspace is intended to create;
- its main kinds of work;
- whether it may involve public surfaces, runtime code, APIs, external
  contact, automation, audit, data, or handoff; and
- material unknowns that could change which guard is needed.

This destination statement is the input to guard selection. It is not an
implementation authorization.

### 2. Transfer the Universal Core

Give every destination a concise active operating core. It must preserve:

- Decision Owner / Seat;
- authority and execution boundaries;
- V12 completion integrity before a V13 Gate;
- Missing Closure / `UNKNOWN` handling;
- handoff as responsibility transfer, including a receiving AI's ownership;
- routine cleanup ownership that must not be returned to the Decision Owner;
- the current Gate, next allowed action, and Completion Line when a current
  operating state exists.

This is the minimum common core, not an instruction to copy the whole source
`AGENTS.md` into the destination.

### 3. Perform the Repo-specific Capsule Fit Audit

Before finalizing the capsule, perform the
[Repo-specific Capsule Fit Audit](../templates/v13_build_capsule_minimum_contract.md#repo-specific-capsule-fit-audit).

Starting from the stated destination, inspect the relevant existing V13 Field
Notes, documentation, templates, and operational rules for foreseeable
failure families. Select only the guards that materially apply to this
destination. If it is not possible to determine whether a candidate guard
applies, record `UNKNOWN`; do not silently omit it or treat the capsule as
complete.

The audit must distinguish:

- selected guards and the destination risk each addresses;
- guards considered but not required, with the reason; and
- unknown applicability or evidence that requires review before the relevant
  work is authorized.

The Fit Audit is mandatory even when the destination appears simple. It is
also mandatory when an existing short universal capsule is available.

### 4. Record the Fit Audit in Its Durable Canonical Home

Every New Repo Capsule must create `docs/capsule_fit_audit.md`. It is the one
canonical durable record of that capsule's Fit Audit. `README.md`,
`AGENTS.md`, and handoffs may summarize or link to it, but must not replace it
with another canonical audit record.

The record must preserve, at minimum:

- Destination / Purpose;
- Active guards, with the destination risk or reason for each;
- Conditional guards, with each guard's exact reconnect trigger and its
  destination risk or reason;
- Excluded guards, with the reason each is not needed for this destination;
- `UNKNOWN`, including what evidence or review is missing; and
- source pointers to the relevant V13 Field Notes, documentation, templates,
  or operational rules for every material selection, exclusion, or `UNKNOWN`.

This record makes an intentional exclusion distinguishable from a guard that
was simply omitted. The next chat or AI must be able to reconstruct the current
selection and its reasoning from this file without relying on transient chat
history.

### 5. Place Each Selected Guard Deliberately

| Disposition | Placement | Required explanation |
| --- | --- | --- |
| Active | Destination `AGENTS.md` | It is needed during ordinary work in this repository. Keep it concise and executable. |
| Conditional | A guide or reference linked from `AGENTS.md` or the capsule | State the exact reconnect trigger that requires it to be read. |
| Excluded | Capsule audit record | State why this V13 knowledge is not needed for the stated destination. |

Conditional guidance must remain reconnectable: the destination must know
exactly when to read it. Exclusion is intentional scope control, not a silent
loss of knowledge. Do not place a destination-specific guard in the universal
core merely because it was selected for one prior repository.

### 6. Create the Minimum Restartability Scaffold

After the destination, universal core, and durable Fit Audit record are
created, create the required files and any narrowly necessary support documents
selected by the audit.

## Required Files

- `README.md`
- `AGENTS.md`
- `handoff/current_handoff.md`
- `docs/handoff_command.md`
- `docs/capsule_fit_audit.md`

If the Fit Audit finds that the repo may involve external contact, also
include:

- `docs/contact_readiness_card.md`

If the Fit Audit finds that the repo may involve audit work, also include:

- `docs/audit_card_template.md`

Additional files are justified only when a selected guard needs them. A file
does not substitute for an active instruction, a reconnect trigger, or an
exclusion reason.

## Fit Audit Re-evaluation Trigger

Re-run the Repo-specific Capsule Fit Audit and update
`docs/capsule_fit_audit.md` whenever the declared Destination / Purpose or a
material operating surface changes. Record the re-evaluation trigger and
current selection in that same canonical file; do not start a parallel audit
record.

Examples include a change from docs-only to runtime work, local-only to a
public surface, no API to API use, no external contact to external contact, or
manual work to automation. These examples explain the trigger; they are not a
fixed taxonomy.

Re-evaluate before authorizing work that relies on the changed purpose or
surface. An earlier Fit Audit does not automatically authorize the changed
operation.

## Compactor Regression Case

For a destination whose purpose is to compact or generate repository
instructions, the Fit Audit must surface at least these candidate guard areas:

- source `AGENTS.md` versus generated `AGENTS.md`;
- double-compression risk;
- persistent repository instructions versus transient chat instructions;
- reconnectable guidance;
- user-equivalent first use / dogfood versus developer-special prompting;
- context loss and restartability;
- instruction-loss and safety-boundary loss; and
- public claims versus their evidence boundary.

These are destination-specific candidates, not additions to every New Repo
Capsule's universal core. This regression case confirms that a Compactor-like
destination cannot pass on a fixed universal minimum alone; it does not
authorize changing that destination repository.

## Handoff Command Requirement

- `docs/handoff_command.md` must define how to produce a compact, paste-ready
  next-chat handoff.
- `AGENTS.md` must include:

```text
When the user selects `Handoff`, follow `docs/handoff_command.md`.
```

## Required Handoff Fields

- Target Layer
- Repo Root
- Current State
- Current Gate
- Active Branch
- Next Authorized Action
- Completion Line
- Missing Closure
- Next Owner
- What the Receiving AI Now Owns
- First One Action
- Do Not Continue Boundary
- What must not be returned to the Decision Owner

`Current State` must distinguish completed work, unresolved work, and routine
cleanup. `What the Receiving AI Now Owns` must assign the unresolved executable
responsibility; `Next Owner` alone is not a substitute for that transfer. If
ownership cannot be established, write `UNKNOWN` and do not imply accepted
transfer, PASS, or closure.

`First One Action: none` is valid only when `Active Branch: none` and `Next
Authorized Action: none` are both explicit, no unfinished work or `UNKNOWN`
ownership remains, and no routine investigation, diff, verification, Git
operation, or cleanup remains executable by the receiving AI. Otherwise the
handoff must name the earliest bounded action and its owner.

## Completion Check

A New Repo Capsule is not complete merely because the required files exist,
it is short, or it contains the universal core. It is also not complete merely
because it copied a broad V13 surface.

Before calling the scaffold ready, verify that:

- the destination/purpose is recorded;
- the Universal Core and destination-specific selected guards are distinct;
- `docs/capsule_fit_audit.md` is the single durable Fit Audit record and
  preserves active, conditional, excluded, and `UNKNOWN` dispositions;
- conditional guidance has an exact reconnect trigger;
- exclusions are explained rather than silently dropped; and
- a changed destination/purpose or material operating surface would require a
  re-run of the Fit Audit before the changed work is authorized; and
- the resulting handoff semantics remain consistent with
  [`docs/handoff_command.md`](handoff_command.md) and restartability guidance
  in [`docs/context_compression.md`](context_compression.md).
