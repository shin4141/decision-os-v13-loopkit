# Field Note 051: Lane Recall Mini-Protocol

Date: 2026-06-15

## Purpose

This note compresses lane-based memory / event-triggered recall into a minimal operator-facing protocol.

It uses:

- `field_notes/048_lane_memory_event_triggered_recall.md`
- `field_notes/049_lane_recall_routing_proof.md`
- `field_notes/050_lane_recall_failure_and_weight_limits.md`

The protocol is a candidate only.

It is not canonical.

It is not automation.

## Why a Mini-Protocol Is Needed

Field note 048 defined lane recall.

Field note 049 showed lane recall can route future work usefully.

Field note 050 showed that lane recall can become too heavy if applied to every small task.

The mini-protocol exists to keep lane recall usable:

```text
enough structure to route memory, not enough structure to become a new burden
```

## Mini-Protocol

Use the following eight-step check when an event may need lane recall.

### 1. Event

Ask:

```text
What happened or what is being requested?
```

Name the event in plain language.

Examples:

- run a loop again
- promote something to AGENTS.md
- rewrite README
- post publicly
- recover from a later failure
- find the next 0.01

### 2. Need

Ask:

```text
Is recall needed, or is chronological/current context enough?
```

Default rule:

```text
No lane recall for tiny one-off tasks.
```

Use no recall when:

- the task is tiny and local
- the touched file is explicit
- no public/canonical/external/high-risk surface is involved
- current context is enough

Use lane recall when:

- the event affects public, canonical, external, execution-loop, or mistake-recovery surfaces
- old mistakes or promotion rules may matter
- the next action could touch the wrong surface

### 3. Lane

Select at most 1-2 lanes by default.

Candidate lanes:

- Judgment Core Lane
- Execution Loop Lane
- Mistake / Breakout Lane
- Public / Positioning Lane
- Promotion / Canonical Lane

Default rule:

```text
If more than two lanes are needed, prefer HOLD or CAP.
```

Select the one lane most likely to change the next action.

Add a second lane only if it protects a distinct risk.

### 4. First Read

Identify what should be read first.

The first read should be the smallest anchor that can change the decision.

Examples:

- execution loop event → read Execution Loop Gate notes first
- AGENTS.md change → read Promotion / Canonical notes first
- public/outreach event → read Public / Positioning and Mistake notes first
- next 0.01 event → read Judgment Core notes first

Do not create a long reading assignment if one anchor is enough.

### 5. Protected Surface

Identify what must not be touched.

Protected surfaces may include:

- AGENTS.md
- AGENTS.ja.md
- README.md
- CLAUDE.md
- schemas
- examples
- prompts
- USE_CASES
- external repos
- public/outreach channels
- pluginization or automation surfaces

The protected surface list should prevent accidental expansion while recall is still resolving the right lane.

### 6. Gate

Assign a GO / HOLD / CAP / BLOCK tendency.

Use:

- GO only when the lane, target, evidence, and surface are clear
- HOLD when the lane, target, owner intent, or authority is unclear
- CAP when one bounded read/check/action can clarify the lane or recover evidence
- BLOCK when recall would justify violating constraints, hiding debt, or touching forbidden surfaces

Default rule:

```text
Stale notes require recheck before reuse.
```

Do not use an old field note as current authority without checking whether later notes supersede it.

### 7. Weight Check

Mark routing as:

- useful
- unclear
- too heavy
- wrong

Default rule:

```text
Routing is useful only if it reduces next-action ambiguity.
```

If routing does not change the gate, protected surfaces, or first read, downshift to light recall or no recall.

### 8. Output

Decide whether to:

- proceed
- hold
- cap
- stop

Output should state the selected lane(s), the protected surface, and the gate tendency only when it helps the next action.

Do not turn every task report into a lane analysis.

## Default Rules

Default rules:

- no lane recall for tiny one-off tasks
- if more than two lanes are needed, prefer HOLD or CAP
- stale notes require recheck before reuse
- lane recall must not create promotion pressure
- routing is useful only if it reduces next-action ambiguity

These defaults prevent lane recall from becoming a new source of process debt.

## Example Compact Form

Compact operator-facing form:

```text
Event:
Need:
Lane:
First Read:
Protected Surface:
Gate:
Weight Check:
Output:
```

This form is for thought and planning.

It is not required in every final report.

## Boundary

This is a candidate protocol only.

Do not modify AGENTS.md.

Do not modify AGENTS.ja.md.

Do not modify README.md.

Do not modify CLAUDE.md.

Do not modify schemas, examples, prompts, or USE_CASES.

Do not implement automation, hooks, MCP, pluginization, or external repo changes.

Do not promote this to canonical yet.

Do not claim public readiness.

Do not rewrite public positioning.

## V13 Signal

Signal:
🟢 BLUE / LANE-RECALL-MINI-PROTOCOL-RECORDED
+
🟢 BLUE / EVENT-NEED-LANE-GATE-COMPRESSED
+
🟢 BLUE / DOWNSHIFT-DEFAULTS-PRESERVED
+
🟡 YELLOW / CANDIDATE-PROTOCOL-ONLY
+
🟡 YELLOW / NO-AUTOMATION
+
🟡 YELLOW / DO-NOT-PROMOTE-TO-AGENTS-YET
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
Lane recall is compressed into a candidate mini-protocol, but it remains non-canonical and has no automation, AGENTS promotion, README rewrite, or public-readiness claim.

Next Loop Command:
Use the mini-protocol only when lane recall would reduce next-action ambiguity; otherwise downshift.
