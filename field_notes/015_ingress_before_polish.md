# Ingress Before Polish

Date: 2026-06-13

## Context

Recent V13 work improved internal repair loops:

- invalid-target guard observation
- fresh external entrypoint proof
- command-room / local-gate split
- final-report cleanliness rule
- Auto-Spend Gate external boundary correction
- documentation drift repair

These repairs made V13 better at cleaning docs, reducing ambiguity, fixing boundaries, recording field notes, and preserving CAP.

## Observation

V13 is becoming good at internal repair.

That is useful, but internal repair can become lower EV when it is no longer blocking entry, trust, restartability, or safe execution.

If adoption or user inflow is the active bottleneck, repeated internal polish may have declining EV.

This does not mean internal repair is bad.

It means the next 0.01 loop should classify the surface before choosing another repair.

## House-Cleaning Analogy

If no one is entering, do not keep polishing the room.

Improve or test an entry path unless an internal blocker prevents entry.

Alternative canon:

If adoption is the bottleneck, prefer external inflow over internal polish unless the internal issue blocks entry.

## Surface Classification

Before selecting the next 0.01 loop, classify the surface:

1. Internal Repair
2. External Inflow
3. Proof / Evidence
4. Carrier Protection

## Internal Repair vs External Inflow

Internal Repair is high EV when it removes a blocker to entry, trust, restartability, or safe execution.

External Inflow is high EV when the repo is usable enough but few people are entering.

Proof / Evidence is high EV when claims need observation before public push.

Carrier Protection is high EV when the operator is overloaded or the loop risks consuming future capacity.

## Why This Matters

Without this classification, V13 can keep finding small internal cleanup tasks even when the larger bottleneck has moved outside the room.

The surface check helps prevent polishing from replacing entry-path testing.

It also prevents the opposite mistake: chasing attention when an internal blocker still prevents safe entry.

## V12/V13 Interpretation

This note adds a pre-selection check for the next 0.01 loop.

It does not launch marketing automation.

It does not tell V13 to chase attention blindly.

It does not replace CAP.

It asks V13 to decide whether the next 0.01 belongs to Internal Repair, External Inflow, Proof / Evidence, or Carrier Protection.

## Boundary

This note does not create an Ingress Gate.

This note does not create posting drafts.

This note does not create marketing automation.

This note does not authorize dependencies, automation, CI, hooks, skills, MCP, CLI, server, package setup, schema changes, plugin implementation, release files, V1 draft, Auto-Spend Gate implementation, or new features.

External repos were not touched.

## Result

Signal:
🟢 BLUE / INGRESS-BEFORE-POLISH-IDENTIFIED
+
🟢 BLUE / NEXT-0.01-SURFACE-CLASSIFICATION-ADDED
+
🟡 YELLOW / DO-NOT-LAUNCH-MARKETING-AUTOMATION

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1

Existing External Gates:
AUTO-SPEND-GATE = automation-spend-gate repo

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
Internal repair loops are now working, but repeated polishing has declining EV if adoption or user inflow is the active bottleneck. V13 needs a pre-selection check to decide whether the next 0.01 belongs to Internal Repair, External Inflow, Proof / Evidence, or Carrier Protection.

## Next Loop

Use the surface classification before selecting the next 0.01 loop.
