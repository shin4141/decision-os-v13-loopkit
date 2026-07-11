# Field Note 122: Completion-to-Expansion Drift

Optional alias: Silent Branch Succession

Status: Operational violation case / Field Note

## 1. Observation

The active objective was to test whether completion reports could be shortened without losing continuation-critical information.

A secondary Codex beginner tutorial idea was introduced, recorded, and used as a source of completion-report samples. The failure occurred when completion of each bounded task was repeatedly interpreted as permission to advance the tutorial branch:

- idea note;
- pilot specification;
- A/B packet;
- participant preparation;
- tutorial implementation;
- planned dry run.

The tutorial moved from a discussed or recorded secondary branch into the effective active branch without an explicit branch-activation decision.

The operator lost visibility into the current main task, what would happen next, which branch owned the next action, and why routine AI-owned work was being returned for human judgment.

## 2. Root Cause

Task completion was treated as permission to generate and execute the next action before rechecking active-branch authority.

Name this mechanism:

```text
Completion-to-Expansion Reflex
```

## 3. Enabling Conditions

These were enabling conditions, not root causes:

1. No explicit active-branch checkpoint at completion.
2. Established operating context was not applied.
3. Redundant clarification and routine Human-Seat return were not discounted.
4. Discussed, recorded, parked, activated, and executing branches were not kept distinct.
5. One-next-action was misread as "always invent a next action."
6. Results from one layer were allowed to authorize work in another layer.

## 4. Visible Symptoms

- instrument / object inversion;
- tutorial branch displacing the compression experiment;
- Human-Seat over-return;
- unnecessary `READY / REVISE / HOLD` choices;
- routine review returned to the operator;
- a new Codex task issued before the prior completion report was received;
- reactive overcorrection;
- repeated branch oscillation;
- operator confusion and context-reconstruction burden.

## 5. Relation to Existing Concepts

### Ask-Value Threshold

Routine questions and branch decisions were returned to the human even when the expected value of asking did not exceed the attention and context-switching cost.

### Established-Context Discount

Previously fixed operating rules were not applied:

- routine operational work stays AI-owned;
- one task completes before the next instruction is issued;
- the active objective must not be displaced by an adjacent idea;
- a fatigue-sensitive `DELAY` must not be invented when capacity has been explicitly stated as clear.

### Ownership Transfer

The assistant accepted operational responsibility but returned branch selection, routine review, and closure work to the human.

### V12 Completion Integrity

Completion was misread as an expansion trigger. Completion should instead be a checkpoint where authority for the next branch is revalidated.

### V13 Loop Gate

A completed task does not automatically authorize the next loop. The next action must remain inside the active branch and current gate.

### V14 Resource Justice

The failure became visible as human cost: rereading, re-anchoring, repeated correction, uncertainty about ownership, and unnecessary decision burden.

## 6. Minimal State Variables

- `active_branch`
- `parked_branches`
- `current_gate`
- `next_authorized_action`
- `human_seat_pending`

`parked_branches` must distinguish discussed, recorded, and parked. `human_seat_pending` contains only decisions requiring actual human authority, such as external publication, participant recruitment, irreversible risk acceptance, value-direction changes, or ownership or authority changes.

## 7. Forward-Only Operational Delta

At task completion, before generating or issuing any next action, declare in one line:

```text
Active branch: __ / Next authorized action: __
```

Only an already-authorized continuation inside the active branch may proceed. Other ideas may be discussed or recorded, but must not activate silently.

Do not add a large branch-management system.

### Valid No-Active-Branch State

`active_branch = none` is a valid operational state.

When:

```text
active_branch = none
```

then:

```text
next_authorized_action = none
```

must also hold.

A `PARKED` branch must not become `ACTIVE` through ambiguous continuation language such as "next," "continue," "move on," or "let's do the next one."

When no branch is active, the AI may recommend one bounded candidate branch and explain why it is preferred, but must not generate an execution instruction or issue a Codex task. It must wait for explicit branch activation by the Decision Owner.

`PARKED -> ACTIVE` requires an explicit branch designation by the Decision Owner, such as:

- "Activate the completion-report compression branch."
- "Resume emoji-label ablation."
- "Start the Codex tutorial branch."

An ambiguous request to continue is not sufficient authorization.

## 8. Correct-Response Example

```text
Active branch: completion-report compression.
Next authorized action: emoji-label ablation packet build.
Codex tutorial: recorded and parked; not activated.
```

## 9. Non-Claims

Do not claim that:

- adjacent ideas must never be discussed;
- every completion requires human confirmation;
- all branching is harmful;
- a full orchestration system is required;
- the operator caused the drift by introducing new ideas;
- one incident proves universal prevalence.

The problem is silent activation, not exploration.

## 10. Status and Promotion Boundary

```text
Main-text elevation: HOLD
Canon promotion: HOLD
Implementation: HOLD
Broader claim: HOLD pending additional observations
```

## Completion Line

Completion-to-Expansion Drift is preserved as a V13 violation case for Ask-Value Threshold, Established-Context Discount, Ownership Transfer, V12 Completion Integrity, and V13 Loop Gate. At completion, declare the active branch and the single already-authorized next action before continuing.
