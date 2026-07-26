# Workflow Incident Intake Distribution Run 001

## Status

```text
As-of:
2026-07-26 / Asia/Tokyo

Result:
PASS / COMPLETE

Exact source commit:
d3ba864c66367e5c676ec14fbaa550801e4f1889

Intake result:
FIT_CHECK_READY

Exit code:
0
```

This run tested whether a third party can download the exact example and launch
the merged Workflow Incident Intake Checker without first cloning the
Decision-OS repository.

## Environment

```text
OS:
macOS 26.2 build 25C56

Architecture:
arm64

uv:
uv 0.11.32 (3010295ae 2026-07-23 aarch64-apple-darwin)

uvx:
uvx 0.11.32 (3010295ae 2026-07-23 aarch64-apple-darwin)

Python:
3.14.3
```

`uv` was not installed globally or already available on `PATH`. For this run,
the official `uv-aarch64-apple-darwin.tar.gz` for `uv 0.11.32` was downloaded
to a mode-0700 temporary root. Its SHA-256 matched the repository's existing
distribution guard:

```text
ed336d0ba49db8ef89b2b41fffa372ce63bd032f22a56f001c265891aec32829
```

The extracted temporary `uvx` SHA-256 was:

```text
572d4d5281ba5b20b9c94ea53fac1b2b9c19287931091b44e8693dc65780cb3d
```

The run used a dedicated empty `UV_CACHE_DIR` and the existing compatible
`/opt/homebrew/bin/python3.14`. These were validation-environment controls, not
changes to the published commands or to the repository.

For isolated capture, the exact `uvx` command was launched inside a
process-local environment wrapper that kept stdout and stderr separate. The
wrapper prepended the extracted temporary uv directory to `PATH`, so bare
`uvx` resolved to the verified temporary executable. It did not change the
published flags, source ref, command, or input filename. The process-local
controls were:

```text
PATH:
<mode-0700 temporary root>/tool/uv-aarch64-apple-darwin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin

UV_CACHE_DIR:
<mode-0700 temporary root>/cache

UV_PYTHON:
/opt/homebrew/bin/python3.14

HOME:
inherited unchanged from the host; not reassigned

Locale and time:
LC_ALL=C / LANG=C / TZ=UTC

Git transport:
GIT_CONFIG_GLOBAL=/dev/null
GIT_CONFIG_NOSYSTEM=1
GIT_TERMINAL_PROMPT=0
```

## Exact raw-example URL

```text
https://raw.githubusercontent.com/shin4141/decision-os-v13-loopkit/d3ba864c66367e5c676ec14fbaa550801e4f1889/examples/workflow_incident_intake_v0_1.json
```

## Exact commands

The temporary run directory was empty before the first command.

```sh
curl -fsSLo workflow_incident_intake_v0_1.json \
  https://raw.githubusercontent.com/shin4141/decision-os-v13-loopkit/d3ba864c66367e5c676ec14fbaa550801e4f1889/examples/workflow_incident_intake_v0_1.json

uvx --isolated --no-config --no-env-file --no-python-downloads \
  --from "git+https://github.com/shin4141/decision-os-v13-loopkit@d3ba864c66367e5c676ec14fbaa550801e4f1889" \
  decision-os intake --format text workflow_incident_intake_v0_1.json
```

## Command receipt

### Download

```text
curl stdout:
empty

curl stderr:
empty

curl exit code:
0

Downloaded bytes:
932

Downloaded file SHA-256:
8e8d164df7e91fa23980767b3149fb004f1f859ba2f3bafb66e72fa8c092cc87
```

The downloaded SHA-256 matched the example at the exact source commit and was
unchanged after intake execution.

### Intake stdout

```text
Decision-OS Workflow Intake v0.1: FIT CHECK READY

Observed:
- workflow
- bounded_path
- trigger
- expected_state
- observed_state
- human_recovery_work
- restart_or_fallback_path
- materials_available
- prohibited_materials

Missing:
- none

This result confirms intake structure only.
It does not diagnose the workflow or accept it for a paid Audit.
```

```text
stdout bytes:
352

stdout lines:
18

stdout SHA-256:
f6e87ef0b7535b56300a85468e987c8c9c0379f2655f52fdab80d2e54426940b

uvx exit code:
0
```

### Intake stderr summary

The five stderr lines were cold transport messages only. They recorded:

- updating the exact GitHub source commit;
- building `decision-os-v13-loopkit` from that exact commit;
- installing one built package.

The stderr named
`d3ba864c66367e5c676ec14fbaa550801e4f1889` throughout the source update and
build. It contained no packet field contents and was not checker stdout.

## Source and clone boundary

The dedicated uv cache contained one Git checkout. A read-only
`git rev-parse HEAD` inside that checkout returned:

```text
d3ba864c66367e5c676ec14fbaa550801e4f1889
```

No pre-existing or manual repository clone was required. The temporary run
directory contained only `workflow_incident_intake_v0_1.json` and no `.git`
entry. Because `--from git+...` is a Git source transport, `uvx` did perform its
own bounded fetch and cache checkout outside the run directory.

## Bounded conclusion

This one run confirms that the exact-commit path distributed the example,
launched the checker, and returned `FIT_CHECK_READY` for the example packet.
It establishes distribution and structural intake only.

## Limitations

- This receipt covers one environment only.
- It does not establish support on all platforms.
- It does not diagnose a real workflow.
- It does not establish demand, paid value, prevention, safety, or
  productivity.
- `curl` and `uvx` transport require network access.
- After launch, the checker itself remains local and read-only.
