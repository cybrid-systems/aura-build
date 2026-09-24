"""Unit tests for Soft --serve-async status-line parsing (aura-build #1).

Pure helpers — no Soft binary required.
"""

from __future__ import annotations

import json

from aura_build.serve_session import _parse_soft_stdout_line


def _status(value, *, session: str = "s", status: str = "ok", **extra) -> str:
    obj = {"session": session, "status": status, "value": value, **extra}
    return json.dumps(obj, separators=(",", ":"))


def test_parse_value_empty_object_literal() -> None:
    """Soft value '\"{}\"' — the bug that rfind choked on."""
    line = _status("{}")
    prefix, obj = _parse_soft_stdout_line(line)
    assert prefix == ""
    assert obj is not None
    assert obj["status"] == "ok"
    assert obj["value"] == "{}"


def test_parse_minimax_like_nested_braces() -> None:
    """MiniMax-like JSON body inside value (escaped quotes / nested braces)."""
    body = json.dumps(
        {"choices": [{"message": {"content": "hi {world}"}}], "usage": {"n": 1}}
    )
    line = _status(body)
    prefix, obj = _parse_soft_stdout_line(line)
    assert prefix == ""
    assert obj is not None
    assert obj["status"] == "ok"
    assert obj["value"] == body
    # Ensure nested braces did not produce a wrong object
    assert "choices" not in obj or obj.get("session") == "s"


def test_parse_plain_string_value() -> None:
    line = _status("hi")
    prefix, obj = _parse_soft_stdout_line(line)
    assert prefix == ""
    assert obj is not None
    assert obj["status"] == "ok"
    assert obj["value"] == "hi"


def test_parse_number_value() -> None:
    line = _status(42)
    prefix, obj = _parse_soft_stdout_line(line)
    assert prefix == ""
    assert obj is not None
    assert obj["status"] == "ok"
    assert obj["value"] == 42


def test_parse_prefix_stdout_before_json() -> None:
    line = "hello from display\n" + _status("{}")
    # Soft usually one line; prefix on same line:
    line = "hello from display" + _status("{}")
    prefix, obj = _parse_soft_stdout_line(line)
    assert prefix == "hello from display"
    assert obj is not None
    assert obj["status"] == "ok"
    assert obj["value"] == "{}"


def test_parse_no_status_returns_none() -> None:
    prefix, obj = _parse_soft_stdout_line("just some stdout without json")
    assert prefix == "just some stdout without json"
    assert obj is None


def test_parse_braces_in_value_not_false_status() -> None:
    """rfind would pick '{' inside value and either fail or miss status."""
    # Craft so last '{' is inside value string — classic rfind failure mode
    line = (
        '{"session":"sess1","status":"ok","value":'
        '"{\\"a\\":1,\\"b\\":{\\"c\\":\\"{nested}\\"}}"}'
    )
    prefix, obj = _parse_soft_stdout_line(line)
    assert obj is not None
    assert obj["status"] == "ok"
    assert '"a"' in obj["value"] or "a" in obj["value"]
    # Must not return the inner dict as the status object
    assert "session" in obj


def test_parse_error_status_with_braces_in_msg() -> None:
    line = json.dumps(
        {"session": "s", "status": "error", "msg": "bad {thing}", "value": ""}
    )
    prefix, obj = _parse_soft_stdout_line(line)
    assert obj is not None
    assert obj["status"] == "error"
    assert obj["msg"] == "bad {thing}"


def test_parse_empty_line() -> None:
    prefix, obj = _parse_soft_stdout_line("")
    assert prefix == ""
    assert obj is None
