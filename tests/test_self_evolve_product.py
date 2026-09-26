"""Host product loop with a fake proposer. No MiniMax and no live Soft."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from aura_build.cli_parser import build_parser
from aura_build.self_evolve_product import cmd_product, run_product

ALLOW = "src/aura_build/stamp_banner.py"
BODY = "def stamp_banner_agrees(text: str) -> bool:\n    return False\n"
DIFF = """diff --git a/src/aura_build/stamp_banner.py b/src/aura_build/stamp_banner.py
--- a/src/aura_build/stamp_banner.py
+++ b/src/aura_build/stamp_banner.py
@@ -1,2 +1,3 @@
 def stamp_banner_agrees(text: str) -> bool:
-    return False
+    import re
+    return bool(re.search("x", text or ""))
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    path = repo / ALLOW
    path.parent.mkdir(parents=True)
    path.write_text(BODY, encoding="utf-8")
    (repo / ".gitignore").write_text("scratch/\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")
    _git(repo, "checkout", "-b", "exp/self-evolve-product-stamp-banner")
    return repo


def _ns(repo: Path, session: Path, **kw: object) -> SimpleNamespace:
    base = dict(
        repo=repo,
        session=session,
        allow=ALLOW,
        pytest=["tests/test_stamp_banner.py"],
        max_rounds=3,
        json=True,
        goal="edit the predicate",
        apply_diff=None,
        aura_bin=None,
        env_file=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _ok_propose(**_kw: object) -> dict:
    return {"ok": True, "content": DIFF, "llm_via": "fiber", "llm_parallel": "fiber_serial"}


def _pytest_ok(argv: list[str], env: dict[str, str], _repo: Path):
    assert "LLM_API_KEY" not in env
    assert "unshare" not in argv
    return subprocess.CompletedProcess(argv, 0, "ok\n", "")


def test_refuse_main_dirty_detached_and_host_allow(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/s"
    _git(repo, "checkout", "main")
    on_main = run_product(_ns(repo, session), propose=_ok_propose)
    assert on_main["reason"] == "diff_ready" and on_main["exit_code"] == 0
    _git(repo, "checkout", "exp/self-evolve-product-stamp-banner")
    (repo / "dirty.txt").write_text("x", encoding="utf-8")
    dirty = run_product(_ns(repo, session), propose=_ok_propose)
    assert dirty["reason"] == "dirty_tree"
    (repo / "dirty.txt").unlink()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    _git(repo, "checkout", "--detach", head)
    detached = run_product(_ns(repo, session), propose=_ok_propose)
    assert detached["reason"] == "detached_head"
    _git(repo, "checkout", "exp/self-evolve-product-stamp-banner")
    host = repo / "src/aura_build/self_evolve_host.py"
    host.write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", str(host))
    _git(repo, "commit", "-m", "host")
    bad = run_product(
        _ns(repo, session, allow="src/aura_build/self_evolve_host.py"),
        propose=_ok_propose,
    )
    assert bad["reason"] == "allow_rejected"


def test_session_outside_scratch_refused(tmp_path: Path):
    repo = init_repo(tmp_path)
    out = run_product(_ns(repo, repo / "elsewhere"), propose=_ok_propose)
    assert out["reason"] == "session_rejected"


def test_two_headers_and_plus_swap_do_not_apply(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/s"
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    two = DIFF + "\ndiff --git a/src/aura_build/other.py b/src/aura_build/other.py\n--- a/src/aura_build/other.py\n+++ b/src/aura_build/other.py\n@@ -0,0 +1 @@\n+x = 1\n"
    sneak = DIFF.replace("+++ b/src/aura_build/stamp_banner.py", "+++ b/sneak.py")

    def propose_two(**_kw: object) -> dict:
        return {"ok": True, "content": two, "llm_via": "host", "llm_parallel": "none"}

    first = run_product(_ns(repo, session), propose=propose_two)
    assert first["reason"] == "diff_path"
    assert not (repo / "sneak.py").exists()
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).strip() == ""

    def propose_sneak(**_kw: object) -> dict:
        return {"ok": True, "content": sneak, "llm_via": "host", "llm_parallel": "none"}

    second = run_product(_ns(repo, session), propose=propose_sneak)
    assert second["reason"] == "diff_path"
    assert not (repo / "sneak.py").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == sha
    assert (repo / ALLOW).read_text(encoding="utf-8") == BODY


def test_denylist_and_secret_redaction(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/s"
    bad = DIFF.replace("+    import re", "+    import os")

    def propose_os(**_kw: object) -> dict:
        return {"ok": True, "content": bad, "llm_via": "host", "llm_parallel": "none"}

    denied = run_product(_ns(repo, session), propose=propose_os)
    assert denied["reason"] == "denylist"
    secret = "sk-test-secret-value"

    def propose_secret(**_kw: object) -> dict:
        return {
            "ok": True,
            "content": DIFF + secret,
            "llm_via": "host",
            "llm_parallel": "none",
            "api_key": secret,
            "_api_key": secret,
        }

    hidden = run_product(_ns(repo, session), propose=propose_secret)
    assert hidden["reason"] == "secret_in_output"
    blob = (session / "episodes.jsonl").read_text(encoding="utf-8")
    assert secret not in blob
    assert secret not in json.dumps({k: v for k, v in hidden.items() if k != "_api_key"})


def test_401_stops_and_timeout_is_not_fiber(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/s"
    calls = {"n": 0}

    def propose_401(**_kw: object) -> dict:
        calls["n"] += 1
        return {"ok": False, "error": "HTTP 401", "llm_via": "fiber", "llm_parallel": "fiber_serial"}

    first = run_product(_ns(repo, session), propose=propose_401)
    assert first["reason"] == "minimax_http_401" and first["exit_code"] == 2
    second = run_product(_ns(repo, session), propose=propose_401)
    assert second["reason"] == "minimax_http_401"
    assert calls["n"] == 1

    session2 = repo / "scratch/self_evolve_product/timeout"
    def propose_timeout(**_kw: object) -> dict:
        return {
            "ok": False,
            "action": "refuse",
            "error": "serve_session_timeout",
            "llm_via": "fiber",
        }

    timed = run_product(_ns(repo, session2), propose=propose_timeout)
    assert timed["reason"] == "serve_session_timeout"
    assert timed.get("llm_via") is None
    line = json.loads((session2 / "episodes.jsonl").read_text(encoding="utf-8"))
    assert line["runtime"]["llm_via"] is None
    assert line["runtime"]["mode"] == "host_pytest"
    assert line["ts_start"] and line["ts_end"]


def test_http_error_counts_and_next_prompt_sees_class(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/http"
    seen: list[str] = []

    def propose(**kw: object) -> dict:
        messages = kw["messages"]
        seen.append(messages[1]["content"])
        return {"ok": False, "error": "connection reset", "llm_via": "host", "llm_parallel": "none"}

    first = run_product(_ns(repo, session), propose=propose)
    assert first["reason"] == "minimax_http"
    second = run_product(_ns(repo, session), propose=propose)
    assert "minimax_http" in seen[1]
    assert second["completions"] == 2


def test_cli_propose_then_apply_commits_without_push(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/stamp-banner"
    pushes: list[list[str]] = []
    real = subprocess.run

    def spy(args, **kwargs):
        argv = list(args)
        if argv[:2] == ["git", "push"]:
            pushes.append(argv)
        return real(args, **kwargs)

    monkeypatch.setattr("aura_build.self_evolve_host.subprocess.run", spy)
    first = cmd_product(_ns(repo, session), propose=_ok_propose)
    assert first == 0
    diff = session / "round-1.diff"
    assert diff.is_file()
    assert "import re" in diff.read_text(encoding="utf-8")
    envs: list[dict[str, str]] = []

    def pytest_run(argv: list[str], env: dict[str, str], _repo: Path):
        envs.append(env)
        assert "LLM_API_KEY" not in env
        assert argv[1:4] == ["-m", "pytest", "-q"]
        assert "unshare" not in argv
        return subprocess.CompletedProcess(argv, 0, "", "")

    os_env = dict(**{"LLM_API_KEY": "sk-should-not-pass"})
    monkeypatch.setenv("LLM_API_KEY", os_env["LLM_API_KEY"])
    second = cmd_product(
        _ns(repo, session, goal=None, apply_diff=diff),
        pytest_run=pytest_run,
    )
    assert second == 0
    assert envs and "LLM_API_KEY" not in envs[0]
    note = (session / "PRODUCT1.md").read_text(encoding="utf-8")
    assert "ok=true" in note and "push=false" in note
    assert pushes == []
    log = subprocess.check_output(["git", "log", "-1", "--format=%s"], cwd=repo, text=True)
    assert log.startswith("self-evolve product:")
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).strip() == ""
    # second process started clean; completions stayed 1
    assert (session / "completions").read_text(encoding="utf-8").strip() == "1"


def test_restore_untracked_after_forced_spill(tmp_path: Path):
    repo = init_repo(tmp_path)
    session = repo / "scratch/self_evolve_product/spill"
    session.mkdir(parents=True)
    (repo / ALLOW).write_text(BODY + "\n", encoding="utf-8")
    sneak = repo / "sneak.py"
    sneak.write_text("x = 1\n", encoding="utf-8")
    from aura_build.self_evolve_product import _restore

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    assert _restore(repo, sha, session)
    assert not sneak.exists()
    assert (repo / ALLOW).read_text(encoding="utf-8") == BODY
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).strip() == ""


def test_parser_requires_session():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["self-evolve", "product", "--allow", ALLOW, "--goal", "x", "--pytest", "tests/test_stamp_banner.py"])
