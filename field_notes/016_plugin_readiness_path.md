# Plugin Readiness Path

Date: 2026-06-13

## Context

V13 has recently established:

- invalid-target guard observation
- fresh external entrypoint proof
- command-room / local-gate split
- ingress before polish
- README entry-path PASS
- pluginization activation timing
- Plugin Readiness as an Aspire Anchor

## Observation

The next phase should not build the plugin yet.

Instead, V13 should move in 0.01 steps toward the condition where pluginization becomes obviously useful.

Core line:

```text
Before building the plugin, build the terrain where the plugin becomes obviously necessary.
```

Alternative line:

```text
Do not build the plugin yet; improve the conditions that would make the plugin obvious to build.
```

## Plugin Readiness Path

Pluginization implementation remains parked.

Plugin Readiness is active as a near-term Aspire Anchor.

Future 0.01 loops should improve the conditions that make the plugin easier to recommend, justify, and eventually build without splitting the canonical rule set.

## Aspire Chain

```text
Plugin Readiness → Stars/adoption → Revenue → Enjoy life
```

This gives V13 a nearer direction than asking only whether each repair might increase stars.

## Readiness Surfaces

1. Recommendation clarity

   Would an AI or human understand why V13 is a plugin candidate?

2. Copy-friction evidence

   Is there evidence that `AGENTS.md` copy-paste is becoming a real setup friction?

3. External proof

   Does V13 work in another normal external repo without feature expansion?

4. Entry-path clarity

   Can a fresh reader understand what to copy first and what not to do yet?

5. Canonical stability

   Can `AGENTS.md` remain canonical without splitting the rule set?

6. Double-update avoidance

   Does this reduce future plugin update cost instead of creating more sync burden?

## What Counts as a Valid 0.01

A valid 0.01 may improve:

- recommendation clarity
- copy-friction evidence
- external proof
- entry-path clarity
- canonical stability
- double-update avoidance

It must improve readiness without creating plugin implementation.

## What Does Not Count

The following do not count as valid Plugin Readiness 0.01 loops:

- creating plugin scaffolding
- creating MCP, hooks, skills, automation, or packaging files
- splitting `AGENTS.md` from the canonical rule set
- launching marketing automation
- treating pluginization as active merely because it is desirable
- building before activation conditions are mostly true

## Boundary

Do not build plugin implementation in this loop.

Do not create plugin scaffolding.

Do not create MCP, hooks, skills, automation, CLI, server, package setup, schema changes, release files, V1 draft, Auto-Spend Gate implementation, marketing automation, or new features.

Do not touch external repos.

Pluginization activates only when the documented activation conditions are mostly true and the owner explicitly activates it.

## V12/V13 Interpretation

Plugin Readiness is now the near-term Aspire Anchor before Stars/adoption.

Future 0.01 loops should improve readiness surfaces while keeping plugin implementation parked and `AGENTS.md` canonical.

This is a CAP path, not a GO signal for plugin construction.

## Result

Signal:
🟢 BLUE / PLUGIN-READINESS-PATH-SELECTED
+
🟢 BLUE / NEAR-TERM-ASPIRE-ANCHOR-STABILIZED
+
🟡 YELLOW / DO-NOT-BUILD-PLUGIN-YET

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1

Existing External Gates:
AUTO-SPEND-GATE = automation-spend-gate repo

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
Plugin Readiness is now the near-term Aspire Anchor before Stars/adoption. Future 0.01 loops should improve readiness surfaces while keeping plugin implementation parked and AGENTS.md canonical.

## Next Loop

Select future 0.01 loops by Plugin Readiness surface while keeping plugin implementation parked.
