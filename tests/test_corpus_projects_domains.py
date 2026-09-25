"""Domain filter for the projects corpus burner (no network)."""

import pytest

from aura_build.corpus_projects import (
    BUSINESS_DOMAINS,
    domain_allowed,
    parse_domains,
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


def test_domain_allowed_filters_backlog():
    wal = {"slug": "mini-wal-x", "domain": "storage_wal"}
    cart = {"slug": "mini-cart-promotion-engine", "domain": "commerce"}
    assert domain_allowed(wal, None) and domain_allowed(cart, None)
    assert domain_allowed(cart, BUSINESS_DOMAINS)
    assert not domain_allowed(wal, BUSINESS_DOMAINS)
