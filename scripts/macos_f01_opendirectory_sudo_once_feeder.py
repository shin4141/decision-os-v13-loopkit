from __future__ import annotations

import getpass
import json
import subprocess
import sys
import warnings
from typing import BinaryIO, Callable, Optional, Sequence


SUDO = "/usr/bin/sudo"
PYTHON = (
    "/Library/Developer/CommandLineTools/Library/Frameworks/"
    "Python3.framework/Versions/3.9/bin/python3.9"
)
LOADER_PAYLOAD_B64 = (
    "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"
)
LOADER_BOOTSTRAP = (
    'import base64,zlib;exec(compile(zlib.decompress(base64.b64decode("'
    + LOADER_PAYLOAD_B64
    + '")),"<decision-os-f01-one-shot-loader>","exec",dont_inherit=True))'
)
SUDO_ARGV = (
    SUDO,
    "-S",
    "-p",
    "",
    "--",
    PYTHON,
    "-I",
    "-S",
    "-c",
    LOADER_BOOTSTRAP,
)
SUDO_ENV = {
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
}
PASSWORD_PROMPT = "DecisionOS administrator password (one attempt): "
PRIVILEGED_HUMAN_INTERACTION_BUDGET = 1
SUDO_INVOCATION_BUDGET = 1
AUTHORIZATION_RETRY_ALLOWED = False
EXPECTED_STATUS = "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW"
EXPECTED_COMPLETED_MUTATIONS = ["user_deleted", "group_deleted"]
HOLD_EXIT_CODE = 3
MAX_RESULT_BYTES = 1024 * 1024


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _is_exact_success(stdout: bytes) -> bool:
    if len(stdout) > MAX_RESULT_BYTES:
        return False
    try:
        decoded = stdout.decode("utf-8")
        report = json.loads(decoded)
    except (UnicodeError, TypeError, ValueError):
        return False
    if type(report) is not dict or _canonical_json_bytes(report) != stdout:
        return False
    return (
        report.get("status") == EXPECTED_STATUS
        and report.get("completed_mutations") == EXPECTED_COMPLETED_MUTATIONS
    )


def run_once(
    *,
    password_reader: Optional[Callable[[str], str]] = None,
    process_factory: Optional[Callable[..., object]] = None,
    stdout: Optional[BinaryIO] = None,
    stderr: Optional[BinaryIO] = None,
) -> int:
    reader = getpass.getpass if password_reader is None else password_reader
    factory = subprocess.Popen if process_factory is None else process_factory
    output = sys.stdout.buffer if stdout is None else stdout
    errors = sys.stderr.buffer if stderr is None else stderr

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = reader(PASSWORD_PROMPT)
    except (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
        return HOLD_EXIT_CODE
    if type(password) is not str or "\n" in password or "\r" in password:
        return HOLD_EXIT_CODE

    credential_line = password.encode("utf-8") + b"\n"
    password = None
    try:
        child = factory(
            list(SUDO_ARGV),
            close_fds=True,
            cwd="/",
            env=dict(SUDO_ENV),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        credential_line = None
        return HOLD_EXIT_CODE

    child_stdout, child_stderr = child.communicate(input=credential_line)
    credential_line = None
    if type(child_stdout) is not bytes or type(child_stderr) is not bytes:
        return HOLD_EXIT_CODE

    output.write(child_stdout)
    output.flush()
    errors.write(child_stderr)
    errors.flush()

    if child.returncode != 0:
        return HOLD_EXIT_CODE
    return 0 if _is_exact_success(child_stdout) else HOLD_EXIT_CODE


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments:
        return HOLD_EXIT_CODE
    return run_once()


if __name__ == "__main__":
    raise SystemExit(main())
