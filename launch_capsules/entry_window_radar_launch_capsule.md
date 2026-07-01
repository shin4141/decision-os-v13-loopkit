# Entry Window Radar Launch Capsule v1.0

## Gate

```text
Launch Capsule: ISSUED
New repo scaffold: GO after this capsule is committed and pushed
Implementation scope: CAP
External posting: HOLD
Delivery Scope Radar: HOLD
V14 Resource Justice deep scoring: HOLD
```

## Purpose

Entry Window Radar is a V13-derived outward-facing OSS candidate that helps evaluate whether a GitHub repo, README, idea, or small project currently sits inside a usable entry window.

It uses three lines:

```text
Market Line
Competition Line
Operator Edge Line
```

to classify the current entry posture as:

```text
FAST ENTRY
NICHE WEDGE
WAIT
SHORT CYCLE
AVOID
```

Its purpose is not to predict the future.

Its purpose is to help the operator see whether the current entry window is usable, crowded, early, late, narrow, short-lived, or not worth entering yet.

## V13 Boundary

Entry Window Radar discovers and compares possible future lines.

V13 remains the Loop Gate.

```text
Entry Window Radar = Future Line Discovery Engine
V13 = GO / HOLD / CAP / BLOCK Gate
```

Entry Window Radar may say:

```text
This looks like FAST ENTRY.
This looks like NICHE WEDGE.
This looks like WAIT.
```

But V13 decides whether the next loop should actually proceed.

## Non-purpose

Initial MVP does not include:

```text
Web SaaS
payment / billing
Delivery Scope Radar implementation
Resource Justice deep analysis
Score History
Entry Window Drift
LP / note / X / artifact full support
external posting
automated web research
Grok / X / API integration
full startup advisor behavior
```

It also must not present itself as a future prediction tool.

## MVP Completion Line

MVP PASS requires the future new repo to include:

```text
repo scaffold
README initial draft
AGENTS.md
idea.md or artifact.md input template
optional evidence.md template
optional operator.md template
chart.json schema for Entry Window Chart
report.md output template
decision.md output template
validate_prompt.md
Operator Edge Extraction Prompt v0.2
one worked example
working tree clean
```

The MVP is complete when a user can provide a repo / README / idea and receive:

```text
Entry Label
Market Line
Competition Line
Operator Edge Line
Missing Evidence
Risk
Recommended Next Action
Recheck Condition
```

without the tool claiming certainty about future success.

## CAP Conditions

CAP the repo immediately if it starts to become:

```text
a full startup advisor
a Web SaaS
a generic business planner
a V14 Resource Justice engine
a Delivery Scope Radar implementation
a scoring-heavy product before the core chart works
another abstract Decision-OS explainer
```

Initial scope stays limited to:

```text
repo / README / idea input
one Entry Window Chart
five entry labels
one bounded next action
one recheck condition
```

## BLOCK Conditions

BLOCK if:

```text
implementation begins without this capsule boundary
Entry Window Radar and Delivery Scope Radar are merged in MVP
V14 Resource Justice is pulled into the free core too early
the tool says "you should build this" without V13-style gate language
the output implies certainty about future success
external posting begins immediately after repo creation
the first version requires too many inputs before producing a useful card
```

## README Direction

The future README should not lead with Decision-OS theory.

It should lead with the user's practical pain:

```text
Is this idea early, late, crowded, or still worth a narrow entry?
Am I entering fast, waiting, wedging into a niche, or avoiding a bad bet?
```

Then show the simplest Entry Window Card.

Decision-OS / V13 should appear as the underlying boundary, not as the first thing the user must understand.

## Initial File Structure Candidate

Suggested initial files for the future new repo:

```text
README.md
AGENTS.md
inputs/idea.md
inputs/evidence.md
inputs/operator.md
schema/chart.json
outputs/report.md
outputs/decision.md
prompts/validate_prompt.md
prompts/operator_edge_extraction_prompt_v0_2.md
examples/example_001.md
```

Do not create the new repo or these files in this task.
This section only records the future repo scaffold candidate.

## Operator Edge Prompt v0.2

Initial parked prompt:

```text
What does the operator know, have, or notice that most competitors do not?

Is the edge based on speed, taste, distribution, workflow, domain knowledge, timing, personal constraint, or proof cost?

Can the operator produce credible proof faster or cheaper than a generic competitor?

Is the edge durable enough for the current entry window, or only useful for a short cycle?

If the edge disappeared, would the project still have a reason to enter now?
```

## New Repo GO Conditions

New repo creation is GO only after this Launch Capsule is committed and pushed.

When new repo creation begins, stay under these limits:

```text
Create scaffold only.
Keep MVP bounded by this capsule.
Do not start external posting.
Do not merge Delivery Scope Radar.
Do not implement V14 Resource Justice scoring.
Do not expand into SaaS / API / automation.
```

The first repo task should be:

```text
Create the new repo scaffold and MVP file structure only.
```

Not:

```text
market launch
posting
full implementation
advanced scoring
multi-product expansion
```

## References

```text
field_notes/101_entry_window_radar_mainline_note.md
field_notes/102_entry_window_radar_derivatives_resource_justice_scope_separation.md
```

## V13 Decision

```text
Decision: GO
Reason: Field Note 101 / 102 separate the mainline from derivatives clearly enough. MVP boundary is bounded. Delivery Scope Radar and Resource Justice are parked. Launch Capsule now defines completion, CAP, and BLOCK conditions.
```
