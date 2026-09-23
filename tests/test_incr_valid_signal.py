"""Incr-valid probe contract: parse markers; never invent true."""

from __future__ import annotations

from aura_build.runtime import (
    INCR_VALID_ENV_LINE,
    INCR_VALID_MARKER,
    OK_MARKER,
    parse_incr_valid_signal,
)


def test_parse_accepts_marker_one():
    assert parse_incr_valid_signal(f"{OK_MARKER} 42\n{INCR_VALID_MARKER} 1\n") is True


def test_parse_accepts_env_line():
    assert parse_incr_valid_signal("", f"noise\n{INCR_VALID_ENV_LINE}\n") is True


def test_parse_rejects_zero():
    assert parse_incr_valid_signal(f"{INCR_VALID_MARKER} 0\n") is False


def test_parse_rejects_missing():
    assert parse_incr_valid_signal(f"{OK_MARKER} 42\nfast but no marker\n") is False
    assert parse_incr_valid_signal("", "") is False


def test_parse_rejects_partial_token():
    assert parse_incr_valid_signal(f"{INCR_VALID_MARKER}\n") is False
    assert parse_incr_valid_signal(f"{INCR_VALID_MARKER} 2\n") is False
