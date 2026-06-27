# LLM Wiki and V13 Context Boundary

## Observation

The LLM Wiki direction is closely related to Decision-OS V11.

It focuses on:

- not loading everything every time
- reading only the needed context
- using an index or router to guide the AI
- reducing context-loading cost
- avoiding bloated `AGENTS.md` / `CLAUDE.md`
- making forgotten or compressed context reconnectable

This is important, but it is not the same layer as V13.

## Layer distinction

LLM Wiki asks:

- where should context live?
- which context should the AI read?
- how can the AI avoid rereading everything?
- how can context be routed or indexed?
- how can always-loaded instructions stay thin?

V13 asks:

- may this context be trusted for the current decision?
- is this context stale, superseded, unverified, or historical-only?
- should this context be passed into the next loop?
- should the next AI loop be `GO / HOLD / CAP / BLOCK`?
- what must return to the human seat before continuation?
- did failure, drift, or uncertainty become future decision material?

## Core distinction

```text
LLM Wiki reduces context-loading cost.
V13 reduces context-misuse and next-loop risk.
```

Japanese framing:

```text
LLM Wikiは、文脈を軽く読むための基盤。
V13は、読んだ文脈を使って次のAIループを回してよいかを判定するOS。
```

## Relationship to V11 and V13

LLM Wiki is V11-adjacent:

- reconnectable memory
- compression without losing the ability to find context
- index / router / selective reading
- stale-context reduction

V13 is downstream of that:

- context validity
- loop permission
- continuation gates
- `GO / HOLD / CAP / BLOCK`
- human-seat return
- next-loop safety

## Lightweight V13 router idea

V13 may later use a lightweight context index such as `CONTEXT_INDEX.md`.

Example future shape:

```md
# V13 Context Index

## Always read
- README
- AGENTS.md
- current handoff

## Use when needed
- Field Notes
- MISTAKEN
- Handoff examples
- Context Compression
- Tutorial Capsule
- Health Check prompt

## Do not trust without recheck
- old posts
- stale screenshots
- outdated experiments
- parked ideas

## Ask human before using
- public messaging
- performance claims
- new V14 concepts
- repo-wide changes
```

However, this note does not create that file now.

## Strategic meaning

V13 is not competing with LLM Wiki.

If LLM Wiki-like structures become common, the next problem becomes:

- which retrieved context is still valid?
- which context is stale?
- which context should not be used?
- which context allows continuation?
- which context requires human confirmation?

That is V13's layer.

## Boundary

Do not implement LLM Wiki now.

Do not create `CONTEXT_INDEX.md` now.

Do not expand `AGENTS.md`.

Do not add new routing machinery.

This note only records the boundary and future direction.

## Status

Signal captured.

No LLM Wiki implementation.
No context-index file.
No README expansion beyond the separate thin `Ask your AI first` block.
No AGENTS.md change.
