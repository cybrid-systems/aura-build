#!/usr/bin/env python3
"""
Mini Tax Jurisdiction Engine — Python reference implementation.

This single-file script mirrors the Aura multi-file project described in
GOAL.md.  All "facts" are in-memory data structures, and each Aura `api`
function is implemented as a plain Python function in the same module.
The `run()` orchestrator prints exactly the 14 KEY=value lines required by
the stdout contract.
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. facts_nexus
# ---------------------------------------------------------------------------
NEXUS_RULES: List[Dict[str, Any]] = [
    # origin-based states (seller collects no destination sales tax)
    {"state": "OR", "origin_based": True,
     "county": "*", "city": "*", "jid": "OR-NONE"},
    {"state": "NH", "origin_based": True,
     "county": "*", "city": "*", "jid": "NH-NONE"},
    # destination-based nexus examples
    {"state": "CA", "origin_based": False,
     "county": "Los Angeles", "city": "*", "jid": "CA-LA"},
    {"state": "CA", "origin_based": False,
     "county": "San Diego", "city": "*", "jid": "CA-SD"},
    {"state": "TX", "origin_based": False,
     "county": "*", "city": "Austin", "jid": "TX-AUS"},
    {"state": "NY", "origin_based": False,
     "county": "Kings", "city": "Brooklyn", "jid": "NY-BK"},
    {"state": "WA", "origin_based": False,
     "county": "King", "city": "Seattle", "jid": "WA-SEA"},
]


def load_nexus_rules() -> List[Dict[str, Any]]:
    return [dict(r) for r in NEXUS_RULES]


# ---------------------------------------------------------------------------
# 2. facts_products
# ---------------------------------------------------------------------------
PRODUCT_TAX_CODES: Dict[str, str] = {
    "PTC-GROCERY":   "groceries",
    "PTC-APPAREL":   "apparel",
    "PTC-DIGITAL":   "digital",
    "PTC-SAAS":      "saas",
    "PTC-TANGIBLE":  "tangible",
}


def load_product_tax_codes() -> Dict[str, str]:
    return dict(PRODUCT_TAX_CODES)


# ---------------------------------------------------------------------------
# 3. facts_exemptions
# ---------------------------------------------------------------------------
EXEMPTION_CERTS: List[Dict[str, Any]] = [
    {"cert_id": "CERT-RESALE-CA-LA",
     "jid": "CA-LA", "category": "*", "reason": "RESALE"},
    {"cert_id": "CERT-NONPROFIT-WA-SEA",
     "jid": "WA-SEA", "category": "*", "reason": "NONPROFIT_501C3"},
    {"cert_id": "CERT-GOV-NY-BK",
     "jid": "NY-BK", "category": "tangible", "reason": "GOVERNMENT"},
]


def load_exemption_certs() -> List[Dict[str, Any]]:
    return [dict(c) for c in EXEMPTION_CERTS]


# ---------------------------------------------------------------------------
# 4. facts_jurisdictions
# ---------------------------------------------------------------------------
JURISDICTION_RATES: Dict[str, int] = {
    # rates in basis points (1 bps = 0.01%). 10000 bps = 100%
    "OR-NONE":     0,
    "NH-NONE":     0,
    "CA-LA":     975,   # 9.75%
    "CA-SD":     825,
    "TX-AUS":   1013,   # 8.25% state + ~1.875% local
    "NY-BK":    1010,   # 8.875% NYC + Kings
    "WA-SEA":   1070,   # 6.5% state + 3.6% local
}


def load_jurisdiction_rates() -> Dict[str, int]:
    return dict(JURISDICTION_RATES)


# ---------------------------------------------------------------------------
# 5. facts_customers
# ---------------------------------------------------------------------------
CUSTOMER: Dict[str, Any] = {
    "customer_id": "CUST-001",
    "ship_to": {
        "state": "CA",
        "county": "Los Angeles",
        "city": "Los Angeles",
    },
    "exemption_cert_ids": ["CERT-RESALE-CA-LA"],
}


def load_customer() -> Dict[str, Any]:
    return {
        "customer_id": CUSTOMER["customer_id"],
        "ship_to": dict(CUSTOMER["ship_to"]),
        "exemption_cert_ids": list(CUSTOMER["exemption_cert_ids"]),
    }


# ---------------------------------------------------------------------------
# 6. facts_invoice
# ---------------------------------------------------------------------------
INVOICE: Dict[str, Any] = {
    "invoice_id": "INV-2026-0001",
    "lines": [
        # line_id, ptc, qty, unit_price_cents, ship_to override (optional)
        {"line_id": "L1", "ptc": "PTC-GROCERY",  "qty": 3, "unit_price_cents": 1299},
        {"line_id": "L2", "ptc": "PTC-APPAREL",  "qty": 2, "unit_price_cents": 4999},
        {"line_id": "L3", "ptc": "PTC-DIGITAL",  "qty": 1, "unit_price_cents": 1999},
        {"line_id": "L4", "ptc": "PTC-SAAS",     "qty": 1, "unit_price_cents": 9900},
        {"line_id": "L5", "ptc": "PTC-TANGIBLE", "qty": 1, "unit_price_cents": 2500},
        # ship_to override → origin-based OR (no destination tax)
        {"line_id": "L6", "ptc": "PTC-TANGIBLE", "qty": 4, "unit_price_cents": 1500,
         "ship_to": {"state": "OR", "county": "*", "city": "*"}},
        # ship_to override → WA Seattle, customer carries nonprofit cert
        {"line_id": "L7", "ptc": "PTC-SAAS",     "qty": 1, "unit_price_cents": 5000,
         "ship_to": {"state": "WA", "county": "King", "city": "Seattle"}},
        # ship_to override → NH origin-based
        {"line_id": "L8", "ptc": "PTC-APPAREL",  "qty": 1, "unit_price_cents": 3500,
         "ship_to": {"state": "NH", "county": "*", "city": "*"}},
    ],
}


def load_invoice() -> Dict[str, Any]:
    lines = []
    for ln in INVOICE["lines"]:
        d = {"line_id": ln["line_id"], "ptc": ln["ptc"],
             "qty": ln["qty"], "unit_price_cents": ln["unit_price_cents"]}
        if "ship_to" in ln:
            d["ship_to"] = dict(ln["ship_to"])
        lines.append(d)
    return {"invoice_id": INVOICE["invoice_id"], "lines": lines}


# ---------------------------------------------------------------------------
# 7. resolve_jurisdiction
# ---------------------------------------------------------------------------
def resolve_jurisdiction(ship_to: Dict[str, Any],
                         nexus: List[Dict[str, Any]]) -> Optional[str]:
    """Pick a nexus rule matching the ship-to; prefer most specific (city > county > state)."""
    candidates = []
    for r in nexus:
        if r["state"] != ship_to.get("state"):
            continue
        county_match = (r["county"] == "*" or r["county"] == ship_to.get("county"))
        city_match = (r["city"] == "*" or r["city"] == ship_to.get("city"))
        if county_match and city_match:
            # specificity score: exact city > exact county > star
            score = (0 if r["city"] == "*" else 2) + (0 if r["county"] == "*" else 1)
            candidates.append((score, r["jid"]))
    if not candidates:
        return None
    candidates.sort(key=lambda t: -t[0])
    return candidates[0][1]


# ---------------------------------------------------------------------------
# 8. apply_exemption
# ---------------------------------------------------------------------------
def apply_exemption(jid: Optional[str],
                    certs: List[Dict[str, Any]],
                    ptc: str,
                    product_categories: Dict[str, str]) -> Tuple[bool, str]:
    """Returns (is_exempt, reason). cert may cover jid + matching category."""
    if jid is None:
        return False, ""
    ptc_cat = product_categories.get(ptc, "tangible")
    for c in certs:
        if c["jid"] == jid:
            if c["category"] == "*" or c["category"] == ptc_cat:
                return True, c["reason"]
    return False, ""


# ---------------------------------------------------------------------------
# 10. round_money
# ---------------------------------------------------------------------------
def round_line(cents: float) -> int:
    """Half-even (banker's) rounding for per-line amounts."""
    import math
    floored = math.floor(cents)
    diff = cents - floored
    if abs(diff) < 1e-9:
        return floored
    # exactly .5
    if abs(diff - 0.5) < 1e-9:
        if floored % 2 == 0:
            return floored
        return floored + 1
    if diff > 0.5:
        return floored + 1
    return floored


def round_invoice(cents: float) -> int:
    """Half-up rounding for the final invoice total."""
    import math
    if cents >= 0:
        return math.floor(cents + 0.5)
    return -math.floor(-cents + 0.5)


# ---------------------------------------------------------------------------
# 11. audit_log
# ---------------------------------------------------------------------------
_AUDIT_LOG: List[Dict[str, Any]] = []


def append_line_log(line_breakdown: Dict[str, Any]) -> None:
    _AUDIT_LOG.append(dict(line_breakdown))


def _mix64(state: int, s: str) -> int:
    h = hashlib.sha256(s.encode("utf-8")).digest()
    chunk = int.from_bytes(h[:8], "big")
    state ^= chunk
    state = (state * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF  # FNV-1a prime
    state ^= (state >> 33)
    state = (state * 0xff51afd7ed558ccd) & 0xFFFFFFFFFFFFFFFF
    state ^= (state >> 33)
    return state


def make_audit_hash(breakdowns: List[Dict[str, Any]]) -> str:
    state = 0xcbf29ce484222325 & 0xFFFFFFFFFFFFFFFF
    for bd in breakdowns:
        canon = json.dumps(bd, sort_keys=True, separators=(",", ":"))
        state = _mix64(state, canon)
    return f"{state:016x}"


# ---------------------------------------------------------------------------
# 9. compute_line_tax
# ---------------------------------------------------------------------------
def compute_line_tax(line: Dict[str, Any],
                     nexus: List[Dict[str, Any]],
                     rates: Dict[str, int],
                     certs: List[Dict[str, Any]],
                     origin_states: List[str],
                     product_categories: Dict[str, str]
                     ) -> Dict[str, Any]:
    ptc = line["ptc"]
    qty = line["qty"]
    unit = line["unit_price_cents"]
    ship_to = line.get("ship_to") or CUSTOMER["ship_to"]

    jid = resolve_jurisdiction(ship_to, nexus)
    state = ship_to.get("state", "")

    breakdown: Dict[str, Any] = OrderedDict()
    breakdown["line_id"] = line["line_id"]
    breakdown["ptc"] = ptc
    breakdown["ship_to"] = dict(ship_to)
    breakdown["jid"] = jid

    line_subtotal = unit * qty
    breakdown["subtotal_cents"] = line_subtotal

    # No nexus at all
    if jid is None:
        breakdown["status"] = "NO_NEXUS"
        breakdown["rate_bps"] = 0
        breakdown["raw_tax_cents"] = 0.0
        breakdown["rounded_tax_cents"] = 0
        breakdown["reason"] = "NO_NEXUS"
        breakdown["taxable"] = False
        breakdown["exempt"] = False
        append_line_log(breakdown)
        return breakdown

    # Origin-based override: no tax collected
    if state in origin_states:
        breakdown["status"] = "EXEMPT" if state in origin_states and rates.get(jid, 0) == 0 else "OK"
        breakdown["status"] = "ZERO_RATE"
        breakdown["rate_bps"] = rates.get(jid, 0)
        breakdown["raw_tax_cents"] = 0.0
        breakdown["rounded_tax_cents"] = 0
        breakdown["reason"] = "ORIGIN_BASED"
        breakdown["taxable"] = False
        breakdown["exempt"] = True
        append_line_log(breakdown)
        return breakdown

    # Exemption certificate?
    is_exempt, reason = apply_exemption(jid, certs, ptc, product_categories)
    rate_bps = rates.get(jid, 0)

    if is_exempt:
        breakdown["status"] = "EXEMPT"
        breakdown["rate_bps"] = rate_bps
        breakdown["raw_tax_cents"] = 0.0
        breakdown["rounded_tax_cents"] = 0
        breakdown["reason"] = "EXEMPT_CERT:" + reason
        breakdown["taxable"] = False
        breakdown["exempt"] = True
        append_line_log(breakdown)
        return breakdown

    # Normal taxable computation
    if rate_bps == 0:
        breakdown["status"] = "ZERO_RATE"
        breakdown["rate_bps"] = 0
        breakdown["raw_tax_cents"] = 0.0
        breakdown["rounded_tax_cents"] = 0
        breakdown["reason"] = "ZERO_RATE"
        breakdown["taxable"] = False
        breakdown["exempt"] = False
        append_line_log(breakdown)
        return breakdown

    raw_tax = (line_subtotal * rate_bps) / 10000.0
    rounded = round_line(raw_tax)
    breakdown["status"] = "OK"
    breakdown["rate_bps"] = rate_bps
    breakdown["raw_tax_cents"] = raw_tax
    breakdown["rounded_tax_cents"] = rounded
    breakdown["reason"] = "TAXED"
    breakdown["taxable"] = True
    breakdown["exempt"] = False
    append_line_log(breakdown)
    return breakdown


# ---------------------------------------------------------------------------
# 12. invoice_aggregate
# ---------------------------------------------------------------------------
def aggregate_invoice(line_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    taxable_lines = sum(1 for r in line_results if r.get("taxable"))
    exempt_lines = sum(1 for r in line_results if r.get("exempt"))
    zero_lines = sum(1 for r in line_results
                     if (not r.get("taxable")) and (not r.get("exempt"))
                     and r.get("status") in ("NO_NEXUS", "ZERO_RATE"))
    subtotal = sum(r["subtotal_cents"] for r in line_results)
    tax_total = sum(r["rounded_tax_cents"] for r in line_results)
    jurisdictions = sorted({r["jid"] for r in line_results if r.get("jid")})
    certs_applied = sorted({
        bd.split(":", 1)[1]
        for r in line_results for bd in [r.get("reason", "")]
        if bd.startswith("EXEMPT_CERT:")
    })
    origin_based = sum(1 for r in line_results if r.get("reason") == "ORIGIN_BASED")
    destination_based = sum(
        1 for r in line_results
        if r.get("status") == "OK" and r.get("reason") == "TAXED"
    )
    return {
        "taxable_lines": taxable_lines,
        "exempt_lines": exempt_lines,
        "zero_tax_lines": zero_lines,
        "subtotal_cents": subtotal,
        "tax_total_cents_raw": tax_total,
        "jurisdictions_resolved": jurisdictions,
        "exemption_certs_applied": certs_applied,
        "origin_based_lines": origin_based,
        "destination_based_lines": destination_based,
    }


# ---------------------------------------------------------------------------
# 13. main orchestrator
# ---------------------------------------------------------------------------
def run() -> None:
    # 1. load facts
    nexus = load_nexus_rules()
    ptcs = load_product_tax_codes()
    certs = load_exemption_certs()
    rates = load_jurisdiction_rates()
    customer = load_customer()
    invoice = load_invoice()

    # 2. derive origin-states once
    origin_states = [r["state"] for r in nexus if r.get("origin_based")]

    # 3+4. per-line resolver
    line_results: List[Dict[str, Any]] = []
    for ln in invoice["lines"]:
        result = compute_line_tax(ln, nexus, rates, certs, origin_states, ptcs)
        line_results.append(result)

    # 5. aggregate
    agg = aggregate_invoice(line_results)

    # 6. round invoice tax total + grand total
    tax_total = round_invoice(agg["tax_total_cents_raw"])
    grand_total = agg["subtotal_cents"] + tax_total

    # 7. audit hash (also exercises the global log via make-audit-hash)
    audit_hash = make_audit_hash(_AUDIT_LOG)

    # 8/9. resolution_ok sanity gate
    OK_STATUSES = {"OK", "EXEMPT", "ZERO_RATE", "NO_NEXUS"}
    resolution_ok = all(r.get("status") in OK_STATUSES for r in line_results)

    # 9. print exactly the 14 KEY=value lines, in the required order
    print(f"INVOICE_ID={invoice['invoice_id']}")
    print(f"LINE_COUNT={len(invoice['lines'])}")
    print(f"TAXABLE_LINES={agg['taxable_lines']}")
    print(f"EXEMPT_LINES={agg['exempt_lines']}")
    print(f"ZERO_TAX_LINES={agg['zero_tax_lines']}")
    print(f"SUBTOTAL_CENTS={agg['subtotal_cents']}")
    print(f"TAX_TOTAL_CENTS={tax_total}")
    print(f"GRAND_TOTAL_CENTS={grand_total}")
    print(f"JURISDICTIONS_RESOLVED={','.join(agg['jurisdictions_resolved']) or 'NONE'}")
    print(f"EXEMPTION_CERTS_APPLIED={','.join(agg['exemption_certs_applied']) or 'NONE'}")
    print(f"ORIGIN_BASED_LINES={agg['origin_based_lines']}")
    print(f"DESTINATION_BASED_LINES={agg['destination_based_lines']}")
    print(f"AUDIT_HASH={audit_hash}")
    print(f"RESOLUTION_OK={'#t' if resolution_ok else '#f'}")


if __name__ == "__main__":
    run()
