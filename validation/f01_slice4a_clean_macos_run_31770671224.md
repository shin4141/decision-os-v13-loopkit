# F-01 Slice 4A — clean macOS capsule run 31770671224

**As-of:** 2026-08-14 JST

**Decision Owner:** Shin

**Authority:** one authorized qualification/deployment capsule

**Implementation base:** `11bc417c2104840676003d2cc3d5f12517e9d13f`

**Workflow commit:** `e7174ff2ec973d4823c389b35a6e12dbb2b36677`

**Workflow run:** `31770671224`, attempt `1`

**Job:** `94675766936`

**Artifact:** `9207999730`, `f01-slice4a-clean-macos-31770671224-1`

**Artifact archive SHA-256:** `bc7f231e9c837485a173b060646ba0d3792a50df785bb5c274b1dd0124b8aa5b`

This record fixes the single authorized GitHub-hosted macOS attempt. It does
not authorize a rerun, recovery campaign, main merge, or Host Attempt 1 work.

## Runner identity

- provider: GitHub-hosted macOS;
- image: `macos-26-arm64`, version `20260728.0273.1`;
- OS: macOS `26.5.2`, build `25F84`;
- architecture: `arm64`;
- runner: `GitHub Actions 1000001053`;
- ephemeral identity SHA-256:
  `16378afc667bd302eb25f21d05f923abcabf0c4ce18173fea4a082b6cceca48a`;
- repository/ref/SHA:
  `shin4141/decision-os-v13-loopkit`,
  `refs/heads/codex/13-154-f01-slice4a-clean-macos-capsule`,
  `e7174ff2ec973d4823c389b35a6e12dbb2b36677`.

Raw platform identifiers were not persisted.

## Phase 1 — clean-host qualification

Result: `PASS_CLEAN_HOST`

- `_decisionos_codex`, `_decisionos_guardian`, and `_decisionos_broker`
  user/group names were absent;
- UIDs and GIDs `510`, `511`, and `512` were free;
- `/Library/Application Support/DecisionOS` and both Slice 4A descendants
  were absent;
- the checkout had no ACL entries;
- protected-repository ACL installation was false;
- sole-writer claim was false;
- qualification ran unprivileged as EUID `501` and attempted no mutation.

The exact qualification evidence is
`f01_slice4a_clean_macos_run_31770671224/01_clean_host_qualification.json`.

## Focused verification

The four focused modules covering principal separation and accepted Broker
Slices 1–3 ran `216` tests in `3.624s`. Result: `OK` with no truncation.

## Phase 2 — bounded deployment

Phase 2 was entered once after Phase 1 and focused verification passed.

The one privileged command used `sudo -n`; no prompt, credential, retry, or
fallback was permitted. It failed closed with exit `1` while writing the
Codex user's `GeneratedUID`:

```text
dscl . -create /Users/_decisionos_codex GeneratedUID <fresh runner GUID>
exit 40: eDSPermissionError / DS Error -14120
```

The fresh GUID is intentionally omitted from this summary and remains only in
the hash-bound run evidence. The provisioner returned `HOLD`, installed no
protected-repository ACL, and made no sole-writer claim. No retry, rollback,
or recovery experiment ran.

## Post-failure observation boundary

The read-only post observation found:

- nonempty fixed Codex name and UID/GID `510` search surfaces;
- Guardian and Broker surfaces absent;
- all DecisionOS host-state paths absent;
- no checkout ACL entry;
- no receipt;
- no qualified principal separation.

The generic search parser also captured multiline attribute values as record
names. Therefore exact post-failure record cardinality and the complete partial
Codex attribute surface are `UNKNOWN`; the post observation must not be used as
evidence of qualified separation. This limitation does not alter the exact
pre-provisioning PASS or the provisioner's fixed failure point.

The ephemeral runner was destroyed after artifact upload, so its partial guest
state is outside future authority and cannot be adopted or repaired.

## Evidence identity

The GitHub artifact archive SHA-256 matched the Actions API digest. Its eleven
extracted files total `52,592` bytes. Every file named by the extracted
`SHA256SUMS.txt` was rehashed locally and passed. The manifest itself has
SHA-256:

```text
f5b4ee09dbaa62eb65ceab747231ce33609a5d8dcff31b43581dbe16561e67db
```

The exact extracted evidence is fixed under:

```text
validation/f01_slice4a_clean_macos_run_31770671224/
```

This fixation commit removes the temporary workflow and capsule runner from
branch HEAD. The workflow remains traceable only through its fixed commit; it
is not a standing privileged automation surface.

## Gate and missing closure

```text
HOLD — NEW BOUNDED FAILURE PRESERVED
```

Missing Closure: Slice 4A still lacks one real clean macOS deployment whose
Directory Services policy permits the complete accepted three-principal
transaction and whose final verification passes. This run does not authorize
another provider, retry, recovery transport, or architecture change.

Host Attempt 1 remained untouched. Main remained unchanged by this capsule.
F-01 remains OPEN. Slice 4A remains incomplete.
