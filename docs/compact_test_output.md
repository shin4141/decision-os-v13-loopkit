# Compact test output

`scripts/compact_test_output.py` is the V13-local output wrapper for the
repository's existing `unittest` command. It does not select tests or add runner
options. The command after `--` is passed to the operating system unchanged.

Representative full-suite use:

```console
python3 scripts/compact_test_output.py \
  --log .test-logs/full-suite.log \
  -- python3 -B -m unittest discover -s tests
```

The wrapper sends the underlying process's complete combined stdout/stderr byte
stream to the named log. On `OK`, the visible surface contains only the runner's
`Ran` count, `OK` status, elapsed time, and absolute full-log path. On `FAILED`,
the surface contains bounded failure identities and traceback context, the
runner's final summary, the original exit result, and the full-log path.

If output does not contain a recognizable final `unittest` summary, the wrapper
reports the summary as `UNKNOWN`; it does not invent a test count. The wrapper
still preserves the underlying process exit result. A signal result uses the
shell-observable `128 + signal` exit convention and names both the signal and
exit value.

Generated logs default to `.test-logs/`, which is ignored by Git but is not
deleted by the wrapper. Suppressed output therefore remains available for
inspection until the caller intentionally removes it.

## Value port contract

For a later separately authorized Value port, the repository supplies its own
test command; the wrapper captures its complete output; PASS returns a compact
summary; FAIL returns bounded diagnostics; the full log remains recoverable;
and the underlying exit semantics remain unchanged. This is the reusable
contract only—no shared cross-repository implementation or Value change is part
of this task.
