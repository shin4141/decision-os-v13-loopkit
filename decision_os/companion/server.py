"""Authenticated localhost-only HTTP presentation for Decision OS Companion."""

from __future__ import annotations

import base64
import binascii
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import secrets
import threading
from typing import Any
from urllib.parse import urlsplit

from .controller import (
    ApprovalStateError,
    CompanionController,
    CompanionError,
    CompanionStateError,
    RepositorySelectionError,
    RunConflictError,
)
from .manual_bridge import (
    ManualBridgeConflictError,
    ManualBridgeError,
    ManualBridgeIntegrityError,
    ManualBridgeValidationError,
)
from decision_os.acceleration.store import StateIntegrityError


_MAX_REQUEST_BYTES = 64 * 1024
_MAX_BRIDGE_REQUEST_BYTES = 2 * 1024 * 1024
_STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}
_CSP = (
    "default-src 'none'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "connect-src 'self'; "
    "img-src 'self'; "
    "font-src 'none'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)


class CompanionHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        controller: CompanionController,
        static_root: Path,
    ) -> None:
        self.controller = controller
        self.static_root = static_root.resolve(strict=True)
        self.bootstrap_token = secrets.token_urlsafe(32)
        self.session_token = secrets.token_urlsafe(32)
        self.csrf_token = secrets.token_urlsafe(32)
        self.bootstrap_available = True
        super().__init__(("127.0.0.1", 0), CompanionRequestHandler)

    @property
    def origin(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"


class CompanionRequestHandler(BaseHTTPRequestHandler):
    server: CompanionHTTPServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Security-Policy", _CSP)
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def _send_bytes(
        self,
        status: HTTPStatus,
        payload: bytes,
        content_type: str,
        *,
        cookie: str | None = None,
        location: str | None = None,
    ) -> None:
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        if location is not None:
            self.send_header("Location", location)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _json(self, status: HTTPStatus, value: Any) -> None:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        serialized = (
            serialized.replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        payload = serialized.encode("utf-8")
        self._send_bytes(
            status,
            payload,
            "application/json; charset=utf-8",
        )

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"error": message})

    def _host_valid(self) -> bool:
        expected = f"127.0.0.1:{self.server.server_address[1]}"
        observed = self.headers.get("Host", "")
        return hmac.compare_digest(observed, expected)

    def _origin_valid(self, *, required: bool) -> bool:
        observed = self.headers.get("Origin")
        if observed is None:
            return not required
        return hmac.compare_digest(observed, self.server.origin)

    def _session_valid(self) -> bool:
        raw = self.headers.get("Cookie")
        if not raw:
            return False
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except Exception:
            return False
        value = cookie.get("decision_os_session")
        return bool(
            value
            and hmac.compare_digest(
                value.value,
                self.server.session_token,
            )
        )

    def _csrf_valid(self) -> bool:
        observed = self.headers.get("X-Decision-OS-CSRF", "")
        return bool(
            observed
            and hmac.compare_digest(observed, self.server.csrf_token)
        )

    def _request_allowed(self, *, state_change: bool = False) -> bool:
        if not self._host_valid():
            self._error(HTTPStatus.FORBIDDEN, "Request host was rejected.")
            return False
        if not self._origin_valid(required=state_change):
            self._error(HTTPStatus.FORBIDDEN, "Request origin was rejected.")
            return False
        if not self._session_valid():
            self._error(HTTPStatus.UNAUTHORIZED, "Private session required.")
            return False
        if state_change and not self._csrf_valid():
            self._error(HTTPStatus.FORBIDDEN, "CSRF validation failed.")
            return False
        return True

    def _bootstrap(self, path: str) -> bool:
        prefix = "/bootstrap/"
        if not path.startswith(prefix):
            return False
        if not self._host_valid() or not self._origin_valid(required=False):
            self._error(HTTPStatus.FORBIDDEN, "Bootstrap request was rejected.")
            return True
        candidate = path[len(prefix) :]
        valid = (
            self.server.bootstrap_available
            and candidate
            and hmac.compare_digest(candidate, self.server.bootstrap_token)
        )
        if not valid:
            self._error(HTTPStatus.UNAUTHORIZED, "Bootstrap token was rejected.")
            return True
        self.server.bootstrap_available = False
        cookie = (
            "decision_os_session="
            f"{self.server.session_token}; HttpOnly; SameSite=Strict; Path=/"
        )
        self._send_bytes(
            HTTPStatus.SEE_OTHER,
            b"",
            "text/plain; charset=utf-8",
            cookie=cookie,
            location="/",
        )
        return True

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if self._bootstrap(path):
            return
        if not self._request_allowed():
            return
        if path == "/api/state":
            try:
                snapshot = self.server.controller.snapshot()
            except (
                CompanionError,
                CompanionStateError,
                StateIntegrityError,
            ):
                self._error(
                    HTTPStatus.CONFLICT,
                    "Local companion state could not be read safely.",
                )
                return
            snapshot["csrf"] = self.server.csrf_token
            self._json(HTTPStatus.OK, snapshot)
            return
        static = _STATIC_FILES.get(path)
        if static is None:
            self._error(HTTPStatus.NOT_FOUND, "Resource not found.")
            return
        filename, content_type = static
        target = self.server.static_root / filename
        try:
            payload = target.read_bytes()
        except OSError:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "UI resource unavailable.")
            return
        self._send_bytes(HTTPStatus.OK, payload, content_type)

    def _read_json(
        self,
        *,
        maximum_bytes: int = _MAX_REQUEST_BYTES,
    ) -> dict[str, Any] | None:
        if self.headers.get_content_type() != "application/json":
            self._error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "JSON request required.",
            )
            return None
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError:
            self._error(HTTPStatus.BAD_REQUEST, "Content length is invalid.")
            return None
        if length < 0 or length > maximum_bytes:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request is too large.")
            return None
        try:
            value = json.loads(self.rfile.read(length))
        except (UnicodeError, json.JSONDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "Request JSON is invalid.")
            return None
        if not isinstance(value, dict):
            self._error(HTTPStatus.BAD_REQUEST, "Request object required.")
            return None
        return value

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if not self._request_allowed(state_change=True):
            return
        maximum_bytes = (
            _MAX_BRIDGE_REQUEST_BYTES
            if path.startswith("/api/bridge/")
            else _MAX_REQUEST_BYTES
        )
        value = self._read_json(maximum_bytes=maximum_bytes)
        if value is None:
            return
        try:
            if path == "/api/repository/pick":
                if value:
                    raise CompanionError("Repository picker takes no input.")
                snapshot = self.server.controller.pick_repository()
            elif path == "/api/run":
                if set(value) != {"task"}:
                    raise CompanionError("Run request fields are invalid.")
                snapshot = self.server.controller.start_run(value["task"])
            elif path == "/api/approval":
                if set(value) != {"choice"}:
                    raise CompanionError("Approval request fields are invalid.")
                snapshot = self.server.controller.submit_approval(value["choice"])
            elif path == "/api/new-run":
                if value:
                    raise CompanionError("New Run takes no input.")
                snapshot = self.server.controller.new_run()
            elif path == "/api/default/revoke":
                if set(value) != {"handle"}:
                    raise CompanionError("Revoke request fields are invalid.")
                snapshot = self.server.controller.revoke_default(value["handle"])
            elif path == "/api/bridge/session":
                if set(value) != {"boundary"} or not isinstance(
                    value["boundary"],
                    dict,
                ):
                    raise CompanionError("Bridge session fields are invalid.")
                snapshot = self.server.controller.start_bridge_session(
                    value["boundary"]
                )
            elif path == "/api/bridge/copy":
                if value:
                    raise CompanionError("Copy for Pro takes no input.")
                snapshot = self.server.controller.bridge_copy_for_pro()
            elif path == "/api/bridge/import":
                allowed = {
                    "mode",
                    "selected_role",
                    "source_path_or_label",
                    "payload_base64",
                    "payload_text",
                    "metadata",
                    "declared_sha256",
                    "supersedes_import_event_id",
                    "correction_reason",
                }
                required = {
                    "mode",
                    "selected_role",
                    "source_path_or_label",
                }
                if not required.issubset(value) or not set(value).issubset(
                    allowed
                ):
                    raise CompanionError("Bridge import fields are invalid.")
                mode = value["mode"]
                if mode == "BYTE_EXACT_FILE_IMPORT":
                    encoded = value.get("payload_base64")
                    if (
                        not isinstance(encoded, str)
                        or "payload_text" in value
                    ):
                        raise CompanionError(
                            "Byte-exact import payload is invalid."
                        )
                    try:
                        payload = base64.b64decode(
                            encoded.encode("ascii"),
                            validate=True,
                        )
                    except (UnicodeError, ValueError, binascii.Error) as exc:
                        raise CompanionError(
                            "Byte-exact import payload is invalid."
                        ) from exc
                elif mode == "PASTE_CAPTURE":
                    captured = value.get("payload_text")
                    if (
                        not isinstance(captured, str)
                        or "payload_base64" in value
                    ):
                        raise CompanionError(
                            "Paste capture payload is invalid."
                        )
                    try:
                        payload = captured.encode("utf-8")
                    except UnicodeEncodeError as exc:
                        raise CompanionError(
                            "Paste capture is not valid UTF-8 text."
                        ) from exc
                else:
                    raise CompanionError("Bridge import mode is invalid.")
                metadata = value.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    raise CompanionError("Bridge metadata is invalid.")
                snapshot = self.server.controller.bridge_import_artifact(
                    selected_role=value["selected_role"],
                    payload=payload,
                    source_path_or_label=value["source_path_or_label"],
                    import_mode=mode,
                    metadata=metadata,
                    declared_sha256=value.get("declared_sha256"),
                    supersedes_import_event_id=value.get(
                        "supersedes_import_event_id"
                    ),
                    correction_reason=value.get("correction_reason"),
                )
            elif path == "/api/bridge/handoff/generate":
                if value:
                    raise CompanionError(
                        "Execution Handoff generation takes no input."
                    )
                snapshot = self.server.controller.bridge_generate_handoff()
            elif path == "/api/bridge/output/freeze":
                if set(value) != {"role"}:
                    raise CompanionError("Bridge freeze fields are invalid.")
                snapshot = self.server.controller.bridge_freeze_output(
                    value["role"]
                )
            elif path == "/api/bridge/receipt/generate":
                if value:
                    raise CompanionError(
                        "Bridge Receipt generation takes no input."
                    )
                snapshot = self.server.controller.bridge_generate_receipt()
            elif path == "/api/bridge/manifest/generate":
                if value:
                    raise CompanionError(
                        "Golden manifest generation takes no input."
                    )
                snapshot = self.server.controller.bridge_generate_manifest()
            elif path == "/api/bridge/replay":
                if (
                    set(value) != {"baseline", "candidate"}
                    or not isinstance(value["baseline"], dict)
                    or not isinstance(value["candidate"], dict)
                ):
                    raise CompanionError("Replay fields are invalid.")
                snapshot = self.server.controller.bridge_replay(
                    value["baseline"],
                    value["candidate"],
                )
            elif path == "/api/bridge/observation":
                required = {"field", "value", "unit", "method"}
                if (
                    not required.issubset(value)
                    or not set(value).issubset(required | {"notes"})
                ):
                    raise CompanionError(
                        "Burden observation fields are invalid."
                    )
                snapshot = self.server.controller.bridge_record_observation(
                    field=value["field"],
                    value=value["value"],
                    unit=value["unit"],
                    method=value["method"],
                    notes=value.get("notes", ""),
                )
            else:
                self._error(HTTPStatus.NOT_FOUND, "Endpoint not found.")
                return
        except (RepositorySelectionError, CompanionStateError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except (RunConflictError, ApprovalStateError) as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        except (ManualBridgeConflictError, ManualBridgeIntegrityError) as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        except (ManualBridgeValidationError, ManualBridgeError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except CompanionError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except StateIntegrityError:
            self._error(
                HTTPStatus.CONFLICT,
                "Repository verification state is corrupted.",
            )
            return
        snapshot["csrf"] = self.server.csrf_token
        self._json(HTTPStatus.OK, snapshot)


class CompanionServer:
    """Lifecycle wrapper around the authenticated loopback HTTP server."""

    def __init__(
        self,
        controller: CompanionController,
        *,
        static_root: Path,
    ) -> None:
        self._server = CompanionHTTPServer(controller, static_root)
        self._thread: threading.Thread | None = None

    @property
    def origin(self) -> str:
        return self._server.origin

    @property
    def bootstrap_url(self) -> str:
        return (
            f"{self.origin}/bootstrap/"
            f"{self._server.bootstrap_token}"
        )

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start_background(self) -> None:
        if self._thread is not None:
            raise RuntimeError("Companion server is already running.")
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="decision-os-companion-http",
            daemon=True,
        )
        self._thread.start()

    def serve_forever(self) -> None:
        self._server.serve_forever()

    def close(self) -> None:
        if self._thread is not None:
            self._server.shutdown()
            self._thread.join(timeout=5)
            self._thread = None
        self._server.server_close()
