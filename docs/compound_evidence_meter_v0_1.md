# Compound Evidence Meter v0.1

## Purpose and boundary

This internal meter answers what was counted and where the evidence lives. It
is not a benchmark, execution authority, routing rule, telemetry surface, or
performance claim.

The progression remains separate:

```text
EXTRACT → REUSE → COMPOUND → MEASURE
```

- `STRUCTURE_EXTRACTED` requires an explicitly identified reusable structure.
- `VERIFIED_REUSE` requires a later distinct use of that prior structure.
- `CAUSAL_CONTINUATION` requires a preceding Worker Run plus persisted source
  evidence and constructed-Task identities.
- `EFFICIENCY_COMPARISON` requires two distinct routes, an actual pairing
  basis, and at least one measured resource axis.

Availability, narrative claims, repeated Runs, and plausible savings do not
satisfy those transitions.

## Machine-readable ledger

The append-only JSONL ledger is
[`evidence/compound_evidence_meter_v0_1.jsonl`](../evidence/compound_evidence_meter_v0_1.jsonl).
Its first record is the bounded baseline register; every later record is one
countable event. New evidence is appended as a new event. Historical event
records are not rewritten to change a headline count.

The runtime-enforced schemas are:

```text
decision-os.compound-evidence-baseline.v0.1
decision-os.compound-evidence-event.v0.1
decision-os.compound-evidence-snapshot.v0.1
```

Every counted event preserves:

- `event_id` and one of the nine fixed v0.1 `event_type` values;
- `as_of`;
- `source_artifact`, exact canonical commit, Git blob, and SHA-256;
- a source-local `evidence_pointer`;
- `goal_or_chain_id` where applicable;
- `related_prior_event_id` where causality or reuse requires it;
- typed `measured_values` where applicable;
- an explicit `evidence_boundary` and `claim_status`.

The baseline record separately marks each event class `BACKFILLED` or
`NOT_BACKFILLED`. A category with an unestablished historical baseline remains
`UNKNOWN / NOT BACKFILLED`; the aggregator does not turn its lack of admitted
events into zero.

## Deterministic derivation

Run from the repository root:

```bash
python -B -m decision_os.compound_evidence_meter .
```

The validator resolves every source path at the named Git commit, confirms the
Git blob and SHA-256, rejects duplicate identities and malformed records, and
checks the event-specific causal prerequisites before aggregation. The visible
snapshot below is checked against the command output in the test suite.

## Current derived snapshot

<!-- compound-evidence-meter-snapshot:start -->
```text
Compound Evidence Meter v0.1

As-of canonical commit: 084a1779792abd959c48a86f0ad183231c03526f
Baseline boundary: Directly proven Stage B/C/D events plus the exact Field Note 129 extraction and Stage D reuse/promotion path; no repository-wide Field Note backfill.

Measured bounded Goals: 3 (OBSERVED)
Worker Runs: 8 (OBSERVED)
Causal AI continuations: 5 (OBSERVED)
Verified structures extracted: 1 (OBSERVED)
Verified reuse events: 1 (OBSERVED)
Canon promotions: 1 (OBSERVED)
Human Seat returns: 0 (OBSERVED)
Bounded Operational Assists: UNKNOWN / NOT BACKFILLED
Paired efficiency comparisons: 0 (OBSERVED; measured admission required)

Observed resource deltas
Elapsed-time delta: UNKNOWN
Worker Run-count delta: UNKNOWN
Model-cost delta: UNKNOWN
Token-count delta: UNKNOWN
Human-intervention-burden delta: UNKNOWN
Reconstruction-burden delta: UNKNOWN
```
<!-- compound-evidence-meter-snapshot:end -->

## Baseline interpretation

The starting region is deliberately narrow:

- Stage B, Stage C, and Stage D supply the three bounded Goals, eight
  individually identified Worker Runs, and five causally constructed
  continuations.
- Field Note 129 preserves the identified mutable-path/artifact-identity
  distinction. Stage D later consumed its exact pre-promotion identity and
  carried that residue into the Canon destination, supporting one extraction,
  one verified reuse, and one Canon promotion.
- The Stage B/C/D route evidence shows no actual Human Seat return. Contract
  availability and hypothetical return paths are not events.
- Operational Assist was defined after these runs. Retrospective
  classification would be inference, so its baseline remains not backfilled.
- Field Note 105 records an internal speed observation, not a paired measure.
  Stage D describes only plausible burden reduction, and Field Note 132 says
  the counterfactual route was not executed. They therefore admit no
  efficiency event and no time, Run, cost, token, intervention, or
  reconstruction delta.

No total Field Note count, estimated saving, or repository-wide historical
total is implied.

## Future efficiency event

A future `EFFICIENCY_COMPARISON` event must name two distinct admissible
routes, the pairing basis, and all six v0.1 resource axes. Each axis is either:

```json
{"status":"MEASURED","route_a":10,"route_b":7,"delta":-3,"unit":"seconds"}
```

or:

```json
{"status":"UNKNOWN","reason":"No token observation was available."}
```

At least one axis must be measured. Unknown axes remain unknown and do not
become zero. The next measurement trigger is the first suitable real task with
a comparable autonomous versus bounded-assist route under separate task
authority.
