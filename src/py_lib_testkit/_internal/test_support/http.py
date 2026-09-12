"""Deterministic local HTTP test server primitives."""

from __future__ import annotations

import socket
import threading
import time
from contextlib import AbstractContextManager, suppress
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Self, cast
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ScriptedResponse:
    """One scripted HTTP response returned by the local server."""

    status_code: int
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    delay_seconds: float = 0.0
    disconnect: bool = False


@dataclass(frozen=True, slots=True)
class RequestRecord:
    """Captured inbound request metadata for assertions and debugging."""

    method: str
    path: str
    query: str
    body: bytes
    headers: dict[str, str]


@dataclass(slots=True)
class _RouteState:
    """Mutable route cursor and captured request state."""

    responses: list[ScriptedResponse]
    records: list[RequestRecord] = field(default_factory=list)
    next_index: int = 0

    def next_response(self) -> ScriptedResponse:
        """Return the next scripted response, repeating the final response."""
        if not self.responses:
            return ScriptedResponse(status_code=500, body=b"missing scripted response")
        index = min(self.next_index, len(self.responses) - 1)
        self.next_index += 1
        return self.responses[index]


class _Server(ThreadingHTTPServer):
    """Threaded HTTP server that owns scripted routes and request records."""

    daemon_threads = True
    block_on_close = False
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        routes: dict[tuple[str, str], list[ScriptedResponse]],
    ) -> None:
        """Initialize route state and the shared request-record lock."""
        super().__init__(server_address, _Handler)
        self.routes = {
            (method.upper(), path): _RouteState(list(responses))
            for (method, path), responses in routes.items()
        }
        self._lock = threading.RLock()

    def record_request(self, record: RequestRecord) -> ScriptedResponse | None:
        """Record one request and return its scripted response when configured."""
        key = (record.method, record.path)
        with self._lock:
            route = self.routes.get(key)
            if route is None:
                return None
            route.records.append(record)
            return route.next_response()

    def request_count(self, method: str, path: str) -> int:
        """Return captured request count for one route."""
        key = (method.upper(), path)
        with self._lock:
            route = self.routes.get(key)
            return 0 if route is None else len(route.records)

    def recorded_requests(self, method: str, path: str) -> list[RequestRecord]:
        """Return captured request records for one route."""
        key = (method.upper(), path)
        with self._lock:
            route = self.routes.get(key)
            if route is None:
                return []
            return list(route.records)


class _Handler(BaseHTTPRequestHandler):
    """Minimal request handler backed by the scripted server state."""

    def do_GET(self) -> None:
        """Handle one scripted GET request."""
        self._handle()

    def do_POST(self) -> None:
        """Handle one scripted POST request."""
        self._handle()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Suppress default HTTP server logging during tests."""
        _ = format
        _ = args

    def _handle(self) -> None:
        """Capture the request and emit the configured response."""
        parsed = urlparse(self.path)
        record = RequestRecord(
            method=self.command.upper(),
            path=parsed.path,
            query=parsed.query,
            body=self._read_body(),
            headers=dict(self.headers.items()),
        )
        response = cast("_Server", self.server).record_request(record)
        self._write_response(
            response
            if response is not None
            else ScriptedResponse(status_code=404, body=b"unscripted route")
        )

    def _read_body(self) -> bytes:
        """Read the declared request body, if any."""
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return b""
        return self.rfile.read(int(content_length))

    def _write_response(self, response: ScriptedResponse) -> None:
        """Write one scripted response or terminate the connection."""
        if response.delay_seconds > 0:
            time.sleep(response.delay_seconds)
        if response.disconnect:
            self.close_connection = True
            with suppress(OSError):
                self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        body = response.body
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            with suppress(OSError):
                self.wfile.write(body)


class ScriptedHTTPServer(AbstractContextManager["ScriptedHTTPServer"]):
    """Context-managed local HTTP server with deterministic scripted routes."""

    _SERVE_FOREVER_POLL_INTERVAL_SECONDS = 0.01

    def __init__(
        self,
        *,
        port: int,
        routes: dict[tuple[str, str], list[ScriptedResponse]],
        host: str = "127.0.0.1",
    ) -> None:
        """Configure one local scripted server before it is started."""
        self._host = host
        self._port = port
        self._routes = routes
        self._server: _Server | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> Self:
        """Start the local HTTP server and return this context manager."""
        self._server = _Server((self._host, self._port), self._routes)
        self._port = int(self._server.server_address[1])
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            kwargs={"poll_interval": self._SERVE_FOREVER_POLL_INTERVAL_SECONDS},
            name=f"scripted-http-server-{self._port}",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Stop the server and join all helper threads deterministically."""
        _ = exc_type
        _ = exc
        _ = tb
        server = self._server
        if server is not None:
            shutdown_thread = threading.Thread(
                target=server.shutdown,
                name=f"scripted-http-server-shutdown-{self._port}",
                daemon=True,
            )
            shutdown_thread.start()
            self._wakeup_server()
            shutdown_thread.join(timeout=0.05)
            if shutdown_thread.is_alive():
                self._wakeup_server()
            shutdown_thread.join(timeout=5.0)
            server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._thread = None
        self._server = None

    @property
    def base_url(self) -> str:
        """Return the server base URL."""
        return f"http://{self._host}:{self._port}"

    def request_count(self, method: str, path: str) -> int:
        """Return how many times a scripted route was hit."""
        if self._server is None:
            return 0
        return self._server.request_count(method, path)

    def recorded_requests(self, method: str, path: str) -> list[RequestRecord]:
        """Return captured requests for a scripted route."""
        if self._server is None:
            return []
        return self._server.recorded_requests(method, path)

    def _wakeup_server(self) -> None:
        """Wake the serve_forever loop so shutdown can complete promptly."""
        server = self._server
        if server is None:
            return
        with (
            suppress(OSError),
            socket.create_connection(server.server_address, timeout=0.05),
        ):
            return
