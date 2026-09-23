"""MiniMax adapter + dogfood helpers (no live key required for unit tests)."""

from __future__ import annotations

import json
from pathlib import Path

from aura_build.cli import build_parser, main
from aura_build.minimax import extract_aura_source, lock_cn_base_url, redact_secrets

FIB_SRC = """(define (fib n)
  (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))
(display "FIB10=")(display (fib 10))(newline)
"""


def test_parser_lists_llm_commands():
    help_text = build_parser().format_help()
    assert "llm" in help_text
    assert "llm-dogfood" in help_text


def test_extract_aura_source_fence():
    text = "Sure.\n```aura\n(display 1)\n```\n"
    assert extract_aura_source(text).strip() == "(display 1)"


def test_redact_secrets():
    s = "Bearer sk-abc1234567890xyz Authorization: sk-abc1234567890xyz"
    out = redact_secrets(s, extra="sk-abc1234567890xyz")
    assert "sk-abc" not in out
    assert "<redacted:secret>" in out


def test_lock_cn_base_url():
    assert lock_cn_base_url(None) == "https://api.minimaxi.com/v1"
    assert lock_cn_base_url("https://api.minimax.io/v1") == "https://api.minimaxi.com/v1"
    assert lock_cn_base_url("https://api.minimaxi.com/v1/") == "https://api.minimaxi.com/v1"


def test_llm_refuses_missing_key(monkeypatch, tmp_path):
    missing = tmp_path / "no-such-key"
    env = tmp_path / "minimax.env"
    env.write_text(
        f"MINIMAX_API_KEY_FILE={missing}\n"
        "MINIMAX_BASE_URL=https://api.minimaxi.com/v1\n"
        "MINIMAX_MODEL=MiniMax-M3\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY_FILE", raising=False)
    monkeypatch.delenv("MINIMAX_BASE_URL", raising=False)
    rc = main(["llm", "--prompt", "hi", "--env-file", str(env)])
    assert rc == 2


def test_verify_good_fib(tmp_path):
    from aura_build.llm_dogfood import FIB_SUCCESS_RE, verify_aura_program
    from aura_build.runtime import resolve_aura_bin

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "fib.aura"
    prog.write_text(FIB_SRC, encoding="utf-8")
    got = verify_aura_program(prog, expect_re=FIB_SUCCESS_RE, aura_bin=bin_path)
    assert got["passed"] is True
    assert got["fitness"] == 1.0


def test_closed_loop_mocked_minimax(monkeypatch, tmp_path):
    """One propose returns good fib; ensure select-best + traj without live API."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{FIB_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task="fib",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["rounds"] >= 1
    assert Path(summary["final_program"]).is_file()
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    ep = json.loads(lines[0])
    assert ep["runtime"]["kernel"] == "aura"
    assert ep["runtime"]["llm"]["api_key"] == "<redacted:secret>"
    assert ep["runtime"]["fiber_live"] is False
    assert ep["runtime"]["llm"]["base_url"] == "https://api.minimaxi.com/v1"


GREET_SRC = '(display "GREET=aura")(newline)\n'


def test_parser_lists_greet_task():
    dog = None
    for action in build_parser()._subparsers._group_actions:
        dog = action.choices.get("llm-dogfood")
        if dog is not None:
            break
    assert dog is not None
    task_choices = None
    for act in dog._actions:
        if "--task" in (act.option_strings or []):
            task_choices = act.choices
            break
    assert task_choices is not None
    assert "greet" in task_choices
    assert "fib" in task_choices
    assert "calc" in task_choices


def test_verify_good_greet(tmp_path):
    from aura_build.llm_dogfood import GREET_SUCCESS_RE, verify_aura_program
    from aura_build.runtime import resolve_aura_bin

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "greet.aura"
    prog.write_text(GREET_SRC, encoding="utf-8")
    got = verify_aura_program(prog, expect_re=GREET_SUCCESS_RE, aura_bin=bin_path)
    assert got["passed"] is True
    assert got["fitness"] == 1.0


def test_closed_loop_mocked_greet(monkeypatch, tmp_path):
    """One propose returns good greet; ensure select-best + traj without live API."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{GREET_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task="greet",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "greet"
    assert summary["expect"] == "GREET=aura"
    assert Path(summary["final_program"]).is_file()
    assert "GREET=aura" in Path(summary["final_program"]).read_text(encoding="utf-8")


CALC_SRC = """(define (add a b) (+ a b))
(define (mul a b) (* a b))
(display "ADD=")(display (add 3 4))(newline)
(display "MUL=")(display (mul 3 4))(newline)
(display "MIX=")(display (add (mul 3 4) 5))(newline)
"""

CALC_HARDCODE = """(display "ADD=7")(newline)
(display "MUL=12")(newline)
(display "MIX=17")(newline)
"""


def test_verify_good_calc(tmp_path):
    from aura_build.llm_dogfood import (
        CALC_SOURCE_RES,
        CALC_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "calc.aura"
    prog.write_text(CALC_SRC, encoding="utf-8")
    got = verify_aura_program(
        prog,
        expect_re=CALC_SUCCESS_RES,
        source_res=CALC_SOURCE_RES,
        aura_bin=bin_path,
    )
    assert got["passed"] is True
    assert got["fitness"] == 1.0
    assert got["structure_ok"] is True


def test_verify_calc_rejects_hardcode(tmp_path):
    from aura_build.llm_dogfood import (
        CALC_SOURCE_RES,
        CALC_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "hard.aura"
    prog.write_text(CALC_HARDCODE, encoding="utf-8")
    got = verify_aura_program(
        prog,
        expect_re=CALC_SUCCESS_RES,
        source_res=CALC_SOURCE_RES,
        aura_bin=bin_path,
    )
    assert got["passed"] is False
    assert got["matched_expect"] is True
    assert got["structure_ok"] is False


def test_closed_loop_mocked_calc(monkeypatch, tmp_path):
    """One propose returns good calc; ensure select-best + traj without live API."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{CALC_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task="calc",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "calc"
    assert "ADD=7" in summary["expect"]
    final = Path(summary["final_program"]).read_text(encoding="utf-8")
    assert "(define (add" in final
    assert "(define (mul" in final


KV_SRC = """(define store '())
(define (kv-set k v)
  (set! store (cons (cons k v) store)))
(define (kv-get k)
  (define (lookup s)
    (if (null? s) 'nil
        (if (equal? (car (car s)) k)
            (cdr (car s))
            (lookup (cdr s)))))
  (lookup store))
(kv-set "a" 1)
(kv-set "b" 2)
(display "GET_a=")(display (kv-get "a"))(newline)
(display "GET_b=")(display (kv-get "b"))(newline)
(display "MISS=")(display (kv-get "z"))(newline)
(kv-set "c" 3)
(display "GET_c=")(display (kv-get "c"))(newline)
"""

KV_HARDCODE = """(display "GET_a=1")(newline)
(display "GET_b=2")(newline)
(display "MISS=nil")(newline)
(display "GET_c=3")(newline)
"""


def test_parser_lists_kv_and_project():
    dog = None
    for action in build_parser()._subparsers._group_actions:
        dog = action.choices.get("llm-dogfood")
        if dog is not None:
            break
    assert dog is not None
    task_choices = None
    has_project = False
    for act in dog._actions:
        if "--task" in (act.option_strings or []):
            task_choices = act.choices
        if "--project" in (act.option_strings or []):
            has_project = True
    assert task_choices is not None
    assert "kv" in task_choices
    assert has_project


def test_load_project_spec_mini_kv():
    from aura_build.llm_dogfood import load_project_spec
    from aura_build.kernel import repo_root

    spec = load_project_spec(repo_root() / "examples/projects/mini-kv")
    assert spec["label"] == "kv"
    assert spec["verify_script"] and spec["verify_script"].endswith("verify.sh")
    assert "GET_a=1" in spec["expect"]
    assert spec["source_res"]
    assert "kv-set" in spec["user"]


def test_verify_good_kv(tmp_path):
    from aura_build.llm_dogfood import (
        KV_SOURCE_RES,
        KV_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "kv.aura"
    prog.write_text(KV_SRC, encoding="utf-8")
    script = repo_root() / "examples/projects/mini-kv/verify.sh"
    got = verify_aura_program(
        prog,
        expect_re=KV_SUCCESS_RES,
        source_res=KV_SOURCE_RES,
        aura_bin=bin_path,
        verify_script=str(script),
    )
    assert got["passed"] is True
    assert got["via"] == "verify_script"
    assert got["fitness"] == 1.0


def test_verify_kv_rejects_hardcode(tmp_path):
    from aura_build.llm_dogfood import (
        KV_SOURCE_RES,
        KV_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "hard.aura"
    prog.write_text(KV_HARDCODE, encoding="utf-8")
    script = repo_root() / "examples/projects/mini-kv/verify.sh"
    got = verify_aura_program(
        prog,
        expect_re=KV_SUCCESS_RES,
        source_res=KV_SOURCE_RES,
        aura_bin=bin_path,
        verify_script=str(script),
    )
    assert got["passed"] is False
    assert got["structure_ok"] is False or got["exit_code"] != 0


def test_structure_fail_note_generic():
    import re
    from aura_build.llm_dogfood import _structure_fail_note

    note = _structure_fail_note([re.compile(r"\(define\s+\(kv-set\b")])
    assert "kv-set" in note
    assert "add" not in note or "kv-set" in note


def test_closed_loop_mocked_kv_via_project(monkeypatch, tmp_path):
    """--project path: mock MiniMax returns good kv; verify.sh oracle."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{KV_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task="kv",
        project=repo_root() / "examples/projects/mini-kv",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "kv"
    assert "mini-kv" in summary["project"]
    assert summary.get("verify_script")
    final = Path(summary["final_program"]).read_text(encoding="utf-8")
    assert "(define (kv-set" in final
    assert "(define (kv-get" in final
    ep = json.loads(out.read_text(encoding="utf-8").strip().splitlines()[0])
    assert ep["runtime"]["dogfood"]["task"] == "kv"
    assert "mini-kv" in (ep["runtime"]["dogfood"].get("project") or "")


def test_project_alone_does_not_inherit_default_fib_label(monkeypatch, tmp_path):
    """--project without --task must label traj as project label, not fib."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{KV_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop, DEFAULT_TASK
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    if not resolve_aura_bin():
        return

    summary = run_closed_loop(
        task=DEFAULT_TASK,  # simulates CLI default --task fib
        project=repo_root() / "examples/projects/mini-kv",
        max_rounds=1,
        worldlines=1,
        out=tmp_path / "traj.jsonl",
        workspace=tmp_path / "ws",
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "kv"
    assert summary["task"] != "fib"


STACK_SRC = """(define stk '())
(define (stack-push x) (set! stk (cons x stk)))
(define (stack-pop)
  (if (null? stk) 'nil
      (let ((v (car stk))) (set! stk (cdr stk)) v)))
(define (stack-top) (if (null? stk) 'nil (car stk)))
(define (stack-size)
  (define (len xs n) (if (null? xs) n (len (cdr xs) (+ n 1))))
  (len stk 0))
(define (stack-empty) (if (null? stk) 1 0))
(stack-push 10)
(stack-push 20)
(stack-push 30)
(display "TOP=")(display (stack-top))(newline)
(display "POP=")(display (stack-pop))(newline)
(display "TOP2=")(display (stack-top))(newline)
(display "SIZE=")(display (stack-size))(newline)
(display "EMPTY=")(display (stack-empty))(newline)
"""

STACK_HARDCODE = """(display "TOP=30")(newline)
(display "POP=30")(newline)
(display "TOP2=20")(newline)
(display "SIZE=2")(newline)
(display "EMPTY=0")(newline)
"""


def test_parser_lists_stack_task():
    dog = None
    for action in build_parser()._subparsers._group_actions:
        dog = action.choices.get("llm-dogfood")
        if dog is not None:
            break
    assert dog is not None
    task_choices = None
    for act in dog._actions:
        if "--task" in (act.option_strings or []):
            task_choices = act.choices
    assert task_choices is not None
    assert "stack" in task_choices


def test_load_project_spec_mini_stack():
    from aura_build.llm_dogfood import load_project_spec
    from aura_build.kernel import repo_root

    spec = load_project_spec(repo_root() / "examples/projects/mini-stack")
    assert spec["label"] == "stack"
    assert spec["verify_script"] and spec["verify_script"].endswith("verify.sh")
    assert "TOP=30" in spec["expect"]
    assert spec["source_res"] and len(spec["source_res"]) >= 4
    assert "stack-push" in spec["user"]


def test_verify_good_stack(tmp_path):
    from aura_build.llm_dogfood import (
        STACK_SOURCE_RES,
        STACK_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "stack.aura"
    prog.write_text(STACK_SRC, encoding="utf-8")
    script = repo_root() / "examples/projects/mini-stack/verify.sh"
    got = verify_aura_program(
        prog,
        expect_re=STACK_SUCCESS_RES,
        source_res=STACK_SOURCE_RES,
        aura_bin=bin_path,
        verify_script=str(script),
    )
    assert got["passed"] is True
    assert got["via"] == "verify_script"
    assert got["fitness"] == 1.0
    assert got["matched_expect"] is True


def test_verify_stack_rejects_hardcode(tmp_path):
    from aura_build.llm_dogfood import (
        STACK_SOURCE_RES,
        STACK_SUCCESS_RES,
        verify_aura_program,
    )
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    prog = tmp_path / "hard.aura"
    prog.write_text(STACK_HARDCODE, encoding="utf-8")
    script = repo_root() / "examples/projects/mini-stack/verify.sh"
    got = verify_aura_program(
        prog,
        expect_re=STACK_SUCCESS_RES,
        source_res=STACK_SOURCE_RES,
        aura_bin=bin_path,
        verify_script=str(script),
    )
    assert got["passed"] is False
    assert got["structure_ok"] is False or got["exit_code"] != 0


def test_verify_stack_zero_arity_defines_ok(tmp_path):
    """Regression: (define (stack-pop) ...) must match source_res / verify.sh (\\\\b)."""
    from aura_build.llm_dogfood import STACK_SOURCE_RES
    import re

    src = "(define (stack-pop)\n  1)\n(define (stack-top)\n  2)\n"
    assert STACK_SOURCE_RES[1].search(src)  # stack-pop
    assert STACK_SOURCE_RES[2].search(src)  # stack-top
    # trailing-space pattern must NOT be required
    bad = re.compile(r"\(define\s+\(stack-pop\s")
    assert not bad.search(src)


def test_closed_loop_mocked_stack_via_project(monkeypatch, tmp_path):
    """--project path: mock MiniMax returns good stack; verify.sh oracle."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": f"```aura\n{STACK_SRC}```",
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task="stack",
        project=repo_root() / "examples/projects/mini-stack",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "stack"
    assert "mini-stack" in summary["project"]
    assert summary.get("verify_script")
    final = Path(summary["final_program"]).read_text(encoding="utf-8")
    assert "(define (stack-push" in final
    assert "(define (stack-pop" in final
    ep = json.loads(out.read_text(encoding="utf-8").strip().splitlines()[0])
    assert ep["runtime"]["dogfood"]["task"] == "stack"
    assert "mini-stack" in (ep["runtime"]["dogfood"].get("project") or "")


def test_matched_expect_recognizes_stack_tokens():
    from aura_build.llm_dogfood import _matched_expect, STACK_SUCCESS_RES

    assert _matched_expect(False, "TOP=30\nPOP=30\n", STACK_SUCCESS_RES) is True
    assert _matched_expect(False, "noise only", STACK_SUCCESS_RES) is False
    assert _matched_expect(True, "", None) is True


BANK_LIB = """(define a-bal 100)
(define b-bal 50)
(define (balance acct)
  (if (equal? acct "A") a-bal
      (if (equal? acct "B") b-bal 0)))
(define (credit acct n)
  (if (equal? acct "A") (set! a-bal (+ a-bal n))
      (if (equal? acct "B") (set! b-bal (+ b-bal n)) 0)))
(define (debit acct n)
  (if (equal? acct "A") (set! a-bal (- a-bal n))
      (if (equal? acct "B") (set! b-bal (- b-bal n)) 0)))
"""

BANK_MAIN = """(define a0 (balance "A"))
(define b0 (balance "B"))
(display "A=")(display a0)(newline)
(display "B=")(display b0)(newline)
(debit "A" 30)
(credit "B" 30)
(define a2 (balance "A"))
(define b2 (balance "B"))
(display "A2=")(display a2)(newline)
(display "B2=")(display b2)(newline)
(display "OK=")
(display (if (= (+ a2 b2) (+ a0 b0)) 1 0))
(newline)
"""

BANK_REPLY = "```aura lib.aura\n" + BANK_LIB + "```\n" + "```aura main.aura\n" + BANK_MAIN + "```\n"


def test_extract_aura_sources_named_fences():
    from aura_build.minimax import extract_aura_sources

    got = extract_aura_sources(BANK_REPLY, ["lib.aura", "main.aura"])
    assert "lib.aura" in got and "main.aura" in got
    assert "(define (credit" in got["lib.aura"]
    assert 'display "A="' in got["main.aura"] or 'display "A="' in got["main.aura"].replace(
        " ", " "
    )


def test_extract_aura_sources_json_map():
    import json
    from aura_build.minimax import extract_aura_sources

    payload = json.dumps({"lib.aura": "(define (credit a n) n)\n", "main.aura": "(display 1)\n"})
    got = extract_aura_sources(payload, ["lib.aura", "main.aura"])
    assert got["lib.aura"].startswith("(define (credit")
    assert got["main.aura"].startswith("(display 1)")


def test_load_project_spec_mini_bank_multifile():
    from aura_build.llm_dogfood import load_project_spec
    from aura_build.kernel import repo_root

    spec = load_project_spec(repo_root() / "examples/projects/mini-bank")
    assert spec["label"] == "bank"
    assert spec["multi_file"] is True
    assert spec["files"] == ["lib.aura", "main.aura"]
    assert spec["entry"] == "main.aura"
    assert spec["run_mode"] == "cli_multi"
    assert isinstance(spec["fallback"], dict)
    assert "lib.aura" in spec["fallback"] and "main.aura" in spec["fallback"]
    assert "MULTI-FILE" in spec["user"] or "multi-file" in spec["user"].lower()
    assert spec["verify_script"] and spec["verify_script"].endswith("verify.sh")
    assert "credit" in (spec["user"] + str(spec.get("source_res")))


def test_verify_good_bank_multifile(tmp_path):
    from aura_build.llm_dogfood import verify_aura_program, load_project_spec
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    spec = load_project_spec(repo_root() / "examples/projects/mini-bank")
    cand = tmp_path / "cand"
    cand.mkdir()
    (cand / "lib.aura").write_text(BANK_LIB, encoding="utf-8")
    (cand / "main.aura").write_text(BANK_MAIN, encoding="utf-8")
    got = verify_aura_program(
        cand / "main.aura",
        expect_re=spec["expect_re"],
        source_res=spec["source_res"],
        aura_bin=bin_path,
        verify_script=spec["verify_script"],
        candidate_dir=cand,
        files=spec["files"],
    )
    assert got["passed"] is True
    assert got["via"] == "verify_script"
    assert got["fitness"] == 1.0


def test_verify_bank_rejects_main_only_hardcode(tmp_path):
    from aura_build.llm_dogfood import verify_aura_program, load_project_spec
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    spec = load_project_spec(repo_root() / "examples/projects/mini-bank")
    cand = tmp_path / "cand"
    cand.mkdir()
    (cand / "lib.aura").write_text("; empty lib\n", encoding="utf-8")
    (cand / "main.aura").write_text(
        '(display "A=100")(newline)\n'
        '(display "B=50")(newline)\n'
        '(display "A2=70")(newline)\n'
        '(display "B2=80")(newline)\n'
        '(display "OK=1")(newline)\n',
        encoding="utf-8",
    )
    got = verify_aura_program(
        cand / "main.aura",
        expect_re=spec["expect_re"],
        source_res=spec["source_res"],
        aura_bin=bin_path,
        verify_script=spec["verify_script"],
        candidate_dir=cand,
        files=spec["files"],
    )
    assert got["passed"] is False


def test_closed_loop_mocked_bank_multifile(monkeypatch, tmp_path):
    """Mock MiniMax returns named fences; verify.sh multi-file oracle."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": BANK_REPLY,
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task=None,
        project=repo_root() / "examples/projects/mini-bank",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "bank"
    assert "mini-bank" in summary["project"]
    sel = Path(summary["final_program"]).parent
    assert (sel / "lib.aura").is_file() or Path(summary["final_program"]).name in (
        "main.aura",
        "program.aura",
    )
    # traj records files
    ep = json.loads(out.read_text(encoding="utf-8").strip().splitlines()[0])
    dog = ep["runtime"]["dogfood"]
    assert dog.get("multi_file") is True or "lib.aura" in (dog.get("files") or [])



ROUTER_TABLE = """(define routes '())
(define (route-register method path handler)
  (set! routes (cons (list method path handler) routes)))
(define (route-table) routes)
(define (routes-init)
  (set! routes '())
  (route-register "GET" "/" "home")
  (route-register "GET" "/api" "api")
  (route-register "POST" "/api" "405"))
"""

ROUTER_MATCH = """(define (path-prefix? path prefix)
  (let ((n (string-length prefix)))
    (if (< (string-length path) n)
        #f
        (equal? (substring path 0 n) prefix))))
(define (lookup-exact method path rs)
  (if (null? rs)
      #f
      (let ((r (car rs)))
        (if (and (equal? (car r) method) (equal? (car (cdr r)) path))
            (car (cdr (cdr r)))
            (lookup-exact method path (cdr rs))))))
(define (route-lookup method path)
  (let ((hit (lookup-exact method path (route-table))))
    (if hit
        hit
        (if (and (equal? method "GET") (path-prefix? path "/api"))
            "api"
            "404"))))
"""

ROUTER_MAIN = """(routes-init)
(define (show label val)
  (display label)(display "=")(display val)(newline))
(define c 0)
(define (hit label method path)
  (let ((v (route-lookup method path)))
    (show label v)
    (if (equal? v "404")
        0
        (set! c (+ c 1)))))
(hit "GET_SLASH" "GET" "/")
(hit "GET_API" "GET" "/api")
(hit "GET_API_V1" "GET" "/api/v1")
(hit "GET_API_V2" "GET" "/api/v2")
(hit "POST_API" "POST" "/api")
(hit "MISS" "GET" "/nope")
(show "COUNT" c)
"""

ROUTER_REPLY = (
    "```aura table.aura\n" + ROUTER_TABLE + "```\n"
    + "```aura match.aura\n" + ROUTER_MATCH + "```\n"
    + "```aura main.aura\n" + ROUTER_MAIN + "```\n"
)


def test_extract_aura_sources_three_files():
    from aura_build.minimax import extract_aura_sources

    names = ["table.aura", "match.aura", "main.aura"]
    got = extract_aura_sources(ROUTER_REPLY, names)
    assert list(got.keys()) == names  # stable fence order
    assert "(define (route-register" in got["table.aura"]
    assert "(define (route-lookup" in got["match.aura"]
    assert "(route-lookup" in got["main.aura"]


def test_extract_aura_sources_three_unnamed_zip():
    from aura_build.minimax import extract_aura_sources

    reply = (
        "```aura\n(define (route-register m p h) 1)\n```\n"
        "```aura\n(define (route-lookup m p) 404)\n```\n"
        "```aura\n(display 1)\n```\n"
    )
    names = ["table.aura", "match.aura", "main.aura"]
    got = extract_aura_sources(reply, names)
    assert list(got.keys()) == names
    assert "route-register" in got["table.aura"]
    assert "route-lookup" in got["match.aura"]


def test_extract_aura_sources_byte_cap():
    from aura_build.minimax import extract_aura_sources, MAX_AURA_FILE_BYTES

    huge = "x" * (MAX_AURA_FILE_BYTES + 500)
    reply = f"```aura table.aura\n{huge}\n```\n```aura match.aura\n(define (route-lookup m p) 1)\n```\n"
    got = extract_aura_sources(reply, ["table.aura", "match.aura", "main.aura"])
    assert "table.aura" in got
    assert len(got["table.aura"]) <= MAX_AURA_FILE_BYTES + 80
    assert "truncated" in got["table.aura"]


def test_load_project_spec_mini_router_three_files():
    from aura_build.llm_dogfood import load_project_spec
    from aura_build.kernel import repo_root

    spec = load_project_spec(repo_root() / "examples/projects/mini-router")
    assert spec["label"] == "router"
    assert spec["multi_file"] is True
    assert spec["files"] == ["table.aura", "match.aura", "main.aura"]
    assert spec["entry"] == "main.aura"
    assert spec["run_mode"] == "cli_multi"
    assert isinstance(spec["fallback"], dict)
    assert set(spec["fallback"]) >= {"table.aura", "match.aura", "main.aura"}
    assert "route-lookup" in spec["user"] or "route-lookup" in str(spec.get("source_res"))
    assert spec.get("seed_from_stub") is True


def test_parser_lists_router_and_bank_tasks():
    dog = None
    for action in build_parser()._subparsers._group_actions:
        dog = action.choices.get("llm-dogfood")
        if dog is not None:
            break
    assert dog is not None
    task_choices = None
    for act in dog._actions:
        if "--task" in (act.option_strings or []):
            task_choices = act.choices
            break
    assert task_choices is not None
    assert "router" in task_choices
    assert "bank" in task_choices


def test_verify_good_router_multifile(tmp_path):
    from aura_build.llm_dogfood import verify_aura_program, load_project_spec
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    spec = load_project_spec(repo_root() / "examples/projects/mini-router")
    cand = tmp_path / "cand"
    cand.mkdir()
    (cand / "table.aura").write_text(ROUTER_TABLE, encoding="utf-8")
    (cand / "match.aura").write_text(ROUTER_MATCH, encoding="utf-8")
    (cand / "main.aura").write_text(ROUTER_MAIN, encoding="utf-8")
    got = verify_aura_program(
        cand / "main.aura",
        expect_re=spec["expect_re"],
        source_res=spec["source_res"],
        aura_bin=bin_path,
        verify_script=spec["verify_script"],
        candidate_dir=cand,
        files=spec["files"],
    )
    assert got["passed"] is True
    assert got["via"] == "verify_script"


def test_verify_router_stub_fails():
    from aura_build.llm_dogfood import verify_aura_program, load_project_spec
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    bin_path = resolve_aura_bin()
    if not bin_path:
        return
    spec = load_project_spec(repo_root() / "examples/projects/mini-router")
    stub = repo_root() / "examples/projects/mini-router/stub"
    got = verify_aura_program(
        stub / "main.aura",
        expect_re=spec["expect_re"],
        source_res=spec["source_res"],
        aura_bin=bin_path,
        verify_script=spec["verify_script"],
        candidate_dir=stub,
        files=spec["files"],
    )
    assert got["passed"] is False
    assert "mismatch" in (got["stderr"] or "").lower() or got["exit_code"] != 0


def test_closed_loop_mocked_router_three_files(monkeypatch, tmp_path):
    """Mock MiniMax returns 3 named fences; verify.sh multi-file oracle."""

    class FakeCfg:
        api_key = "sk-test-fake-key-not-real"
        base_url = "https://api.minimaxi.com/v1"
        model = "MiniMax-M3"
        key_file = "/tmp/fake"
        env_file = "/tmp/fake.env"

        def public_dict(self):
            return {
                "provider": "minimax",
                "base_url": self.base_url,
                "model": self.model,
                "api_key": "<redacted:secret>",
            }

    def fake_chat(messages, config=None, **kwargs):
        return {
            "ok": True,
            "content": ROUTER_REPLY,
            "model": "MiniMax-M3",
            "error": "",
        }

    monkeypatch.setattr("aura_build.llm_dogfood.chat_completions", fake_chat)
    monkeypatch.setattr("aura_build.llm_dogfood.prefer_aura_kernel", lambda: False)

    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.runtime import resolve_aura_bin
    from aura_build.kernel import repo_root

    if not resolve_aura_bin():
        return

    out = tmp_path / "traj.jsonl"
    ws = tmp_path / "ws"
    summary = run_closed_loop(
        task=None,
        project=repo_root() / "examples/projects/mini-router",
        max_rounds=2,
        worldlines=2,
        out=out,
        workspace=ws,
        harness_root=tmp_path / "harness",
        keep_workspace=True,
        config=FakeCfg(),  # type: ignore[arg-type]
    )
    assert summary["success"] is True
    assert summary["task"] == "router"
    assert "mini-router" in summary["project"]
    sel = Path(summary["final_program"]).parent
    assert (sel / "table.aura").is_file()
    assert (sel / "match.aura").is_file()
    ep = json.loads(out.read_text(encoding="utf-8").strip().splitlines()[0])
    dog = ep["runtime"]["dogfood"]
    assert dog.get("multi_file") is True
    assert dog.get("files") == ["table.aura", "match.aura", "main.aura"]


def test_parser_fiber_explore_flags():
    help_text = build_parser().format_help()
    # Top-level -h truncates subparser flags; ask the subparser directly.
    dog_help = build_parser().parse_args  # noqa: keep import path warm
    import argparse
    p = build_parser()
    # Reach llm-dogfood subparser help
    for action in p._subparsers._group_actions:
        for name, sub in action.choices.items():
            if name == "llm-dogfood":
                dog_help = sub.format_help()
                break
    assert "--fiber-explore" in dog_help
    assert "--explore-tools" in dog_help
    assert "--agents" not in dog_help


def test_rule_tool_mini_cache():
    from aura_build.llm_dogfood import _tool_rule_sources, load_project_spec, repo_root

    spec = load_project_spec(repo_root() / "examples/projects/mini-cache")
    got = _tool_rule_sources(spec, prev_sources=None, prev_errors="TTL_EXPIRED sticky")
    assert got["ok"] is True
    assert "rule" in got["tools_used"]
    assert "cache-init" in got["sources"]["store.aura"]
    assert "cache-tick" in got["sources"]["ops.aura"]


def test_verify_prefers_session_over_verify_script(tmp_path, monkeypatch):
    """Hot serve path must run even when verify_script is present."""
    from aura_build import llm_dogfood as ld

    class FakeSess:
        harness_root = tmp_path

        def alive(self):
            return True

        def eval_source(self, source, timeout_s=5.0):
            return {
                "ok": True,
                "stdout": "GET_A=1\nGET_MISS=miss\nGET_B=2\nTTL_EXPIRED=miss\nCOUNT=2\n",
                "stderr": "",
                "ms": 3,
            }

    monkeypatch.setattr(
        "aura_build.serve_session.session_status",
        lambda **kw: {
            "serve_attach_ok": True,
            "serve_mode": "async",
            "serve_cross_session_shared_ast": True,
        },
    )
    cdir = tmp_path / "cand"
    cdir.mkdir()
    (cdir / "store.aura").write_text("(define (cache-init) #t)(define (cache-set key val ttl) #t)", encoding="utf-8")
    (cdir / "ops.aura").write_text("(define (cache-get key) \"1\")(define (cache-tick n) #t)", encoding="utf-8")
    (cdir / "main.aura").write_text("(cache-get \"a\")", encoding="utf-8")
    script = tmp_path / "verify.sh"
    script.write_text("#!/bin/bash\necho should_not_run\nexit 1\n", encoding="utf-8")
    script.chmod(0o755)
    import re
    got = ld.verify_aura_program(
        cdir / "main.aura",
        expect_re=[re.compile(r"GET_A\s*=\s*1"), re.compile(r"COUNT\s*=\s*2")],
        source_res=[re.compile(r"\(define\s+\(cache-init\b")],
        verify_script=script,
        candidate_dir=cdir,
        files=["store.aura", "ops.aura", "main.aura"],
        serve_session=FakeSess(),
        prefer_session=True,
        aura_bin="/bin/true",
    )
    assert got["via"] == "serve_session"
    assert got["cold_spawns"] == 0
    assert got["passed"] is True
