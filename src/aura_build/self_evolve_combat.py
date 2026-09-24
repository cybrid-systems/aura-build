"""Self-evolve combat orchestrator (P1).

Thin host loop: Soft serve attach required → llm-dogfood (fiber explore /
optional fiber-llm) → traj + dual-sink findings. Does **not** replace stamp
``aura-build self-evolve`` (L1/stamp dogfood).

SSOT: docs/self-evolve-combat.md
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Soft Ready tip used by combat dogfood (honest inventory in SSOT doc).
DEFAULT_SOFT_AURA_BIN = "/workspace/aura-grok/build_soft4054/aura"
DEFAULT_OUT_DIR = Path("scratch/self_evolve_combat")
DEFAULT_PROJECT = Path("examples/projects/mini-saga")
DEFAULT_ENV_FILE = Path.home() / ".config" / "aura-build" / "minimax.env"
AURA_ISSUE_REPO = "cybrid-systems/aura"


def repo_root() -> Path:
    from aura_build.kernel import repo_root as _rr

    return _rr()


def kill_soft_zombies() -> dict[str, Any]:
    """Kill Soft ``aura --serve`` / ``--serve-async`` zombies (not redis)."""
    patterns = (
        r"/aura .*--serve",
        r"build_soft.*/aura .*--serve",
        r"aura .*--serve-async",
        r"aura .*--serve ",
    )
    killed = 0
    for pat in patterns:
        proc = subprocess.run(
            ["pkill", "-f", pat],
            capture_output=True,
            text=True,
            check=False,
        )
        # pkill exit 0 = matched; 1 = no match
        if proc.returncode == 0:
            killed += 1
    if killed:
        time.sleep(1.0)
    return {"killed_patterns": killed}


def _ts_slug() -> str:
    # Asia/Shanghai box clock; keep filesystem-safe.
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _stamp_honesty_from_status(st: dict[str, Any]) -> dict[str, Any]:
    """Honesty fields from measured session probes only — never invent."""
    return {
        "serve_attach_ok": bool(st.get("serve_attach_ok")),
        "session_model": st.get("session_model"),
        "serve_mode": st.get("serve_mode"),
        "serve_cross_session_shared_ast": bool(
            st.get("serve_cross_session_shared_ast")
        ),
        "serve_same_session_mutate_ok": bool(st.get("serve_same_session_mutate_ok")),
        "serve_async_soft_ready": st.get("serve_async_soft_ready"),
        "aura_bin": st.get("aura_bin"),
        "pid": st.get("pid"),
    }


def _stamp_honesty_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Pull measured runtime honesty from llm-dogfood summary (no env elevate)."""
    hon = dict(summary.get("honesty") or {})
    out: dict[str, Any] = {
        "session_model": hon.get("session_model") or summary.get("session_model"),
        "serve_mode": hon.get("serve_mode") or summary.get("serve_mode"),
        "serve_attach_ok": hon.get("serve_attach_ok"),
        "serve_cross_session_shared_ast": hon.get("serve_cross_session_shared_ast"),
        "via_prefer_session": hon.get("via_prefer_session"),
        "fiber_live": hon.get("fiber_live"),
        "incr_proven": hon.get("incr_proven"),
        "worldline_backend": summary.get("worldline_backend")
        or hon.get("worldline_backend"),
        "explore_parallel": summary.get("explore_parallel"),
        "fiber_explore_n": summary.get("fiber_explore_n"),
        "llm_via": summary.get("llm_via") or hon.get("llm_via"),
        "llm_parallel": summary.get("llm_parallel") or hon.get("llm_parallel"),
        "llm_parallel_ok": summary.get("llm_parallel_ok"),
        "fiber_llm": summary.get("fiber_llm"),
        "concurrent_llm": summary.get("concurrent_llm"),
        "tools_used_selected": summary.get("tools_used_selected"),
        "prove_incr_report_ts": None,  # filled below from measured prove_incr only
    }
    pi = hon.get("prove_incr")
    if hon.get("prove_incr_report_ts") is not None:
        out["prove_incr_report_ts"] = hon.get("prove_incr_report_ts")
    elif isinstance(pi, dict) and pi.get("report_ts") is not None:
        out["prove_incr_report_ts"] = pi.get("report_ts")

    # Drop Nones so stamps stay measured-only.
    return {k: v for k, v in out.items() if v is not None}


def require_serve_attach(
    *,
    harness_root: Path | None,
    aura_bin: str | None,
    start_session_if_needed: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Return (status, meta). status is None when refuse."""
    from aura_build.serve_session import session_status, start_session

    hroot = harness_root
    st = session_status(harness_root=hroot, aura_bin=aura_bin)
    meta: dict[str, Any] = {"started_session": False, "kill_zombies": None}
    if st.get("serve_attach_ok"):
        return st, meta

    if not start_session_if_needed:
        return None, {
            **meta,
            "refuse_reason": "serve_attach_required",
            "hint": (
                "combat requires live Soft serve attach (serve_attach_ok). "
                "Run: aura-build session start --aura-bin $AURA_BIN "
                "or pass --start-session with AURA_BIN / --aura-bin set."
            ),
            "status": _stamp_honesty_from_status(st),
        }

    bin_path = (
        aura_bin
        or os.environ.get("AURA_BIN")
        or (DEFAULT_SOFT_AURA_BIN if Path(DEFAULT_SOFT_AURA_BIN).is_file() else None)
    )
    if not bin_path or not Path(bin_path).is_file():
        return None, {
            **meta,
            "refuse_reason": "aura_bin_required_to_start_session",
            "hint": (
                "set AURA_BIN or --aura-bin to Soft Ready tip "
                f"(default {DEFAULT_SOFT_AURA_BIN}) before --start-session"
            ),
            "status": _stamp_honesty_from_status(st),
        }

    meta["kill_zombies"] = kill_soft_zombies()
    try:
        start_session(aura_bin=bin_path, harness_root=hroot, force=True)
        meta["started_session"] = True
    except Exception as exc:  # noqa: BLE001 — surface to refuse
        return None, {
            **meta,
            "refuse_reason": "session_start_failed",
            "error": str(exc),
            "status": _stamp_honesty_from_status(st),
        }

    st2 = session_status(harness_root=hroot, aura_bin=bin_path)
    if not st2.get("serve_attach_ok"):
        return None, {
            **meta,
            "refuse_reason": "serve_attach_failed_after_start",
            "status": _stamp_honesty_from_status(st2),
        }
    return st2, meta


def classify_findings(
    summary: dict[str, Any],
    *,
    session_st: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Dual-sink classification — Aura issue stubs vs aura-build notes.

    Never auto-edits Aura. Returns finding dicts for print/write.
    """
    findings: list[dict[str, Any]] = []
    hon = _stamp_honesty_from_summary(summary)
    reason = str(summary.get("reason") or "")
    llm_via = hon.get("llm_via")
    llm_parallel = hon.get("llm_parallel")
    fiber_llm = hon.get("fiber_llm")

    # Soft / denseness / fiber-llm probe failures → Aura issue draft candidates
    soft_signals = []
    if summary.get("fiber_llm_probe") and isinstance(summary["fiber_llm_probe"], dict):
        probe = summary["fiber_llm_probe"]
        if probe.get("ok") is False:
            soft_signals.append(f"fiber_llm_probe_fail:{probe.get('reason')}")
    if reason in ("soft_hang", "segv", "serve_dead", "fiber_spawn_fail"):
        soft_signals.append(reason)
    orch = summary.get("orch_observation") or {}
    if isinstance(orch, dict) and orch.get("soft_anomaly"):
        soft_signals.append(str(orch.get("soft_anomaly")))

    # Honest fallback stamps that may indicate Soft body/size issues (ROUND1 class)
    if fiber_llm and llm_via == "host" and "fallback" in reason.lower():
        soft_signals.append("fiber_llm_fallback_to_host")
    # fiber_serial is an honest stamp (not wall-parallel). Only dual-sink when
    # combat *requested* concurrent LLM batch but Soft still serialized.
    if (
        hon.get("concurrent_llm")
        and llm_parallel == "fiber_serial"
        and hon.get("llm_parallel_ok") is False
        and (hon.get("llm_calls_parallel") or 0) >= 2
    ):
        soft_signals.append("llm_parallel_fiber_serial_unexpected")

    tip = None
    if session_st:
        tip = session_st.get("aura_bin")
    tip = tip or hon.get("aura_bin") or os.environ.get("AURA_BIN")

    if soft_signals:
        findings.append(
            {
                "class": "aura_kernel",
                "action": "issue_draft",
                "repo": AURA_ISSUE_REPO,
                "signals": soft_signals,
                "title": (
                    f"combat Soft anomaly: {', '.join(soft_signals[:2])} "
                    f"(tip={Path(str(tip)).name if tip else '?'})"
                ),
                "body_stub": {
                    "aura_bin": tip,
                    "signals": soft_signals,
                    "honesty": hon,
                    "note": (
                        "Do not silent-edit Aura from aura-build. "
                        "File with: gh issue create --repo "
                        f"{AURA_ISSUE_REPO} --title '…' --body-file <this>"
                    ),
                },
            }
        )

    # aura-build product notes (parse/CLI/honesty) — self-improve sink
    ab_signals = []
    if not summary.get("ok") and reason.startswith(("parse", "cli", "honesty", "verify")):
        ab_signals.append(reason)
    if summary.get("ok") and llm_via == "fiber" and llm_parallel == "fiber":
        ab_signals.append("fiber_llm_parallel_ok")  # positive note for round log

    if ab_signals or summary.get("ok") is not None:
        findings.append(
            {
                "class": "aura_build",
                "action": "self_improve_note",
                "signals": ab_signals or ["combat_round_complete"],
                "honesty": hon,
                "summary_ok": bool(summary.get("ok")),
                "reason": reason,
                "note": (
                    "aura-build fixes land on main after verify green; "
                    "never push Aura kernel from combat"
                ),
            }
        )

    return findings


def write_combat_artifacts(
    out_dir: Path,
    *,
    ts: str,
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
    session_st: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, str]:
    """Write traj copy pointer, stdout summary, findings MD/JSON. Returns paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    honesty = _stamp_honesty_from_summary(summary)
    if session_st:
        honesty = {**_stamp_honesty_from_status(session_st), **honesty}

    payload = {
        "combat": True,
        "ts": ts,
        "meta": meta,
        "session": _stamp_honesty_from_status(session_st) if session_st else None,
        "honesty": honesty,
        "summary": summary,
        "findings": findings,
    }
    stdout_path = out_dir / f"combat_{ts}_stdout.json"
    stdout_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths["stdout"] = str(stdout_path)

    findings_json = out_dir / f"combat_{ts}_findings.json"
    findings_json.write_text(
        json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths["findings_json"] = str(findings_json)

    # Human + gh issue create stubs for Aura class findings
    aura_findings = [f for f in findings if f.get("class") == "aura_kernel"]
    if aura_findings:
        md_path = out_dir / f"combat_{ts}_AURA_ISSUE_STUB.md"
        lines = [
            f"# Aura issue stub (combat {ts})",
            "",
            f"Repo: `{AURA_ISSUE_REPO}` — **do not auto-edit Aura**.",
            "",
            "```bash",
            f"gh issue create --repo {AURA_ISSUE_REPO} \\",
            f"  --title {json.dumps(aura_findings[0].get('title') or 'combat Soft anomaly')} \\",
            f"  --body-file {md_path}",
            "```",
            "",
        ]
        for i, f in enumerate(aura_findings, 1):
            lines.append(f"## Finding {i}")
            lines.append("")
            lines.append(f"**Signals:** {', '.join(f.get('signals') or [])}")
            lines.append("")
            body = f.get("body_stub") or {}
            lines.append("```json")
            lines.append(json.dumps(body, indent=2, sort_keys=True))
            lines.append("```")
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        paths["aura_issue_stub"] = str(md_path)

    # Also append a short findings index under docs when durable
    docs_dir = repo_root() / "docs" / "self-evolve-combat"
    docs_dir.mkdir(parents=True, exist_ok=True)
    index = docs_dir / "FINDINGS.md"
    stamp_line = (
        f"- `{ts}` ok={summary.get('ok')} llm_via={honesty.get('llm_via')} "
        f"llm_parallel={honesty.get('llm_parallel')} "
        f"explore={honesty.get('explore_parallel')} "
        f"artifacts=`{stdout_path.name}`\n"
    )
    if index.exists():
        index.write_text(index.read_text(encoding="utf-8") + stamp_line, encoding="utf-8")
    else:
        index.write_text(
            "# Combat findings index\n\n"
            "Append-only stamps from `aura-build self-evolve combat`.\n"
            "Aura kernel edits: issue stubs only (never auto-edit).\n\n"
            + stamp_line,
            encoding="utf-8",
        )
    paths["findings_index"] = str(index)

    return paths


def run_combat(
    *,
    project: Path | str | None = None,
    task: str | None = None,
    max_rounds: int = 8,
    worldlines: int = 3,
    fiber_explore: int | None = None,
    explore_tools: str = "rule,llm,intent",
    concurrent_llm: bool = False,
    fiber_llm: bool | None = None,
    env_file: Path | None = None,
    out_dir: Path | None = None,
    traj_out: Path | None = None,
    harness_root: Path | None = None,
    aura_bin: str | None = None,
    start_session: bool = False,
    stop_session_after: bool = False,
    push: bool = False,
    dry_run: bool = False,
    json_out: bool = False,
) -> dict[str, Any]:
    """One closed combat loop. Refuses without Soft serve_attach_ok."""
    from aura_build.kernel import repo_root as _rr

    repo = _rr()
    out = Path(out_dir) if out_dir else (repo / DEFAULT_OUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    ts = _ts_slug()
    proj = Path(project) if project else (repo / DEFAULT_PROJECT)
    if not proj.is_absolute():
        cand = repo / proj
        if cand.exists():
            proj = cand

    bin_path = aura_bin or os.environ.get("AURA_BIN")
    if not bin_path and Path(DEFAULT_SOFT_AURA_BIN).is_file():
        bin_path = DEFAULT_SOFT_AURA_BIN

    st, attach_meta = require_serve_attach(
        harness_root=harness_root,
        aura_bin=bin_path,
        start_session_if_needed=bool(start_session) and not dry_run,
    )

    result: dict[str, Any] = {
        "ok": False,
        "combat": True,
        "ts": ts,
        "dry_run": dry_run,
        "push": False,
        "no_push": not push,
        "project": str(proj),
        "attach": attach_meta,
    }

    if st is None:
        result["reason"] = attach_meta.get("refuse_reason") or "serve_attach_required"
        result["hint"] = attach_meta.get("hint")
        result["honesty"] = attach_meta.get("status") or {}
        if dry_run:
            # Dry-run still documents the refuse path for CI / --help parity.
            result["ok"] = True
            result["reason"] = "dry_run_refused_without_session"
            result["plan"] = {
                "would_run": "llm-dogfood",
                "project": str(proj),
                "fiber_explore": fiber_explore if fiber_explore is not None else worldlines,
                "fiber_llm": fiber_llm,
                "max_rounds": max_rounds,
                "worldlines": worldlines,
                "push_default": False,
            }
            paths = write_combat_artifacts(
                out,
                ts=ts,
                summary={
                    "ok": True,
                    "reason": result["reason"],
                    "honesty": result["honesty"],
                },
                findings=[
                    {
                        "class": "aura_build",
                        "action": "dry_run_plan",
                        "signals": ["serve_attach_required"],
                        "note": "CI-safe dry-run; no Soft required",
                    }
                ],
                session_st=None,
                meta=attach_meta,
            )
            result["artifacts"] = paths
        return result

    result["session"] = _stamp_honesty_from_status(st)
    result["honesty"] = _stamp_honesty_from_status(st)

    if dry_run:
        result["ok"] = True
        result["reason"] = "dry_run_session_ok"
        result["plan"] = {
            "would_run": "llm-dogfood",
            "project": str(proj),
            "prefer_session": True,
            "fiber_explore": fiber_explore if fiber_explore is not None else worldlines,
            "explore_tools": explore_tools,
            "concurrent_llm": concurrent_llm,
            "fiber_llm": fiber_llm,
            "max_rounds": max_rounds,
            "push_default": False,
        }
        paths = write_combat_artifacts(
            out,
            ts=ts,
            summary={
                "ok": True,
                "reason": result["reason"],
                "honesty": result["honesty"],
            },
            findings=[
                {
                    "class": "aura_build",
                    "action": "dry_run_plan",
                    "signals": ["serve_attach_ok"],
                    "honesty": result["honesty"],
                }
            ],
            session_st=st,
            meta=attach_meta,
        )
        result["artifacts"] = paths
        return result

    # Resolve MiniMax / fiber-llm
    env_path = Path(env_file) if env_file else DEFAULT_ENV_FILE
    use_fiber_llm = fiber_llm
    explore = explore_tools
    if use_fiber_llm is None:
        use_fiber_llm = env_path.is_file()
    if use_fiber_llm and not env_path.is_file():
        use_fiber_llm = False
        # Honest: no key file → rule/intent only (do not invent llm_via=fiber)
        if "llm" in (explore or ""):
            explore = ",".join(
                t for t in explore.split(",") if t.strip() and t.strip() != "llm"
            ) or "rule,intent"

    traj = traj_out or (out / f"combat_{ts}_traj.jsonl")

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.minimax import load_minimax_config

    cfg = None
    try:
        if env_path.is_file() or use_fiber_llm or "llm" in explore:
            cfg = load_minimax_config(env_file=env_path if env_path.is_file() else None)
    except (FileNotFoundError, ValueError, OSError) as exc:
        if use_fiber_llm or concurrent_llm or "llm" in explore.split(","):
            result["reason"] = f"minimax_config:{exc}"
            result["hint"] = "provide --env-file or drop llm from --explore-tools"
            return result
        cfg = None

    # Prefer-session env marker so dogfood hits Soft path
    os.environ["AURA_BUILD_SESSION"] = os.environ.get("AURA_BUILD_SESSION") or "1"
    if use_fiber_llm and cfg is not None:
        os.environ["AURA_BUILD_LLM_VIA"] = "fiber"
        # Soft child must see LLM_* at spawn — restart session if we started it,
        # else rely on already-running Soft that inherited keys (ROUND1 path).
        os.environ.setdefault("LLM_API_KEY", cfg.api_key)
        os.environ.setdefault("LLM_BASE_URL", cfg.base_url)
        os.environ.setdefault("LLM_MODEL", cfg.model)
        if bin_path and not os.environ.get("AURA_PATH"):
            lib = Path(bin_path).resolve().parent.parent / "lib"
            if lib.is_dir():
                os.environ["AURA_PATH"] = str(lib)
        if attach_meta.get("started_session") or start_session:
            try:
                from aura_build.serve_session import start_session as _start
                from aura_build.serve_session import stop_session as _stop

                _stop(harness_root=harness_root)
                _start(aura_bin=bin_path, harness_root=harness_root, force=True)
                st = (
                    __import__("aura_build.serve_session", fromlist=["session_status"])
                    .session_status(harness_root=harness_root, aura_bin=bin_path)
                )
                result["session"] = _stamp_honesty_from_status(st)
            except Exception as exc:  # noqa: BLE001
                result["fiber_llm_restart_warning"] = str(exc)

    fe = fiber_explore if fiber_explore is not None else worldlines
    summary = run_closed_loop(
        task=task or "fib",
        project=proj,
        max_rounds=max_rounds,
        worldlines=worldlines,
        out=traj,
        harness_root=harness_root,
        aura_bin=bin_path,
        keep_workspace=True,
        config=cfg,
        prefer_session=True,
        fiber_explore=fe,
        explore_tools=explore,
        concurrent_llm=concurrent_llm,
        fiber_llm=bool(use_fiber_llm),
    )

    honesty = _stamp_honesty_from_summary(summary)
    # Merge session probe stamps (measured)
    if st:
        honesty = {**_stamp_honesty_from_status(st), **honesty}

    findings = classify_findings(summary, session_st=st)
    paths = write_combat_artifacts(
        out,
        ts=ts,
        summary=summary,
        findings=findings,
        session_st=st,
        meta=attach_meta,
    )
    paths["traj"] = str(traj)

    result.update(
        {
            "ok": bool(summary.get("ok")),
            "reason": summary.get("reason"),
            "summary": summary,
            "honesty": honesty,
            "findings": findings,
            "artifacts": paths,
            "traj": str(traj),
            "fiber_llm": bool(use_fiber_llm),
            "fiber_explore_n": fe,
        }
    )

    # --push only after verify green for aura-build product materialize (if any).
    # Combat llm-dogfood typically does not materialize aura-build sources; refuse
    # push unless explicit materialized paths appear. Never push Aura kernel.
    if push:
        if not summary.get("ok"):
            result["push"] = False
            result["push_reason"] = "verify_not_green"
        else:
            materialized = [
                p
                for p in (summary.get("materialized") or [])
                if isinstance(p, str) and not p.startswith("aura-grok")
            ]
            if not materialized:
                result["push"] = False
                result["push_reason"] = "no_aura_build_materialize_skip_push"
            else:
                from aura_build.self_evolve_host import git_commit_and_maybe_push

                git_res = git_commit_and_maybe_push(
                    repo,
                    message=(
                        f"self-evolve combat: ts={ts} "
                        f"llm_via={honesty.get('llm_via')} "
                        f"llm_parallel={honesty.get('llm_parallel')}"
                    ),
                    paths=materialized,
                    no_push=False,
                )
                result["push"] = bool(git_res.get("pushed"))
                result["git"] = git_res
                result["push_reason"] = git_res.get("reason")
    else:
        result["push"] = False
        result["push_reason"] = "no_push_default"

    if stop_session_after:
        try:
            from aura_build.serve_session import stop_session as _stop

            result["session_stop"] = _stop(harness_root=harness_root)
        except Exception as exc:  # noqa: BLE001
            result["session_stop"] = {"ok": False, "error": str(exc)}

    return result


def format_combat_line(result: dict[str, Any]) -> str:
    hon = result.get("honesty") or {}
    return (
        "self_evolve_combat"
        f" ok={result.get('ok')}"
        f" reason={result.get('reason')}"
        f" project={result.get('project')}"
        f" dry_run={result.get('dry_run')}"
        f" serve_attach_ok={hon.get('serve_attach_ok')}"
        f" session_model={hon.get('session_model')}"
        f" serve_mode={hon.get('serve_mode')}"
        f" llm_via={hon.get('llm_via')}"
        f" llm_parallel={hon.get('llm_parallel')}"
        f" explore_parallel={hon.get('explore_parallel')}"
        f" fiber_llm={result.get('fiber_llm')}"
        f" push={result.get('push')}"
        f" push_reason={result.get('push_reason')}"
        f" traj={result.get('traj') or (result.get('artifacts') or {}).get('traj')}"
        f" findings={len(result.get('findings') or [])}"
    )


def print_findings_stubs(findings: list[dict[str, Any]], *, file=sys.stdout) -> None:
    """Print Aura finding stubs for human / gh issue create (no secrets)."""
    for f in findings:
        if f.get("class") != "aura_kernel":
            continue
        print(
            f"[combat dual-sink] Aura issue stub: {f.get('title')}",
            file=file,
        )
        print(
            f"  signals={f.get('signals')} repo={f.get('repo')}",
            file=file,
        )
        print(
            "  (written under scratch/self_evolve_combat/; do not auto-edit Aura)",
            file=file,
        )


# Redact anything that looks like an API key if it ever leaks into printed JSON.
_KEY_RE = re.compile(
    r"(api[_-]?key|authorization|bearer)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def safe_json_dumps(obj: Any) -> str:
    text = json.dumps(obj, indent=2, sort_keys=True, default=str)
    return _KEY_RE.sub(r"\1=***", text)
