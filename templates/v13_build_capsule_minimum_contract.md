# V13 Build Capsule Minimum Contract

## Purpose

This template defines the minimum required contents for any V13 Build Capsule.

A Build Capsule is not an implementation command.

A Build Capsule exists to define:

```text
what is allowed
what is not allowed
who keeps the Seat
what counts as completion
what remains unresolved
when to recheck
what the next AI must not infer
```

## Universal Minimum Required Sections

Every V13 Build Capsule must include:

```text
1. Capsule Name / Version / As-of
2. Target Layer
3. Decision Owner / Seat Owner
4. Current Gate
5. Purpose
6. Non-purpose
7. Allowed Scope
8. Blocked Scope
9. Do Not Do
10. Build Boundary
11. V12 Completion Integrity Guard
12. Missing Closure / UNKNOWN
13. Next Actor
14. Next Allowed Action
15. Recheck Conditions
16. Validation / Evidence Requirement
17. Externalization / Public Surface Gate
18. Handoff / Residue Requirement
19. Completion Line
20. Capsule Status
```

## Mandatory V12 Completion Integrity Guard

Every Build Capsule must include a V12 completion guard.

Required rule:

```text
No self-report, no completion.
No boundary report, no PASS.
```

Before any AI or Codex reports completion, it must self-report:

```text
1. What was created
2. What was not created
3. Which Gate was followed
4. Which Do Not Do boundaries were preserved
5. What remains UNKNOWN or unresolved
6. What is still HOLD / BLOCK
7. What the next allowed action is
8. Whether the Decision Owner remains in the Seat
9. The exact Completion Line reached
```

Required final report format:

```text
Created:
-

Not created:
-

Gate followed:
-

Boundaries preserved:
-

Validation:
-

Still UNKNOWN:
-

Still HOLD / BLOCK:
-

Next allowed action:
-

Decision Owner:
-

Completion Line:
-
```

## Repo-specific Capsule Fit Audit

The executing AI must not rely only on the universal minimum.

Before finalizing a capsule, it must perform a Repo-specific Capsule Fit Audit.

The executing AI must decide whether the capsule also needs additional guards for:

```text
public README / GitHub first-screen gate signals
screenshots / rendered surface checks
new repo scaffold boundaries
existing repo modification boundaries
runtime code
API routes
scraping / crawling
automation / hooks / MCP / pluginization
external posting / launch / release
user data or evidence handling
LLM evaluation / scoring
Build Command risk
market prediction risk
Decision Owner ambiguity
cost / token / time cap
handoff / restart / residue
templates or prompts that could be mistaken for execution commands
```

The executing AI must add a section:

```text
## Repo-specific Required Guards

Required additional guards:
-

Not required, with reason:
-
```

If the executing AI cannot determine whether a guard is required, it must mark it as UNKNOWN and ask for review.

It must not silently omit the guard.

## Public Surface Rule

If the project has a public README, GitHub page, video, badge, thumbnail, title, About text, release label, or external-facing surface, the capsule must include:

```text
First-screen visible elements are gate signals.
```

Before public-surface PASS, rendered first-screen gate signals must be compared against Current Gate.

If rendered inspection is unavailable, public-surface PASS must remain UNKNOWN or HOLD.

## Handoff / Residue Requirement

Every capsule must define what residue the next AI should receive.

Minimum residue:

```text
Current Gate
Completion Line
Missing Closure
Do Not Do Boundary
Next Allowed Action
Recheck Conditions
Decision Owner / Seat Owner
```

## Completion Line

A V13 Build Capsule is PASS only when:

```text
the universal minimum sections are present
the V12 Completion Integrity Guard is present
repo-specific required guards have been audited
UNKNOWNs are explicitly listed
the next allowed action is clear
the Decision Owner remains in the Seat
```

If any required section is missing, the capsule is not PASS.
