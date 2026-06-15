# Field Note 073: Traffic-Based Entrypoint Review

Date: 2026-06-15

## Purpose

This note reviews the current V13 entrypoint strategy using the provided GitHub Traffic data.

This is an evidence note only.

It does not edit README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Traffic Snapshot

14-day clones:

```text
1,248
```

14-day unique cloners:

```text
417
```

14-day total views:

```text
118
```

14-day unique visitors:

```text
7
```

Popular content:

| Content | Views | Unique visitors |
| --- | ---: | ---: |
| Overview | 54 | 7 |
| `/blob/main/AGENTS.md` | 11 | 2 |
| `/blob/main/AGENTS.ja.md` | 4 | 1 |
| `/blob/main/docs/ai_readin...` | 1 | 1 |

## Main Observation

Clone activity is much stronger than human page-reading activity.

The repo may be pulled, mirrored, inspected by tools, or fetched more than it is read deeply by humans in the GitHub UI.

Human readers mostly touch:

- Overview
- a little `AGENTS.md`
- very little deep documentation

Deep docs are not yet visible enough from traffic evidence.

In one line:

```text
traffic currently supports an entrypoint problem, not a public-readiness conclusion
```

## Interpretation Boundary

Do not treat clone count as proof of human understanding.

High clone count may reflect:

- automated fetches
- fork or clone curiosity
- tool-side inspection
- repeated local or remote access
- non-human traffic

Do not treat low views as proof of no value.

Low view count may reflect:

- people cloning before reading
- agents or tools reading files outside the GitHub UI
- early-stage discovery
- unclear entry routing
- small human sample size

This data supports a Codex-first / fork-user restartability strategy more than a theory-first article strategy.

## Entry-Point Risk

`docs/fork_codex_quickstart.md` exists.

But traffic does not yet show that human visitors reach it.

`examples/README.md` exists.

But traffic does not yet prove users reach it.

Current visible entry may still be:

- Overview
- `AGENTS.md`
- possibly `AGENTS.ja.md`

Risk:

```text
the repo may have useful reconnectable manuals that are not yet discoverable from the observed human entrypoints
```

## Current Strategy Implication

Current strategy:

- keep article/public promotion at `CAP` or `HOLD`
- continue strengthening repo-internal restartability
- continue strengthening the fork + Codex path
- do not rewrite README from this data alone
- do not overreact to clones
- do not treat traffic as proof of public comprehension

The traffic supports caution:

```text
improve entrypoint evidence before broad public explanation
```

## Possible Next 0.01 Candidates

### README Pointer To Fork Quickstart

Assessment:

```text
possible but not yet authorized
```

Reason:

Overview is the main human entrypoint, so README may eventually need to point readers toward the fork + Codex quickstart.

Risk:

- README/public-entry edits remain sensitive
- data does not prove reader confusion yet
- could become public-copy churn

Gate tendency:

```text
CAP / HOLD
```

### AGENTS.md Pointer To Examples Quickstart

Assessment:

```text
possible but not first
```

Reason:

`AGENTS.md` has some traffic, but it is a canonical operating surface. A pointer there could help agents reconnect to examples, but AGENTS promotion remains HOLD.

Risk:

- canonical surface pressure
- instruction bloat
- always-read surface expansion

Gate tendency:

```text
HOLD
```

### Docs Discoverability Note

Assessment:

```text
possible
```

Reason:

A docs-side discoverability note could preserve public/README boundaries while improving internal navigation. However, deep docs are not currently visible in traffic, so a docs-only note may not help the observed human entrypoint.

Risk:

- may improve structure without improving discoverability
- could add another hidden file

Gate tendency:

```text
CAP
```

### No Action Until More Traffic

Assessment:

```text
valid fallback
```

Reason:

The data is suggestive but not definitive. Waiting avoids premature README or AGENTS edits.

Risk:

- entrypoint ambiguity remains
- fork + Codex quickstart may stay hidden from human visitors

Gate tendency:

```text
HOLD
```

### External Article Later

Assessment:

```text
not next
```

Reason:

Field Note 072 prepared an article outline review, but this traffic suggests public explanation should remain capped until entrypoint routing is understood better.

Risk:

- theory-first article may attract attention before the repo path is easy to follow
- could overclaim from clone counts

Gate tendency:

```text
CAP / HOLD
```

## Recommended Next 0.01

Recommended next 0.01:

```text
Run a bounded entrypoint-pointer decision review.
```

Purpose:

Decide whether the current traffic justifies one small pointer from the observed human entrypoint toward the fork + Codex quickstart.

Likely review question:

```text
Should the repo add a minimal pointer to docs/fork_codex_quickstart.md, and if so, what is the safest surface?
```

This is not an edit recommendation yet.

Do not edit README, AGENTS, docs, or public/canonical surfaces from this note alone.

## Gate

V12 State:

```text
PASS
```

Reason:

The traffic snapshot was recorded, interpretation boundaries were set, entrypoint risk was identified, possible next 0.01 candidates were compared, and no protected surfaces were changed.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The data supports a bounded entrypoint-pointer decision review, but not README edits, AGENTS edits, article drafting, public promotion, canonical promotion, automation, or pluginization.

## Boundaries

This is an evidence note only.

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
BLUE / TRAFFIC-BASED-ENTRYPOINT-REVIEW-RECORDED
+
BLUE / CLONE-ACTIVITY-STRONGER-THAN-HUMAN-PAGE-READING
+
BLUE / OVERVIEW-AND-AGENTS-ARE-VISIBLE-ENTRYPOINTS
+
YELLOW / DEEP-DOCS-NOT-YET-VISIBLE-IN-TRAFFIC
+
YELLOW / DO-NOT-OVERCLAIM-CLONES
+
YELLOW / ENTRYPOINT-POINTER-DECISION-REVIEW-CANDIDATE
+
YELLOW / NO-README-OR-AGENTS-EDIT

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording the traffic-based entrypoint review. Do not edit README, AGENTS, docs, public/canonical surfaces, write articles, or implement anything without separate approval.
