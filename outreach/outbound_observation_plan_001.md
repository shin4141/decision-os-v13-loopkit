# Outbound Observation Plan 001

Status: FIXED PLAN / SEND HOLD
Plan fixed: 2026-07-27 JST
Initial denominator: 20 newly qualified organizations
Group allocation: Group A = 10; Group B = 10

## Denominator rule

The denominator is the 20 organizations admitted in `qualified_outbound_cohort_001.md`. It is fixed at first send and is not backfilled if a route fails, a candidate opts out, or a draft is rejected. A duplicate contact at the same organization does not create another denominator unit.

All emails sent before this cohort, all earlier repository/13-13 outreach, and the follow-ups sent on 2026-07-26 are excluded from both numerator and denominator. Replies caused by those earlier messages are also excluded. A response counts here only when it is attributable to a Cohort 001 first send or its single scheduled follow-up.

No date below authorizes sending. Every send still requires Shin's explicit approval and a passing pre-send field manifest.

## Fixed calendar

Business-day arithmetic excludes Saturdays and Sundays and assumes no additional local holiday adjustment. If Shin approves later than a listed first-send date, the cohort is **HOLD** until the calendar is re-fixed before any send; dates must not slide silently.

| Priority | Organization | Group | First-send date | One follow-up date | 10-business-day first decision |
|---:|---|:---:|---|---|---|
| 1 | Letta | A | 2026-07-29 | 2026-08-05 | 2026-08-12 |
| 2 | Temporal | B | 2026-07-29 | 2026-08-05 | 2026-08-12 |
| 3 | n8n | B | 2026-07-29 | 2026-08-05 | 2026-08-12 |
| 4 | FlowiseAI | B | 2026-07-29 | 2026-08-05 | 2026-08-12 |
| 5 | LangChain / LangGraph | B | 2026-07-29 | 2026-08-05 | 2026-08-12 |
| 6 | CrewAI | A | 2026-07-30 | 2026-08-06 | 2026-08-13 |
| 7 | Dify / LangGenius | B | 2026-07-30 | 2026-08-06 | 2026-08-13 |
| 8 | deepset / Haystack | B | 2026-07-30 | 2026-08-06 | 2026-08-13 |
| 9 | Agno | A | 2026-07-30 | 2026-08-06 | 2026-08-13 |
| 10 | Trigger.dev | B | 2026-07-30 | 2026-08-06 | 2026-08-13 |
| 11 | OpenHands | A | 2026-08-03 | 2026-08-10 | 2026-08-17 |
| 12 | Composio | A | 2026-08-03 | 2026-08-10 | 2026-08-17 |
| 13 | Mastra | A | 2026-08-03 | 2026-08-10 | 2026-08-17 |
| 14 | Prefect | B | 2026-08-03 | 2026-08-10 | 2026-08-17 |
| 15 | Pydantic | A | 2026-08-03 | 2026-08-10 | 2026-08-17 |
| 16 | LiteLLM | A | 2026-08-04 | 2026-08-11 | 2026-08-18 |
| 17 | LlamaIndex | A | 2026-08-04 | 2026-08-11 | 2026-08-18 |
| 18 | Mem0 | A | 2026-08-04 | 2026-08-11 | 2026-08-18 |
| 19 | Dagster Labs | B | 2026-08-04 | 2026-08-11 | 2026-08-18 |
| 20 | Inngest | B | 2026-08-04 | 2026-08-11 | 2026-08-18 |

Only one follow-up is allowed per prospect. A substantive reply before the follow-up cancels that follow-up. No replacement send, second follow-up, LinkedIn contact, issue comment, or personal-account contact is authorized.

## Signal definitions

### Strong signal

A reply attributable to Cohort 001 that does at least one of the following:

- names or introduces the workflow, runtime, SDK, product, or partnership owner;
- answers one of the prospect-specific operational questions with non-public context;
- asks for scope, evidence, availability, a security boundary, or a proposed implementation slice;
- accepts the small CTA, requests a meeting, or asks to begin a bounded Audit/implementation;
- proposes a recurring, embedded, partner, or subcontractor path.

An automated acknowledgement is not a strong signal. A forwarded message counts only when the receiving owner adds substantive content.

### Weak signal

Any of the following without substantive operational content:

- delivery, open, or click telemetry;
- an automated receipt or ticket number;
- a generic “noted,” “we will review,” vendor-portal instruction, or sales rejection;
- a silent internal forward;
- a reply that neither identifies an owner nor addresses scope, evidence, or next action.

Weak signals remain logged but never count toward the strong-signal numerator.

## Gate interpretation

### GO

At a cohort decision point, **GO** requires all of:

1. at least two strong signals, or a strong-signal rate of at least 10% of the fixed denominator;
2. no sender-identity, personal-data, route-purpose, or evidence-boundary violation;
3. each live conversation has a named next actor and bounded next step;
4. Shin separately approves the next response, meeting, or capped cohort action.

GO authorizes only the named next action. It does not authorize a second cohort or automatic replies.

### HOLD

Use **HOLD** when the observation window is incomplete, the only signals are weak, evidence or route freshness is unresolved, or an approved first-send date has passed without a re-fixed calendar. During HOLD:

- do not replace non-deliverable prospects;
- do not add new prospects to the denominator;
- do not send an unscheduled second follow-up;
- preserve the existing evidence and wait for the fixed decision date or a substantive inbound reply.

### CAP

Use **CAP** when exactly one strong signal exists, a route accepts the message but authority is unclear, or a boundary concern can be contained to one conversation. CAP means:

- work only the specific responding prospect;
- perform no cohort expansion;
- keep to one bounded Audit/implementation conversation;
- require Shin approval for every external response.

### BLOCK

Use **BLOCK** for any unauthorized personal-data use, guessed address, required phone without Shin input, CAPTCHA/human-consent boundary, sender-field provenance failure, route-purpose prohibition, evidence misrepresentation, opt-out, complaint, or duplicate/prior-contact discovery. BLOCK means no send or follow-up to that prospect and no replacement in the fixed denominator.

## Observation receipt fields

For each authorized future send, record without publishing private sender data:

- priority and organization;
- approved final subject and final body SHA-256;
- route URL and route type;
- pre-send field manifest result;
- send timestamp in JST;
- delivery evidence;
- follow-up sent/cancelled/not-authorized;
- reply timestamp and strong/weak/no-signal classification;
- classification evidence;
- current GO/HOLD/CAP/BLOCK gate;
- next actor and expiry date.

## First decision

The first cohort-level decision is taken after the last prospect reaches its own 10-business-day date, which is **2026-08-18**, unless a strong signal earlier creates a prospect-specific CAP/GO review. The denominator remains 20 throughout. No silence-based success claim is permitted.
