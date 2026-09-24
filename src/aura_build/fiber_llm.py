"""Soft-fiber MiniMax path: http-post inside fiber:spawn (measured, honest).

Requires a live Soft ``--serve-async`` session with ``LLM_API_KEY`` /
``LLM_BASE_URL`` / ``LLM_MODEL`` in the Soft process env, and ``std/llm``
(or any require that installs the deferred ``http-post`` host prim).

Honesty:
- ``llm_via=fiber`` only when http-post ran inside a fiber body and join
  returned a real chat response (response file has choices/content).
- ``llm_parallel=fiber`` when ≥2 in-fiber HTTP calls were joined in one Soft
  eval (wall concurrency not proven without oneshot baseline; see note);
  else ``fiber_serial``. Soft status braces were aura-build #1, not Soft hang.
- Denseness ``fiber_graph`` ≠ in-fiber LLM.
"""

from __future__ import annotations

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
    """Require std/llm so Soft installs deferred http-post. Never logs secrets."""
    if serve_session is None:
        return {"ok": False, "reason": "no_session"}
    try:
        r = serve_session.raw_line(
            '(begin (require "std/llm" all:) (procedure? http-post))',
            timeout_s=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"require_exc:{type(exc).__name__}:{exc}"}
    if r.get("status") != "ok" or str(r.get("value")) != "#t":
        return {
            "ok": False,
            "reason": f"http_post_missing:{r.get('msg') or r.get('status')}:{r.get('value')!r}",
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


def _prefer_write_file(*, max_tokens: int) -> bool:
    """Direct Soft status join is fine after aura-build #1; write-file for huge bodies.

    Override with ``AURA_BUILD_FIBER_LLM_MODE=direct|write_file``.
    """
    mode = (os.environ.get("AURA_BUILD_FIBER_LLM_MODE") or "").strip().lower()
    if mode in ("write_file", "write-file", "file"):
        return True
    if mode in ("direct", "join", "status"):
        return False
    return int(max_tokens) > 1024


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
    """One Soft-fiber MiniMax chat via http-post (direct join or write-file).

    After aura-build #1, Soft status ``value`` may contain ``{`` (MiniMax JSON)
    without wedging the client. Default: **direct** ``fiber:join`` of the HTTP
    body when ``max_tokens <= 1024`` (no resp-file disk). write-file remains for
    large ``max_tokens`` or ``AURA_BUILD_FIBER_LLM_MODE=write_file`` (hygiene /
    short status). Soft Ready still serializes denseness HTTP (Aura #4053).
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
    body_path = scratch / f"fiber_llm_body_{tag}.json"
    resp_path = scratch / f"fiber_llm_resp_{tag}.json"
    body = _messages_to_body(
        messages,
        cfg,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_disabled=thinking_disabled,
    )
    body_path.write_text(json.dumps(body), encoding="utf-8")
    url = f"{cfg.base_url}/chat/completions"
    use_write = _prefer_write_file(max_tokens=max_tokens)
    if use_write:
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
        code = (
            f'(fiber:join (fiber:spawn (lambda () '
            f'(http-post "{url}" (read-file "{body_path}") '
            f'(getenv "LLM_API_KEY")))))'
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
        }
    if use_write:
        out = _parse_chat_file(resp_path, cfg)
    else:
        out = _parse_chat_json(_soft_string_payload(r.get("value")), cfg)
    out["latency_ms"] = ms
    out["soft_value"] = redact_secrets(str(r.get("value") or ""), cfg.api_key)[:80]
    out["fiber_llm_mode"] = "write_file" if use_write else "direct"
    if out.get("ok"):
        try:
            body_path.unlink(missing_ok=True)
            if use_write:
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
    """N concurrent Soft fibers each doing file-backed MiniMax http-post.

    Returns ``{ok, results, llm_parallel, wall_ms, ...}``.
    ``llm_parallel`` is ``fiber`` when N≥2, Soft status ok, and wall time
    looks concurrent vs median oneshot latency; else ``fiber_serial`` when
    wall suggests serialization (Soft #4048 body mutex / workers=1).
    Batch still uses write-file (short status). Soft Ready HTTP concurrency: Aura #4053 (g_http_post_async missing on Soft Ready — denseness serial).
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
    bodies: list[Path] = []
    resps: list[Path] = []
    for i, messages in enumerate(messages_list):
        bp = scratch / f"fiber_llm_batch_{tag}_{i}_body.json"
        rp = scratch / f"fiber_llm_batch_{tag}_{i}_resp.json"
        bp.write_text(
            json.dumps(
                _messages_to_body(
                    messages,
                    cfg,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_disabled=thinking_disabled,
                )
            ),
            encoding="utf-8",
        )
        if rp.exists():
            rp.unlink()
        bodies.append(bp)
        resps.append(rp)

    # Build: (let ((f0 (fiber:spawn ...)) (f1 ...)) (string-append ...))
    bindings = []
    joins = []
    for i, (bp, rp) in enumerate(zip(bodies, resps)):
        bindings.append(
            f"(f{i} (fiber:spawn (lambda () "
            f"(let ((r (http-post \"{url}\" (read-file \"{bp}\") "
            f"(getenv \"LLM_API_KEY\")))) "
            f"(if (string? r) "
            f"(begin (write-file \"{rp}\" r) (string-length r)) "
            f"0)))))"
        )
        joins.append(f'"|{i}=" (number->string (fiber:join f{i}))')
    code = "(let (" + " ".join(bindings) + ") (string-append " + " ".join(joins) + "))"
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
        }
    results = [_parse_chat_file(rp, cfg) for rp in resps]
    for got in results:
        got["latency_ms"] = wall_ms
    ok_n = sum(1 for x in results if x.get("ok"))
    # Best-effort scratch cleanup (never log secrets). Bodies always; resp on ok.
    for bp in bodies:
        try:
            bp.unlink(missing_ok=True)
        except OSError:
            pass
    for i, rp in enumerate(resps):
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
    }
    if parallel_note:
        out["llm_parallel_note"] = parallel_note
    return out
