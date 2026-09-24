"""Soft-fiber MiniMax path: http-post inside fiber:spawn (measured, honest).

Requires a live Soft ``--serve-async`` session with ``LLM_API_KEY`` /
``LLM_BASE_URL`` / ``LLM_MODEL`` in the Soft process env, and ``std/llm``
(or any require that installs the deferred ``http-post`` host prim).

Honesty:
- ``llm_via=fiber`` only when http-post ran inside a fiber body and join
  returned a real chat response (Soft status ``value`` or opt-in resp file).
- ``llm_parallel=fiber`` when ≥2 in-fiber HTTP calls were joined in one Soft
  eval (wall concurrency not proven without oneshot baseline; see note);
  else ``fiber_serial``. Soft status braces were aura-build #1, not Soft hang.
- Default path is **in-memory**: Soft ``fiber:join`` of ``(base64-encode (http-post …))``
  (Soft Ready ``std::println`` status hangs on raw ``{``/``}`` in ``value`` — not a Soft
  fiber hang; aura-build #1 fixed client parse only). Python base64-decodes then JSON-parses.
  ``write-file`` is opt-in / inefficient (``AURA_BUILD_FIBER_LLM_MODE=write_file``).
- Denseness ``fiber_graph`` ≠ in-fiber LLM.
"""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from aura_build.minimax import MiniMaxConfig, load_minimax_config, redact_secrets


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def fiber_llm_requested(
    *,
    flag: bool | None = None,
    environ: dict[str, str] | None = None,
) -> bool:
    """True when ``--fiber-llm`` or ``AURA_BUILD_LLM_VIA=fiber``."""
    if flag is True:
        return True
    if flag is False:
        return False
    env = environ if environ is not None else os.environ
    via = (env.get("AURA_BUILD_LLM_VIA") or "").strip().lower()
    if via == "fiber":
        return True
    return _truthy_env("AURA_BUILD_FIBER_LLM") if environ is None else (
        (environ.get("AURA_BUILD_FIBER_LLM") or "").strip().lower()
        in ("1", "true", "yes", "on")
    )


def ensure_http_post(serve_session: Any, *, timeout_s: float = 20.0) -> dict[str, Any]:
    """Require std/llm + std/encoding (http-post, base64-encode). Never logs secrets."""
    if serve_session is None:
        return {"ok": False, "reason": "no_session"}
    try:
        r = serve_session.raw_line(
            '(begin'
            ' (require "std/llm" all:)'
            ' (require "std/encoding" all:)'
            ' (and (procedure? http-post) (procedure? base64-encode)))',
            timeout_s=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"require_exc:{type(exc).__name__}:{exc}"}
    if r.get("status") != "ok" or str(r.get("value")) != "#t":
        return {
            "ok": False,
            "reason": f"http_post_or_b64_missing:{r.get('msg') or r.get('status')}:{r.get('value')!r}",
        }
    return {"ok": True}


def fiber_llm_probe(
    serve_session: Any,
    *,
    scratch_dir: Path | str | None = None,
    timeout_s: float = 60.0,
    config: MiniMaxConfig | None = None,
) -> dict[str, Any]:
    """Measured Soft in-fiber MiniMax oneshot via std/llm → http-post.

    Returns ``{ok, llm_via, reason, latency_ms, ...}``. Never invents fiber.
    """
    t0 = time.monotonic()
    if serve_session is None:
        return {
            "ok": False,
            "llm_via": None,
            "reason": "no_session",
            "latency_ms": 0,
        }
    cfg = config or load_minimax_config()
    # getenv must see key in Soft process (inherited at serve start)
    glen = serve_session.raw_line(
        '(string-length (getenv "LLM_API_KEY"))', timeout_s=5.0
    )
    key_len = glen.get("value")
    try:
        key_n = int(str(key_len).strip('"'))
    except (TypeError, ValueError):
        key_n = 0
    if glen.get("status") != "ok" or key_n <= 0:
        return {
            "ok": False,
            "llm_via": None,
            "reason": "env_empty_LLM_API_KEY",
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "getenv_status": glen.get("status"),
            "getenv_value": glen.get("value"),
        }
    inst = ensure_http_post(serve_session, timeout_s=min(20.0, timeout_s))
    if not inst.get("ok"):
        return {
            "ok": False,
            "llm_via": None,
            "reason": inst.get("reason") or "no_http_post",
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }

    extract = (
        '(string-append "ok=" (if (hash-ref r "ok") "1" "0")'
        ' "|err=" (hash-ref r "error" "")'
        ' "|content=" (hash-ref r "content" ""))'
    )
    code = (
        "(fiber:join (fiber:spawn (lambda () "
        f"(let ((r (llm:chat \"\" \"reply with exactly OK\"))) {extract}))))"
    )
    try:
        r = serve_session.raw_line(code, timeout_s=timeout_s)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "llm_via": None,
            "reason": f"fiber_llm_exc:{type(exc).__name__}:{exc}",
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }
    ms = int((time.monotonic() - t0) * 1000)
    val = str(r.get("value") or "")
    val_r = redact_secrets(val, cfg.api_key)
    if r.get("status") != "ok":
        return {
            "ok": False,
            "llm_via": None,
            "reason": f"fiber_llm_failed:{r.get('msg') or r.get('status')}",
            "latency_ms": ms,
            "value_snip": val_r[:200],
        }
    ok_chat = "ok=1" in val_r and (
        "content=OK" in val_r or "|content=" in val_r and "OK" in val_r.split("|content=", 1)[-1]
    )
    if not ok_chat:
        # Accept any non-empty content with ok=1
        ok_chat = "ok=1" in val_r and "content=" in val_r and len(val_r.split("content=", 1)[-1]) > 0
    if not ok_chat:
        return {
            "ok": False,
            "llm_via": None,
            "reason": f"fiber_llm_bad_join:{val_r[:180]!r}",
            "latency_ms": ms,
        }
    return {
        "ok": True,
        "llm_via": "fiber",
        "reason": "fiber_llm_chat_ok",
        "latency_ms": ms,
        "value_snip": val_r[:240],
        "path": "std/llm→http-post",
        "note": "in-fiber llm:chat; denseness fiber_graph is separate",
    }


def _messages_to_body(
    messages: list[dict[str, str]],
    cfg: MiniMaxConfig,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    thinking_disabled: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if thinking_disabled:
        body["thinking"] = {"type": "disabled"}
    return body


def _parse_chat_file(path: Path, cfg: MiniMaxConfig) -> dict[str, Any]:
    if not path.is_file():
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "fiber_resp_missing",
            "provider": "minimax",
            "llm_via": "fiber",
        }
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(f"fiber_resp_parse:{exc}", cfg.api_key),
            "provider": "minimax",
            "llm_via": "fiber",
        }
    try:
        content = str(payload["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "no_content_in_response",
            "provider": "minimax",
            "llm_via": "fiber",
        }
    return {
        "ok": True,
        "content": content,
        "model": str(payload.get("model") or cfg.model),
        "error": "",
        "provider": "minimax",
        "usage": payload.get("usage") if isinstance(payload.get("usage"), dict) else {},
        "llm_via": "fiber",
    }



def _soft_string_payload(value: object) -> str:
    """Unwrap Soft status string values (printed with surrounding quotes)."""
    s = str(value or "").strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def _parse_chat_json(raw: str, cfg: MiniMaxConfig) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(f"fiber_resp_parse:{exc}", cfg.api_key),
            "provider": "minimax",
            "llm_via": "fiber",
        }
    try:
        content = str(payload["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "no_content_in_response",
            "provider": "minimax",
            "llm_via": "fiber",
        }
    return {
        "ok": True,
        "content": content,
        "model": str(payload.get("model") or cfg.model),
        "error": "",
        "provider": "minimax",
        "usage": payload.get("usage") if isinstance(payload.get("usage"), dict) else {},
        "llm_via": "fiber",
    }



def _parse_chat_b64(raw_b64: str, cfg: MiniMaxConfig) -> dict[str, Any]:
    """Decode Soft base64-encoded http-post JSON (brace-safe Soft Ready status)."""
    s = (raw_b64 or "").strip()
    if not s:
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "fiber_resp_empty_b64",
            "provider": "minimax",
            "llm_via": "fiber",
        }
    try:
        decoded = base64.b64decode(s, validate=False).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(f"fiber_resp_b64:{type(exc).__name__}:{exc}", cfg.api_key),
            "provider": "minimax",
            "llm_via": "fiber",
        }
    return _parse_chat_json(decoded, cfg)


def _soft_escape_string(s: str) -> str:
    """Escape a Python string for embedding as a Soft double-quoted literal."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


# Soft string-literal embed bound for http-post **request** body.
# Above: keep request on disk via (read-file …); response still joins in memory
# (default fiber_llm_mode=direct). Soft double-quoted literals + heavy JSON
# backslash density (~5KB MiniMax propose) have been measured to yield MiniMax
# bad_request / no_content_in_response while host HTTP and read-file body ok
# (combat round1 2026-09-24 Soft Ready tip a9975a3). Keep this well under propose
# size so dogfood stamps llm_via=fiber instead of silent host fallback.
_INLINE_BODY_MAX = 2_000

# Unlikely in MiniMax chat JSON; used to pack N join strings into one Soft value.
_BATCH_SEP = "@@@AURA_FIBER_LLM_SEP@@@"  # outside base64 alphabet


def _prefer_write_file(*, max_tokens: int = 0) -> bool:
    """write-file is opt-in only (inefficient after aura-build #1).

    Default: in-memory Soft ``fiber:join`` of base64-encoded http-post JSON.
    Opt-in: ``AURA_BUILD_FIBER_LLM_MODE=write_file`` (huge bodies / debugging).
    ``max_tokens`` is ignored for mode selection (kept for call-site compat).
    """
    del max_tokens  # mode is env-only; threshold auto-write removed
    mode = (os.environ.get("AURA_BUILD_FIBER_LLM_MODE") or "").strip().lower()
    if mode in ("write_file", "write-file", "file"):
        return True
    # direct|join|status|empty → memory
    return False


def _body_soft_expr(body_json: str, *, scratch: Path, tag: str) -> tuple[str, Path | None]:
    """Soft expr yielding the request body string.

    Prefer embedding as Soft string literal (全内存). If sexpr would be huge,
    fall back to a temp body file + ``(read-file …)`` — response still joins
    in memory on the default path.
    """
    esc = _soft_escape_string(body_json)
    # Rough sexpr overhead for http-post wrapper (~200) + escaped body.
    if len(esc) <= _INLINE_BODY_MAX:
        return f'"{esc}"', None
    body_path = scratch / f"fiber_llm_body_{tag}.json"
    body_path.write_text(body_json, encoding="utf-8")
    return f'(read-file "{body_path}")', body_path


def fiber_chat_completions(
    serve_session: Any,
    messages: list[dict[str, str]],
    *,
    config: MiniMaxConfig | None = None,
    scratch_dir: Path | str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    thinking_disabled: bool = True,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """One Soft-fiber MiniMax chat via http-post (default: in-memory join).

    **Default (全内存)**: Soft ``fiber:join`` of ``(base64-encode (http-post …))``;
    Python base64-decodes then JSON-parses. Soft Ready ``std::println`` status
    hangs on raw ``{``/``}`` in ``value`` (aura-build #1 fixed client parse only).
    Request body embeds as Soft string when small; else body file + in-memory
    response. ``write-file`` is opt-in only via
    ``AURA_BUILD_FIBER_LLM_MODE=write_file`` (inefficient; debugging / huge
    resp hygiene). Soft Ready denseness HTTP still serial (Aura #4053).
    """
    cfg = config or load_minimax_config()
    if serve_session is None:
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "no_session",
            "provider": "minimax",
            "llm_via": None,
        }
    inst = ensure_http_post(serve_session)
    if not inst.get("ok"):
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": str(inst.get("reason") or "no_http_post"),
            "provider": "minimax",
            "llm_via": None,
        }
    scratch = Path(scratch_dir)
    scratch.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:12]
    body = _messages_to_body(
        messages,
        cfg,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_disabled=thinking_disabled,
    )
    body_json = json.dumps(body)
    url = f"{cfg.base_url}/chat/completions"
    use_write = _prefer_write_file(max_tokens=max_tokens)
    body_path: Path | None = None
    resp_path: Path | None = None
    body_inline = False
    if use_write:
        body_path = scratch / f"fiber_llm_body_{tag}.json"
        resp_path = scratch / f"fiber_llm_resp_{tag}.json"
        body_path.write_text(body_json, encoding="utf-8")
        code = (
            f'(fiber:join (fiber:spawn (lambda () '
            f'(let ((r (http-post "{url}" (read-file "{body_path}") '
            f'(getenv "LLM_API_KEY")))) '
            f'(if (string? r) '
            f'(begin (write-file "{resp_path}" r) '
            f'(string-append "wrote=" (number->string (string-length r)))) '
            f'"bad-nonstring")))))'
        )
    else:
        body_expr, body_path = _body_soft_expr(body_json, scratch=scratch, tag=tag)
        body_inline = body_path is None
        # Soft Ready status println hangs on raw '{' in value — base64 keeps status brace-free.
        code = (
            f'(fiber:join (fiber:spawn (lambda () '
            f'(base64-encode (http-post "{url}" {body_expr} '
            f'(getenv "LLM_API_KEY"))))))'
        )
    assert cfg.api_key not in code
    t0 = time.monotonic()
    try:
        r = serve_session.raw_line(code, timeout_s=timeout_s)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(f"fiber_chat_exc:{type(exc).__name__}:{exc}", cfg.api_key),
            "provider": "minimax",
            "llm_via": None,
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "fiber_llm_mode": "write_file" if use_write else "direct",
            "body_inline": body_inline,
        }
    ms = int((time.monotonic() - t0) * 1000)
    if r.get("status") != "ok":
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(
                f"fiber_chat_failed:{r.get('msg') or r.get('status')}", cfg.api_key
            ),
            "provider": "minimax",
            "llm_via": None,
            "latency_ms": ms,
            "soft_value": redact_secrets(str(r.get("value") or ""), cfg.api_key)[:120],
            "fiber_llm_mode": "write_file" if use_write else "direct",
            "body_inline": body_inline,
        }
    if use_write:
        assert resp_path is not None
        out = _parse_chat_file(resp_path, cfg)
    else:
        out = _parse_chat_b64(_soft_string_payload(r.get("value")), cfg)
    out["latency_ms"] = ms
    out["soft_value"] = redact_secrets(str(r.get("value") or ""), cfg.api_key)[:80]
    out["fiber_llm_mode"] = "write_file" if use_write else "direct"
    out["body_inline"] = body_inline
    if out.get("ok"):
        try:
            if body_path is not None:
                body_path.unlink(missing_ok=True)
            if use_write and resp_path is not None:
                resp_path.unlink(missing_ok=True)
        except OSError:
            pass
    return out


def fiber_chat_completions_batch(
    serve_session: Any,
    messages_list: list[list[dict[str, str]]],
    *,
    config: MiniMaxConfig | None = None,
    scratch_dir: Path | str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    thinking_disabled: bool = True,
    timeout_s: float = 180.0,
    oneshot_median_ms: float | None = None,
) -> dict[str, Any]:
    """N Soft fibers each doing MiniMax http-post; default in-memory join.

    Returns ``{ok, results, llm_parallel, wall_ms, ...}``.
    ``llm_parallel`` is ``fiber`` when N≥2, Soft status ok, and wall time
    looks concurrent vs median oneshot latency; else ``fiber_serial`` when
    wall suggests serialization (Soft #4048 body mutex / workers=1).

    **Default**: each fiber returns the full http-post JSON string; Soft
    ``string-append`` packs joins with a separator; Python parses from Soft
    status ``value`` — no response disk. Request bodies embed as Soft string
    literals when small; else body file fallback (response still joined).
    ``write-file`` opt-in only (``AURA_BUILD_FIBER_LLM_MODE=write_file``).
    Soft Ready HTTP concurrency: Aura #4053 (g_http_post_async missing on Soft
    Ready — denseness serial).
    """
    cfg = config or load_minimax_config()
    n = len(messages_list)
    if serve_session is None or n <= 0:
        return {
            "ok": False,
            "results": [],
            "llm_parallel": None,
            "wall_ms": 0,
            "reason": "no_session_or_empty",
        }
    if n == 1:
        one = fiber_chat_completions(
            serve_session,
            messages_list[0],
            config=cfg,
            scratch_dir=scratch_dir,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_disabled=thinking_disabled,
            timeout_s=timeout_s,
        )
        return {
            "ok": bool(one.get("ok")),
            "results": [one],
            "llm_parallel": None,
            "wall_ms": int(one.get("latency_ms") or 0),
            "reason": one.get("error") or "",
            "fiber_llm_mode": one.get("fiber_llm_mode"),
            "body_inline": one.get("body_inline"),
        }
    inst = ensure_http_post(serve_session)
    if not inst.get("ok"):
        return {
            "ok": False,
            "results": [],
            "llm_parallel": None,
            "wall_ms": 0,
            "reason": inst.get("reason") or "no_http_post",
        }
    scratch = Path(scratch_dir)
    scratch.mkdir(parents=True, exist_ok=True)
    tag = uuid.uuid4().hex[:10]
    url = f"{cfg.base_url}/chat/completions"
    use_write = _prefer_write_file(max_tokens=max_tokens)

    body_paths: list[Path | None] = []
    resp_paths: list[Path] = []
    body_exprs: list[str] = []
    body_inline_flags: list[bool] = []
    for i, messages in enumerate(messages_list):
        body_json = json.dumps(
            _messages_to_body(
                messages,
                cfg,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_disabled=thinking_disabled,
            )
        )
        if use_write:
            bp = scratch / f"fiber_llm_batch_{tag}_{i}_body.json"
            rp = scratch / f"fiber_llm_batch_{tag}_{i}_resp.json"
            bp.write_text(body_json, encoding="utf-8")
            if rp.exists():
                rp.unlink()
            body_paths.append(bp)
            resp_paths.append(rp)
            body_exprs.append(f'(read-file "{bp}")')
            body_inline_flags.append(False)
        else:
            expr, bp = _body_soft_expr(
                body_json, scratch=scratch, tag=f"{tag}_{i}"
            )
            body_paths.append(bp)
            body_exprs.append(expr)
            body_inline_flags.append(bp is None)

    bindings = []
    joins = []
    if use_write:
        for i, (bp, rp) in enumerate(zip(body_paths, resp_paths)):
            bindings.append(
                f"(f{i} (fiber:spawn (lambda () "
                f"(let ((r (http-post \"{url}\" (read-file \"{bp}\") "
                f"(getenv \"LLM_API_KEY\")))) "
                f"(if (string? r) "
                f"(begin (write-file \"{rp}\" r) (string-length r)) "
                f"0)))))"
            )
            joins.append(f'"|{i}=" (number->string (fiber:join f{i}))')
        code = (
            "(let (" + " ".join(bindings) + ") (string-append " + " ".join(joins) + "))"
        )
    else:
        # Separator is base64-alphabet-safe (no A-Za-z0-9+/=).
        sep_esc = _soft_escape_string(_BATCH_SEP)
        for i, bexpr in enumerate(body_exprs):
            bindings.append(
                f"(f{i} (fiber:spawn (lambda () "
                f'(base64-encode (http-post "{url}" {bexpr} '
                f'(getenv "LLM_API_KEY"))))))'
            )
            joins.append(f"(fiber:join f{i})")
        # Pack N base64 response strings into one Soft status value.
        parts: list[str] = []
        for i, jexpr in enumerate(joins):
            if i:
                parts.append(f'"{sep_esc}"')
            parts.append(jexpr)
        code = (
            "(let (" + " ".join(bindings) + ") (string-append " + " ".join(parts) + "))"
        )
    assert cfg.api_key not in code
    t0 = time.monotonic()
    try:
        r = serve_session.raw_line(code, timeout_s=timeout_s)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "results": [],
            "llm_parallel": None,
            "wall_ms": int((time.monotonic() - t0) * 1000),
            "reason": redact_secrets(f"batch_exc:{type(exc).__name__}:{exc}", cfg.api_key),
            "fiber_llm_mode": "write_file" if use_write else "direct",
        }
    wall_ms = int((time.monotonic() - t0) * 1000)
    if r.get("status") != "ok":
        return {
            "ok": False,
            "results": [],
            "llm_parallel": None,
            "wall_ms": wall_ms,
            "reason": redact_secrets(
                f"batch_failed:{r.get('msg') or r.get('status')}", cfg.api_key
            ),
            "soft_value": redact_secrets(str(r.get("value") or ""), cfg.api_key)[:120],
            "fiber_llm_mode": "write_file" if use_write else "direct",
        }
    if use_write:
        results = [_parse_chat_file(rp, cfg) for rp in resp_paths]
    else:
        packed = _soft_string_payload(r.get("value"))
        chunks = packed.split(_BATCH_SEP)
        if len(chunks) != n:
            return {
                "ok": False,
                "results": [],
                "llm_parallel": None,
                "wall_ms": wall_ms,
                "reason": f"batch_sep_mismatch:{len(chunks)}!={n}",
                "soft_value": redact_secrets(str(r.get("value") or ""), cfg.api_key)[:120],
                "fiber_llm_mode": "direct",
                "body_inline": all(body_inline_flags),
            }
        results = [_parse_chat_b64(chunk, cfg) for chunk in chunks]
    for got in results:
        got["latency_ms"] = wall_ms
        got["fiber_llm_mode"] = "write_file" if use_write else "direct"
    ok_n = sum(1 for x in results if x.get("ok"))
    # Best-effort scratch cleanup (never log secrets).
    for bp in body_paths:
        if bp is None:
            continue
        try:
            bp.unlink(missing_ok=True)
        except OSError:
            pass
    if use_write:
        for i, rp in enumerate(resp_paths):
            if results[i].get("ok"):
                try:
                    rp.unlink(missing_ok=True)
                except OSError:
                    pass
    # Honest parallel stamp: Soft joined ≥2 fiber HTTP in one eval.
    # Soft #4048 may still serialize denseness. Without oneshot_median_ms,
    # stamp fiber + note that wall concurrency is unproven; with baseline,
    # downgrade to fiber_serial when wall suggests serialization.
    if ok_n >= 2:
        llm_parallel = "fiber"
        parallel_note = "joined_ge2_wall_concurrency_unproven"
        if oneshot_median_ms is not None and oneshot_median_ms > 0:
            ratio = wall_ms / float(oneshot_median_ms)
            # Remasure Soft Ready #4053: N=2 ~1.34×, N=4 ~3.5×, N=8 ~5.2×.
            # Prior max(1.6, 0.7*N) under-stamped N=8 as fiber; tighten.
            if ratio > max(1.35, 0.55 * ok_n):
                llm_parallel = "fiber_serial"
                parallel_note = f"wall_{wall_ms}ms_{ratio:.2f}x_oneshot"
            else:
                parallel_note = f"wall_{wall_ms}ms_{ratio:.2f}x_oneshot"
    elif ok_n == 1:
        llm_parallel = "fiber_serial"
        parallel_note = ""
    else:
        llm_parallel = None
        parallel_note = ""
    out: dict[str, Any] = {
        "ok": ok_n == n,
        "results": results,
        "llm_parallel": llm_parallel,
        "wall_ms": wall_ms,
        "ok_n": ok_n,
        "n": n,
        "soft_value": redact_secrets(str(r.get("value") or ""), cfg.api_key)[:120],
        "reason": "" if ok_n == n else f"partial_ok:{ok_n}/{n}",
        "fiber_llm_mode": "write_file" if use_write else "direct",
        "body_inline": all(body_inline_flags) if body_inline_flags else False,
    }
    if parallel_note:
        out["llm_parallel_note"] = parallel_note
    return out
