# V13 Creator-Live Whole-Flow Re-entry Charter Delta v0.6

Status: `HOLD — independent review and merge required`

## Purpose

This Forward-only Delta records the dedicated Creator-Live Cycle 005
production entrypoint implementation, non-live qualification, canonical build
and installation, current-HEAD Contract fixation, and the boundary for final
exact-merge P0.

It does not start Cycle 005, open a proof, create a proof-attempt identity,
invoke a product/runtime model, transmit either fixed task, or grant retry,
replacement, release, or publication authority. It changes no product code,
test, installed runtime byte, or historical proof artifact.

## Parent Authority

| Authority | Identity |
| --- | --- |
| Parent Charter | `validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md` |
| Parent Charter SHA-256 | `84e65d12e7b7dd2c86204273c7dc96c16689580e3148f9a0beb2993fd7ee0585` |
| Delta v0.1 SHA-256 | `d34bf2f00de56b0869cc341ce0db65c2fa147ca8a824a81ccd2bde1a8cfe47fa` |
| Delta v0.2 SHA-256 | `da6347ee71512ab135ac0c418a7e6487adf243b0adaae89ee72f17774404ddc5` |
| Delta v0.3 SHA-256 | `8a221220281e100ca0fc0d42efccc530902250da04a32138ee0fbc5415e5f45c` |
| Delta v0.4 SHA-256 | `e90f8410eb9becc1da520e0b7ef10a490ce13024bd63a536b59270bd2e91726c` |
| Delta v0.5 SHA-256 | `d366f5de62bb2f5ea4dccd999cace1b6d436819c43c2165f2d43a631cc56d26a` |
| Implementation authorization observed at | `2026-08-05T08:47:00Z` |
| Separate Cycle authorization observed at | `2026-08-05T06:22:00Z` |
| PR #100 implementation merge | `96460a46b9f8d0e32a1d9596a126492f7d23e9e3` |

The two authorization timestamps remain separate fixed observations. This
Delta does not replace, regenerate, reinterpret, or consume either one.

## Implemented Entrypoint Boundary

PR #100 added the dedicated authenticated Installed Companion control backed
only by:

```text
POST /api/creator-live/cycles/005/start
```

The request admits only one exact lowercase 64-character
`launch_binding_sha256`. Session, loopback Host, same-origin Origin, CSRF,
content type, duplicate-key rejection, exact request keys, digest shape, and
fresh binding equality all fail closed. The ordinary `/api/run` route is not a
Creator-Live alias.

The backend derives repository, Contract, task, runtime, authorization,
historical, network, and attempt identities. The fixed Cycle root is:

```text
/Users/sn/Documents/v13/decision-os-v13-loopkit/.decision-os/field-notes/proofs/cycle-005
```

The only permitted future proof identity is
`proof_a7_creator_live_cycle_005_<full launch_binding_sha256>`. P0 and durable
exclusive `open_attempt()` must complete before HTTP `202`. The fixed root,
deterministic identity, cycle lease, journal and anchor fsyncs, directory
fsync, and typed readback make a post-open interruption consuming. A restart
can expose only `OPEN_UNRESUMABLE`; no resume, deletion, retry, replacement,
alternate identity, or second proof path exists.

No proof root existed before or after this qualification.

## Network and Runtime Boundary

The fixed runtime is OpenAI through the authenticated ChatGPT account,
`gpt-5.6-sol`, `ultra`, `priority`, Codex CLI `0.146.0-alpha.3.1`, canonical
repository cwd, read-only sandbox, and one fresh ephemeral thread per Run.

Authenticated loopback Companion HTTP, local stdio to the bundled Codex
app-server, and authenticated provider transport remain enabled. Provider
transport is required only for initialization, account/model verification,
thread and turn startup, and response streaming.

Model-accessible sandbox network, web, browser/general URL access, MCP,
plugins, apps, hooks, remote plugins, multi-agent, shell/command execution,
dependency installation, and arbitrary file mutation remain disabled.
`networkAccess: false` binds the model sandbox and tools; it does not disable
the authorized app-server provider transport.

The exact task identities remain:

| Run | Bytes | SHA-256 | Lane |
| --- | ---: | --- | --- |
| Run 1 | `832` | `e377fb2f9e003f3f04e8d1b10d2aef96347416d86f78305102d4671519ed3417` | `A1_ONLY` |
| Run 2 | `856` | `688203fd91c880cb4c9e32619219e9e660160b31fded0ae630ae2a401ea6cdcf` | `EXACT_A2_ONLY` |

Neither task body was displayed, regenerated, normalized, transmitted, or
executed during implementation or qualification.

## First Current-HEAD Contract Fixation

The exact tracked Contract source remained:

| Field | Exact value |
| --- | --- |
| Filename | `Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md` |
| SHA-256 | `519bd39305af1a3a7cc35e61e1b9cfc742c5723d0cc64d0d970b070d0e65068e` |
| Byte count | `11039` |
| Encoding | `UTF-8` |
| Profile | `ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1` |
| Wrapper SHA-256 | `c3de6236a450666d8a8ef59a8f8db303bf4654cc9cb20d6ab816f3066177b11e` |
| Interpretation SHA-256 | `7503f4b01c7c05c9ec3aed8855c9fd538c66b9b3b38840f423ec41c2101f4dd7` |

One production-UI preparation and Forward-only fixation at the exact PR #100
merge created this current lineage:

| Current lineage field | Exact value |
| --- | --- |
| Repository identity | `96460a46b9f8d0e32a1d9596a126492f7d23e9e3` |
| Preparation ID | `OUP-PREP-2740cbd7-e1a7-47bb-b758-db04219a5dae` |
| Preparation receipt SHA-256 | `7ccae7fdff2c86c4b2b8c591425e9005ced304d2fc42c1161b01ebcfbdbbc3fa` |
| Active request ID | `GI-REQ-99c3e2dc-4f38-4b81-8973-25235abd8e2c` |
| Active draft ID | `GI-DRAFT-425d3445-5788-4aa2-acb0-55335f58b4c0` |
| Current freeze ID | `GI-FREEZE-f093c50c-9c4b-444e-a796-66ccd469cdeb` |
| Frozen intake SHA-256 | `6819cf838da1b9c57e65e4b928314686d4f0bb4e3b6da998c1f4aec664533edc` |
| Freeze receipt SHA-256 | `54209f6600e5459bd7175449d2cf6f3eda24c01be30e5db8d0823483c2bfa8f9` |
| Guided Intake current event-chain head | `2e8d04d158581550cc1ca4a276c7dfe709f20a9429dd2217027192ab314cb311` |
| Preparation receipt event-chain head | `e49901e211a67d3591381db277e6c9c1d58e403c2b5d4eb2609d975154494899` |
| Freeze receipt event-chain head | `e49901e211a67d3591381db277e6c9c1d58e403c2b5d4eb2609d975154494899` |
| Projected execution authority | `INTERPRETATION_ONLY` |
| Guided Intake freeze authority | `IMMUTABLE_INTERPRETATION_ONLY` |
| Current gate | `CLEAR ENOUGH TO FREEZE` |

The Guided Intake current head is the appended `INTAKE_FROZEN` event. The two
receipt fields bind its exact predecessor `PRO_DRAFT_IMPORTED` event. The
authority strings are distinct raw fields and are not aliases.

The preceding request, draft, freeze, receipts, and events remain preserved in
the append-only lineage. Fixation grants interpretation authority only; it
does not authorize an ordinary bounded Run or start Cycle 005.

## Build, Installation, and Process Qualification

The exact clean PR #100 merge was built and installed through the canonical
builder. Recoverable pre-install backups are:

```text
/Users/sn/Library/Application Support/Decision OS Companion/runtime.backup.20260805185303
/Users/sn/Applications/Decision OS Companion.app.backup.20260805185303
```

| Product identity | Value |
| --- | --- |
| Implementation baseline | `96460a46b9f8d0e32a1d9596a126492f7d23e9e3` |
| Source product-code tree | `815613804a6028a33806afe096ca072c80515ee8ebb73514b96f85ca02f784d6` |
| Installed product-code tree | `815613804a6028a33806afe096ca072c80515ee8ebb73514b96f85ca02f784d6` |
| Installed/source byte equivalence | `PASS` |
| Installed applet executable SHA-256 | `00307012dac37c6cb090ad1cb0e3423900ed63c5599accb41e56180d60f7c4c5` |
| Installed launcher-source SHA-256 | `7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538` |
| Expected Python launcher | `/opt/homebrew/bin/python3` |

The canonical post-install process qualification returned:

```json
{"details":{"applet_parent_verified":true,"installed_launcher_sha256":"7a00ba53d04b820f33c29490fccabeeb6329e0a62b06ccf88b21ad529f13c538","installed_product_tree":"815613804a6028a33806afe096ca072c80515ee8ebb73514b96f85ca02f784d6","listener_host":"127.0.0.1","listener_owner_pid":9216,"listener_port":49255,"module":"decision_os.companion"},"passed":true,"result":"PASS","schema":"decision-os.companion-process-qualification.v0.1"}
```

The PID and ephemeral port are observations, not future authority. The exact
installed tree, canonical launcher bytes, expected Python and module argv,
single loopback listener owner, and installed applet parent all passed.
Authenticated root startup passed; an unauthenticated `/api/state` request
returned exactly `401`.

## Non-Live Qualification

All qualification used fakes, deterministic local fixtures, static checks,
the authenticated Installed Companion UI, or bounded process evidence. No
live provider/model smoke test was performed.

| Qualification | Result |
| --- | --- |
| Creator-Live focused source qualification | `PASS` — 104 tests, 2 declared skips |
| Canonical installed-product focused qualification | `PASS` — 104 tests, 2 declared skips |
| Full default discovery | `PASS` — 1,189 tests, 2 declared skips |
| Current installed process replay | `PASS` — 2 tests |
| JavaScript syntax check | `PASS` |
| Python compilation | `PASS` |
| `git diff --check` | `PASS` |
| Source/installed product-tree equality | `PASS` |

The full implementation review found no blocking defect inside the authorized
Candidate A surface. GitHub reported no configured checks; PR #100 received an
independent non-approving review comment and was merged by normal forward
history.

## Historical and A3 Boundary

Cycle 004 remains permanently:

```text
FAILED / A1_CAPTURE / A1_CAPTURE_CHRONOLOGY_INVALID
```

Cycle 002 and Proofs 001–004 remain terminal. Their protected Notes, proof
journals, anchors, typed readbacks, receipts, and maturity entries were not
edited, opened, replaced, migrated, normalized, or reinterpreted.

The implemented A3 compiler admits only a unique, non-whole, exact UTF-8 Note
byte range reproduced in the normal Run 2 final-output bytes, with deterministic
source/output offsets and typed `OUTPUT_ARTIFACT` evidence. Ambiguity, ties,
normalization, fuzzy or semantic substitution, whole-note claims, and
usefulness/authority inference fail terminally at A3 and prevent A4–A7.

## Final Exact-Merge Authority

Future execution repository HEAD is:

```text
The exact merge commit of the Delta v0.6 PR, resolved only after merge.
```

The PR #100 merge and the Delta branch head are not final execution authority.
After this Delta merges, the selected repository must be fast-forwarded to the
exact Delta merge, the same exact Contract must be Forward-only fixed again to
that merge, source/installed product equality must remain exact, and the
content-free Cycle 005 P0 must pass at that exact merge.

The Delta is documentation-only and is not copied into the installed
`decision_os` runtime. The final launch binding must nevertheless include its
tracked Charter lineage SHA-256 and bind both the unchanged PR #100 product
tree and the final repository merge commit. Any later repository commit
requires new bounded requalification or a separately reviewed Forward-only
Charter Delta.

Merge and P0 alone do not start the Cycle. The later Start action remains a
separate explicit live decision.

## Claim Boundary

This Delta claims only that Candidate A was implemented and reviewed, source
and installed product bytes were made exact, the canonical installed process
was qualified, the same Contract was Forward-only fixed to the implementation
merge, and non-live P0 was ready at that merge.

It does not claim Cycle 005 start or success, proof opening, task transmission,
model invocation, A1–A7 live success, retry/replacement authority, Warehouse
eligibility, portability, release, publication, or `PROMOTABLE` status.

## Gates

Implementation, tests, review, merge, build, installation, first Contract
fixation, source/installed equivalence, and process qualification:

```text
PASS
```

Charter Delta v0.6:

```text
HOLD — independent review and merge required
```

Cycle 005 proof root:

```text
UNOPENED
```

Live Proof Gate:

```text
BLOCK — final exact-merge Contract refix and P0 still required
```

## Completion Line

One merged dedicated entrypoint, one exact installed product, one qualified
canonical process, and one Forward-only implementation-merge Contract lineage
await independent Delta review and final exact-merge Contract refix/P0 without
proof opening or model invocation.
