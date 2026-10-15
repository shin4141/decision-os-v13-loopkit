# Qualified Outbound Cohort 001 — Send-Readiness Revision Receipt

Status: PASS / REVIEW HOLD
Validated: 2026-07-27 JST
Repository: `shin4141/decision-os-v13-loopkit`
Base commit: `3c9142692dfe60785a033b91ad7b6e5226712a93`
Branch: `codex/qualified-outbound-cohort-001`

## Completion result

The 20 organizations remain the research pool. The original 8/10 scoring threshold remains satisfied by all 20, but score is no longer sufficient for admission.

After applying Pain Ownership, Route-Purpose, Evidence-Boundary, and Economic-Parent as non-compensable gates:

- send-ready: **3**;
- HOLD: **5**;
- BLOCK: **12**;
- send-ready Group A / B: **0 / 3**;
- send-ready organizations: Dify / LangGenius, deepset / Haystack, and Inngest.

The missing Group A dimension is Route-Purpose. None of the Group A research candidates has a currently usable route that explicitly accepts this service proposal under the approved sender identity.

No email, form submission, direct message, issue comment, or other outreach occurred while producing or validating this revision.

## Exact output scope

Only these four existing PR files are revised:

1. `outreach/qualified_outbound_cohort_001.md`
2. `outreach/qualified_outbound_cohort_001.csv`
3. `outreach/outbound_observation_plan_001.md`
4. `validation/qualified_outbound_cohort_001_receipt.md`

Pricing, public claims, `README.md`, releases, private/public Canon files, and other pull requests are unchanged.

## Hard-gate result

| Research priority | Candidate | Decision | Non-passing gate or admission basis |
|---:|---|---|---|
| 1 | Letta | BLOCK | Business contact is not explicitly a vendor/implementation/partnership route. |
| 2 | Temporal | HOLD | Agency/SI route exists, but current sole-proprietor eligibility without a documented Temporal service line is not established. |
| 3 | n8n | HOLD | Program requires proven n8n experience and immediate enterprise-scale implementation capacity; approved proof is absent. |
| 4 | FlowiseAI | BLOCK | Verified route is support. |
| 5 | LangChain / LangGraph | HOLD | Partner form rejects personal email and requires company website plus delivered LangSmith implementations. |
| 6 | CrewAI | BLOCK | Buyer meeting route and repository-specific marketplace intake do not accept this proposal. |
| 7 | Dify / LangGenius | PASS | Official Service Partner program accepts external paid technical services. |
| 8 | deepset / Haystack | PASS | Official Services Partner form accepts hands-on implementation partners. |
| 9 | Agno | BLOCK | Buyer/product contact; no explicit service-partner purpose. |
| 10 | Trigger.dev | BLOCK | General contact lacks explicit vendor/partner purpose. |
| 11 | OpenHands | BLOCK | General contact and buyer-side Design Partner intake do not accept this proposal. |
| 12 | Composio | HOLD | Current product/platform partnership form does not establish fit for the approved service-only sender identity. |
| 13 | Mastra | HOLD | Partner route requires an already-shipped Mastra integration and public supporting assets. |
| 14 | Prefect | BLOCK | Buyer sales route; shared economic parent with Dagster and no distinct authority. |
| 15 | Pydantic | BLOCK | Buyer sales route; no verified service-partner route. |
| 16 | LiteLLM | BLOCK | Buyer Enterprise route. |
| 17 | LlamaIndex | BLOCK | Buyer sales route. |
| 18 | Mem0 | BLOCK | Buyer Enterprise route. |
| 19 | Dagster Labs | BLOCK | Program excludes the relevant individual/freelancer posture; shared economic parent with Prefect. |
| 20 | Inngest | PASS | Partnerships & Integrations explicitly accepts parties building with or alongside Inngest; static evidence limit is stated. |

## Required-correction validation

| Required correction | Result | Evidence |
|---|---|---|
| Preserve 20 researched candidates | PASS | 20 Markdown records and 20 CSV rows remain |
| Add four non-compensable gates | PASS | Gate matrix in Markdown and gate columns in CSV |
| Return actual count | PASS | 3; no attempt to force 20 |
| Prefect + Dagster one parent | PASS | Both use `economic_parent_id=prefect-dagster`; neither enters denominator |
| Buyer demo/sales/support routes | PASS | Reclassified HOLD/BLOCK; none enters denominator |
| Temporal actual-status eligibility | PASS | HOLD pending evidence that current sole-proprietor operation fits Agency/SI route |
| n8n actual-status eligibility | PASS | HOLD pending proven n8n delivery and enterprise implementation evidence |
| Evidence-boundary language | PASS | 20 advance rules and 20 drafts use verification invariants and state unconfirmed cause boundaries |
| Inferred Inngest evidence | PASS | Static analysis is not described as a production occurrence or confirmed ordering |
| Public credibility anchor | PASS | Every PASS draft links the complete public Before / After example |
| Consecutive business-day schedule | PASS | 2026-07-29 and 2026-07-30 |
| First cohort decision | PASS | 2026-08-14, 10 business days after the second send day; 2026-08-11 Japanese national holiday excluded |
| Rejected candidates retained | PASS | 17 HOLD/BLOCK records remain with exact reasons |
| External contact | PASS | None |
| Merge boundary | PASS | Draft PR only; merge HOLD |

## Research score and evidence validation

| Check | Result |
|---|---|
| Research-pool count | PASS — 20 |
| Original Group A / B count | PASS — 10 / 10 |
| Original minimum score | PASS — 9/10 |
| Score arithmetic | PASS — every total recomputes from five sub-scores |
| Public incident URL | PASS — one exact URL per candidate |
| Evidence class | PASS — observed / owner-reported / inferred |
| Closed-issue boundary | PASS — not treated as a current unresolved defect |
| Hypothesis promotion | PASS — no advance rule claims an unconfirmed root cause |
| Economic-parent uniqueness in denominator | PASS — 3 distinct parents |

## Newness and denominator validation

The prior-contact exclusion set remains read-only and unchanged:

- existing repository outreach records;
- the separate 13-13 sent record;
- Gmail Sent messages from 2026-06-01 through the research cut-off;
- follow-ups sent on 2026-07-26.

No research-pool candidate is a previously emailed contact. Prior emails and the 2026-07-26 follow-ups remain excluded from the numerator and denominator.

The fixed denominator is three. HOLD/BLOCK candidates cannot be replacements. A changed route or new eligibility proof requires a new gate audit and a re-fixed plan.

## Format and consistency validation

| Check | Result |
|---|---|
| Markdown candidate headings | PASS — 20 |
| Markdown required 18 fields per candidate | PASS |
| Markdown gate rows | PASS — 20 |
| Markdown complete research drafts | PASS — 20 |
| Markdown evidence-bounded rules | PASS — 20 |
| CSV parse | PASS — 20 rows, 37 columns |
| CSV research-priority sequence | PASS — integers 1 through 20 |
| CSV status count | PASS — PASS 3 / HOLD 5 / BLOCK 12 |
| CSV send-priority sequence | PASS — 1 through 3 for PASS only |
| CSV schedule boundary | PASS — dates only on PASS rows |
| CSV credibility anchors | PASS — present on all PASS rows only |
| Markdown / CSV evidence-rule and draft alignment | PASS |
| Private Sender Canon values | PASS — absent |
| Repository test suite | PASS — `python3 -m unittest discover -s tests -v`, 166 tests |
| `git diff --check` | PASS |
| Exact changed-file scope | PASS — four requested PR files only |
| Branch cleanliness after commit | PASS — no uncommitted or staged residue |

## Externalization boundary

Current Gate: **HOLD — receiving AI audit and Shin decision**

The three PASS rows are send-ready candidates, not send authorization. Every future send still requires Shin's explicit approval, route re-open, sender-field provenance, and a passing DOM field manifest.

HOLD/BLOCK research drafts are not sendable. No merge, send, follow-up, reply, form completion, or other external action is authorized by this receipt.

## Completion line

The PR distinguishes researched candidates from genuinely send-ready prospects, and every denominator unit passes pain ownership, route purpose, evidence boundary, and economic-parent identity as hard gates.
