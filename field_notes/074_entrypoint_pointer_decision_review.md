# Field Note 074: Entrypoint Pointer Decision Review

Date: 2026-06-15

## Purpose

This note decides whether V13 should add a minimal pointer from currently visible entrypoints to the fork + Codex quickstart or examples start path, based on Field Note 073.

This is a decision review only.

It does not edit README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Evidence From Traffic

Field Note 073 recorded:

- 14-day clones: 1,248
- 14-day unique cloners: 417
- 14-day total views: 118
- 14-day unique visitors: 7

Popular content:

- Overview: 54 views / 7 unique visitors
- `/blob/main/AGENTS.md`: 11 views / 2 unique visitors
- `/blob/main/AGENTS.ja.md`: 4 views / 1 unique visitor
- `/blob/main/docs/ai_readin...`: 1 view / 1 unique visitor

Interpretation:

- clones are much stronger than page-reading
- Overview and AGENTS are visible entrypoints
- deep docs are not yet visible enough
- clone count must not be overclaimed as human understanding

Decision pressure:

```text
useful fork + Codex and examples paths exist, but observed human entrypoints may not expose them clearly
```

## Candidate Pointer Surfaces

### README Short Pointer

Assessment:

```text
strongest candidate, but edit must be bounded
```

Reason:

Overview is the visible human entrypoint. A tiny README pointer could route fork users to `docs/fork_codex_quickstart.md` without rewriting public copy.

Benefits:

- reduces ambiguity for human readers who start at Overview
- helps fork users after clone
- avoids adding more always-read content to `AGENTS.md`
- can be kept to one line or one small bullet

Risks:

- README/public-entry churn
- could become a broader public-copy rewrite if not capped
- traffic does not prove exact reader confusion yet

Gate tendency:

```text
CAP
```

### AGENTS.md Short Pointer

Assessment:

```text
not preferred
```

Reason:

`AGENTS.md` has some traffic, but it is an always-read / canonical operating surface. Adding navigation content there risks the exact context-bloat problem V13 is trying to avoid.

Benefits:

- visible to agents that read AGENTS
- could route agents to the quickstart or examples

Risks:

- AGENTS bloat
- canonical promotion pressure
- always-read surface expansion
- unnecessary if README can route human fork users

Gate tendency:

```text
HOLD
```

### AGENTS.ja.md Short Pointer

Assessment:

```text
not preferred
```

Reason:

`AGENTS.ja.md` has small traffic, but adding a pointer there would create translation/surface-sync pressure and canonical-entry expansion.

Benefits:

- may help Japanese readers who enter through `AGENTS.ja.md`

Risks:

- bilingual maintenance burden
- canonical surface expansion
- premature without evidence that Japanese readers need the quickstart pointer there

Gate tendency:

```text
HOLD
```

### docs/ai_reading_order.md Update

Assessment:

```text
reasonable but may not solve visible-entry problem
```

Reason:

`docs/ai_reading_order.md` is already intended for "ask the user's AI to read these files." Adding fork quickstart there would be semantically natural.

But traffic shows deep docs are barely reached, so this may improve internal structure without improving the observed entrypoint.

Benefits:

- docs-side edit
- avoids README/public copy
- fits current file purpose

Risks:

- may remain hidden
- could add another internal pointer without helping Overview readers

Gate tendency:

```text
CAP
```

### No Action Yet

Assessment:

```text
valid fallback, but less useful than a bounded decision toward README pointer
```

Reason:

The data is limited. Waiting avoids overreacting to small human-view samples.

However, the traffic pattern plus existing quickstart work suggests a real routing gap candidate.

Benefits:

- avoids premature edits
- avoids public/canonical churn

Risks:

- fork + Codex quickstart remains hidden from the main human entrypoint
- article/public work may proceed before entry routing is clean

Gate tendency:

```text
HOLD
```

## Candidate Destinations

### `docs/fork_codex_quickstart.md`

Assessment:

```text
best destination
```

Reason:

It directly answers the fork-user problem:

- what Codex should read first
- what V13 helps decide
- what not to edit
- what output to return
- where the start example is
- what reusable residue to leave

Gate tendency:

```text
GO as destination / CAP as edit
```

### `examples/README.md`

Assessment:

```text
useful secondary destination
```

Reason:

It identifies the start example, but it does not provide the full fork + Codex first request.

Gate tendency:

```text
CAP
```

### `examples/cap.v12_handoff_review.json`

Assessment:

```text
not best as direct pointer
```

Reason:

The example is useful, but raw JSON is not the best first destination for a beginner. It works better after the quickstart or examples README gives context.

Gate tendency:

```text
HOLD / CAP
```

### No Destination Yet

Assessment:

```text
not preferred
```

Reason:

The repo already has a good destination: `docs/fork_codex_quickstart.md`.

Gate tendency:

```text
HOLD
```

## Risk / Weight Check

Would a pointer reduce ambiguity?

```text
yes
```

Reason:

The quickstart exists, but observed human entrypoints do not yet show users reaching it.

Would it create README/public churn?

```text
low if one-line / one-bullet only
```

Reason:

The risk is manageable only if the future edit is strictly capped and does not become a README rewrite.

Would it bloat AGENTS?

```text
not if AGENTS is avoided
```

Reason:

The preferred surface avoids adding navigation text to the always-read operating file.

Would it imply canonical promotion?

```text
no if framed as a fork-user quickstart pointer
```

Reason:

A link to a docs-side quickstart does not change V13 rules, AGENTS instructions, or canonical status.

Would it help fork users after clone?

```text
likely
```

Reason:

Fork users who land on Overview would get a direct route to the copy-paste Codex request.

Would it overreact to low human visitor count?

```text
possible, but bounded if kept to one pointer
```

Reason:

The human sample is small. The edit should therefore be minimal and reversible, not a broad rewrite.

## Preferred Decision

Preferred decision:

```text
README pointer candidate
```

Destination:

```text
docs/fork_codex_quickstart.md
```

Reason:

Overview is the visible human entrypoint, and the fork + Codex quickstart is the best destination for a user who has cloned or forked but does not know what to ask Codex first.

The future edit should be:

```text
one bounded README pointer only
```

Not:

- README rewrite
- AGENTS pointer
- AGENTS.ja.md pointer
- docs-only pointer
- public launch copy
- canonical promotion

## Gate

V12 State:

```text
PASS
```

Reason:

The decision review evaluated traffic evidence, visible entrypoints, candidate surfaces, candidate destinations, risk/weight, and selected a bounded pointer candidate without editing protected surfaces.

V13 Next Loop Gate:

```text
CAP
```

Reason:

One pointer is justified only under a strict cap: a minimal README pointer to `docs/fork_codex_quickstart.md`. No README rewrite, AGENTS edit, public/canonical promotion, article writing, automation, or pluginization is authorized by this note.

## Recommended Next 0.01

Recommended next 0.01:

```text
If separately authorized, make one bounded README pointer edit to `docs/fork_codex_quickstart.md`.
```

Cap:

- one small pointer only
- no README rewrite
- no AGENTS edit
- no docs rewrite
- no public/canonical claims
- no article writing

If authorization is not given:

```text
park until more traffic or real fork-user evidence
```

## Boundaries

This is a decision review only.

Do not:

- edit README
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs
- edit schema
- edit examples
- edit prompts
- edit USE_CASES
- edit handoff files
- modify public or canonical surfaces
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- modify release state
- modify external repos
- write an article
- publish anything

## V13 Signal

Signal:
BLUE / ENTRYPOINT-POINTER-DECISION-REVIEW-RECORDED
+
BLUE / README-POINTER-CANDIDATE-SELECTED
+
BLUE / FORK-CODEX-QUICKSTART-DESTINATION-SELECTED
+
YELLOW / STRICT-ONE-POINTER-CAP
+
YELLOW / NO-README-EDIT-YET
+
YELLOW / NO-AGENTS-BLOAT
+
YELLOW / NO-PUBLIC-OR-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording the pointer decision review. Do not edit entrypoints without separate approval.
