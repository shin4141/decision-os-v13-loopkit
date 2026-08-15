# Field Note 133: Model/Substrate Drift Detection Gap

Date: 2026-08-15 JST

Lifecycle status: Verification pending

Primary layer: V8 / V9.1 bridge

Supporting layer: V13

Evidence class: External independent convergence / internal missing-bridge audit

Canon promotion: HOLD

## Classification

- Artifact type: Decision-OS research Field Note
- Field Note type: Forward-only research residue
- Status: FORWARD-ONLY FIELD NOTE / HOLD
- Current Gate: HOLD — DETECTION PRIMITIVE NOT YET MATURE
- Gate addition: NONE
- Canon modification: NONE
- Implementation authority: NONE

This Field Note records one unresolved bridge between existing Decision-OS
layers. It does not modify V8, V9, or V9.1 Canon, create a Gate, authorize V13
implementation, or block unrelated Decision-OS work.

## Origin and External Observation

Shin identified the external paper:

Sophia Abraham and Ben Bucknall, “Silent Updates: Measuring and Closing the
Post-Deployment Disclosure Gap,” arXiv:2608.11803, 2026.

The connection to Decision-OS was then examined independently through Claude
and GPT and compressed into this Field Note.

The paper studies a post-deployment governance problem: a published evaluation
may describe one evaluated model or system state while the system currently
served through an API may have changed. Relevant changes are not limited to
model weights. They can include fine-tuning, classifiers, system prompts,
retrieval, routing, tool access, inference budgets, and other deployment-layer
components capable of changing user-visible behavior.

Across the paper's sample of nine first-party API providers, the reported
externally verifiable API-to-evaluation round-trip was `0 / 9`. The study did
not identify a public mechanism by which an external evaluator could
independently prove that the artifact currently served by an API was the same
system configuration described in the corresponding published evaluation. The
paper characterizes this as a chain-of-custody problem.

## External Scope Boundary

The paper demonstrates a binding and verification gap. It does not provide a
complete primitive for detecting every silent substrate change at the moment
it occurs.

The authors bound their measurement to publicly observable artifacts and do
not directly measure underlying weight changes for closed models, production
system-prompt contents, or undisclosed routing and load-balancing state.
Therefore:

```text
Need for chain-of-custody verification is demonstrated.

A complete external Model/Substrate Drift Detection primitive is not
demonstrated.
```

## Existing Decision-OS Coverage

### V9.1 downstream judgment

V9.1 already supplies the downstream judgment rule when binding cannot be
trusted. Its reusable judgment state is condition-bound:

```text
(outcome, residue_key, condition)
```

A prior PASS remains reusable only while its stored condition remains valid.
If the condition is invalidated, stale, or unverified, the judgment is not
silently reused as PASS. It downshifts to DELAY and returns to Recheck / DFR.

The response to a condition whose validity can no longer be established is
therefore already present: do not inherit PASS; DELAY and recheck. No V9 or
V9.1 amendment is required for that response.

### V8 upstream trajectory language

V8 treats safety and control as trajectory questions rather than only
pointwise-output questions. Its trajectory dimensions include direction,
curvature, branching, drift, and reversibility, and it recognizes goal drift,
reference drift, and seat drift.

This supplies a conceptual surface on which behavioral change over time can
become a control-relevant signal. V8 does not, however, define a dedicated
observable for provider-side silent replacement or modification of the served
model or system substrate, including changes to weights, prompts, routing,
classifiers, retrieval, tool availability, inference budgets, or other
deployment components.

## Missing Bridge

> **Model/Substrate Drift Detection is a missing bridge between V8 trajectory signals and V9 condition invalidation: V8 can represent observed drift and V9 can downshift an unverified condition to DELAY, but Decision-OS does not yet define a reliable primitive for detecting when provider-side model or system-substrate changes should invalidate that binding.**

The unresolved connection is:

```text
observed behavioral / substrate-change signal
→ V8 trajectory drift observation
→ binding condition becomes questionable
→ V9.1 condition = invalidated / stale / unverified
→ DELAY
→ Recheck / DFR
```

The downstream judgment semantics and upstream trajectory language already
exist. The unresolved component is the detection and binding primitive that
determines when a change in the served system should invalidate or reopen a
previously qualified condition.

## Detection Gap

The unresolved question is not which Gate should fire. It is:

> What observable evidence is sufficient to conclude that the substrate
> binding relied upon by a previous judgment may no longer hold?

Possible future primitive classes include provider-signed snapshot
attestations, cryptographic served-artifact binding, standardized deployment
manifests, externally verifiable model or system fingerprints, repeatable
behavioral change detection, routing or version disclosure, and other
independently auditable provenance mechanisms.

These are candidate classes only. None is promoted into a Decision-OS
requirement by this Field Note.

## Why No New Gate Is Added

A Gate without an operationally credible detection primitive would create a
stopping condition that Decision-OS cannot reliably evaluate: a policy promise
without a sufficiently observable trigger.

The current action is to record the Missing Bridge, not manufacture the
missing detector. Existing V9.1 behavior remains sufficient once a condition
actually becomes invalidated, stale, or unverified.

## Canon and Implementation Impact

```text
V8:        NO CANON CHANGE
V9 / V9.1: NO CANON CHANGE
V13:       NO IMPLEMENTATION CHANGE
New Gate:  NONE
```

This observation is Forward-only residue. It identifies a missing connection
rather than falsifying an existing layer.

## External Independent Convergence and Self-Audit

The paper independently reaches a structurally adjacent problem: deployment-
time changes can break the binding between previously evaluated safety claims
and the system actually being served. This provides narrow external
convergence with Decision-OS problem structures including temporal validity,
evidence binding, condition validity, bounded reuse, and re-evaluation after
changed conditions. It does not validate Decision-OS as a whole.

Applying the paper back onto Decision-OS also exposed an unclosed boundary. V8
can represent trajectory drift, and V9.1 can invalidate stale or unverified
judgment conditions, but the bridge that turns a suspected served-system
change into a condition-validity event has not been operationalized.

This comparison illustrates that external convergence can both corroborate a
problem structure and expose missing internal structure. This methodological
observation is not promoted into a new Decision-OS layer by this task.

## Non-Claims

This Field Note does not claim:

- that any particular provider has silently changed a specific model currently
  in use;
- that behavioral drift necessarily proves model-weight drift;
- that model weights are the only relevant substrate;
- that V8 already detects provider-side substrate replacement;
- that V9 lacks a response to invalid conditions;
- that a complete external detection primitive currently exists;
- that the Silent Updates paper solves substrate-fidelity verification;
- that the `0 / 9` result proves providers have no internal chain-of-custody
  controls;
- that a new Gate should be deployed now.

The paper measures what an independent external evaluator can verify from
public information and standard access.

## Current Gate

```text
HOLD — DETECTION PRIMITIVE NOT YET MATURE
```

This HOLD applies only to development of the missing bridge. It does not modify
ordinary V8 or V9 operation and does not block unrelated Decision-OS work.

## Re-evaluation Trigger

Re-open this Field Note when at least one credible detection/binding primitive
becomes operationally available, for example:

- an industry-standard externally verifiable served-system attestation;
- cryptographic binding between served system and evaluated artifact;
- provider-exposed version/routing/component provenance sufficient for
  independent verification;
- a validated behavioral/substrate-fidelity detector with known
  false-positive / false-negative properties;
- or a Decision-OS implementation capable of making the V8 → V9 bridge
  observable and falsifiable.

Do not reopen merely because another paper discusses silent updates
conceptually. The trigger is **operational detectability / verifiability**, not
additional terminology.

## Ownership and Authority Boundary

```text
Decision Owner:
Shin

Current Next Actor:
NONE

Implementation work:
NOT AUTHORIZED

Detector issue or task creation:
NOT AUTHORIZED
```

This Field Note is parked. Do not assign implementation work or create an
issue or task to build the detector unless Shin explicitly reopens the line.

## Missing Closure

Decision-OS has no reliable, observable, falsifiable primitive that determines
when a provider-side model or system-substrate change should invalidate or
reopen the binding relied upon by a previous judgment.

## Completion Line

PASS — MODEL/SUBSTRATE DRIFT DETECTION GAP FIXED AS FORWARD-ONLY FIELD NOTE
