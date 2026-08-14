import hashlib
import json
import os
import stat
import sys

INTERPRETER = "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"
INTERPRETER_IDENTITY = (
    16777234,
    113376340,
    0,
    0,
    0o755,
    1,
    102352,
)
INTERPRETER_SHA256 = "bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e"
STAGE = "/private/tmp/decision-os-f01-slice4a-one-shot-0450739ae668"
STAGE_IDENTITY = (16777234, 123725406, 501, 0, 0o500)
WRAPPER_NAME = "macos_f01_opendirectory_one_shot_wrapper.py"
WRAPPER_IDENTITY = (
    16777234,
    123725636,
    501,
    0,
    0o444,
    1,
    21377,
)
WRAPPER_SHA256 = "faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9"


def emit(status, phase, error):
    report = {
        "authorization_requests_issued_by_loader": 0,
        "authorization_retry_allowed": False,
        "completed_mutations": [],
        "effective_gid": os.getegid(),
        "effective_uid": os.geteuid(),
        "error": error,
        "gate": "HOLD",
        "mutation_execution_attempts": 0,
        "phase": phase,
        "privileged_interaction_budget": 1,
        "privileged_prompts_issued_by_loader": 0,
        "status": status,
    }
    sys.stdout.write(
        json.dumps(report, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    )
    sys.stdout.flush()


def regular_identity(observed):
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_uid,
        observed.st_gid,
        stat.S_IMODE(observed.st_mode),
        observed.st_nlink,
        observed.st_size,
    )


def require_regular(observed, expected, label):
    if not stat.S_ISREG(observed.st_mode) or regular_identity(observed) != expected:
        raise RuntimeError(label + " identity or metadata mismatch")


def hash_fixed_interpreter():
    descriptor = os.open(
        INTERPRETER,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        before = os.fstat(descriptor)
        require_regular(before, INTERPRETER_IDENTITY, "interpreter")
        digest = hashlib.sha256()
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        after = os.fstat(descriptor)
        require_regular(after, INTERPRETER_IDENTITY, "interpreter")
        path_status = os.lstat(INTERPRETER)
        require_regular(path_status, INTERPRETER_IDENTITY, "interpreter path")
        if digest.hexdigest() != INTERPRETER_SHA256:
            raise RuntimeError("interpreter SHA-256 mismatch")
    finally:
        os.close(descriptor)


def read_fixed_wrapper():
    directory = os.open(
        STAGE,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        directory_status = os.fstat(directory)
        directory_identity = (
            directory_status.st_dev,
            directory_status.st_ino,
            directory_status.st_uid,
            directory_status.st_gid,
            stat.S_IMODE(directory_status.st_mode),
        )
        if not stat.S_ISDIR(directory_status.st_mode) or directory_identity != STAGE_IDENTITY:
            raise RuntimeError("staged directory identity or metadata mismatch")
        directory_path_status = os.lstat(STAGE)
        directory_path_identity = (
            directory_path_status.st_dev,
            directory_path_status.st_ino,
            directory_path_status.st_uid,
            directory_path_status.st_gid,
            stat.S_IMODE(directory_path_status.st_mode),
        )
        if not stat.S_ISDIR(directory_path_status.st_mode) or directory_path_identity != STAGE_IDENTITY:
            raise RuntimeError("staged directory path substitution")
        descriptor = os.open(
            WRAPPER_NAME,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=directory,
        )
        try:
            before = os.fstat(descriptor)
            require_regular(before, WRAPPER_IDENTITY, "wrapper")
            chunks = []
            digest = hashlib.sha256()
            total = 0
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                chunks.append(block)
                digest.update(block)
                total += len(block)
                if total > WRAPPER_IDENTITY[-1]:
                    raise RuntimeError("wrapper size exceeded fixed identity")
            after = os.fstat(descriptor)
            require_regular(after, WRAPPER_IDENTITY, "wrapper")
            path_status = os.stat(
                WRAPPER_NAME,
                dir_fd=directory,
                follow_symlinks=False,
            )
            require_regular(path_status, WRAPPER_IDENTITY, "wrapper path")
            if (before.st_dev, before.st_ino) != (path_status.st_dev, path_status.st_ino):
                raise RuntimeError("wrapper path no longer names opened inode")
            if total != WRAPPER_IDENTITY[-1] or digest.hexdigest() != WRAPPER_SHA256:
                raise RuntimeError("wrapper size or SHA-256 mismatch")
            final_directory_status = os.lstat(STAGE)
            final_directory_identity = (
                final_directory_status.st_dev,
                final_directory_status.st_ino,
                final_directory_status.st_uid,
                final_directory_status.st_gid,
                stat.S_IMODE(final_directory_status.st_mode),
            )
            if (
                not stat.S_ISDIR(final_directory_status.st_mode)
                or final_directory_identity != STAGE_IDENTITY
            ):
                raise RuntimeError(
                    "staged directory path or metadata changed during validation"
                )
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)


def main():
    if len(sys.argv) != 1:
        emit("HOLD_LOADER_RUNTIME_INPUT_REJECTED", "runtime_input", "loader accepts no arguments")
        return 0
    if os.geteuid() != 0 or os.getegid() != 0:
        emit(
            "HOLD_LOADER_PRIVILEGE_REQUIRED",
            "privilege_gate",
            "exact root execution identity is required",
        )
        return 0
    try:
        if sys.executable != INTERPRETER:
            raise RuntimeError("interpreter path mismatch")
        hash_fixed_interpreter()
        wrapper = read_fixed_wrapper()
    except Exception as exc:
        emit("HOLD_LOADER_IDENTITY_FAILURE", "identity_validation", str(exc))
        return 0
    wrapper_path = STAGE + "/" + WRAPPER_NAME
    sys.argv = [wrapper_path]
    scope = {
        "__builtins__": __builtins__,
        "__file__": wrapper_path,
        "__name__": "__main__",
        "__package__": None,
    }
    try:
        exec(compile(wrapper, wrapper_path, "exec", dont_inherit=True), scope, scope)
    except SystemExit:
        raise
    except Exception as exc:
        emit("HOLD_WRAPPER_UNHANDLED_FAILURE", "wrapper_execution", str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
