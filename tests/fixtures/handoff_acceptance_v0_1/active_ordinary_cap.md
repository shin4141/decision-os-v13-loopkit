# Responsibility Transfer

- **Target Layer**: V13
- **Repository**: example/handoff-fixture
- **Current State**: ACTIVE
- **V13 Gate**: GO UNDER CAP — B DESIGN ONLY
- **Active Branch**: main
- **Next Authorized Action**: VALIDATE [VAL-1]; closure=VAL-1; branch=main
- **Completion Line**:
  OPEN:
  - [DONE-1] TEST; subject=handoff_guard; expected=passes
- **Missing Closure**:
  - [VAL-1] VALIDATION; owner=RECEIVER; subject=handoff_guard; scope=B_DESIGN_ONLY
- **Next Owner**: Codex Executor
- **Receiving Ownership**:
  - [VAL-1] VALIDATION; owner=RECEIVER; subject=handoff_guard; scope=B_DESIGN_ONLY
- **First Action**: VALIDATE [VAL-1]; closure=VAL-1; branch=main
- **Stop Boundary**:
  CAP_TO: VAL-1
  SCOPE: B_DESIGN_ONLY
  STOP_BEFORE: EXTERNAL, IRREVERSIBLE
- **AI-Retained Work**: RETAIN: VAL-1
