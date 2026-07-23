# One-Paste Codex Execution Packet v0.1

This template defines one complete, directly pasteable execution packet for a
bounded Codex repository task. Fill every applicable field before delivery,
then copy from `# Task Identity` through `## Stop Condition` in one continuous
operation.

The template is a manual authoring surface. It does not authorize work by
itself, create runtime automation, or transfer Human Seat.

# Task Identity

Packet ID:
{unique packet identifier}

Task title:
{one bounded task title}

Packet status:
COMPLETE / DIRECT EXECUTION INPUT

Delivery mode:
ORIGINAL / FULL REPLACEMENT

Invalidated prior packet ID:
{`none` for ORIGINAL; required for FULL REPLACEMENT}

For `FULL REPLACEMENT`, state explicitly that the prior packet is invalidated
in full and must not be merged with this packet.

Instruction version:
{version or date}

Sender:
{Decision Owner or authorized sender}

## Destination

Receiving Codex task:
{existing task identity}

Receiver role:
{bounded execution role}

## Repository

Repository path:
{exact absolute repository path}

Repository identity:
{repository name and remote, when relevant}

## Repository As-of

Required starting commit:
{full commit SHA}

Starting-state requirement:
{for example: clean working tree and HEAD equal to origin/main}

If the identity, As-of, or working state does not match:
{HOLD or BLOCK condition}

## Canonical Authority

Canonical authority file:
{exact path}

Authority precedence:
{current Human instruction, current repository authority, and any bounded
source order}

## Active Branch

Authorized operational branch:
{exact V13 branch name}

Adjacent branches:
INACTIVE unless a later complete packet explicitly authorizes one

## Next Authorized Action

One authorized action:
{one bounded action}

Execution limit:
{iteration, exposure, files, time, or other concrete cap}

## Purpose

{What this task must establish and why this bounded action is sufficient.}

## Delivery Contract

### One delivery packet

The sender provides this as one complete packet intended for direct copy and
paste. The receiver must not require another instruction merely to assemble or
interpret the authorized task.

### No human integration burden

The receiver must not ask the Decision Owner to merge assistant messages,
remove obsolete sections, combine replacement text, choose between conflicting
drafts, perform routine Git work, or decide routine cleanup.

### Full replacement rule

Before delivery, the sender resolves errors by replacing the entire internal
draft. If a delivered packet must be corrected before execution, the sender
must explicitly invalidate it and issue one complete replacement packet.

Do not deliver additive corrections such as:

- delete the previous paragraph;
- add this to the earlier packet;
- replace only this section;
- combine the two messages;
- use the previous packet except for the following change.

### One outer copy surface

The filled packet must remain one continuous copy surface. Do not require
nested copy blocks, multiple separately copied fragments, or reconstruction
from prose outside the packet.

### Receiver-owned closure

The sender defines what the Completion Line must establish but does not supply
the finished Completion Line when receiver-owned understanding or closure is
being tested.

### One active branch

This packet authorizes one Active Branch and one Next Authorized Action only.
No adjacent branch starts from implication, momentum, or routine cleanup.

### Exact file authority

Only the files listed below may be created or modified. Routine validation,
commit, push, synchronization checks, and safe cleanup within this exact task
remain receiver work.

### Human Seat boundary

Direction, value, risk acceptance, public release, monetary decisions,
credentials, ownership, and genuine authority change remain Human Seat
matters. The receiver may execute only the bounded authority stated here.

## Exact Authorized Files

Create exactly:

1. {exact path or `none`}

Update exactly:

1. {exact path or `none`}

Modify no other file.

Deletion authority:
{none or exact paths}

## Required Result

Required artifacts or changes:

- {result 1}
- {result 2}

Required distinctions or invariants:

- {distinction 1}
- {distinction 2}

Required receipt or classification:
{exact result vocabulary}

## Boundaries

Do:

- preserve historical As-of and later Forward-only receipts;
- keep source definitions separate from current-layer mappings;
- expose `UNKNOWN`, missing evidence, and unvalidated claims;
- preserve the Decision Owner's refusal and stop authority.

Do not:

- expand beyond the one Active Branch;
- modify an unlisted file;
- invent missing authority or evidence;
- claim validation, generalization, runtime behavior, or burden reduction that
  was not observed;
- transfer Human Seat;
- begin an adjacent task after completion.

Task-specific prohibited actions:

- {prohibited action 1}
- {prohibited action 2}

## Validation

The receiver must verify, as applicable:

- repository identity and starting As-of;
- exactly the authorized files changed;
- required content and distinctions are present;
- prohibited content and adjacent-branch changes are absent;
- current state surfaces agree;
- Markdown fences and local links pass;
- `git diff --check` passes;
- the intended commit contains only the authorized files;
- commit and push complete;
- the working tree ends clean;
- `HEAD`, `origin/main`, and the remote branch agree.

Task-specific checks:

- {check 1}
- {check 2}

If any required check cannot be established:
{HOLD or BLOCK result and re-entry condition}

## Final State Constraints

V12 State:
{PASS / DELAY / BLOCK / UNKNOWN}

V13 Next Loop Gate:
{GO / HOLD / CAP / BLOCK}

Reason:
{why this is the correct final Gate}

Active Branch:
{none or exact continuing branch}

Next Authorized Action:
{none or one bounded action}

Decision Packet Required:
{yes / no}

Decision Owner:
{owner}

## Completion Line Requirement

After completing the actual work and validation, the receiver writes one
Completion Line in its own words.

It must establish:

- {what completed or what failed};
- {what reusable or restartable structure now exists};
- {whether correction or clarification occurred};
- {what remains unverified};
- {the resulting V13 Gate and why}.

The sender supplies no finished receiver Completion Line here.

Receiver-authored Completion Line:
{write only after actual work and validation}

## Stop Condition

After the authorized work, validation, commit, push, synchronization check, and
receiver-authored Completion Line are complete, stop. Do not start another
proof, validation, implementation, deep read, runtime task, or adjacent branch.
