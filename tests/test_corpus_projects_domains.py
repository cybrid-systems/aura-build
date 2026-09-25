"""Domain filter for the projects corpus burner (no network)."""

import pytest

from aura_build.corpus_projects import (
    BUSINESS_DOMAINS,
    aura_rel_file,
    domain_allowed,
    parse_domains,
    write_aura_source,
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


def test_domain_allowed_filters_backlog():
    wal = {"slug": "mini-wal-x", "domain": "storage_wal"}
    cart = {"slug": "mini-cart-promotion-engine", "domain": "commerce"}
    assert domain_allowed(wal, None) and domain_allowed(cart, None)
    assert domain_allowed(cart, BUSINESS_DOMAINS)
    assert not domain_allowed(wal, BUSINESS_DOMAINS)
