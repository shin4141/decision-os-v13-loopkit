# Use Case: Research Loop

Use this when a research pass has produced notes, sources, claims, or candidate decisions and the next step could be more research.

The danger is non-compounding depth: research can feel productive while producing unclear residue, growing uncertainty, or delaying decision.

V13 decides whether to deepen, pause for synthesis, continue under a cap, or block the current research form.

## Typical Completed State

- A research pass has finished.
- Sources, notes, comparisons, or hypotheses exist.
- The next loop would search more, read more, test more, or ask another model.
- The value of additional research may be uncertain.

## V13 Question

Given the completed research state, should the next research loop be GO, HOLD, CAP, or BLOCK?

## Copy-Paste Input

Paste the research summary into [`../prompts/v13_loop_review.md`](../prompts/v13_loop_review.md).

Add this context:

```text
Use case: research loop.

Pay special attention to:
- whether the last loop produced reusable residue
- whether the next variable is specific
- whether more research will change a decision
- whether cost, attention, or uncertainty is increasing
- whether synthesis should happen before more collection
```

## Gate Examples

- GO: continue when the next question is specific and likely to improve a real decision.
- HOLD: pause when the current residue has not been synthesized.
- CAP: run one bounded research pass with a source, time, or model-cost limit.
- BLOCK: stop when research is avoiding a decision, expanding without residue, or damaging re-entry capacity.

## Example CAP

```text
Run one 45-minute research pass using at most 5 sources. Stop after extracting decision-relevant evidence.
```

## Example Next Loop Command

```text
Synthesize the current notes into three decision-relevant claims before any further research.
```
