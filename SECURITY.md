# Security Policy

V13 LoopKit is a manually governed prototype that includes executable command-line
interfaces and an optional, manually invoked loopback Companion.

`decision-os scan` is a local, read-only observation workflow. Other explicitly
invoked workflows, including the Companion, can be stateful and can read or write
approved local data. The Companion binds to loopback; it is not a remote service.

These surfaces do not provide an automated security boundary.

## Reporting a vulnerability

No private vulnerability-reporting channel is currently enabled for this
repository.

Do not post credentials, private paths, personal data, exploit details, or other
sensitive material in a public GitHub issue. A public issue may be used only for
non-sensitive coordination. Until a documented private channel is enabled, retain
sensitive details privately rather than disclosing them in the public repository.

## Important note

Do not treat V13 LoopKit as a substitute for:

- code review
- tests
- CI
- access control
- secrets management
- production security review

V13 LoopKit can help agents report completion, next-loop gates, handoff risk, and context-compression state.

Its CLIs and optional loopback Companion do not guarantee safety by themselves.
