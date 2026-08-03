"""Launch the private Decision OS Companion without a Terminal surface."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import webbrowser

from .field_notes_controller import FieldNotesCompanionController
from .field_notes_server import configure_field_notes_server
from .server import CompanionServer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decision-os-companion")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--state-path", type=Path)
    parser.add_argument("--picker-script", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    package_root = Path(__file__).resolve().parent
    picker = arguments.picker_script
    if picker is None:
        configured = os.environ.get("DECISION_OS_COMPANION_PICKER_SCRIPT")
        picker = (
            Path(configured)
            if configured
            else package_root.parents[1]
            / "macos"
            / "DecisionOSCompanion.applescript"
        )
    controller = FieldNotesCompanionController(
        state_path=arguments.state_path,
        picker_script=picker,
    )
    server = CompanionServer(controller, static_root=package_root / "static")
    configure_field_notes_server(server)
    if not arguments.no_browser:
        webbrowser.open(server.bootstrap_url, new=1, autoraise=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
