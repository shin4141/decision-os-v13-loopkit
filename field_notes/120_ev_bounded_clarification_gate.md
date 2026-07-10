# Field Note 120: EV-Bounded Clarification Gate

Status: Prior adopted / verification pending

## Layer

V13 / Loop Gate / ASK - CONTINUE - HOLD

Adjacent layers:

- V12 Completion Integrity
- V14 Resource Justice
- Human Seat / responsibility boundary

## Observation

AI clarification is not free. A question can recover a material missing condition, but it can also transfer attention, context-loading, and routine operational choice back to the human.

The decision is not simply whether more information would be useful. It is whether clarification is required by the Human Seat or whether its expected decision value exceeds the Carrier cost imposed by asking.

## Core Rule

ASK when either condition is true:

1. Human Seat is required for:
   - consent
   - value judgment
   - risk tolerance
   - public release
   - financial commitment
   - authority or ownership change
   - irreversible action

2. The expected decision value gained from clarification exceeds the Carrier cost imposed on the human by asking.

Otherwise:

- choose the safest bounded and reversible option;
- continue without asking;
- state a material assumption briefly when necessary;
- do not return routine operational choices to the human.

## Uncertainty Rule

If the AI cannot estimate the consequence and the possible harm is material, use `HOLD` or `ASK`. Do not silently guess.

## Gate Meaning

This is a V13 Loop Gate governing `ASK / CONTINUE / HOLD`.

`ASK` is not a default for ordinary ambiguity. `CONTINUE` is valid only when the option is safely bounded and reversible. `HOLD` is required when the consequence cannot be estimated and material harm remains possible.

## V14 Connection

Unnecessary clarification transfers attention, context-loading, and decision burden to the human. That is a Resource Justice cost even when the question appears harmless.

## V12 Connection

Skipping clarification must not create false completion, hidden Missing Closure, or a non-restartable handoff. A material assumption must remain visible enough for the next human or AI to recheck it.

## Risks

- Under-asking can hide material assumptions.
- Over-asking consumes Carrier and returns routine decisions to the human.
- This rule must not be interpreted as permission to bypass the Human Seat.

## Verification-Pending Questions

- Did avoided questions reduce human burden without increasing correction work?
- Did `ASK` decisions materially change the result?
- Were assumptions safely bounded and reversible?
- Did skipped questions later create Missing Closure?
- Did users experience the rule as relief or as loss of control?

## Lifecycle

If this becomes the higher-level parent concept, older narrower question-tree observations may later be marked `Folded` under the Field Note Lifecycle rule. Do not perform mass reclassification in this task.

## Boundary

This is an adopted prior, not Canon.

Do not promote it into `AGENTS.md`, README, templates, schemas, runtime behavior, automation, public posting, outreach, or release work without verification and Concept Promotion Gate.

## Completion Line

EV-Bounded Clarification Gate is preserved as a verification-pending V13 prior for deciding when AI should ask, continue with a bounded decision, or hold.
