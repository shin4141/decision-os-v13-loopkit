# Companion Product Roadmap v0.3

## Status

```text
Layer:
V13 — Compound Loop / Product Value Gate

Direction:
FIXED — FORWARD-ONLY SUCCESSOR TO v0.2

Product Thesis:
Human-Seat-Preserving Autonomous Compounding

Build Authorization:
BOUNDED — first Compound Loop proof only

Release Authority:
NONE

Publication Authority:
NONE
```

This roadmap does not rewrite `companion_product_roadmap_v0_2.md`.
v0.2 remains preserved at its own historical As-of.

## 1. Why v0.3 Exists

The current Companion proved a safe bounded Run, but the post-audit product gate
established a value deficit: a single governed Run is not enough to make the
Companion meaningfully preferable to direct Codex for the creator.

The product-value threshold is not more evidence presentation, more README
polish, or more isolated guardrails.

The threshold is reached when the governed record begins doing work:

```text
Goal
→ bounded Worker Run
→ evidence / completion state
→ Supervisor judgment
→ GO / HOLD / CAP / BLOCK
→ next bounded Run or Human Seat return
```

The user should not have to supervise every intermediate Run.

The intended value is:

> AI keeps routine continuation AI-owned, and returns to the Decision Owner
> only when the expected value of Human Seat judgment is higher than autonomous
> continuation.

A correct stop or return to Human Seat is a successful governance outcome, not
a failed automation outcome.

## 2. Relationship to Existing V13 Assets

This roadmap consumes existing assets rather than replacing them:

- bounded Run execution;
- exact one-file mutation boundary per Run;
- Approval and authority checks;
- execution / mutation / verification separation;
- Receipt and reconnectable state;
- Completion Integrity;
- current-state and historical As-of surfaces;
- GO / HOLD / CAP / BLOCK;
- Roadmap Anchors;
- Minimum Autonomous Loop v0.2 Human-Seat routing principles;
- creator dogfood and existing failure evidence.

The new missing product layer is the controlled transition from one completed
Run into the next bounded Run.

## 3. Worker / Supervisor Separation

The Worker asks:

> How can I complete the authorized task?

The Supervisor asks:

> Should another bounded loop be allowed, under the current Goal, authority,
> evidence, cost boundary, and Human Seat contract?

The Supervisor is an authority role, not necessarily a stronger model.

For the first bounded proof, Worker and Supervisor may use the same underlying
model if their roles, inputs, outputs, and authority are separated. Independent
cross-model or cross-vendor supervision is not required for the first proof.

## 4. Human Seat Return Contract

Routine work must not be returned to the Decision Owner merely because another
AI call, repository read, verification step, bounded repair, or ordinary
continuation is required.

Autonomous continuation may remain AI-owned only while all of the following are
true:

- the declared Goal / Aspire direction is unchanged;
- the next action remains inside current authority;
- the next mutation remains inside the current bounded blast radius;
- the action is reversible or already covered by explicit authority;
- evidence is sufficient to justify the next step;
- no material value trade-off requires a human preference;
- no external publication or irreversible commitment is introduced;
- no authorized cost / loop cap is exceeded.

Return to Human Seat when continuing would require any of the following:

- changing the Goal or Aspire;
- expanding authority or risk tolerance;
- choosing between materially different value directions;
- changing a Protected Object or ownership boundary;
- making an irreversible or externally visible commitment;
- exceeding the authorized cost / loop boundary;
- proceeding without sufficient evidence;
- resolving a genuine authoritative conflict or truly unanswered Human-Seat
  question.

When Human Seat is required, return only the smallest irreducible decision that
cannot be safely closed by AI. Do not return routine cleanup, Git operations,
verification, or ordinary repair work to the Decision Owner.

## 5. Product Value Target

The immediate product value is not "more autonomous agent behavior."

It is:

> More safe autonomous progress per Human decision.

A useful V13 Compound Loop should let the Decision Owner submit one meaningful
Goal, leave the execution loop, and later receive either:

```text
COMPLETE
with bounded evidence and restartable state
```

or:

```text
HUMAN SEAT REQUIRED
with completed work preserved and exactly one irreducible decision exposed
```

The product fails its value test if the user still has to read every Receipt,
choose every next Run, or manually reconstruct routine continuation state.

## 6. First Build Roadmap

### Stage A — Supervisor Judgment

Consume one real bounded Run result and produce one structured continuation
judgment:

```text
GO / HOLD / CAP / BLOCK
Reason
Established state
Remaining gap
Next bounded action or Human Seat return
```

No automatic second Run is required for Stage A.

Completion line:
The Supervisor can distinguish routine AI-owned continuation from a genuine
Human Seat return without changing Goal or authority.

### Stage B — One Automatic Continuation

On `GO`, automatically construct and execute exactly one next bounded Run using
persisted Goal, authority, evidence, and completion state.

Completion line:
One user Goal produces two causally connected bounded Runs without the user
manually translating the first Receipt into the second Task.

### Stage C — Small Compound Loop

Extend the same contract to a hard maximum of three total bounded Runs for the
first creator-live proof.

Allowed outcomes:

```text
COMPLETE
HOLD
CAP
BLOCK
HUMAN SEAT REQUIRED
```

The numeric cap is a first-proof safety boundary, not a permanent product
limit. Raising it requires later evidence and a separate Forward-only decision.

Completion line:
One user Goal enters the system once; V13 performs up to three bounded Runs,
consumes its own prior evidence between Runs, and either completes or returns
one irreducible Human Seat decision while preserving restartable state.

### Stage D — Leave-the-Desk Dogfood

The creator delegates a real repository task and does not supervise each
intermediate Run.

Success is not measured only by task completion. Record:

- number of bounded Runs;
- AI-owned continuations;
- CAP / HOLD / BLOCK events;
- unnecessary Human Seat calls;
- missed Human Seat calls;
- unauthorized expansion attempts;
- restart / reconstruction burden;
- whether the creator would prefer V13 to direct Codex for that task.

If the creator still rationally prefers direct Codex after this stage, stop
feature expansion and re-evaluate the product thesis.

## 7. Initial Use Order

First validation target:

```text
creator-owned repository work
```

Second validation target after creator value is established:

```text
bounded repair of another person's repository
→ diagnosis
→ repair
→ verification
→ explicit limits of what was established
→ restartable / reviewable delivery state
```

External repair work is a validation and service opportunity, not authorization
to expose private operational policy.

## 8. Public Core / Private Operator Boundary

### Public V13 Core

The public repository may contain the general governance mechanism required to
make the research claim inspectable and usable, including:

- bounded Compound Loop control;
- Worker / Supervisor role separation;
- GO / HOLD / CAP / BLOCK;
- Human Seat return contract;
- bounded authority and blast-radius enforcement;
- evidence / completion / reconnect contracts;
- reference implementation and public validation sufficient to evaluate the
  mechanism.

The public Core must be useful enough to stand on its own. It must not be
artificially crippled merely to create a paid tier.

### Private Operator Layer

Do not automatically publish accumulated operational intelligence whose value
comes from repeated real use, including concrete internal policies, learned
repair heuristics, customer-specific workflows, operational routing choices,
private cost / model optimization, and accumulated service know-how.

One-line boundary:

> Open the governance mechanism; retain accumulated operator intelligence.

This is a Forward-only boundary. Previously public material remains public and
must not be rewritten as if it had always been private.

## 9. Deferred Horizons

The first Compound Loop proof does not require:

- cross-vendor continuation;
- Claude ↔ Codex handoff as a delivered product outcome;
- long unattended fleets;
- unrestricted multi-file mutation inside one Run;
- self-modification;
- automatic Canon modification;
- paid-tier implementation;
- customer billing automation;
- release or publication;
- generalized superiority claims.

These remain separate later decisions.

## 10. Product Disconfirmation

Pause or redirect this product line if real dogfood shows that:

- creator reconstruction cost is too small to justify the Compound Loop;
- Human Seat is still called so often that direct Codex remains simpler;
- the Supervisor cannot reliably distinguish routine continuation from
  value-bearing human decisions;
- governance friction remains larger than the autonomous time returned to the
  user;
- direct-agent native capabilities absorb the relevant value gap before V13
  demonstrates independent value.

## 11. Current Gate

```text
Roadmap:
FIXED

Product Direction:
GO — bounded Compound Loop proof

Stage A / B / C implementation:
AUTHORIZED IN ORDER, subject to existing repository authority and safety gates

Stage D creator-live use:
REQUIRES a qualified build and explicit live-run authorization

Public release:
BLOCK

Publication:
BLOCK

Private Operator Layer publication:
NOT AUTHORIZED
```

## 12. Current Completion Line

The next development phase is complete only when:

> A single user Goal can produce a bounded multi-Run chain in which V13 consumes
> prior Run evidence itself, continues routine work without returning it to the
> Decision Owner, and returns exactly when a higher-value Human Seat decision is
> required.

The first proof is capped at three total bounded Runs. Cross-vendor continuation,
long unattended execution, and commercial operator intelligence are outside the
first completion line.
