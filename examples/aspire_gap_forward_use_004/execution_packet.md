# Forward Use 004 — Public-Safe Independent Execution Packet

## Target Root

`<TARGET_REPO_ROOT>`

## Target Authority and Completion Files

- `<TARGET_REPO_ROOT>/AGENTS.md`
- `<TARGET_REPO_ROOT>/handoff/current_handoff.md`
- `<TARGET_REPO_ROOT>/audits/audit_021_reddit_announcement_cap_observation.md`

## Supplied Causal Field Notes

- `<V13_ROOT>/field_notes/021_required_intermediate_node.md`
- `<V13_ROOT>/field_notes/022_v12_to_v13_mapping.md`
- `<V13_ROOT>/field_notes/024_aspire_carrier_reentry_operational_definitions.md`
- `<V13_ROOT>/field_notes/025_footer_axis_consolidation.md`

## Bounded Instruction

Inspect the target repository’s current authority and completion state.

The selected issue is limited to the stale `Next One Action` in the canonical handoff, which still points to commit/push work already completed for `audit_021`.

Use only the target repository’s native authority and terminology, together with the supplied Field Notes as causal rationale.

Replace only that stale instruction with a target-native state-based instruction equivalent in substance to:

```text
HOLD. No new audit or execution loop is authorized. To restart audit work, first obtain an explicitly named target repository or workspace and a bounded audit scope, then re-evaluate the gate.
```

Preserve the target’s existing B-side terminology, Gate, Decision Owner, Missing Closure, Completion Line, and prohibited scope.

Do not add V13 footers, templates, files, terminology, branch machinery, or automation.

Do not rerun `audit_021`. Do not start another audit. Do not modify any file other than the canonical target handoff unless the target’s own authority proves that the canonical instruction is elsewhere. If authority is ambiguous, stop without editing.

Validate the bounded change, commit, and push only when the target repository remains clean, private, and synchronized.

Before editing, verify identity and remote, `main`, clean state, the fixed pre-patch HEAD, target authority surfaces, `audit_021` completion, and the stale instruction. If state changed, stop and report exact evidence.

Return only the exact file changed, stale state removed, new state, reason, effect, rollback, validation, commit/push, correction burden, and uninspected or `UNKNOWN` boundaries. Do not inspect unrelated files or search for other improvements.

The exact unredacted packet is anchored in [evidence_manifest.md](evidence_manifest.md).
