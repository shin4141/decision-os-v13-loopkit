# GOAL Health Overlay Loop

## One-line claim

GOAL-style execution moves the loop; LoopKit keeps the map healthy enough for the next 0.01 action.

## Problem

AI execution loops can keep moving even when the map is weakening:

- context is getting long
- anchors are fading
- the next action is visible but not dependency-valid
- the model may jump to a future node
- Seat may drift
- handoff or split may be needed before external action

The failure is not that the AI cannot execute.
The failure is that execution continues after the map becomes weak.

## Loop before

1. GOAL-style execution continues.
2. The next visible task appears useful.
3. Context pressure or route uncertainty increases.
4. The AI continues anyway.
5. The loop jumps beyond the dependency frontier or loses returnability.

## LoopKit intervention

LoopKit adds a health overlay around execution:

- Next Action Card
- Loop Map Confidence
- Required Confidence
- Context Risk Modifier
- Route Fidelity
- Returnability
- Consult Mode
- Handoff / Split / Stop choices

Proceed only when:

`Loop Map Confidence >= Required Confidence`

and

`Context Risk is not RED`

## Loop after

1. GOAL-style execution continues while the map is healthy.
2. If Context Risk is YELLOW, Required Confidence is raised and Consult / Handoff / Split is surfaced.
3. If the dependency frontier is unclear, Route Fidelity weakens.
4. If recovery is unclear, Returnability weakens.
5. Consult Mode asks one question and returns Seat to the human.
6. The loop either continues under cap, splits, hands off, or stops before breaking.

## Key rule

`Loop Map may see islands. Next Action must not jump to islands.`

Japanese:
`Loop Mapは飛び地で見えてよい。Next Actionは飛び地に飛んではいけない。`

## Consult rule

`Consult Mode returns Seat before the loop breaks.`

Japanese:
`Consult Modeは、ループが壊れる前にSeatを人間へ戻す。`

## Minimal example

A docs loop is moving quickly.
A future node is visible: public post or Forward Future Loop Library submission.
But Context Risk is YELLOW and Route Fidelity is not high enough.

LoopKit produces a Next Action Card:

- Context Risk: YELLOW
- Base Required Confidence: 70
- Modifier: +10
- Adjusted Required Confidence: 80
- Loop Map Confidence: 76
- Route Fidelity: Medium / weak
- Returnability: Medium
- Recommended next: Consult or split/handoff before external action

The loop does not stop forever.
It avoids jumping to a future node before the dependency frontier is ready.

## What this is not

This is not:

- an execution engine
- automatic decision-making
- a replacement for GOAL-style execution
- a slowdown protocol
- a productized automation system

It is:

- a map-health overlay
- a missing-context injector
- a Seat-return mechanism
- a recovery path before context failure

## Library candidate status

Status:
Draft candidate.

V12 State:
PASS.

V13 Next Loop Gate:
CAP.

Scope:
Docs-only MVP candidate.
No hooks, MCP, pluginization, automation, or execution engine.
