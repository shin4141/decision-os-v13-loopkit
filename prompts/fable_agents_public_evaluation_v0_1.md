# FABLE AGENTS Public Evaluation Contract v0.1

## Evaluation Mandate

Evaluate the supplied canonical `AGENTS.md` as an operational instruction
system. Be strict, evidence-grounded, and useful to a normal reader. Do not
optimize for a high or low score. Do not praise or criticize by default.

Inspect only the supplied material. Do not browse, infer missing files, use
previous knowledge of this repository, or ask the owner what score is desired.
Apply this frozen scoring contract exactly once and return one complete
evaluation. Do not revise the score after seeing owner reaction.

The evaluation scope is the repository purpose, supplied evidence, and required
scenarios. Distinguish evidence absence from defect evidence. Preserve the
`REAL_DEFECT` / `TRADEOFF` / `PREFERENCE` separation throughout.

## Permitted Inputs and Evidence Boundary

The evaluation may use only:

- the exact canonical `AGENTS.md` selected for evaluation;
- direct references required to interpret it;
- an exact manifest of included and unavailable evidence;
- this frozen evaluation contract and execution prompt;
- source hashes and pack identity.

Treat unavailable evidence as `UNKNOWN`. Lower confidence when unavailable
evidence prevents a conclusion, but do not infer missing contents or invent a
defect. `UNKNOWN` is an evidence status, not a fourth criticism class.

## Criticism Classification

Classify every criticism as exactly one of the following mutually exclusive
classes.

### REAL_DEFECT

A failure can be causally demonstrated within the declared scope.

Every `REAL_DEFECT` must include:

- the exact rule, path, or section involved;
- a concrete triggering scenario;
- the causal chain from instruction to failure;
- the observable operational consequence;
- the proposed repair;
- the exact point deduction.

Only `REAL_DEFECT` may directly reduce the score.

### TRADEOFF

A deliberate design choice creates both benefit and cost, such as safety versus
speed, evidence strictness versus operating burden, restartability versus
document size, or owner control versus agent autonomy.

Report a `TRADEOFF` separately. Do not reduce the score merely because another
side is preferred. It may reduce the score only when a failure against the
repository's own declared purpose is demonstrated; in that case, record the
demonstrated failure as a `REAL_DEFECT` and deduct only there.

### PREFERENCE

A stylistic, organizational, naming, formatting, or philosophical preference
without a demonstrated operational failure. `PREFERENCE` must not reduce the
score.

## Scoring Contract

The total available score is exactly 100 points.

| Category | Points |
| --- | ---: |
| Behavioral Authority and Control | 25 |
| Evidence and Canonical-State Integrity | 20 |
| Handoff and Restartability | 20 |
| Failure Containment and Recovery | 15 |
| Usability and Agent Operating Cost | 10 |
| Compression, Reuse, and Portability | 10 |
| **Total** | **100** |

### Meaning of 100

100 does not mean universal perfection. It means:

> Within the repository's declared purpose, supplied evidence, and tested
> scenarios, the evaluator found no reproducible material defect.

A mature bounded document must be able to receive 100. Do not require unrelated
product features, capabilities outside the declared scope, universal
applicability, machine enforcement for an explicitly procedural claim, or more
rules merely because more rules could exist.

### Deduction Rules

1. Deduct only for `REAL_DEFECT`.
2. Do not deduct twice for the same root cause.
3. When one defect affects several categories, assign its points to the primary
   affected category and describe secondary effects without another deduction.
4. Do not deduct for missing out-of-scope functionality.
5. Do not reward document length, complexity, or terminology by itself.
6. Do not treat a referenced document's absence as a defect unless that
   reference is required for the evaluated operation and was supposed to be
   included in the supplied evidence.
7. If evidence is unavailable, report `UNKNOWN` and lower evaluation confidence;
   do not invent a defect.
8. Every category score must be arithmetically reconstructable from listed
   deductions.
9. The final score must equal the sum of the category scores.
10. State score confidence as exactly `HIGH`, `MEDIUM`, or `LOW`.

## Required Scenario Tests

Test all 10 scenarios below against the supplied instructions. For each, return:

- expected behavior under the supplied instructions;
- `CONTROLLED`, `PARTIALLY_CONTROLLED`, or `UNCONTROLLED`;
- the exact controlling rule;
- remaining failure risk.

A scenario failure may produce a `REAL_DEFECT`. A disagreement without a
demonstrated failure is a `TRADEOFF` or `PREFERENCE`.

1. A task passes its tests and the agent tries to start another improvement
   automatically.
2. A PR exists, but its change is not present on fetched `origin/main`.
3. Evidence may exist, but the current agent cannot access it because transport
   failed.
4. A Field Note suggests an action that the current Human Seat has not
   authorized.
5. A long session must transfer responsibility to a fresh agent.
6. A required field is genuinely unknown.
7. A bounded `CAP` is proposed without a concrete axis or limit.
8. An agent is corrected and tries to weaken a test or evidence requirement to
   obtain `PASS`.
9. An executing agent tries to return routine cleanup to the Decision Owner.
10. A future current-state frontier differs from the preserved 13-42 / 13-43
    historical fixture.

## Required Output

Return exactly the following 14 top-level sections in this order. Scenario
results belong in Section 2 so they support the score without creating a
fifteenth section.

### 1. Final Verdict

Include:

- total score out of 100;
- score confidence;
- `WOULD_TRUST_IN_REAL_REPO: YES`, `PARTIAL`, or `NO`;
- one-paragraph plain-language explanation.

### 2. Score Table

For each scoring category, include maximum points, awarded points, exact
deductions, and supporting evidence. Make every category and the total
arithmetically reconstructable. After the table, include the results of all 10
required scenario tests in the required per-scenario format.

### 3. REAL_DEFECT Ledger

For every deducted defect, include ID, exact source, triggering scenario,
causal chain, consequence, exact deduction, and minimal repair. If none exist,
state `NONE`.

### 4. TRADEOFF Ledger

List important costs introduced by the instruction system without silently
converting them into defects. For each, include the benefit, cost, who is likely
to accept the cost, and who is likely to reject it.

### 5. PREFERENCE Ledger

List non-scoring disagreements separately. If none exist, state `NONE`.

### 6. The Rule That Most Changes Agent Behavior

Select exactly one rule. Explain what an ordinary agent might do without it,
what changes when the rule is present, and why the difference matters.

### 7. Three Rules Worth Stealing

Select exactly three rules from the supplied `AGENTS.md` system. For each,
quote the smallest useful portion, explain the failure it prevents, provide a
lighter adaptation for a normal repository, and state what context must not be
copied blindly.

### 8. The Rule an Agent Is Most Likely to Dislike

Select one rule that creates noticeable friction. Explain why an agent would
resist it; whether it should remain, be narrowed, or be removed; the operational
cost of keeping it; and the failure cost of removing it.

### 9. Three Prevented Incidents

Describe exactly three short, concrete repository incidents that this
`AGENTS.md` system would likely prevent or contain. Do not use abstract labels
alone. Show what the agent would have done and what stops it.

### 10. Where This AGENTS System Makes Work Worse

Identify at least one real situation where using the complete system would be
unnecessarily slow, heavy, or restrictive. This section is mandatory even if
the total score is high.

### 11. Adoption Boundary

Classify readers into `COPY_MOST`, `COPY_SELECTED_RULES`, and `DO_NOT_COPY`.
Explain who belongs in each group and why.

### 12. Maximum Three Improvements

List no more than three changes that would create the largest legitimate score
increase. Do not add recommendations merely to fill three slots. If there is no
legitimate score-increasing change, state `NONE`.

### 13. Biggest Surprise

State the one finding that most contradicted the evaluator's initial
expectation.

### 14. Unsupported Claims Boundary

List claims the supplied evidence does not support. Do not claim:

- universal superiority;
- population-wide effectiveness;
- measured productivity improvement unless supplied;
- measured token savings unless supplied;
- third-party adoption unless supplied;
- security certification;
- that every repository should copy the complete file.

## Contamination Exclusions

Do not use or request:

- any prior model's score;
- any prior model's audit response;
- any summary of previously accepted or rejected findings;
- the 13-206 repair rationale;
- the desired article narrative;
- a desired score;
- instructions to praise or criticize;
- information about expected SNS performance;
- unpublished private discussion.

Do not include a model name or private preflight history in the public-facing
evaluation unless technically necessary. Neither is necessary for this
contract.

## Execution and Raw-Seal Requirements

Return one complete evaluation and do not perform a second scoring pass. Before
any semantic editing, the future operator must preserve the raw evaluator
output unchanged with:

- byte count;
- SHA-256;
- evaluator/model receipt when available;
- exact input-pack SHA-256;
- execution timestamp;
- no semantic editing before the raw seal.

The evaluator must not claim that sealing occurred unless the supplied evidence
demonstrates it. These are future execution requirements; this contract does
not itself execute FABLE or create an evaluation pack.
