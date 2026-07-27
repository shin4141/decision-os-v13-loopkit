# Qualified Outbound Cohort 001 — Validation Receipt

Status: PASS / REVIEW HOLD
Validated: 2026-07-27 JST
Repository: `shin4141/decision-os-v13-loopkit`
Base commit: `3c9142692dfe60785a033b91ad7b6e5226712a93`
Branch: `codex/qualified-outbound-cohort-001`

## Completion result

Twenty organizations honestly pass the admission threshold. The cohort contains 10 Group A prospects and 10 Group B prospects. The lowest score is 9/10; no threshold relaxation or replacement candidate was used.

No email, form submission, direct message, issue comment, or other outreach occurred while producing or validating this cohort.

## Exact output scope

Only these four files are in scope:

1. `outreach/qualified_outbound_cohort_001.md`
2. `outreach/qualified_outbound_cohort_001.csv`
3. `outreach/outbound_observation_plan_001.md`
4. `validation/qualified_outbound_cohort_001_receipt.md`

Pricing, public claims, `README.md`, releases, private/public Canon files, and existing pull requests are unchanged.

## Qualification validation

| Check | Result | Evidence |
|---|---|---|
| Candidate count | PASS | 20 numbered Markdown records and 20 CSV data rows |
| Group allocation | PASS | Group A = 10; Group B = 10 |
| Minimum admission score | PASS | Minimum 9/10; maximum 10/10 |
| Score arithmetic | PASS | Every total equals the five recorded sub-scores |
| Unique organizations | PASS | 20 unique organization labels; no duplicate-organization exception used |
| Ongoing AI/agent/automation workflow | PASS | Every candidate scores 2/2 |
| Public operational reason | PASS | Every record includes one exact public GitHub issue URL and an evidence class |
| Evidence language | PASS | Closed issues are treated as historical boundaries; inferred analysis is identified rather than reported as an incident |
| Recurrence or expansion case | PASS | Every record states a workflow-specific recurrence path |
| Rule shown in advance | PASS | Every record and draft contains one operational rule before the CTA |
| Unresolved questions | PASS | Every record contains three workflow-specific questions |
| Exactly one proposed next step | PASS | Every draft closes with one small prospect-specific CTA |
| Professional contact route | PASS | Every route is an official company form, designated partner/sales route, or officially published business address |
| Prohibited routes | PASS | No guessed address, personal-only account, commit metadata, issue-comment outreach, broker data, or private identity source is used |
| Guarantee language | PASS | No prevention, safety, productivity, or effectiveness guarantee is made |
| “Free fit check” framing | PASS | Phrase absent; it is not used as the value proposition |

## Newness and denominator validation

The exclusion set was built read-only from:

- existing repository outreach records;
- the separate 13-13 sent record;
- Gmail Sent messages from 2026-06-01 through the research cut-off;
- follow-ups sent on 2026-07-26.

Candidate organization labels and the public entities behind them were compared against that exclusion set. No admitted candidate is a previously emailed contact. Private addresses discovered during the read-only check are neither reproduced here nor copied into cohort artifacts.

The observation plan fixes:

- the initial denominator at 20;
- Group A / B at 10 / 10;
- a first-send date, one follow-up date, and a 10-business-day first decision date for every prospect;
- strong- and weak-signal definitions;
- GO / HOLD / CAP / BLOCK interpretation;
- the exclusion of prior emails and the 2026-07-26 follow-ups from this cohort's numerator and denominator.

The dates are observation controls, not send authority. A missed first-send date forces calendar re-approval rather than silent date movement.

## Format and consistency validation

| Check | Result |
|---|---|
| Markdown candidate headings | PASS — 20 |
| Markdown required 18 fields per candidate | PASS |
| Markdown complete email drafts | PASS — 20 |
| Markdown advance-value rules | PASS — 20 |
| CSV parse | PASS — 20 rows, 27 columns |
| CSV priority sequence | PASS — integers 1 through 20 |
| CSV Group A / B count | PASS — 10 / 10 |
| CSV score floor and arithmetic | PASS — all totals 9–10 and recomputed |
| CSV evidence and contact route fields | PASS — non-empty, explicit URL/scheme |
| CSV subjects, drafts, rules, and dates | PASS — complete |
| Markdown / CSV organization order | PASS — priorities 1 through 20 align |
| Private sender email / company-field value in outputs | PASS — absent |
| `git diff --check` | PASS |
| Exact changed-file scope | PASS — four requested files only |
| Branch cleanliness after commit | PASS — no uncommitted or staged residue |

## Externalization boundary

Current Gate: **HOLD — receiving AI audit and Shin send-cohort decision**

The Draft PR is review material only. Merge is HOLD. First sends, follow-ups, replies, form completion, and any other external action remain unauthorized until Shin approves a final send cohort and the applicable pre-send provenance check passes.

## Completion line

Twenty genuinely qualified prospects are presented as a reviewable cohort with public evidence, individualized advance value, official professional routes, complete email drafts, and a fixed observation calendar. No contact has occurred.
