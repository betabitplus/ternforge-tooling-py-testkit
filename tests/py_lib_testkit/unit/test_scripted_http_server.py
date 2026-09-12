from __future__ import annotations

import http.client
from urllib.parse import urlsplit

import pytest

from py_lib_testkit import ScriptedHTTPServer, ScriptedResponse
from py_lib_testkit._internal.test_support import http as http_support


def _request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    parsed = urlsplit(base_url)
    assert parsed.hostname is not None
    assert parsed.port is not None
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=2)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def test_scripted_http_server_publishes_its_producer_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Using the substitute automatically records its stable producer identity."""
    captured: list[tuple[str, str, object]] = []

    def capture(name: str, *, kind: str, payload: object) -> None:
        captured.append((name, kind, payload))

    monkeypatch.setattr(http_support, "publish_verification_observation", capture)

    with ScriptedHTTPServer(port=0, routes={}):
        pass

    assert captured == [
        (
            "PRODUCER_SCRIPTED_HTTP_SERVER evidence producer",
            "evidence-producer-use",
            {"producer_id": "PRODUCER_SCRIPTED_HTTP_SERVER"},
        )
    ]


def test_scripted_http_server_replays_sequence_and_records_requests() -> None:
    routes = {
        ("POST", "/example"): [
            ScriptedResponse(
                status_code=503,
                body=b"retry",
                headers={"Content-Type": "text/plain"},
            ),
            ScriptedResponse(status_code=200, body=b"ok"),
        ]
    }

    with ScriptedHTTPServer(port=0, routes=routes) as server:
        kwargs = {
            "body": b"payload",
            "headers": {"X-Test": "yes"},
        }
        assert _request(server.base_url, "POST", "/example?mode=test", **kwargs) == (
            503,
            b"retry",
        )
        assert _request(server.base_url, "POST", "/example?mode=test", **kwargs) == (
            200,
            b"ok",
        )
        assert _request(server.base_url, "POST", "/example?mode=test", **kwargs) == (
            200,
            b"ok",
        )

        assert server.request_count("post", "/example") == 3
        records = server.recorded_requests("POST", "/example")
        assert [record.query for record in records] == ["mode=test"] * 3
        assert [record.body for record in records] == [b"payload"] * 3
        assert records[0].headers["X-Test"] == "yes"


def test_scripted_http_server_returns_404_for_unscripted_route() -> None:
    with ScriptedHTTPServer(port=0, routes={}) as server:
        assert _request(server.base_url, "GET", "/missing") == (
            404,
            b"unscripted route",
        )
