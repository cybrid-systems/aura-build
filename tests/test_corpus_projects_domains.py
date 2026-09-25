"""Domain filter for the projects corpus burner (no network)."""

import pytest

import json

from aura_build.corpus_projects import (
    BUSINESS_DOMAINS,
    ProjectBurnConfig,
    aura_rel_file,
    domain_allowed,
    parse_domains,
    project_needs_work,
    sanitize_python_ref,
    write_aura_source,
    write_project_verify,
)


def test_parse_domains_business_alias():
    assert parse_domains("business") == BUSINESS_DOMAINS
    assert parse_domains("biz") == BUSINESS_DOMAINS
    assert parse_domains(None) is None
    assert parse_domains("all") is None
    assert parse_domains("commerce,ledgers") == ("commerce", "ledgers")


def test_parse_domains_rejects_unknown():
    with pytest.raises(SystemExit):
        parse_domains("commerce,not-a-domain")


def test_write_nested_aura_file(tmp_path):
    dest = write_aura_source(tmp_path, "rules/aura_rules_pct.aura", "(define x 1)\n")
    assert dest.is_file()
    assert dest.parent.name == "rules"
    with pytest.raises(ValueError):
        aura_rel_file("../escape.aura")


def test_sanitize_python_ref_fence_and_predicate():
    raw = "```python run_scenarios.py\ndef token_kind?(t, k):\n    print('A=1')\n```\n"
    out = sanitize_python_ref(raw)
    assert out.startswith("def token_kind_p(t, k):")
    assert "```" not in out
    assert "token_kind?" not in out


def test_ref_attempt_cap_skips_repeat_failure(tmp_path):
    slug = "mini-example"
    pdir = tmp_path / slug
    pdir.mkdir()
    (pdir / "GOAL.md").write_text("# goal\n", encoding="utf-8")
    (pdir / "meta.json").write_text(
        json.dumps({"ref_attempts": 2, "variants": []}),
        encoding="utf-8",
    )
    bc = ProjectBurnConfig(
        corpus_dir=tmp_path,
        scratch=tmp_path,
        run_log=tmp_path / "run_log.jsonl",
        aura_bin="aura",
        env_file=None,
    )
    assert project_needs_work({"slug": slug, "domain": "commerce"}, bc) is False


def test_write_project_verify_embeds_expect(tmp_path):
    path = write_project_verify(
        tmp_path,
        ["rates.aura", "main.aura"],
        "TAX=1\nOK=1\nCOUNT=2\n",
    )
    assert path is not None and path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "rates.aura" in text and "main.aura" in text
    assert "TAX" in text and "AURA_SANDBOX" in text


def test_domain_allowed_filters_backlog():
    wal = {"slug": "mini-wal-x", "domain": "storage_wal"}
    cart = {"slug": "mini-cart-promotion-engine", "domain": "commerce"}
    assert domain_allowed(wal, None) and domain_allowed(cart, None)
    assert domain_allowed(cart, BUSINESS_DOMAINS)
    assert not domain_allowed(wal, BUSINESS_DOMAINS)
