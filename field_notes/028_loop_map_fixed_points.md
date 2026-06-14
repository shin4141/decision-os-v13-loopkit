# Field Note 028: Loop Map Fixed Points

Date: 2026-06-14

## Purpose

This note records whether the V13 loop map is accumulating fixed points, not merely adding notes or footer formats.

The goal is to distinguish reusable judgment anchors from useful but unproven observations.

## Fixed Point Definition

A fixed point is a reusable judgment anchor that lets a future agent or future self restart without reconstructing the full conversation.

A field note is only a candidate fixed point until it is connected to later judgment or used in a task.

The test is not:

```text
Was a note written?
```

The test is:

```text
Did a later judgment rely on the note without needing the full prior chat?
```

## Current Loop Line

The current loop line is:

```text
footer/reporting prompt shock
→ missing judgment logic
→ 0.01 definition
→ V12→V13 mapping
→ CAP axis/limit
→ Aspire/Carrier/Re-entry proxies
→ footer-axis consolidation
→ AGENTS routing
→ internal routing test
→ external routing test
→ loop map observation
→ contrastive judgment example
```

This line shows a move from output format toward judgment routing.

The question is whether the nodes on this line became reusable.

## Candidate Fixed Points

Candidate fixed points:

- `field_notes/021_required_intermediate_node.md`
- `field_notes/022_v12_to_v13_mapping.md`
- `field_notes/023_cap_axis_limit_selection.md`
- `field_notes/024_aspire_carrier_reentry_operational_definitions.md`
- `field_notes/025_footer_axis_consolidation.md`
- `field_notes/026_loop_map_observation.md`
- `field_notes/027_contrastive_judgment_example.md`

Each note may become a fixed point if later judgment uses it as an anchor.

## Confirmed Fixed Points

Confirmed fixed points:

- `field_notes/021_required_intermediate_node.md`
  - Confirmed because it was used in AGENTS routing tests to select the earliest missing required node.
- `field_notes/022_v12_to_v13_mapping.md`
  - Confirmed because it was used to prevent V12 PASS from automatically producing V13 GO.
- `field_notes/023_cap_axis_limit_selection.md`
  - Confirmed because it was used to choose CAP axis and concrete limit.
- `field_notes/024_aspire_carrier_reentry_operational_definitions.md`
  - Confirmed because it was used to check Aspire, Carrier, and Re-entry preservation.
- `field_notes/025_footer_axis_consolidation.md`
  - Confirmed because it was used to avoid unnecessary footer expansion.
- AGENTS.md routing commit: `249ae99 Add AGENTS judgment reference routing`
  - Confirmed because it connected field notes 021–025 to operational judgment.
- External V12 repo routing test
  - Confirmed because it showed the routing outside V13 self-reference.

These anchors let a future agent restart from operational references instead of replaying the whole conversation.

## Weak / Not-Yet Fixed Points

Weak or not-yet fixed points:

- `field_notes/026_loop_map_observation.md`
  - Useful observation, but not yet reused as a decision input.
- `field_notes/027_contrastive_judgment_example.md`
  - Useful demonstration, but not yet tested against a real external contrast.
- Public value / star-worthiness
  - Not fixed.
- Plugin readiness
  - Not fixed.
- Automation path
  - Not fixed.

These may become fixed points later, but they are not confirmed yet.

## What Increased

The loop now has multiple reusable judgment anchors.

What increased:

- "Next 0.01" is no longer arbitrary.
- PASS no longer implies GO.
- CAP now requires axis and limit.
- Aspire / Carrier / Re-entry are no longer undefined labels.
- Footer use is no longer additive by default.
- AGENTS.md now points agents to the relevant judgment anchors.

This is real structural gain.

It is not a feature, but it improves restartability and judgment quality.

## What Did Not Increase

What did not increase:

- No product feature.
- No automation.
- No plugin.
- No public proof.
- No star-worthiness proof.
- No guarantee that ordinary users will adopt it.

The fixed points strengthen internal judgment.

They do not yet prove external demand.

## Next Fixed-Point Candidate

The next candidate fixed point is a real external contrast:

```text
ordinary agent judgment
vs
Decision-OS judgment
on the same external task
```

This would test whether `field_notes/027_contrastive_judgment_example.md` becomes a confirmed fixed point.

The contrast should show whether V13 changes the next-loop decision in a real external setting, not only in an internal explanatory example.

## Boundary

This is observation only.

Do not claim readiness.

Do not claim public value.

Do not broaden into outreach.

Do not modify AGENTS.md in this loop.

This note does not modify AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / LOOP-MAP-FIXED-POINTS-OBSERVED
+
🟢 BLUE / CONFIRMED-JUDGMENT-ANCHORS-IDENTIFIED
+
🟢 BLUE / FIELD-NOTE-VS-FIXED-POINT-DISTINGUISHED
+
🟡 YELLOW / PUBLIC-VALUE-NOT-FIXED
+
🟡 YELLOW / REAL-EXTERNAL-CONTRAST-STILL-MISSING

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The loop now has confirmed judgment anchors, but public value and real external contrast remain unproven. The next loop should stay capped to testing whether the contrastive example becomes a fixed point.

Next Loop Command:
Run one real external contrast later to test whether field note 027 becomes a confirmed fixed point.
