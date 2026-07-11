# New Repo Scaffold Standard

When creating a new repo/workspace capsule, include the minimal restartability scaffold.

## Required Files

- README.md
- AGENTS.md
- handoff/current_handoff.md
- docs/handoff_command.md

If the repo may involve external contact, also include:

- docs/contact_readiness_card.md

If the repo may involve audit work, also include:

- docs/audit_card_template.md

## Handoff Command Requirement

- `docs/handoff_command.md` must define how to produce a compact, paste-ready next-chat handoff.
- `AGENTS.md` must include:

```text
When the user selects `Handoff`, follow `docs/handoff_command.md`.
```

## Required Handoff Fields

- Target Layer
- Repo Root
- Current Gate
- Active Branch
- Next Authorized Action
- Completion Line
- Missing Closure
- Next Owner
- First One Action
- Do Not Continue Boundary
- What must not be returned to the Decision Owner

`First One Action: none` is valid only when `Active Branch: none` and `Next Authorized Action: none` are both explicit, no unfinished work or `UNKNOWN` ownership remains, and no routine investigation, diff, verification, Git operation, or cleanup remains executable by the receiving AI. Otherwise the handoff must name the earliest bounded action and its owner.

## Do Not Authorize

Adding this scaffold does not authorize implementation, outreach, public posting, pricing, release, scraping, API, automation, or target selection.
