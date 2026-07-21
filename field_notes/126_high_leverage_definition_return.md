# Field Note 126: High-Leverage Definition Return

Optional alias: Upstream Definition Gap Return

Status: Prior adopted / verification pending

## Layer

Primary:

- V13 Compound Loop / Loop Gate

Supporting:

- V10 Survival-Bounded Planning
- V11 Reconnectable Forgetting
- V12 Completion Integrity
- V14 Resource Justice

## Observation

A more capable or differently capable execution AI may detect that an upstream definition remains underspecified. The gap may affect not only the current task, but several rules, capsules, handoffs, prompts, or later agent decisions.

The useful response is not to:

- silently invent or redesign the missing definition;
- return every ambiguity to the human;
- ask an open-ended clarification question;
- ask the Decision Owner to locate every dependent file;
- stop every time any ambiguity appears.

The useful mechanism is:

1. identify the exact upstream definition gap;
2. attempt to close it from established context and current authority;
3. identify the concrete downstream judgments affected;
4. determine whether an actual Human Seat judgment is required;
5. return one bounded question only when the answer has high propagation value;
6. after the answer, keep canonical wording, authorized propagation, consistency checks, and restart-state updates AI-owned.

## Core Claim

> AI should not return every ambiguity to the human.
>
> It should return only an upstream definition gap that cannot be safely closed from established context, requires an actual Human Seat judgment, and would improve multiple future loops if resolved once.
>
> After the human answers, the AI owns the routine propagation and verification work.

Japanese fixed candidate:

> AIはすべての曖昧さを人間へ返してはならない。
>
> 既存文脈では安全に閉じられず、人間のSeatを必要とし、一度閉じれば複数の将来loopを改善する上流定義だけを、一つの限定質問として返す。
>
> 回答後の正準化、依存surfaceへの伝播、整合確認、再開状態の更新はAI側が所有する。

## Compound Loop Mechanism

```text
Later or differently capable model detects an upstream definition gap
-> one bounded Human Seat answer
-> AI propagates the answer across authorized dependent surfaces
-> several future decisions begin from a better condition
-> a later loop may detect a deeper or previously unreachable gap
```

This is not merely one output becoming better. One irreducible upstream judgment can improve the starting condition of multiple future loops while routine propagation remains outside the Human Seat.

## High-Leverage Definition Return Gate

### 1. Concrete Gap

Is there a concrete definition gap?

- `NO`: continue normally.
- `YES`: state the exact ambiguity.

### 2. Established Context

Can established context or current authority safely close it?

- `YES`: the AI closes it without asking.
- `NO`: continue the gate.

### 3. Human Seat

Does the gap require Human Seat judgment?

Human Seat includes:

- value direction;
- risk tolerance;
- protected-object priority;
- ownership or authority;
- public or irreversible commitment;
- a choice between materially different valid meanings.

- `NO`: use a bounded reversible assumption or `HOLD`.
- `YES`: continue the gate.

### 4. Propagation Value

Would one answer improve multiple downstream judgments?

Relevant evidence may include:

- multiple rules depending on the same term;
- capsules or handoffs branching differently from the same ambiguity;
- repeated correction caused by the same definition gap;
- a model change exposing a previously invisible joint;
- resolution changing future-loop starting conditions.

- `NO`: handle the ambiguity inside the current task or preserve `UNKNOWN`.
- `YES`: return one bounded question.

### 5. After the Answer

The AI owns:

- canonical wording inside the authorized scope;
- mapping affected surfaces;
- authorized Forward-only propagation;
- consistency validation;
- the record of changed and unaffected surfaces;
- restart-state and handoff updates.

Routine propagation, file comparison, Git work, and consistency checking must not be returned to the Decision Owner.

## Bounded-Question Pattern

```text
Definition Gap:

Current wording:
<exact definition or rule>

Ambiguity:
<two or more materially different readings>

Why existing context cannot close it:
<one short explanation>

Downstream impact:
- <surface / judgment 1>
- <surface / judgment 2>
- <surface / judgment 3>

Human Seat question:
<one answerable question>

After answer:
AI owns canonical wording, authorized propagation, validation, and handoff update.
```

This pattern is conditional. It must not become a mandatory question loop.

## Distinction from Existing V13 Material

### Field Note 120 — EV-Bounded Clarification Gate

[Field Note 120](120_ev_bounded_clarification_gate.md) decides whether the value of asking exceeds Human Carrier cost and whether to `ASK / CONTINUE / HOLD`.

This note adds upstream-definition detection, one-answer-to-many-loops propagation value, and AI-owned downstream propagation after the Human Seat answer.

### Field Note 121 — Intergenerational Re-entry Compounding

[Field Note 121](121_intergenerational_reentry_compounding.md) explains how preserved structure can raise the starting point and reachable branch set of later models.

This note defines an active feedback joint: a later model detects the gap, Human Seat resolves only the irreducible value question, and the AI converts that answer into reusable authorized structure.

### Field Note 079 — Model Upgrade Precondition Delta

[Field Note 079](079_precondition_delta_example_model_upgrade.md) governs defensive stability checking after a model-version change.

This note adds a bounded constructive possibility: a model change may expose a high-leverage definition gap. It does not claim that newer models automatically detect better definitions or have authority to rewrite them.

### Field Note 105 and 0.01 Correction

[Field Note 105](105_compound_loop_speed_as_os_evidence.md) and the [Aspire-Oriented Loop Map](../docs/aspire_oriented_loop_map.md#phase-4-001-correction) explain that accumulated structure and exposed-gap correction can improve future starting conditions.

This note defines one specific mechanism for creating that condition: one irreducible upstream clarification followed by AI-owned authorized propagation.

### Human Seat and Ownership Transfer

[Field Note 108](108_ai_autonomy_requires_design_guardrails.md#seat-boundary) keeps root design, responsibility boundaries, and extension direction in the Human Seat while bounded implementation remains AI-owned.

[Field Note 122](122_completion_to_expansion_drift.md#ownership-transfer) shows the failure created when routine branch selection, review, or closure work is returned to the human after AI ownership was accepted.

This note preserves both boundaries: the human resolves only the irreducible upstream judgment; the AI owns routine propagation after the answer.

## Verification Criteria

Future verification requires at least one real case where:

1. an execution AI identifies a concrete upstream definition gap;
2. established context cannot safely close it;
3. one bounded Human Seat question is sufficient;
4. the Decision Owner answers without reconstructing the whole system;
5. the AI propagates the answer to at least two dependent decision surfaces;
6. propagation does not alter unrelated authority or historical As-of;
7. later work shows reduced correction, ambiguity, or re-explanation;
8. total human burden is lower than resolving each downstream ambiguity separately.

A vague clarification question does not count. A case where the Decision Owner must identify affected files, compare surfaces, or perform propagation does not count.

## Safety and Authority Boundary

- Historical decisions remain valid at their own As-of.
- Improvements are Forward-only deltas.
- The source definition must not be silently redesigned.
- Public, irreversible, authority-changing, or Protected-Object changes require explicit Decision Owner approval.
- AI propagation is limited to surfaces already inside the authorized scope.
- Unauthorized dependent surfaces are listed, not edited.
- Use `HOLD` when propagation impact is unclear.
- Do not convert this Field Note into runtime enforcement or an automatic ambiguity detector.

## Non-Claims

This Field Note does not claim that:

- all ambiguity should be returned to the human;
- more detailed definitions are always better;
- every model upgrade produces positive insight;
- a newer model may rewrite prior definitions;
- one answer automatically improves every downstream surface;
- propagation is safe without dependency and authority checks;
- this mechanism already operates automatically;
- the mechanism proves a universal `1.01` multiplier;
- Human Seat means human working-memory burden;
- one recorded observation verifies the mechanism.

## Current Gate and Missing Closure

```text
Independent Candidate registration: GO
Status: Prior adopted / verification pending
Canon promotion: HOLD
AGENTS.md promotion: HOLD
Runtime enforcement: BLOCK
Automated ambiguity detection: BLOCK
Automatic dependency propagation: BLOCK
Public claim / model comparison: HOLD
Additional experiment: HOLD after registration
```

Missing Closure:

A bounded real case satisfying all eight verification criteria. Until then, this mechanism remains a verification-pending prior and must not control Canon or runtime behavior.

## Completion Line

High-Leverage Definition Return is preserved as a verification-pending V13 mechanism for returning only high-propagation-value upstream definition gaps to the Human Seat and converting one bounded answer into AI-owned Forward-only improvements across future loops.

## Forward-Only Addendum — Latent Propagation Activation and Post-Answer Discovery

Date: 2026-07-21

Source As-of: `f36b4bad718a5d058f3354df6a65e7c62095dc6d`

Human Seat decision: `YES`

The original Candidate wording above remains preserved at its own As-of. This addendum fixes the later Decision Owner judgment without retroactively claiming that latent dependencies were already known or realized.

### Pre-Answer Activation Basis

FN126 may activate from either:

```text
KNOWN PROPAGATION VALUE
```

or:

```text
REASONABLE LATENT PROPAGATION POTENTIAL
```

`KNOWN PROPAGATION VALUE` means that two or more concrete dependent judgments or surfaces are already known before asking.

`REASONABLE LATENT PROPAGATION POTENTIAL` may apply when only one concrete effect is visible before asking, but all of the following hold:

- the ambiguity sits in an upstream definition, authority joint, Protected Object, ownership rule, Completion Line, or another governing concept;
- at least one real dependent judgment is visible;
- a plausible dependency path exists;
- the Human Seat question is irreducible;
- unseen future dependencies are not claimed as proven.

A definition sounding important is not sufficient evidence of latent propagation potential.

### Bounded-Question Delta

When activation relies on latent potential, the bounded question must distinguish:

- impact already known before the answer;
- propagation that is only plausible before the answer;
- the post-answer discovery the AI will own.

The `Downstream impact` field must not present latent possibilities as realized dependencies. The `After answer` field must include bounded Propagation Discovery in addition to authorized wording, validation, and handoff work.

### Post-Answer Propagation Discovery

After the Human Seat answers, the AI must:

1. fix the bounded meaning inside the authorized scope;
2. inspect actual dependency paths;
3. identify independently affected judgments;
4. distinguish discovered dependencies from speculative possibilities;
5. apply only authorized Forward-only propagation;
6. list unauthorized dependencies without editing them;
7. validate that unrelated authority and historical As-of remain unchanged;
8. update restart and handoff state.

The Decision Owner must not be asked to search for dependent files, compare surfaces, or perform propagation.

### Result Classifications

```text
LOCAL DEFINITION RETURN
```

The answer resolves a valid upstream or important local ambiguity, but post-answer discovery finds only one independently affected decision surface. This is useful but does not verify the FN126 Compound Loop claim.

```text
LATENT PROPAGATION CANDIDATE
```

Post-answer discovery identifies additional plausible or real dependencies, but propagation is not yet authorized, completed, or validated. Preserve exact re-entry conditions and keep verification on `HOLD`.

```text
REALIZED HIGH-LEVERAGE RETURN
```

The answer is propagated to at least two independently affected decision surfaces, unrelated authority and historical As-of are preserved, and the propagation is validated. This may become an FN126 verification candidate, but full verification still requires later evidence of reduced ambiguity, correction, re-explanation, or Human Carrier burden.

### Verification Boundary Clarification

The original eight verification criteria remain unchanged.

- Multiple dependent surfaces need not be visible before asking.
- Realized propagation is evaluated after the answer.
- File count is not the metric.
- Two judgments inside one file count only when they are genuinely independent decision surfaces.
- Repeated wording locations expressing one identical judgment count as one.
- Speculative future branches do not count.
- Human burden reduction must be observed, not assumed.

### Case 001 Result

Validation record: [FN126 Case 001 — Latent Propagation](../validation/field_note_126_case_001_latent_propagation.md)

```text
Case status: FIRST BOUNDED REAL CASE — PARTIAL
Propagation classification: REALIZED HIGH-LEVERAGE RETURN
FN126 lifecycle: Prior adopted / verification pending
Canon promotion: HOLD
Runtime / automation: BLOCK
```

Case 001 propagated the Human Seat answer into four independent decision surfaces inside FN126: activation eligibility, the bounded-question contract, post-answer discovery ownership, and result/verification classification. Later evidence of reduced downstream ambiguity and total Human Carrier burden remains open.

## Forward-Only Addendum — Human-Seat Distinguishability

Date: 2026-07-21

Source As-of: `af34776c51289da01299168d0b009f9bbaba8656`

Source response:

> 任せる。これはどれも俺には一緒で選べない。

The original FN126 text and Case 001 addendum remain preserved at their own As-of. This addendum fixes the later distinction exposed when operationally different routes were not meaningfully different to the Decision Owner.

### Human-Seat Distinguishability

Operational difference is not automatically Human-Seat difference.

A residual choice belongs to Human Seat only when the alternatives remain materially distinguishable in at least one dimension such as:

- value direction;
- risk tolerance;
- Protected Object priority;
- ownership or authority;
- public exposure;
- irreversible commitment;
- a trade-off the Decision Owner can meaningfully rank.

Differences limited to the following usually remain AI-owned when established context and current gates can rank them:

- implementation sequence;
- evidence order;
- validation route;
- file organization;
- bounded reversible method;
- which admissible proof is run first;
- routine operational cleanup;
- selection among routes equivalent under the Decision Owner's declared values and constraints.

### Residual Human-Seat Test

Before returning alternatives to the Decision Owner, apply:

```text
After applying established context, current gates, Roadmap Anchors, authority,
risk, and Protected Object, does a human-distinguishable choice remain?
```

- `YES`: return one bounded Human Seat question.
- `NO`: select the highest-EV bounded and reversible route without asking.
- `UNKNOWN` with material consequence: `HOLD` and state the exact unresolved human distinction.
- `UNKNOWN` without material consequence: choose the safest bounded option.

### Delegation Interpretation

When the Decision Owner states that alternatives are equivalent and delegates the choice:

- treat the operational selection as AI-owned;
- do not return the same menu again;
- apply established context, current gates, and Roadmap Anchors;
- state the selected route and reason;
- preserve Human Seat for later value, risk, authority, public, or irreversible decisions.

Delegation does not authorize unrelated expansion.

### Menu Burden Rule

Do not create a Decision Packet or option menu merely because several operationally valid routes exist.

A menu is justified only when the Decision Owner can meaningfully distinguish the residual alternatives at the Human Seat level. Otherwise the menu transfers comparison and selection burden without adding decision value.

### Case 002 Result

Validation record: [FN126 Case 002 — Human-Seat Distinguishability](../validation/field_note_126_case_002_human_seat_distinguishability.md)

```text
Case classification: REALIZED HIGH-LEVERAGE RETURN — PARTIAL
Selected route: B — Proof-to-Adoption Bridge
Route state: PARKED / not active
FN126 lifecycle: Prior adopted / verification pending
Canon promotion: HOLD
Runtime / automation: BLOCK
```

The Human Seat response propagated into five independent decision surfaces: Human Seat eligibility, option-menu permission, delegation interpretation, AI-owned route selection from established gates, and the condition under which a Decision Packet is unnecessary. Immediate comparison burden was reduced in this case; later avoidance of similar menus and long-term Human Carrier reduction remain unverified.

## Forward-Only Addendum: Adaptive Human-Seat Question Depth

Date: 2026-07-21

Source As-of: `1b07d73b6c8061250ff6bba6ba50324c7f881c9c`

Human Seat decision: `ADOPT ADAPTIVE HUMAN-SEAT QUESTION DEPTH`

The original FN126 text and Case 001 / Case 002 addenda remain preserved at their own As-of. This addendum changes how an already-justified Human Seat question is presented; it does not make asking mandatory or create a permanent user category.

### Core Rule

Human-Seat question depth is not fixed by a permanent user label. It is calibrated for the current combination of:

```text
person × domain × current state × decision consequence
```

Begin from the minimum sufficient depth. Increase depth only after evidence that prior questions produced useful definitions, improved future starting conditions, and did not impose disproportionate Human Carrier cost.

Reduce depth, narrow scope, or change question form when the question creates confusion, passive agreement, repeated equivalent-choice responses, reconstruction burden, fatigue, or low propagation value.

Expected propagation value informs the calibration, but does not convert speculative value into evidence.

### No Fixed Person Classification

Do not classify a person as:

- advanced or weak;
- a `1.01 person` or `0.99 person`;
- capable or incapable of difficult questions.

The same person may need different depth across familiar and unfamiliar domains, healthy and fatigued states, reversible and irreversible choices, local and system-wide decisions, and low and high reconstruction burdens.

### Human-Seat Question Ladder

#### Level 1 — Recognition

Use a concrete example and ask which outcome feels wrong or preferable.

Example:

> Which result would bother you more?

Use when the domain is unfamiliar, no stable preference has been expressed, or abstraction would create unnecessary burden.

#### Level 2 — Correction

Propose a provisional interpretation and ask the human to correct only the wrong part.

Example:

> I understand your preference as X. What part is wrong?

Use when established context exists and the AI can reduce reconstruction burden.

#### Level 3 — Trade-off

Ask which value becomes the floor when two values cannot both be maximized.

Example:

> If both cannot be maximized, which one must not be lost?

Use only when a genuine Human Seat conflict remains after applying established context and gates.

#### Level 4 — Definition

Allow the Decision Owner to reject the AI's framing and create a third principle.

Example:

> A/B are provisional. If the framing itself is wrong, redefine the split.

Use when prior answers show independent judgment, the original menu may constrain the real answer, and a new definition has high propagation value.

#### Level 5 — Propagation Boundary

Ask how broadly an already-understood principle should apply.

Example:

> Does this apply only to this repo, to all handoffs, or only under named conditions?

Use only when propagation scope materially changes authority, risk, Protected Object, or long-term operation and cannot be safely inferred.

### Depth-Increase Conditions

A deeper question is permitted when prior evidence shows one or more of:

- the user generated a definition outside the AI's menu;
- the answer improved multiple independent decision surfaces;
- later correction or re-explanation decreased;
- the user explicitly found the question valuable;
- the answer clarified Aspire or value direction;
- the user retained Seat rather than passively adopting the AI recommendation;
- Human Carrier cost remained proportionate to propagation value.

Where practical, increase only one material axis at a time:

- abstraction;
- impact range;
- irreversibility;
- value conflict;
- required reconstruction.

A successful prior question does not justify raising every axis at once.

### Depth-Reduction and Reformulation Conditions

Reduce depth, narrow scope, or change form when:

- equivalent-choice or “any option is fine” responses recur;
- alternatives are operationally different but Human-Seat equivalent;
- delegation signals that the distinction has no value to the user;
- the question requires unnecessary system reconstruction;
- the answer merely mirrors the AI recommendation;
- fatigue, impatience, confusion, or disengagement appears;
- the task is blocked without corresponding propagation value;
- the human must compare files, rules, or technical evidence the AI could compress first;
- the same question must be repeatedly explained.

Available adjustments include:

- move from abstraction to a concrete example;
- ask one dimension only;
- offer a provisional interpretation for correction;
- reduce propagation scope;
- separate the current decision from future generalization;
- preserve `UNKNOWN`;
- stop asking and choose the bounded reversible route when Human Seat is not required.

### Selective Human Auditability and CHALLENGE REQUIRED

Question simplification must not hide material risk or remove Human Seat.

```text
MUST READ
Human decisions, authority changes, Protected Object choices, public or
irreversible commitments, and other material judgments the Decision Owner must
personally understand.

CHALLENGE REQUIRED
Material contradictions, irreversible risks, authority conflicts, Protected
Object damage, or evidence that could change the Decision Owner's judgment.

AI-OWNED
Low-decision-value technical detail, routine comparison, propagation,
validation, cleanup, and other authorized operational work.

REOPEN IF
Named evidence, contradiction, consequence, or scope change makes an AI-owned
detail material to Human Seat.
```

At lower question depth, reduce explanation burden without reducing importance. State the consequence plainly and identify the decision required. `CHALLENGE REQUIRED` remains independent of question depth.

### Relationship to FN120 and FN126

```text
FN120:
Should the AI ask?

FN126:
Which high-leverage upstream judgment belongs to Human Seat?

Adaptive Human-Seat Question Depth:
At what depth and in what form should the justified question be asked now?
```

### Case 003 Result

Validation record: [FN126 Case 003 — Adaptive Human-Seat Question Depth](../validation/field_note_126_case_003_adaptive_human_seat_question_depth.md)

```text
Case classification: REALIZED HIGH-LEVERAGE RETURN — PARTIAL
FN126 lifecycle: Prior adopted / verification pending
Fixed user profiling: prohibited
Canon promotion: HOLD
Runtime / automation: BLOCK
```

Case 003 records a movement from an abstract trade-off through concrete reformulation to a third definition and a propagation-boundary insight. Future calibration accuracy, proactive downshifting, Human Carrier reduction, challenge preservation, and generalization remain unverified.
