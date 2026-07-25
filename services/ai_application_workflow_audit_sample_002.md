# AI Application Workflow Audit — Sample 002

## When “Publish Ready” Leaves the Next Operator Guessing

> **Synthetic demonstration — evidence boundary**
>
> - This is a synthetic bounded demonstration.
> - It is not a paid-client result, testimonial, measured productivity claim,
>   or diagnosis of a named product.
> - It demonstrates the delivery format for one non-repository AI-assisted
>   operational workflow.
> - Quantities, time savings, incident frequency, and commercial outcomes
>   remain `UNKNOWN`.

## Audit Scope

This sample reviews one synthetic AI-assisted content-production path from
approved inputs through a scheduled CMS publication step.

Included:

- one content-production workflow path;
- completion-state integrity;
- evidence continuity;
- restartability;
- next-actor ownership;
- returned human recovery work.

Excluded:

- content quality;
- factual review of the article itself;
- CMS security;
- vendor reliability;
- model evaluation;
- full workflow redesign;
- measured productivity or revenue impact.

## Source Materials

Reviewed synthetic materials:

- a workflow diagram showing the bounded content-production path;
- a final run status reporting `complete`;
- a sanitized event sequence;
- an expected completion definition;
- available operator notes.

Not reviewed:

- a real article, visual asset, source document, or CMS record;
- raw prompts, model configuration, or vendor-side telemetry;
- CMS credentials, security settings, or production data;
- a complete application log or independently verified scheduler history;
- measured operator time, cost, labor, or business impact;
- a post-repair run or recurrence record.

## Incident As-of State

Run / item identity:
`SYNTH-CONTENT-002`

As-of time:
`UNKNOWN` — this synthetic demonstration does not assign a real clock time.

Trigger:
A bounded content-production run receives a human-approved brief, an approved
source list, a requested article, one required visual asset, and a scheduled
CMS publication step. During finalization, the visual upload fails.

Expected state:
The workflow should preserve the approved brief and source-list identities,
record the article and required visual states, verify the CMS draft and
scheduler states, expose unresolved items, and transfer ownership of the next
safe action before declaring publication readiness.

Observed state:

- the article draft is generated;
- the required visual upload fails;
- the approved-source state is not preserved in the final record;
- the CMS scheduler state is not verified;
- the workflow reports `complete` because the text exists;
- the next operator cannot determine whether publication is safe, what failed,
  what source set was approved, whether the schedule is active, or who owns the
  next action.

Current fallback path:
Do not infer publication readiness from the `complete` label. The next operator
must inspect the CMS and available logs, reconstruct the approved source state,
determine the required visual state, establish the scheduler state, and leave a
restart record before any further publication decision. Whether the scheduled
publication can still be held is `UNKNOWN`.

Items still `UNKNOWN`:

- whether the scheduler actually ran;
- whether the missing visual was recoverable;
- whether the approved source list changed after approval;
- whether the CMS contains a usable draft identity;
- which actor currently has authority to cancel or preserve publication.

## Observed Failure

The workflow reduced completion to the existence of the article text. That
status did not carry the approved-source identity, required-visual state, CMS
draft identity, scheduler state, unresolved items, current owner, or next safe
action.

The text output therefore exists, but the bounded publication workflow does
not have a trustworthy accepted-completion record.

## Returned Human Burden

The incident returns these unquantified recovery tasks to the next operator:

- inspect the CMS;
- inspect available logs;
- reconstruct the approved source state;
- determine whether the visual must be recreated;
- decide whether to cancel or preserve the scheduled publication;
- write the missing restart state.

Actual time, cost, and labor remain `UNKNOWN`.

## Friction Map

| Point | Expected carrier | Observed gap | Returned human work |
|---|---|---|---|
| Brief and source approval | Recorded identities for the approved brief and approved source list | The final record does not preserve the approved-source state | Reconstruct which source set was approved and whether it changed |
| Text generation | Article state linked to the accepted brief and sources | The text exists, but its relationship to the accepted inputs is not preserved in the completion record | Revalidate the article state against reconstructed inputs |
| Visual generation / upload | Required visual identity, state, and upload evidence | The upload fails and recoverability is not established | Inspect logs and determine whether the visual must be recreated |
| CMS scheduler state | CMS draft identity plus verified scheduler state | The scheduler state is not verified | Inspect the CMS and decide whether to cancel or preserve the scheduled publication |
| Completion declaration | A gate covering every required publication state | The workflow reports `complete` because the text exists | Revalidate the full workflow instead of relying on the completion label |
| Next-actor transfer | Current owner, unresolved items, next safe action, and stop condition | Ownership and the next action are absent | Determine authority and write the missing restart state |

## Restartability Diagnosis

| Dimension | Result | Basis |
|---|---|---|
| Trigger clarity | `PASS` | The synthetic event sequence identifies the visual-upload failure followed by the false completion declaration |
| Accepted-state clarity | `PARTIAL` | The expected workflow state is described, but the run record does not preserve or enforce it |
| Evidence continuity | `FAIL` | Approved-source, visual, CMS, and scheduler evidence does not survive into the final record |
| Completion integrity | `FAIL` | Main-text existence is treated as completion of the entire publication workflow |
| Restartability | `FAIL` | The next operator cannot safely reconstruct publication readiness from the returned state |
| Ownership / next actor | `FAIL` | No current owner or next safe action is recorded |
| Human recovery burden | `PARTIAL` | Recovery tasks are visible, but their time, cost, and outcome remain `UNKNOWN` |
| Safe next action | `UNKNOWN` | The exact safe action depends on an unverified scheduler state and unestablished publication authority |

Overall diagnosis:

`DELAY — Output exists, but trustworthy publication completion and restart state are not established.`

## Root Cause

### Primary: Output-Existence → False-Completion Collapse

The workflow treated creation of the main text output as completion of the
entire bounded publication workflow. Required asset, evidence, scheduling,
ownership, and restart conditions were outside the completion decision.

### Contributing: Transport-State → Accepted-State Confusion

Even if the application or run can be reopened, persistence alone does not
establish approved sources, verified asset state, scheduler state, completion,
or the next safe action. A native resume path can transport state without
proving that the transported state is accepted or publication-ready.

## Priority Fix

Apply one fix only:

`PUBLISH-READY COMPLETION GATE`

The workflow may report `PUBLISH READY` only when all of these are recorded:

- approved brief identity;
- approved source-list identity;
- article state;
- required visual state;
- CMS draft identity;
- scheduler state;
- unresolved items;
- next actor;
- next safe action.

Otherwise it must report:

`NOT PUBLISH READY — RESTART RECORD REQUIRED`

This fix does not redesign the workflow or claim that the underlying upload or
scheduler behavior will be repaired.

## Copy-Paste Operational Asset

Use this complete reusable block at the end of the bounded workflow or whenever
the publish-ready gate cannot be satisfied:

```markdown
# PUBLISH-READY RESTART RECORD

Workflow:

Run / item identity:

As-of time:

Approved brief:
- Identity:
- State: APPROVED / NOT APPROVED / UNKNOWN

Approved sources:
- Identity:
- State: APPROVED / NOT APPROVED / UNKNOWN

Article state:
- Draft identity:
- State:
- Verified by:

Visual state:
- Asset identity:
- Generation state:
- Upload state:
- Evidence:

CMS state:
- Draft identity:
- State:
- Evidence:

Scheduler state:
- State: ACTIVE / INACTIVE / RAN / UNKNOWN
- Scheduled time:
- Evidence:

Verified actions:
- <verified action>

Unresolved items:
- <unresolved item>

Current owner:

Next safe action:

Must not happen next:

Completion status:
PUBLISH READY / NOT PUBLISH READY / UNKNOWN

Rule:
Native resume, saved tabs, or reopened workflow state must not be treated as
proof of accepted completion.
```

## Before / After Restart Check

### Before

- `complete` exists;
- publication readiness is unverified;
- the next operator must reconstruct state.

### After

- completion is separated from output existence;
- missing evidence remains visible;
- the next actor and safe action are explicit;
- no publication-readiness guarantee is claimed.

The asset makes the restart condition inspectable. This synthetic sample does
not establish that an operator used it or that a later incident was prevented.

## Unknowns

- whether the scheduler actually ran;
- whether the missing visual was recoverable;
- whether the approved source list changed;
- actual human recovery time;
- whether the operational asset would prevent recurrence;
- whether the CMS draft identity can be recovered;
- whether a real operator would accept or correctly apply the completion gate.

## Claim Boundary

This sample does not establish:

- prevention of a future incident;
- recovery of an asset, session, or prior state;
- workflow, product, or publication safety;
- factual correctness of the article;
- productivity improvement;
- reduced labor;
- revenue impact;
- general reliability of a model, vendor, application, or workflow.

## Completion Line

This synthetic sample is complete when:

- one bounded synthetic incident is diagnosed;
- one priority repair is selected;
- one reusable operational asset is shown;
- before / after restartability is visible;
- `UNKNOWN` items and exclusions remain explicit.
