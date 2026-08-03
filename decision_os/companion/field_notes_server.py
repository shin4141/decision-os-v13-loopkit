"""Authenticated HTTP extension for Field Notes Lite v0.1."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit

from decision_os.companion.field_notes_controller import (
    FieldNoteError,
    FieldNotesCompanionController,
)
from decision_os.companion.server import CompanionRequestHandler, CompanionServer


class FieldNotesRequestHandler(CompanionRequestHandler):
    """Serve Field Notes assets and three bounded state-change routes."""

    def _asset(self, filename: str, content_type: str) -> None:
        if not self._request_allowed():
            return
        target = Path(__file__).resolve().parent / "static" / filename
        try:
            payload = target.read_bytes()
        except OSError:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "UI resource unavailable.")
            return
        self._send_bytes(HTTPStatus.OK, payload, content_type)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/field-notes.js":
            self._asset("field_notes.js", "text/javascript; charset=utf-8")
            return
        if path == "/field-notes.css":
            self._asset("field_notes.css", "text/css; charset=utf-8")
            return
        if path == "/":
            if self._bootstrap(path):
                return
            if not self._request_allowed():
                return
            target = self.server.static_root / "index.html"
            try:
                html = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "UI resource unavailable.")
                return
            html = html.replace(
                "</head>",
                '<link rel="stylesheet" href="/field-notes.css">\n</head>',
            )
            html = html.replace(
                "</body>",
                '<script src="/field-notes.js"></script>\n</body>',
            )
            self._send_bytes(
                HTTPStatus.OK,
                html.encode("utf-8"),
                "text/html; charset=utf-8",
            )
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path not in {
            "/api/field-notes/save",
            "/api/field-notes/skip",
            "/api/field-notes/approval",
        }:
            super().do_POST()
            return
        if not self._request_allowed(state_change=True):
            return
        value = self._read_json(strict=True)
        if value is None:
            return
        controller = self.server.controller
        if not isinstance(controller, FieldNotesCompanionController):
            self._error(HTTPStatus.CONFLICT, "Field Notes controller is unavailable.")
            return
        try:
            if path == "/api/field-notes/save":
                if value:
                    raise FieldNoteError("Save takes no input.")
                snapshot = controller.field_note_save()
            elif path == "/api/field-notes/skip":
                if value:
                    raise FieldNoteError("Skip takes no input.")
                snapshot = controller.field_note_skip()
            else:
                if set(value) != {"choice"} or not isinstance(value["choice"], str):
                    raise FieldNoteError("Approval fields are invalid.")
                snapshot = controller.field_note_approval(value["choice"])
        except FieldNoteError as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        snapshot["csrf"] = self.server.csrf_token
        self._json(HTTPStatus.OK, snapshot)


def configure_field_notes_server(server: CompanionServer) -> None:
    """Select the Field Notes request handler before the server starts."""

    setattr(server._server, "RequestHandlerClass", FieldNotesRequestHandler)
