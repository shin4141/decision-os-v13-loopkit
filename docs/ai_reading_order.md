# AI Reading Order

Use this when a user does not want to understand V13 directly at first.

Ask the user's AI to read these files in order, then recommend how V13 should fit the target repository.

## Read In This Order

1. `README.md`

   Understand what this repository is and the fastest first-use path.

2. The Lite Footer section in `README.md`

   Understand the no-install first benefit.

3. `docs/plugin_surface_spec.md`

   Understand why pluginization is parked and what would make it worth activating later.

4. `field_notes/013_fresh_external_entrypoint_proof.md`

   Understand that V13 worked in an external normal repo.

5. `field_notes/017_second_external_proof_copy_friction.md`

   Understand `AGENTS.md` copy friction and existing instruction-surface conflict.

6. `field_notes/018_aspire_fit_adoption_modes.md`

   Understand adoption modes for repos that already have their own instruction surface.

## Ask The AI To Answer

1. What problem does V13 solve for this repo?
2. Is this repo better served by:
   - keeping current instructions,
   - trying Lite Footer only,
   - using V13 as a review-only completion lane,
   - or merging V13 into local instructions?
3. What is the expected benefit?
4. What is the setup friction?
5. What should not be changed yet?
6. What is the smallest safe first test?

## Adoption Modes

1. Keep current instructions
2. Try Lite Footer only as the smallest first-use test
3. Add V13 as review-only completion lane
4. Merge V13 into local instructions

## Boundaries

Do not tell all users to adopt V13.

Do not force `AGENTS.md` replacement.

Do not build plugin implementation, plugin scaffolding, comparison tooling, automation, marketing workflows, posting workflows, MCP, hooks, skills, CLI, server, package setup, schema changes, release files, V1 draft, or new features.

The purpose is only to help the user's AI compare V13 against the target repo and choose the smallest safe adoption path.
