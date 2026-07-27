#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TARGET_DIRECTORY="${HOME}/Applications"
TARGET_APP="${TARGET_DIRECTORY}/Decision OS Companion.app"
SUPPORT_DIRECTORY="${HOME}/Library/Application Support/Decision OS Companion"
TARGET_RUNTIME="${SUPPORT_DIRECTORY}/runtime"
BUILD_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/decision-os-companion-build.XXXXXX")
STAGED_APP="${BUILD_ROOT}/Decision OS Companion.app"
STAGED_RUNTIME="${BUILD_ROOT}/runtime"
RENDERED_SCRIPT="${BUILD_ROOT}/DecisionOSCompanion.applescript"

cleanup() {
    rm -rf "$BUILD_ROOT"
}
trap cleanup EXIT HUP INT TERM

select_python() {
    for candidate in \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
        /usr/bin/python3
    do
        if [ -x "$candidate" ] && "$candidate" -c \
            'import sys; raise SystemExit(sys.version_info < (3, 10))'
        then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BINARY=$(select_python) || {
    printf '%s\n' "Python 3.10 or newer is required to build the private app." >&2
    exit 1
}

"$PYTHON_BINARY" -c \
    'import functools, json, pathlib, re, sys; source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"); marker = r"-- APPLET_PICKER_ENTRY_BEGIN.*?-- APPLET_PICKER_ENTRY_END"; assert len(re.findall(marker, source, flags=re.S)) == 1; source = re.sub(marker, "on run", source, count=1, flags=re.S); values = {"__PYTHON_BINARY__": sys.argv[3], "__RUNTIME_ROOT__": sys.argv[4]}; assert all(source.count(key) == 1 for key in values); rendered = functools.reduce(lambda text, item: text.replace(item[0], json.dumps(item[1])), values.items(), source); pathlib.Path(sys.argv[2]).write_text(rendered, encoding="utf-8")' \
    "$REPOSITORY_ROOT/macos/DecisionOSCompanion.applescript" \
    "$RENDERED_SCRIPT" \
    "$PYTHON_BINARY" \
    "$TARGET_RUNTIME"
/usr/bin/osacompile \
    -s \
    -o "$STAGED_APP" \
    "$RENDERED_SCRIPT"
"$PYTHON_BINARY" -c \
    'import shutil, sys; shutil.copytree(sys.argv[1], sys.argv[2], ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))' \
    "$REPOSITORY_ROOT/decision_os" \
    "$STAGED_RUNTIME/decision_os"
/bin/mkdir -p "$STAGED_RUNTIME/macos"
/bin/cp \
    "$REPOSITORY_ROOT/macos/DecisionOSCompanion.applescript" \
    "$STAGED_RUNTIME/macos/DecisionOSCompanion.applescript"

/bin/mkdir -p "$TARGET_DIRECTORY"
/bin/mkdir -p "$SUPPORT_DIRECTORY"
/bin/chmod 700 "$SUPPORT_DIRECTORY"
if [ -e "$TARGET_RUNTIME" ]; then
    BACKUP_RUNTIME="${TARGET_RUNTIME}.backup.$(/bin/date +%Y%m%d%H%M%S)"
    /bin/mv "$TARGET_RUNTIME" "$BACKUP_RUNTIME"
    printf 'Previous private runtime moved to: %s\n' "$BACKUP_RUNTIME"
fi
/usr/bin/ditto --norsrc "$STAGED_RUNTIME" "$TARGET_RUNTIME"
if [ -e "$TARGET_APP" ]; then
    BACKUP_APP="${TARGET_APP}.backup.$(/bin/date +%Y%m%d%H%M%S)"
    /bin/mv "$TARGET_APP" "$BACKUP_APP"
    printf 'Previous private app moved to: %s\n' "$BACKUP_APP"
fi
/usr/bin/ditto --norsrc "$STAGED_APP" "$TARGET_APP"

printf 'Built private app: %s\n' "$TARGET_APP"
printf 'Installed private runtime: %s\n' "$TARGET_RUNTIME"
printf 'Python runtime: %s\n' "$PYTHON_BINARY"
