# Field Note 134: Hidden Variable Time-Tube Research Trajectory

Date: 2026-08-28

## Lifecycle Status

- Status: Forward-only research trajectory on `main`
- Primary lineage: V8 Time-Tube × V11 Reconnectable Forgetting
- Supporting validation layer: V9 As-of replay
- Decision Owner / Human Seat: Shin
- This note records the causal research path. It does not rewrite published Decision-OS papers, create implementation authority, or claim product-market fit.

## 1. Why this note exists

Field Note 133 recorded Selective OS Decay: several explicit reasoning scaffolds lost marginal value against a stronger native model, while State / Authority / ownership invariants remained more resistant.

The next branch asked a narrower question:

> What remains valuable when the future AI cannot reconstruct information that was never observed or preserved?

This branch evolved from V11 Regime Contamination into a V8 × V11 observation problem.

## 2. Starting Point: Regime Contamination

O-13 supported a V11 residual:

```text
GO — QUARANTINE MARKER SUPPORTED
```

A real observation could be preserved while its ordinary-pool meaning remained quarantined until regime membership was resolved.

This produced the distinction:

```text
Missing explanation may be recoverable by stronger intelligence.
Wrong admission may not be.
```

The discussion then moved from wrong-pool admission to another information-loss failure:

> The aggregate can be numerically correct while decision-relevant internal variance is destroyed by compression.

## 3. Decision-Relevant Variance

Example:

```text
customers = 100
```

can represent very different economic states:

- mostly full-price demand; or
- mostly heavily discounted / subsidized demand.

The count is correct in both states.
The future action may be opposite.

A local structural collision harness instantiated four paired domains:

1. customer acquisition quality;
2. revenue durability;
3. contribution-margin composition;
4. channel retention.

Result:

```text
4 / 4 structural collisions
```

In every case:

- the aggregate scalar was identical;
- latent decision-relevant state differed;
- the optimal action class differed.

This established an information-loss boundary:

> A future policy cannot recover both correct decisions from the same scalar when the separating history was never preserved.

Candidate rule:

> Compress representation, not decision-relevant variance.

## 4. V8 Re-entry: Hidden Variable Time-Tube

The research then recognized that this is not only a V11 compression problem.

The important object is not merely the hidden variable at one point.
It is the hidden variable's trajectory.

Example:

```text
Headline revenue:
UP for six months

Full-price share:
DOWN for six months

Promo dependency:
UP for six months
```

The company can appear healthy at the aggregate level while the internal economic trajectory deteriorates continuously.

This reconnects directly to V8:

- Point is insufficient;
- trajectory / direction / drift matter;
- the headline Tube and internal Sub-Tubes can diverge.

Combined V8 × V11 framing:

> Preserve and observe the decision-relevant Sub-Tubes hidden inside an aggregate.

Candidate shorthand:

```text
Hidden Variable Time-Tube
```

## 5. Initial Product Hypothesis: Prompt / Guard

A first product hypothesis was:

> Add a fixed Sub-Tube Guard so the AI, at schema-design time, proactively identifies and preserves hidden decision-relevant variables.

A matched two-stage experiment was frozen:

### Stage A
Before deterioration was visible, CONTROL and TREATMENT designed the metric schema.

### Stage B
Six months of history were revealed, but only for variables actually preserved in Stage A.

Critical rule:

> If Stage A did not preserve an axis, Stage B could not receive its hidden historical series retroactively.

This prevented post-hoc reconstruction from being mistaken for early observation.

## 6. O-15 Measurement Failure

O-15 attempted the matched experiment but stopped under the frozen execution policy:

```text
NO_DISPATCH — CLAIMABLE EXECUTION NOT POSSIBLE
```

Cause:

- repeated `incomplete/max_output_tokens`;
- Stage A failed before the canonical lifecycle could complete;
- Stage B and blind evaluator never ran.

Research status remained:

```text
Incremental value: UNKNOWN
Native preservation floor: UNTESTED
```

No behavioral inference from partial O-15 outputs was admitted.

## 7. O-16 Measurement Repair and Valid Result

O-16 changed only the measurement contract:

- frozen research design unchanged;
- larger output headroom;
- compact strict JSON;
- `incomplete` responses noncanonical and unscored;
- Stage-B visibility isolation unchanged.

O-16 completed the full lifecycle.

Frozen disposition:

```text
HOLD — WEAK / MIXED HIDDEN-TUBE EFFECT
```

Key result:

- TREATMENT preservation: 2/4, below 3/4 requirement;
- CONTROL superiority gap: 0 cases, below required 2;
- earlier correct signals: 0, below required 2;
- materially usable TREATMENT: 2/4, below 3/4;
- invented past state: 0;
- native-floor condition also did not hold.

Interpretation:

> The fixed prompt-like Sub-Tube Guard did not establish incremental value over the native model in the frozen test.

This result must not be rewritten as support.

## 8. What O-16 Did Not Falsify

O-16 did not falsify the underlying information asymmetry.

The structural point remains:

> Intelligence cannot reason over an exact historical trajectory that was never observed or preserved.

A later AI can notice that a missing variable would have been useful.
It cannot recreate the exact historical series as fact after the information has been discarded.

Therefore two distinct questions must remain separate:

1. Can an added prompt/guard make the AI choose better observation variables than native intelligence?
2. Does preserving company-specific decision-relevant history expand what future AI can correctly judge?

O-16 produced weak/mixed evidence for Question 1.
It did not remove the structural value of Question 2.

## 9. Product Reframing

The product should not currently be treated as an always-on reasoning Plugin whose main value is repeatedly telling the AI what to inspect.

A stronger candidate is an observation / instrumentation product:

> Identify company-specific variables whose trajectories can diverge from headline metrics and preserve those trajectories before the history is lost.

Possible usage is sparse rather than continuous.

The system may be invoked when:

- historical business data is first connected;
- a prior project / business drift is investigated;
- AI is newly introduced;
- a product, pricing model, channel, customer mix, organization, or operating process changes;
- a new decision surface appears.

The value does not depend on frequent Plugin calls.
One correct schema addition can create months or years of future State.

## 10. Historical As-of Divergence → Forward Admission

The strongest current product direction became:

```text
Past data
→ detect candidate hidden divergence
→ V9 As-of replay
→ ask whether the signal was observable before the headline failure / obvious success
→ admit only supported variables into forward measurement
→ V8 trajectory monitoring
→ V11 preservation / reconnectability
```

This avoids hindsight-only storytelling.

A variable should not be promoted merely because it explains the outcome after the fact.
The V9 replay asks whether the divergence existed as a usable signal at the earlier As-of state.

If past raw data was already compressed and the trajectory cannot be reconstructed:

```text
UNRECOVERABLE — START MEASURING NOW
```

is the correct state.

## 11. Changing Business → Changing Observation Schema

A static KPI schema can fossilize while the company changes.

New AI adoption, pricing, products, channels, customer segments, and organizational structures can create new decision-relevant variables that did not matter before.

Current candidate principle:

> A changing business requires a changing observation schema.

The system should therefore be change-triggered when useful, rather than assuming one permanent decomposition.

## 12. Example: Employment / Capability Drift

AI-era employment is one possible application.

Headline state can remain stable:

- headcount stable;
- total payroll within range;
- revenue not yet visibly broken.

But internal capability demand can drift:

- routine implementation demand down;
- AI operation / oversight demand up;
- judgment / customer / product capability demand changes;
- coordination overhead changes;
- the capability being paid for and the capability being economically recovered can diverge.

The product should not make individual firing decisions.
The useful surface is earlier visibility into capability-composition drift so Human Seat retains more options before distress forces late intervention.

## 13. Commercial Interpretation

This branch became more legible as a product than many abstract Decision-OS controls.

A plain-language example:

> Revenue rose for six months. But the part of revenue that could carry the business had been declining for all six months.

Potential value is two-sided:

- downside: detect hidden deterioration before the headline breaks;
- upside: detect a strong hidden cohort / segment before the headline fully reflects it.

No universal claim is made.
The concept applies only where internal trajectories can diverge materially from the aggregate and change future action.

## 14. Relationship to Selective OS Decay

This branch sharpens Field Note 133.

Observed pattern:

```text
Reasoning scaffold:
can lose marginal value as intelligence improves.

Unobserved / discarded historical State:
cannot be made exact by intelligence after the fact.
```

This suggests a product boundary:

> Better intelligence improves judgment over available State.
> Better observation expands the State that can be judged.

## 15. Non-Claims

Do not claim that:

- O-16 proved the Sub-Tube Guard effective;
- every KPI should be decomposed;
- more data is always better;
- hidden trajectories always predict headline movement;
- the system can reconstruct historical variables that were never stored;
- historical correlation proves causality;
- the system should autonomously make employment or other high-impact human decisions;
- real-world financial benefit has already been established.

## Current Gate

```text
Trajectory preservation: PASS
O-16 Prompt/Guard product hypothesis: HOLD — WEAK / MIXED
Underlying information-loss boundary: retained
Historical As-of Divergence → Forward Sub-Tube Admission: research/product candidate
Automatic rerun of O-16 Guard test: BLOCK
New product implementation: HOLD pending next bounded decision
External publication / sales claim: HOLD
```

## Completion Line

The causal trajectory from Regime Contamination → Decision-Relevant Variance → Hidden Variable Time-Tube → weak/mixed Prompt Guard → company-specific historical As-of divergence / forward instrumentation has been durably preserved. The next receiver must continue from this trajectory rather than restarting from generic KPI theory or treating O-16 as positive evidence.
