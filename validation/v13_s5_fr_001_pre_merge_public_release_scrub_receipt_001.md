# V13-S5-FR-001 Pre-Merge Public-Release Scrub Receipt 001

```yaml
schema_version: decision-os.public-release-scrub-receipt.v0.1
build_or_run_id: V13-S5-FR-001
receipt_id: V13-S5-FR-001-PRE-MERGE-PUBLIC-RELEASE-SCRUB-001
audit_as_of: 2026-07-31T17:08:00+09:00
repository: shin4141/decision-os-v13-loopkit
audited_head: COMMIT_CONTAINING_THIS_RECEIPT
audited_implementation_repair_head: 5f3a2673d0d34e6498be29b977450c286e1608c8
cleanup_commit: COMMIT_CONTAINING_THIS_RECEIPT
base_head: 0dca2e5a11a10bc3436d84e4333c66be139de333
branch: feat/v13-s5-fr-001-public-claim-guard-v0-1
pull_request: 48
pull_request_state: OPEN_DRAFT_UNMERGED
pr_or_release_candidate: PR_48
canonical_matrix: templates/v13_public_release_audit_matrix_v0_1.md
canonical_matrix_version: v0.1
baseline_mode: INITIAL_BASELINE

python_3_10_runtime:
  installation_method: Homebrew python@3.10 source rebuild
  executable: /opt/homebrew/bin/python3.10
  implementation: CPython
  exact_version: 3.10.20
  system_default_replaced: false
  shell_startup_files_modified: false
  requires_python_modified: false

pre_edit_python_3_10_evidence:
  full_suite: 602 tests / OK / 3 declared skips / 0 failures / 0 errors
  scan: PASS
  intake: PASS

post_edit_full_suite_evidence:
  python_3_10: 602 tests / OK / 3 declared skips / 0 failures / 0 errors
  python_3_10_elapsed_seconds: 303.484
  default_python: CPython 3.14.3
  default_python_result: 602 tests / OK / 0 failures / 0 errors
  default_python_elapsed_seconds: 351.723

intermediate_verification_correction:
  non_decisive_concurrent_run: FAILED
  failure_count_each_runtime: 4
  cause: first cleanup header omitted parser-required V12 State and Current Gate aliases
  product_code_changed: false
  repair_paths:
    - docs/current_signal.md
    - handoff/current_codex_handoff.md
  repair: added V12 State PASS and Current Gate HOLD to both authorized current blocks
  focused_check_after_repair: PASS
  decisive_serial_reruns: PASS

native_public_boundary:
  execution_status: ACTIVE
  delta_state: REUSED
  current_gate: HOLD
  missing_evidence:
    - GENERALIZED_TRANSPLANT_NOT_ESTABLISHED
  authority_provenance: MANUAL_OWNER_ATTESTED
  cryptographic_provenance: NOT_ESTABLISHED
  private_native_store_inspected: false
  native_store_written: false

row_status_vector:
  PRV: PASS
  SEC: PASS
  PATH: PASS
  CLM: PASS
  ENTRY: PASS
  PKG: PASS
  EX: PASS
  BUG: HOLD
  TEST: PASS
  HYG: PASS
  BIN: PASS
  LIC: PASS
  RPT: PASS
  VER: PASS
  GH: HOLD
  RBK: PASS
  AUTH: PASS

post_edit_verification: PASS
final_gate: PRE_MERGE_SCRUB_PASS
exact_next_action: Create and push the sole cleanup commit, reconcile only PR 48 body, keep Draft, and await a separate Owner merge decision.
```

## Changed rows

| Row | Severity | Disposition | Result |
|---|---|---|---|
| `PRV` | HIGH | MUST_FIX_BEFORE_MERGE | Approved `Shin` / `shin4141` attribution only; unapproved full-name scan has zero matches. |
| `PATH` | HIGH | MUST_FIX_BEFORE_MERGE | Fourteen literals across ten records were replaced by neutral placeholders; current-tree private-path scan has zero matches. |
| `CLM` | HIGH | MUST_FIX_BEFORE_MERGE | Canonical current blocks now state V13-S5-FR-001, `ACTIVE / REUSED / HOLD`, and no merge/release/publication authority. |
| `PKG` | MEDIUM | DOCUMENT_BEFORE_MERGE | CPython 3.10.20 was provisioned without replacing the default; pre- and post-edit 602-test suites passed. |
| `RPT` | HIGH | MUST_FIX_BEFORE_MERGE | Security text now states executable CLIs, optional loopback Companion, scan/stateful distinction, and no private reporting channel. |
| `GH` | INFORMATIONAL | SAFE_AS_IS | PR was OPEN/DRAFT/UNMERGED with no reviews, requests, comments, labels, checks, or workflows; absence is not CI or independent-review PASS. |

## Evidence commands and results

| Evidence | Result |
|---|---|
| `/opt/homebrew/bin/python3.10 -B -m unittest discover -s tests` before edit | 602 tests / `OK` / 3 declared skips |
| `/opt/homebrew/bin/python3.10 -B -m unittest discover -s tests` after edit, serial localhost-capable rerun | 602 tests / `OK` / 3 declared skips / 303.484s |
| `python3 -B -m unittest discover -s tests` after edit, serial localhost-capable rerun | 602 tests / `OK` / 351.723s |
| `python3 -B scripts/validate_loop_record_examples.py` | 12/12 PASS |
| Default and CPython 3.10 `decision_os scan --format text .` | PASS |
| Default and CPython 3.10 `decision_os intake --format text examples/workflow_incident_intake_v0_1.json` | PASS |
| `decision_os check .` after canonical-header correction | Exit 0 / `V12 State: PASS` / `V13 Gate: HOLD` / no missing field or contradiction |
| All tracked JSON parse | 31/31 PASS |
| Markdown-aware local-link scan | 326 files / 264 local links / 0 failures |
| Current-tree private-path scan | 0 matches |
| Current-tree unapproved full-name scan | 0 matches |
| Current-tree and 485-reachable-commit high-risk secret scan | 0 matches |
| Current-tree and 485-reachable-commit common private-provider email scan | 0 matches |
| Cleanup allowlist equality | 19 expected / 19 actual / no missing or extra path |
| File, mode, symlink, and artifact inventory | No new binary, archive, database, cache, build output, symlink, or executable |
| `git diff --check` | PASS |

The first concurrent post-edit experiment is not represented as a PASS. Both
runtimes exposed the same four current-state parser failures. The two
authorized canonical blocks were corrected, `decision-os check` passed, and
the decisive full suites were then rerun serially in the localhost-capable
environment with the passing results above.

## Exact cleanup allowlist

1. `LICENSE`
2. `pyproject.toml`
3. `SECURITY.md`
4. `CONTRIBUTING.md`
5. `docs/prototype_status.md`
6. `docs/current_signal.md`
7. `handoff/current_codex_handoff.md`
8. `validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_03_execution_handoff.md`
9. `validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_04_build_receipt.md`
10. `validation/companion_manual_bridge_v0_1_shared_evidence_packet.md`
11. `validation/decision_os_companion_acceptance_run_001.md`
12. `validation/guided_intake_v0_1_build_receipt.md`
13. `validation/guided_intake_v0_1_shared_evidence_packet.md`
14. `validation/handoff_acceptance_guard_v0_1_b_execution.md`
15. `validation/handoff_acceptance_guard_v0_1_shared_evidence_packet.md`
16. `validation/verified_save_claude_mvp_run_001.md`
17. `validation/verified_save_codex_mvp_run_001.md`
18. `templates/v13_public_release_audit_matrix_v0_1.md`
19. `validation/v13_s5_fr_001_pre_merge_public_release_scrub_receipt_001.md`

## Historical redaction policy

- History rewrite is prohibited and was not performed.
- Old blobs remain reachable at their recorded commits.
- Embedded historical hashes remain true only for the commits and bytes they
  originally identified.
- The ten changed validation records are current-HEAD public redacted
  presentation copies.
- The sanitized current-HEAD bytes do not replace or reinterpret old hashes.
- Native E1–E5, Lower Run, sidecar, completion receipt, event, anchor, and
  authority identities are outside this cleanup and are not reinterpreted.

## Before/after identities of the ten public presentation copies

| Path | Previous Git blob | Previous file SHA-256 | Redacted Git blob | Redacted file SHA-256 |
|---|---|---|---|---|
| `validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_03_execution_handoff.md` | `9ade681953f7b9276fe5fc1f110b25222acf9080` | `cf125e67d13acc7a72c1b500d5c31d7b34f83e221d5177695f990e42d501c43f` | `05784f93a947b563790b9fccb9f5612a348c1c62` | `d0b8f8e24418ed058ec7a3e0a6b2ac7b98878a21ab4b35b65edafb34c3d31e23` |
| `validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_04_build_receipt.md` | `7874cefe59c3088384affd6302ff64e98aa7b3af` | `e98c5a3eb759dd01b2cea422ae24a6be3604f16a9b7b9cff19f9f7c6831c366d` | `3e3aa8174d60362cb42dc91caa9b44685a0fb090` | `ad8c3647c13e248f788326abb0476277f8a75058beb4f2ca4f5906039ac5d365` |
| `validation/companion_manual_bridge_v0_1_shared_evidence_packet.md` | `92f9f69f18db052b421fa5fa7f233ce77f5a42b8` | `847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab` | `c9c429e531679e10649a69eb3858c0dd0743bb25` | `1afaf5c2b3bdc26629ab7099294df0f83d3d9e03a283e3cb45d6d00712ee2b68` |
| `validation/decision_os_companion_acceptance_run_001.md` | `ffb7a1e09c08ff2bf03a4a284608e35e86a4b6bb` | `366a4897418577aef15df5343a0f178d9e338b584d48507dc1bf59deec9769e4` | `6e3f269a85a8325f155cc0b8d3faada1e8008e96` | `c8f008dadce1d7a9684b5a658a3302f83bd50c17a48e2a916c71ed7f4971e336` |
| `validation/guided_intake_v0_1_build_receipt.md` | `e3396d1ffbecb90bee8d5391fb3b74c431a7e0cc` | `eeb90d570a64c591ca9f2ada2166abc1b56f47db672a487ef1083bf80a52c353` | `63de99b8920f7f4f53c872f83a3df0eec684309c` | `5cb8d427a5f62d5755fe8f18595b9ad3995f19f813e01bbf8102434de1d30e4a` |
| `validation/guided_intake_v0_1_shared_evidence_packet.md` | `54d8fa7988e86d94d16f01beb90a5ed22cbcb52c` | `6be28f7e3a2ee3063c173cf5782e8c123f993f6b63a1d557a79b38e8aff4869a` | `493ab6950330418dd12722dcea844703b5a5f657` | `92ba2dd9b1f82f63fad7a7eec030542ad3f3d803716812d4c6aa5c293b8e6b2a` |
| `validation/handoff_acceptance_guard_v0_1_b_execution.md` | `dc0b725eb444a50c4701144cefe65a21177154b7` | `10ce3d0d5d7a30a38cad2e041360c3ed4de48b5797d24bb45b8045436a9b7ec4` | `eb83377f9b5ae6070db451740e561c2affabc2e3` | `3e7942fc2edbfff9e1f7353f94f16ca1a2e1db2b7bc0f0f6f0086405d67d34b6` |
| `validation/handoff_acceptance_guard_v0_1_shared_evidence_packet.md` | `502ba73f643e8dabf19a2cbeaa06db3c910a32c5` | `fff0b9b7394749556c7ee94184aebbd304f0b94c10222e8766806f672a8a62f2` | `b6e7f920549fd3ff14d0312c9bb93cc2f52d2f22` | `4afba9d5e3257d5293881a4db3ea24303d1632d665021a7d1f75b7d0c07c30af` |
| `validation/verified_save_claude_mvp_run_001.md` | `8a7b8cb8a9e455c5744c0db8733811aecaec7cd2` | `99153d0efff3cfefef4dbd7b81820e649991c49fbd1f03b1e8d8bd2690929f64` | `5e275624338b714411b86227759bb10e20657141` | `6d0a1799c023fb4a59681d3b0e33fab433c13384e40851d50ff38af6e6ee350e` |
| `validation/verified_save_codex_mvp_run_001.md` | `7744405b02beaad0fb0361112d903c7ec90149b0` | `23d216cbf90f769cbc612cc82c45c5d832dda4873eef97c46579d9d30ee2c760` | `3e2df956031952ac5c9f2cc14949f45cfe9b592e` | `1535e4183b3a23a63087e9c594b4bb0e790a821f10a9b8a6986e8e2f469e293c` |

## Exceptions and unresolved items

- `Shin` and `shin4141` are the Owner-approved public identities.
- GitHub noreply and reserved `.invalid` / `.test` fixture addresses are not
  private-email findings.
- Synthetic credential strings remain bounded negative-test fixtures and did
  not match the high-confidence live-secret scan.
- Conventional CLI help outside the acceleration CLI remains a separately
  gated post-merge backlog item.
- No GitHub reviews or checks are reported; that absence is not represented as
  CI or independent reproduction.
- `GENERALIZED_TRANSPLANT_NOT_ESTABLISHED` remains the current missing
  evidence.
- Merge, release, and publication remain separately unauthorized.

## Owner decisions

- Shin authorized this exact 19-path cleanup.
- Shin approved `Shin` and `shin4141` as public attribution identities.
- Shin authorized provisioning one isolated CPython 3.10 runtime for current
  and future release-audit reuse.
- No Owner decision authorized review request, ready transition, merge,
  release, package, or publication.

## Re-evaluation triggers

Re-evaluate on any local, upstream, or PR head change; PR body, title, Draft,
review, check, or merge-state change; cleanup allowlist change; identity,
private-path, secret, link, test, package, security, license, binary, tag,
release, registry, or publication result change; or any proposal to inspect or
write the native store.

## No-mutation attestation

- Product code, schemas, tests, CI/workflows, `main`, prior commits, tags,
  releases, packages, and publication state were not modified.
- Private native-store contents were not inspected, invoked, or written.
- Native E1–E5, Lower Run lineage, sidecar, completion receipt, event count,
  chain head, anchor, and authority identities were not changed or
  reinterpreted.
- No review was requested, no ready transition occurred, and no merge,
  release, or publication was performed.

## Forward-only rollback

Do not rewrite history or restore private literals to current HEAD. Correct any
cleanup defect with a new forward-only change retaining neutral placeholders.
Correct PR-body metadata through GitHub edit history. Do not use rollback to
represent the Formal Run implementation/repair evidence HEAD or historical
native identities as current sanitized bytes.
