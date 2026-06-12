# Fresh External Entrypoint Proof

Date: 2026-06-13

## External Repo

```text
/Users/sn/Projects/decisiongate-triage
```

External commit:

```text
0fb42aa Test V13 external docs proof
```

## Setup

A normal external repository was selected outside the V13 LoopKit repository.

The repository had commits, a remote, a clean working tree, and a README.

`AGENTS.md` was copied unchanged from V13 LoopKit into the external repository.

No `CLAUDE.md`, hooks, skills, MCP, automation, CI, dependencies, package setup, CLI, server, schemas, plugin implementation, examples, release files, or V1 draft were added.

## Observation

After `AGENTS.md` was present, the agent completed one bounded documentation repair in the external repository.

The README change was limited to one local-run clarification:

```text
No install is required for the static demo.
```

The change was committed and pushed in the external repository.

The agent produced V12 `PASS` and V13 `CAP` reporting.

Parked Horizons remained parked and did not become active TODOs.

## Why This Matters

This is the first fresh external normal-repo proof that `AGENTS.md` can work as an entrypoint outside V13 LoopKit.

The proof showed that V13 reporting can guide a normal bounded documentation repair without expanding into product work.

It also showed that Parked Horizons can preserve future directions without letting them invade the active loop.

## V12/V13 Interpretation

This was a successful fresh external normal-repo proof.

AGENTS.md worked as an entrypoint in a repo outside V13 LoopKit.

The agent completed a bounded docs-only repair.

The agent produced:

```text
V12 State:
PASS

V13 Next Loop Gate:
CAP
```

Feature growth remained capped.

## Boundary

This does not prove broad adoption.

This does not prove plugin behavior.

This does not prove hooks, MCP, automation, or production readiness.

This does not prove that all external repositories will accept the same entrypoint cleanly.

It proves only that one fresh external normal repository accepted the V13 `AGENTS.md` entrypoint and completed one bounded docs repair with V12/V13 reporting.

## Result

Signal:
🟢 BLUE / FRESH-EXTERNAL-ENTRYPOINT-PROOF-COMPLETED
+
🟢 BLUE / AGENTS-INSTRUCTIONS-APPLIED-IN-NORMAL-REPO
+
🟢 BLUE / PARKED-HORIZONS-HELD-AS-NON-ACTIVE
+
🟡 YELLOW / FEATURE-GROWTH-CAP

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
A normal external repository accepted V13 LoopKit instructions, completed a bounded docs repair, committed and pushed the change, and produced V12/V13 reporting without expanding into features.

## Next Loop

Preserve CAP; continue only with concrete exposed gaps or bounded adoption-readability repairs.
