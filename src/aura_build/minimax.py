"""Thin MiniMax (OpenAI-compatible) LLM adapter for aura-build.

Loads key from file into process env only. Never prints or persists the key.
Env file default: ``~/.config/aura-build/minimax.env`` (or ``AURA_BUILD_MINIMAX_ENV``).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_ENV_FILE = Path.home() / ".config" / "aura-build" / "minimax.env"
DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
DEFAULT_MODEL = "MiniMax-M3"
DEFAULT_KEY_FILE = Path.home() / ".config" / "aura-build" / "minimax_api_key"

# CN site only — api.minimax.io returns 401 for this key; never prefer .io
CN_BASE_URL = "https://api.minimaxi.com/v1"
_IO_HOST_MARKERS = ("api.minimax.io",)


def lock_cn_base_url(url: str | None) -> str:
    """Force MiniMax CN endpoint; rewrite .io → minimaxi.com/v1."""
    raw = (url or "").strip().rstrip("/")
    if not raw:
        return CN_BASE_URL
    lower = raw.lower()
    for mark in _IO_HOST_MARKERS:
        if mark in lower:
            return CN_BASE_URL
    if "minimaxi.com" in lower:
        # normalize to canonical CN v1
        if lower.endswith("/v1"):
            return "https://api.minimaxi.com/v1"
        return CN_BASE_URL
    # Unknown host — still dogfood on CN (key is CN-only)
    return CN_BASE_URL


_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+|MINIMAX_API_KEY[=:]\s*\S+)",
    re.IGNORECASE,
)


def redact_secrets(text: str, extra: str | None = None) -> str:
    """Replace API key material in logs/traj. Never invent content."""
    if not text:
        return text
    out = _SECRET_RE.sub("<redacted:secret>", text)
    if extra and extra.strip():
        out = out.replace(extra.strip(), "<redacted:secret>")
    return out


@dataclass(frozen=True)
class MiniMaxConfig:
    api_key: str
    base_url: str
    model: str
    key_file: str
    env_file: str

    def public_dict(self) -> dict[str, str]:
        return {
            "provider": "minimax",
            "base_url": self.base_url,
            "model": self.model,
            "key_file": self.key_file,
            "env_file": self.env_file,
            "api_key": "<redacted:secret>",
        }


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_minimax_config(
    *,
    env_file: str | Path | None = None,
    environ: dict[str, str] | None = None,
) -> MiniMaxConfig:
    """Load MiniMax settings; key from file only (never from traj/README)."""
    env = environ if environ is not None else os.environ
    ef = Path(
        env_file
        or env.get("AURA_BUILD_MINIMAX_ENV")
        or env.get("MINIMAX_ENV_FILE")
        or DEFAULT_ENV_FILE
    )
    file_vals = _parse_env_file(ef)

    # Explicit env-file KEY path wins over ambient process env (dogfood isolation).
    if env_file is not None and file_vals.get("MINIMAX_API_KEY_FILE"):
        key_file = Path(file_vals["MINIMAX_API_KEY_FILE"])
    else:
        key_file = Path(
            env.get("MINIMAX_API_KEY_FILE")
            or file_vals.get("MINIMAX_API_KEY_FILE")
            or DEFAULT_KEY_FILE
        )
    if not key_file.is_file():
        raise FileNotFoundError(f"MiniMax key file missing: {key_file}")
    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError(f"MiniMax key file empty: {key_file}")

    # Prefer process env (already loaded) then env file; never require echoing key.
    base = lock_cn_base_url(
        env.get("MINIMAX_BASE_URL")
        or file_vals.get("MINIMAX_BASE_URL")
        or DEFAULT_BASE_URL
    )
    model = (
        env.get("MINIMAX_MODEL")
        or file_vals.get("MINIMAX_MODEL")
        or DEFAULT_MODEL
    )

    # Inject into process env for child Aura llm:chat if used; do not print.
    os.environ.setdefault("LLM_API_KEY", api_key)
    os.environ.setdefault("LLM_BASE_URL", base)
    os.environ.setdefault("LLM_MODEL", model)
    os.environ.setdefault("MINIMAX_BASE_URL", base)
    os.environ.setdefault("MINIMAX_MODEL", model)
    os.environ.setdefault("MINIMAX_API_KEY_FILE", str(key_file))

    return MiniMaxConfig(
        api_key=api_key,
        base_url=base,
        model=model,
        key_file=str(key_file),
        env_file=str(ef),
    )


def chat_completions(
    messages: list[dict[str, str]],
    *,
    config: MiniMaxConfig | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    thinking_disabled: bool = True,
    timeout_s: float = 90.0,
) -> dict[str, Any]:
    """POST ``{base}/chat/completions`` with Bearer key. Returns redacted-safe result.

    Result keys: ok, content, model, raw_keys, error (never includes api_key).
    """
    cfg = config or load_minimax_config()
    body: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if thinking_disabled:
        body["thinking"] = {"type": "disabled"}

    url = f"{cfg.base_url}/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            err_body = ""
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(
                f"http_{exc.code}: {err_body}", cfg.api_key
            ),
            "provider": "minimax",
        }
    except Exception as exc:  # noqa: BLE001 — surface honest failure
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": redact_secrets(f"{type(exc).__name__}: {exc}", cfg.api_key),
            "provider": "minimax",
        }

    content = ""
    try:
        content = str(payload["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError):
        return {
            "ok": False,
            "content": "",
            "model": cfg.model,
            "error": "no_content_in_response",
            "provider": "minimax",
        }

    return {
        "ok": True,
        "content": content,
        "model": str(payload.get("model") or cfg.model),
        "error": "",
        "provider": "minimax",
        "usage": payload.get("usage") if isinstance(payload.get("usage"), dict) else {},
    }


def extract_aura_source(text: str) -> str:
    """Pull Aura source from model reply (fenced or raw)."""
    if not text:
        return ""
    # Prefer ```aura / ```scheme / ```lisp fences, else first ``` block
    for lang in ("aura", "scheme", "lisp", ""):
        if lang:
            pat = rf"```{lang}\s*([\s\S]*?)```"
        else:
            pat = r"```\s*([\s\S]*?)```"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip() + "\n"
    # Raw: if it looks like Aura forms, take whole reply
    stripped = text.strip()
    if stripped.startswith("(") or stripped.startswith(";"):
        return stripped + ("\n" if not stripped.endswith("\n") else "")
    return stripped + "\n"
