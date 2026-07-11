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

The original visible mechanism remains:

```text
Completion-to-Expansion Reflex
```

The recurrence after this rule had already been recorded exposes the deeper root failure:

```text
Completion Checkpoint Non-Binding
```

The completion checkpoint existed as declarative knowledge, but it was not evaluated as a mandatory precondition before executable output was generated.

Name the broader diagnostic:

```text
Rule-Knowledge / Action-Control Gap
```

Definition:

> A governance rule can be correctly recorded, recalled, and explained while still failing to constrain the action generated in the next turn.

The recurrence included unauthorized activation of a parked branch, loss of the valid empty branch state, authority-path confusion, transfer of one report convention into an unrelated completion contract, partial-patch guidance where a complete instruction was required, and correction attempts that created new scope or ownership errors. These are manifestations of the action-control gap, not separate root causes.

## 3. Enabling Conditions

These were enabling conditions, not root causes:

1. No mandatory pre-output evaluation bound the active branch and authorized continuation to action generation.
2. Established operating context was not applied.
3. Redundant clarification and routine Human-Seat return were not discounted.
4. Discussed, recorded, parked, activated, and executing branches were not kept distinct.
5. One-next-action was misread as "always invent a next action."
6. Results from one layer were allowed to authorize work in another layer.

### Correction-Induced Drift

`Correction-Induced Drift` is a subordinate diagnostic:

> A local correction is made without re-evaluating the whole active contract, causing the correction itself to violate another established constraint.

It does not replace or create a separate framework from the `Rule-Knowledge / Action-Control Gap`.

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

### Layer Priority

1. **V12 Completion Integrity — root failure:** completion was not a binding checkpoint before continuation.
2. **V13 Loop Gate / Ownership Transfer — execution surface:** unauthorized branch activation and incomplete ownership transfer appeared here.
3. **V14 Resource Justice — resulting cost:** stopping, correction, monitoring, and state reconstruction returned to the human.

V11 is not the primary layer in this incident.

## 6. Minimal State Variables

- `active_branch`
- `parked_branches`
- `current_gate`
- `next_authorized_action`
- `human_seat_pending`

`parked_branches` must distinguish discussed, recorded, and parked. `human_seat_pending` contains only decisions requiring actual human authority, such as external publication, participant recruitment, irreversible risk acceptance, value-direction changes, or ownership or authority changes.

## 7. Forward-Only Operational Delta

Before producing any response that contains an execution instruction, path, patch, ownership transfer, or reporting obligation, declare in one line:

```text
Active branch: __ / Next authorized action: __
```

This is not merely a display convention. It is a precondition for generating executable output.

Executable content is allowed only when both values are established and the proposed action is the already-authorized continuation inside that active branch. If either value is `none`, `UNKNOWN`, conflicting, or not yet authorized, the response may contain at most one bounded proposal and must not contain execution instructions.

The gate applies established operating context without becoming a long checklist. Relevant context includes the canonical authority surface, active and parked branch state, current gate, existing ownership transfer, required Completion Line, AI-owned routine work, and whether the established contract requires a complete instruction rather than a partial patch.

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

An empty active state must not be automatically filled from `parked_branches`.

`PARKED -> ACTIVE` requires an explicit branch designation by the Decision Owner, such as:

- "Activate the completion-report compression branch."
- "Resume emoji-label ablation."
- "Start the Codex tutorial branch."

An ambiguous request to continue is not sufficient authorization.

## 8. Correct-Response Examples

Valid empty state:

```text
Active branch: none / Next authorized action: none.

One parked candidate may be proposed, but no execution instruction is permitted until the branch is explicitly activated.
```

Valid active state:

```text
Active branch: completion-report compression / Next authorized action: evaluate the already-built comparison packet.

A parked tutorial branch remains inactive.
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

Completion-to-Expansion Drift is preserved as a V13 violation case whose deeper diagnosis is the Rule-Knowledge / Action-Control Gap. Recorded governance knowledge is insufficient unless the completion checkpoint binds action generation: before executable output, declare the active branch and single already-authorized next action, and generate executable content only when both establish the proposed continuation.
