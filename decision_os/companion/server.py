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
from .continuation import (
    ContinuationIntegrityError,
    StageBContinuationRequest,
)
from .small_compound_loop import StageCContinuationRequest
from .guided_intake import (
    GuidedIntakeBusyError,
    GuidedIntakeConflictError,
    GuidedIntakeError,
    GuidedIntakeIntegrityError,
    GuidedIntakeValidationError,
)
from .intelligence_transplant import (
    IntelligenceTransplantBusyError,
    IntelligenceTransplantConflictError,
    IntelligenceTransplantError,
    IntelligenceTransplantIntegrityError,
    IntelligenceTransplantValidationError,
)
from .manual_bridge import (
    ManualBridgeConflictError,
    ManualBridgeError,
    ManualBridgeIntegrityError,
    ManualBridgeValidationError,
)
from .ordinary_user_path import MAX_SOURCE_BYTES, OrdinaryUserPathError
from decision_os.acceleration.store import StateIntegrityError


_MAX_REQUEST_BYTES = 64 * 1024
_MAX_BRIDGE_REQUEST_BYTES = 2 * 1024 * 1024
_MAX_GUIDED_INTAKE_REQUEST_BYTES = 2 * 1024 * 1024
_MAX_INTELLIGENCE_TRANSPLANT_REQUEST_BYTES = 2 * 1024 * 1024
_MAX_ORDINARY_CONTRACT_REQUEST_BYTES = 131_072
_GUIDED_INTAKE_POST_ROUTES = frozenset(
    {
        "/api/guided-intake/capture",
        "/api/guided-intake/confirm",
        "/api/guided-intake/copy",
        "/api/guided-intake/freeze",
        "/api/guided-intake/import-draft",
        "/api/guided-intake/purge",
        "/api/guided-intake/transfer-to-bridge",
    }
)
_INTELLIGENCE_TRANSPLANT_POST_ROUTES = frozenset(
    {
        "/api/intelligence-transplant/charter/freeze",
        "/api/intelligence-transplant/manifest/freeze",
        "/api/intelligence-transplant/evidence/attach",
        "/api/intelligence-transplant/receipt/attach",
        "/api/intelligence-transplant/control/record",
    }
)
_ORDINARY_CONTRACT_POST_ROUTES = frozenset(
    {
        "/api/ordinary-contract/prepare",
        "/api/ordinary-contract/confirm",
        "/api/ordinary-contract/fix",
        "/api/ordinary-contract/error/dismiss",
    }
)
_COMPOUND_LOOP_POST_ROUTES = frozenset(
    {"/api/compound-run", "/api/compound-loop"}
)
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


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON object key.")
        value[key] = item
    return value


def _reject_non_finite_json(constant: str) -> None:
    raise ValueError(f"Non-finite JSON number: {constant}")


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

    def _ordinary_error(
        self,
        status: HTTPStatus,
        code: str,
        message: str,
        *,
        error_id: str | None = None,
    ) -> None:
        try:
            ordinary = self.server.controller.snapshot().get(
                "ordinary_contract"
            )
        except Exception:
            ordinary = None
        self._json(
            status,
            {
                "error": {
                    "code": code,
                    "error_id": error_id,
                    "message": message,
                },
                "ordinary_contract": ordinary,
            },
        )

    def _persist_ordinary_error(
        self,
        code: str,
        message: str,
        error_id: str | None = None,
    ) -> str | None:
        if error_id is not None:
            return error_id
        try:
            return self.server.controller.ordinary_contract_record_error(
                code,
                message,
            )
        except Exception:
            return None

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
        if path in {"/api/state", "/api/guided-intake/state"}:
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
        strict: bool = False,
        ordinary: bool = False,
    ) -> dict[str, Any] | None:
        def reject(status: HTTPStatus, code: str, message: str) -> None:
            if ordinary:
                self._ordinary_error(
                    status,
                    code,
                    message,
                    error_id=self._persist_ordinary_error(code, message),
                )
            else:
                self._error(status, message)

        if self.headers.get_content_type() != "application/json":
            reject(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "JSON request required.",
            )
            return None
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError:
            reject(
                HTTPStatus.BAD_REQUEST,
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "Content length is invalid.",
            )
            return None
        if length < 0 or length > maximum_bytes:
            reject(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "PREP_SOURCE_TOO_LARGE",
                "Request is too large.",
            )
            return None
        try:
            raw = self.rfile.read(length)
            if strict:
                value = json.loads(
                    raw,
                    object_pairs_hook=_strict_object,
                    parse_constant=_reject_non_finite_json,
                )
            else:
                value = json.loads(raw)
        except (UnicodeError, ValueError):
            reject(
                HTTPStatus.BAD_REQUEST,
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "Request JSON is invalid.",
            )
            return None
        if not isinstance(value, dict):
            reject(
                HTTPStatus.BAD_REQUEST,
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "Request object required.",
            )
            return None
        return value

    @staticmethod
    def _transport_payload(
        value: dict[str, Any],
    ) -> tuple[bytes, dict[str, Any]]:
        common = {
            "mode",
            "source_path_or_label",
            "declared_sha256",
            "context_evidence_ref",
            "as_of",
        }
        payload_fields = {"payload_base64", "payload_text"} & set(value)
        if (
            set(value) != common | payload_fields
            or len(payload_fields) != 1
            or not isinstance(value["mode"], str)
            or not isinstance(value["source_path_or_label"], str)
            or not isinstance(value["declared_sha256"], str)
            or (
                value["context_evidence_ref"] is not None
                and not isinstance(value["context_evidence_ref"], dict)
            )
            or not isinstance(value["as_of"], str)
        ):
            raise CompanionError(
                "Intelligence Transplant transport fields are invalid."
            )
        mode = value["mode"]
        if mode == "BYTE_EXACT_FILE_IMPORT":
            encoded = value.get("payload_base64")
            if not isinstance(encoded, str) or "payload_text" in value:
                raise CompanionError(
                    "Intelligence Transplant byte-exact payload is invalid."
                )
            try:
                payload = base64.b64decode(
                    encoded.encode("ascii"),
                    validate=True,
                )
            except (UnicodeError, ValueError, binascii.Error) as exc:
                raise CompanionError(
                    "Intelligence Transplant byte-exact payload is invalid."
                ) from exc
        elif mode == "PASTE_CAPTURE":
            captured = value.get("payload_text")
            if not isinstance(captured, str) or "payload_base64" in value:
                raise CompanionError(
                    "Intelligence Transplant paste payload is invalid."
                )
            try:
                payload = captured.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CompanionError(
                    "Intelligence Transplant paste payload is invalid."
                ) from exc
        else:
            raise CompanionError(
                "Intelligence Transplant transport mode is invalid."
            )
        metadata = {
            "mode": mode,
            "source_path_or_label": value["source_path_or_label"],
            "declared_sha256": value["declared_sha256"],
            "context_evidence_ref": value["context_evidence_ref"],
            "as_of": value["as_of"],
        }
        return payload, metadata

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if not self._request_allowed(state_change=True):
            return
        if path.startswith("/api/bridge/"):
            maximum_bytes = _MAX_BRIDGE_REQUEST_BYTES
        elif path in _INTELLIGENCE_TRANSPLANT_POST_ROUTES:
            maximum_bytes = _MAX_INTELLIGENCE_TRANSPLANT_REQUEST_BYTES
        elif path in _GUIDED_INTAKE_POST_ROUTES:
            maximum_bytes = _MAX_GUIDED_INTAKE_REQUEST_BYTES
        elif path in _ORDINARY_CONTRACT_POST_ROUTES:
            maximum_bytes = _MAX_ORDINARY_CONTRACT_REQUEST_BYTES
        else:
            maximum_bytes = _MAX_REQUEST_BYTES
        value = self._read_json(
            maximum_bytes=maximum_bytes,
            strict=(
                path in _INTELLIGENCE_TRANSPLANT_POST_ROUTES
                or path in _ORDINARY_CONTRACT_POST_ROUTES
                or path in _COMPOUND_LOOP_POST_ROUTES
            ),
            ordinary=path in _ORDINARY_CONTRACT_POST_ROUTES,
        )
        if value is None:
            return
        try:
            if path == "/api/repository/pick":
                if value:
                    raise CompanionError("Repository picker takes no input.")
                snapshot = self.server.controller.pick_repository()
            elif path == "/api/run":
                if set(value) not in ({"task"}, {"task", "task_mode"}):
                    raise CompanionError("Run request fields are invalid.")
                if "task_mode" in value:
                    snapshot = self.server.controller.start_run(
                        value["task"],
                        task_mode=value["task_mode"],
                    )
                else:
                    snapshot = self.server.controller.start_run(value["task"])
            elif path == "/api/compound-run":
                if set(value) != {"request"} or not isinstance(
                    value["request"],
                    dict,
                ):
                    raise CompanionError(
                        "Stage B continuation request fields are invalid."
                    )
                try:
                    request = StageBContinuationRequest.from_dict(
                        value["request"]
                    )
                except ContinuationIntegrityError as exc:
                    raise CompanionError(
                        "Stage B continuation request fields are invalid."
                    ) from exc
                snapshot = (
                    self.server.controller.start_one_automatic_continuation(
                        request
                    )
                )
            elif path == "/api/compound-loop":
                if set(value) != {"request"} or not isinstance(
                    value["request"],
                    dict,
                ):
                    raise CompanionError(
                        "Stage C compound-loop request fields are invalid."
                    )
                try:
                    request = StageCContinuationRequest.from_dict(
                        value["request"]
                    )
                except ContinuationIntegrityError as exc:
                    raise CompanionError(
                        "Stage C compound-loop request fields are invalid."
                    ) from exc
                snapshot = self.server.controller.start_small_compound_loop(
                    request
                )
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
            elif path == "/api/intelligence-transplant/charter/freeze":
                if set(value) != {"record"} or not isinstance(
                    value["record"],
                    dict,
                ):
                    raise CompanionError(
                        "Intelligence Transplant Charter fields are invalid."
                    )
                snapshot = (
                    self.server.controller
                    .intelligence_transplant_freeze_charter(value["record"])
                )
            elif path == "/api/intelligence-transplant/manifest/freeze":
                payload, metadata = self._transport_payload(value)
                snapshot = (
                    self.server.controller
                    .intelligence_transplant_freeze_manifest(
                        payload=payload,
                        **metadata,
                    )
                )
            elif path == "/api/intelligence-transplant/evidence/attach":
                payload, metadata = self._transport_payload(value)
                snapshot = (
                    self.server.controller
                    .intelligence_transplant_attach_evidence(
                        payload=payload,
                        **metadata,
                    )
                )
            elif path == "/api/intelligence-transplant/receipt/attach":
                payload, metadata = self._transport_payload(value)
                snapshot = (
                    self.server.controller
                    .intelligence_transplant_attach_receipt(
                        payload=payload,
                        **metadata,
                    )
                )
            elif path == "/api/intelligence-transplant/control/record":
                payload, metadata = self._transport_payload(value)
                snapshot = (
                    self.server.controller
                    .intelligence_transplant_record_control(
                        payload=payload,
                        **metadata,
                    )
                )
            elif path == "/api/ordinary-contract/prepare":
                if (
                    set(value)
                    != {
                        "filename",
                        "source_base64",
                        "source_byte_size",
                        "source_sha256",
                        "expected_repository_identity",
                        "expected_active_request_id",
                        "idempotency_key",
                    }
                    or not isinstance(value["filename"], str)
                    or not isinstance(value["source_base64"], str)
                    or not isinstance(value["source_byte_size"], int)
                    or isinstance(value["source_byte_size"], bool)
                    or not isinstance(value["source_sha256"], str)
                    or not isinstance(value["expected_repository_identity"], str)
                    or (
                        value["expected_active_request_id"] is not None
                        and not isinstance(value["expected_active_request_id"], str)
                    )
                    or not isinstance(value["idempotency_key"], str)
                ):
                    raise OrdinaryUserPathError(
                        "PREP_SOURCE_TRANSPORT_MISMATCH",
                        "Contract preparation fields are invalid.",
                        http_status=400,
                    )
                if value["source_byte_size"] > MAX_SOURCE_BYTES:
                    raise OrdinaryUserPathError(
                        "PREP_SOURCE_TOO_LARGE",
                        "The Contract is too large for this bounded path.",
                        http_status=413,
                    )
                try:
                    source = base64.b64decode(
                        value["source_base64"].encode("ascii"),
                        validate=True,
                    )
                except (UnicodeError, ValueError, binascii.Error) as exc:
                    raise OrdinaryUserPathError(
                        "PREP_SOURCE_TRANSPORT_MISMATCH",
                        "The selected Contract bytes are invalid.",
                        http_status=400,
                    ) from exc
                snapshot = self.server.controller.ordinary_contract_prepare(
                    filename=value["filename"],
                    source_bytes=source,
                    source_byte_size=value["source_byte_size"],
                    source_sha256=value["source_sha256"],
                    expected_repository_identity=value[
                        "expected_repository_identity"
                    ],
                    expected_active_request_id=value[
                        "expected_active_request_id"
                    ],
                    idempotency_key=value["idempotency_key"],
                )
            elif path == "/api/ordinary-contract/confirm":
                if (
                    set(value)
                    != {
                        "preparation_id",
                        "clarification_id",
                        "answer",
                        "expected_interpretation_sha256",
                        "idempotency_key",
                    }
                    or not all(
                        isinstance(value[field], str)
                        for field in value
                    )
                    or value["answer"] not in {"CONFIRM", "REJECT"}
                ):
                    raise OrdinaryUserPathError(
                        "CONFIRM_ANSWER_INVALID",
                        "Contract confirmation fields are invalid.",
                        http_status=400,
                    )
                snapshot = self.server.controller.ordinary_contract_confirm(
                    preparation_id=value["preparation_id"],
                    clarification_id=value["clarification_id"],
                    answer=value["answer"],
                    expected_interpretation_sha256=value[
                        "expected_interpretation_sha256"
                    ],
                    idempotency_key=value["idempotency_key"],
                )
            elif path == "/api/ordinary-contract/fix":
                if (
                    set(value)
                    != {
                        "preparation_id",
                        "expected_repository_identity",
                        "expected_source_sha256",
                        "expected_request_id",
                        "expected_draft_id",
                        "expected_interpretation_sha256",
                        "idempotency_key",
                    }
                    or not all(
                        isinstance(value[field], str)
                        for field in value
                    )
                ):
                    raise OrdinaryUserPathError(
                        "FIX_NOT_READY",
                        "Contract fixation fields are invalid.",
                        http_status=400,
                    )
                snapshot = self.server.controller.ordinary_contract_fix(
                    preparation_id=value["preparation_id"],
                    expected_repository_identity=value[
                        "expected_repository_identity"
                    ],
                    expected_source_sha256=value["expected_source_sha256"],
                    expected_request_id=value["expected_request_id"],
                    expected_draft_id=value["expected_draft_id"],
                    expected_interpretation_sha256=value[
                        "expected_interpretation_sha256"
                    ],
                    idempotency_key=value["idempotency_key"],
                )
            elif path == "/api/ordinary-contract/error/dismiss":
                if (
                    set(value) != {"error_id", "idempotency_key"}
                    or not isinstance(value["error_id"], str)
                    or not isinstance(value["idempotency_key"], str)
                ):
                    raise OrdinaryUserPathError(
                        "ORDINARY_IDEMPOTENCY_CONFLICT",
                        "Error dismissal fields are invalid.",
                        http_status=400,
                    )
                snapshot = (
                    self.server.controller.ordinary_contract_dismiss_error(
                        error_id=value["error_id"],
                        idempotency_key=value["idempotency_key"],
                    )
                )
            elif path == "/api/guided-intake/capture":
                required = {"original_request"}
                allowed = required | {"supersedes_request_id"}
                if (
                    not required.issubset(value)
                    or not set(value).issubset(allowed)
                    or not isinstance(value["original_request"], str)
                    or (
                        "supersedes_request_id" in value
                        and not isinstance(value["supersedes_request_id"], str)
                    )
                ):
                    raise CompanionError(
                        "Guided Intake capture fields are invalid."
                    )
                snapshot = self.server.controller.guided_intake_capture(
                    value["original_request"],
                    supersedes_request_id=value.get("supersedes_request_id"),
                )
            elif path == "/api/guided-intake/copy":
                if value:
                    raise CompanionError(
                        "Guided Intake copy takes no input."
                    )
                snapshot = self.server.controller.guided_intake_copy_for_pro()
            elif path == "/api/guided-intake/import-draft":
                if (
                    set(value) != {"draft_json", "producer_label"}
                    or not isinstance(value["draft_json"], str)
                    or not isinstance(value["producer_label"], str)
                ):
                    raise CompanionError(
                        "Guided Intake draft fields are invalid."
                    )
                snapshot = self.server.controller.guided_intake_import_draft(
                    value["draft_json"],
                    value["producer_label"],
                )
            elif path == "/api/guided-intake/confirm":
                if (
                    set(value) != {"question", "answer", "resulting_delta"}
                    or not isinstance(value["question"], str)
                    or not isinstance(value["answer"], str)
                    or not isinstance(value["resulting_delta"], dict)
                ):
                    raise CompanionError(
                        "Guided Intake confirmation fields are invalid."
                    )
                snapshot = self.server.controller.guided_intake_confirm(
                    value["question"],
                    value["answer"],
                    value["resulting_delta"],
                )
            elif path == "/api/guided-intake/freeze":
                if value:
                    raise CompanionError(
                        "Guided Intake freeze takes no input."
                    )
                snapshot = self.server.controller.guided_intake_freeze()
            elif path == "/api/guided-intake/purge":
                if (
                    set(value)
                    != {"request_id", "request_sha256", "confirmed"}
                    or not isinstance(value["request_id"], str)
                    or not isinstance(value["request_sha256"], str)
                    or type(value["confirmed"]) is not bool
                ):
                    raise CompanionError(
                        "Guided Intake purge fields are invalid."
                    )
                snapshot = self.server.controller.guided_intake_purge(
                    value["request_id"],
                    value["request_sha256"],
                    value["confirmed"],
                )
            elif path == "/api/guided-intake/transfer-to-bridge":
                if value:
                    raise CompanionError(
                        "Guided Intake transfer takes no input."
                    )
                snapshot = (
                    self.server.controller.guided_intake_transfer_to_bridge()
                )
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
        except OrdinaryUserPathError as exc:
            error_id = self._persist_ordinary_error(
                exc.code,
                exc.message,
                exc.error_id,
            )
            self._ordinary_error(
                HTTPStatus(exc.http_status),
                exc.code,
                exc.message,
                error_id=error_id,
            )
            return
        except (RepositorySelectionError, CompanionStateError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except (RunConflictError, ApprovalStateError) as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        except (
            GuidedIntakeBusyError,
            GuidedIntakeConflictError,
            GuidedIntakeIntegrityError,
        ) as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        except GuidedIntakeValidationError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except GuidedIntakeError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except IntelligenceTransplantBusyError:
            self._error(
                HTTPStatus.CONFLICT,
                "Intelligence Transplant is temporarily busy.",
            )
            return
        except IntelligenceTransplantIntegrityError:
            self._error(
                HTTPStatus.CONFLICT,
                "Intelligence Transplant state is corrupted.",
            )
            return
        except IntelligenceTransplantConflictError as exc:
            self._error(HTTPStatus.CONFLICT, str(exc))
            return
        except IntelligenceTransplantValidationError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except IntelligenceTransplantError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
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
