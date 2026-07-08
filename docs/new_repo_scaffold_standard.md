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
- Completion Line
- Missing Closure
- Next Owner
- First One Action
- Do Not Continue Boundary
- What must not be returned to Shin

## Do Not Authorize

Adding this scaffold does not authorize implementation, outreach, public posting, pricing, release, scraping, API, automation, or target selection.
