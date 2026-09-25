#!/usr/bin/env python3
"""
mini-tax-rules-engine — Python reference port of the Aura scenario.

Implements toy in-memory semantics for the tax-rules engine:
- Hierarchical jurisdiction graph (Country -> State -> City)
- Rate resolution via path traversal
- Overrides (by priority) applied on top of base rates
- Exemptions (full or half) applied per line
- Per-line tax + invoice totals

Money is stored as cents internally; formatter rounds to 2dp.
"""

from __future__ import annotations
from typing import Any, Callable

# ---------------------------------------------------------------------------
# rates.aura  —  (make-rate code rate) / accessors / (add-rate alist r)
# ---------------------------------------------------------------------------

def make_rate(code: str, rate: float) -> dict:
    return {"code": code, "rate": rate}


def rate_code(r: dict) -> str:
    return r["code"]


def rate_value(r: dict) -> float:
    return r["rate"]


def add_rate(alist: list, r: dict) -> list:
    alist.append(r)
    return alist


# ---------------------------------------------------------------------------
# jurisdiction.aura  —  (make-jurisdiction code rate children) / accessors
#                         (jur-lookup graph code) / (jur-path graph code)
# ---------------------------------------------------------------------------

def make_jurisdiction(code: str, rate, children: list) -> dict:
    return {"code": code, "rate": rate, "children": children}


def jur_code(j: dict) -> str:
    return j["code"]


def jur_rate(j: dict):
    return j["rate"]


def jur_children(j: dict) -> list:
    return j["children"]


def jur_lookup(graph: list, code: str):
    """Return the jurisdiction dict whose code matches, or None."""
    stack = list(graph)
    while stack:
        node = stack.pop()
        if jur_code(node) == code:
            return node
        stack.extend(jur_children(node))
    return None


def jur_path(graph: list, code: str) -> list:
    """Return the list of jurisdictions on the path root -> target."""
    def walk(node, trail):
        new_trail = trail + [node]
        if jur_code(node) == code:
            return new_trail
        for child in jur_children(node):
            found = walk(child, new_trail)
            if found is not None:
                return found
        return None
    for root in graph:
        result = walk(root, [])
        if result is not None:
            return result
    return []


# ---------------------------------------------------------------------------
# override.aura  —  (make-override target-code field value priority) /
#                   accessors / (apply-overrides rules overrides)
# ---------------------------------------------------------------------------

def make_override(target_code: str, field: str, value, priority: int) -> dict:
    return {
        "target": target_code,
        "field": field,
        "value": value,
        "priority": priority,
    }


def ov_target(o: dict) -> str:
    return o["target"]


def ov_field(o: dict) -> str:
    return o["field"]


def ov_value(o: dict):
    return o["value"]


def ov_priority(o: dict) -> int:
    return o["priority"]


def apply_overrides(rules: dict, overrides: list) -> dict:
    """rules: {field: value, ...}; returns new dict with overrides merged."""
    out = dict(rules)
    applicable = [o for o in overrides if ov_field(o) in out]
    # highest priority last -> wins
    applicable.sort(key=lambda o: ov_priority(o))
    for o in applicable:
        out[ov_field(o)] = ov_value(o)
    return out


# ---------------------------------------------------------------------------
# exemption.aura  —  (make-exemption code kind amount predicates) /
#                     accessors / (apply-exemptions line taxable exemptions)
# ---------------------------------------------------------------------------

def make_exemption(code: str, kind: str, amount, predicates: dict) -> dict:
    return {"code": code, "kind": kind, "amount": amount, "preds": predicates}


def ex_code(e: dict) -> str:
    return e["code"]


def ex_kind(e: dict) -> str:
    return e["kind"]


def ex_amount(e: dict):
    return e["amount"]


def ex_matches(e: dict, line: dict) -> bool:
    """Check whether an exemption's predicates match a line."""
    preds = e["preds"]
    for k, v in preds.items():
        if k == "category":
            if line.get("category") != v:
                return False
        elif k == "exempt":
            # explicit flag
            if bool(line.get("exempt", False)) != bool(v):
                return False
        else:
            if line.get(k) != v:
                return False
    return True


def apply_exemptions(line: dict, taxable: float, exemptions: list) -> tuple:
    """
    Return (taxable_after_exemption, total_exemption_amount, applied_count).
    Each matching exemption subtracts its amount (full) or half (half).
    """
    applied = [e for e in exemptions if ex_matches(e, line)]
    total_ex = 0.0
    for e in applied:
        kind = ex_kind(e)
        amt = ex_amount(e)
        if kind == "full":
            total_ex += amt
        elif kind == "half":
            total_ex += amt * 0.5
        else:
            total_ex += amt
    new_taxable = max(taxable - total_ex, 0.0)
    return new_taxable, total_ex, len(applied)


# ---------------------------------------------------------------------------
# rules.aura  —  (make-rule jur-code rate) / accessors / (merge-rules a b)
# ---------------------------------------------------------------------------

def make_rule(jur_code_: str, rate) -> dict:
    return {"jur": jur_code_, "rate": rate}


def rule_jur(r: dict) -> str:
    return r["jur"]


def rule_rate(r: dict):
    return r["rate"]


def merge_rules(a: dict, b: dict) -> dict:
    return {"jur": b["jur"], "rate": b["rate"]}


# ---------------------------------------------------------------------------
# resolver.aura  —  (resolve-rate graph code overrides) /
#                   (applicable-rate graph target-code overrides)
# ---------------------------------------------------------------------------

def resolve_rate(graph: list, code: str, overrides: list) -> dict:
    """
    Walk the path to `code`, sum rates along the way, then apply overrides.
    Returned dict contains:
      - 'base': summed base rate
      - 'effective': rate after overrides
      - 'components': {field: value, ...} for each jurisdiction on the path
      - 'path': [jur-dicts]
    """
    path = jur_path(graph, code)
    components = {}
    base = 0.0
    for j in path:
        field = f"{jur_code(j)}_RATE"
        components[field] = jur_rate(j)
        base += jur_rate(j)
    rules = {"BASE": base, **components}
    effective_dict = apply_overrides(rules, overrides)
    effective = effective_dict.get("BASE", base)
    return {
        "base": base,
        "effective": effective,
        "components": components,
        "path": path,
    }


def applicable_rate(graph: list, target_code: str, overrides: list) -> float:
    return resolve_rate(graph, target_code, overrides)["effective"]


# ---------------------------------------------------------------------------
# line.aura  —  (make-line id qty unit-price category exempt?) /
#               (line-amount l) / (line-tax l rate taxable) / (line-display l tax)
# ---------------------------------------------------------------------------

def make_line(line_id, qty, unit_price, category: str, exempt: bool = False) -> dict:
    return {
        "id": line_id,
        "qty": qty,
        "unit_price": unit_price,
        "category": category,
        "exempt": exempt,
    }


def line_amount(l: dict) -> float:
    return l["qty"] * l["unit_price"]


def line_tax(l: dict, rate: float, taxable: float) -> float:
    return taxable * rate


def line_display(l: dict, tax: float) -> str:
    return f"line:{l['id']} tax={tax:.2f}"


# ---------------------------------------------------------------------------
# invoice.aura  —  (make-invoice lines jur-code) / accessors / (add-line inv ln)
# ---------------------------------------------------------------------------

def make_invoice(lines: list, jur_code_: str) -> dict:
    return {"lines": list(lines), "jur": jur_code_}


def inv_lines(inv: dict) -> list:
    return inv["lines"]


def inv_jur(inv: dict) -> str:
    return inv["jur"]


def add_line(inv: dict, ln: dict) -> dict:
    inv["lines"].append(ln)
    return inv


# ---------------------------------------------------------------------------
# compute.aura  —  (compute-line-tax line rate exemptions)
#                 (compute-invoice invoice graph overrides exemptions)
# ---------------------------------------------------------------------------

def compute_line_tax(line: dict, rate: float, exemptions: list) -> dict:
    amount = line_amount(line)
    taxable, ex_amount_, applied = apply_exemptions(line, amount, exemptions)
    tax = taxable * rate
    return {
        "line": line,
        "amount": amount,
        "exemption": ex_amount_,
        "applied": applied,
        "taxable": taxable,
        "tax": tax,
    }


def compute_invoice(invoice: dict, graph: list, overrides: list, exemptions: list) -> dict:
    jur_code_ = inv_jur(invoice)
    rate_info = resolve_rate(graph, jur_code_, overrides)
    effective = rate_info["effective"]
    line_results = [compute_line_tax(l, effective, exemptions)
                    for l in inv_lines(invoice)]
    subtotal = sum(r["amount"] for r in line_results)
    tax_total = sum(r["tax"] for r in line_results)
    grand = subtotal + tax_total
    total_exemptions = sum(r["applied"] for r in line_results)
    return {
        "rate_info": rate_info,
        "line_results": line_results,
        "subtotal": subtotal,
        "tax_total": tax_total,
        "grand_total": grand,
        "exemptions_applied": total_exemptions,
    }


# ---------------------------------------------------------------------------
# format.aura  —  (fmt-money n)  → string rounded to 2dp
# ---------------------------------------------------------------------------

def fmt_money(n) -> str:
    return f"{round(float(n), 2):.2f}"


# ---------------------------------------------------------------------------
# sample.aura  —  builders for the demo graph / overrides / exemptions / invoice
# ---------------------------------------------------------------------------

def sample_graph() -> list:
    """
    US (0.00) -> CA (0.05) -> SF (0.075), NYC (0.04)
              -> NY (0.04) -> NYC (0.04)
    Also a District (0.01) under SF to match the "0.135" hint
    (0.05 + 0.075 + 0.01 = 0.135).
    """
    sf = make_jurisdiction("SF", 0.075, [
        make_jurisdiction("SOMA", 0.01, []),
    ])
    ca = make_jurisdiction("CA", 0.05, [sf])
    nyc = make_jurisdiction("NYC", 0.04, [])
    ny = make_jurisdiction("NY", 0.04, [nyc])
    us = make_jurisdiction("US", 0.0, [ca, ny])
    return [us]


def sample_overrides() -> list:
    """Override SF's CITY_RATE field with a different value (priority 10)."""
    return [
        make_override("SF", "CITY_RATE", 0.085, 10),
        make_override("SOMA", "DISTRICT_RATE", 0.01, 5),
    ]


def sample_exemptions() -> list:
    return [
        make_exemption("FOOD_FULL", "full", 50.0, {"category": "FOOD"}),
        make_exemption("BOOKS_HALF", "half", 20.0, {"category": "BOOKS"}),
        make_exemption("MEDICINE_FULL", "full", 100.0, {"category": "MEDICINE"}),
    ]


def sample_invoice() -> dict:
    inv = make_invoice([], "SF")
    add_line(inv, make_line("L0", 2, 100.00, "FOOD", False))      # amt 200
    add_line(inv, make_line("L1", 1,  50.00, "BOOKS", False))     # amt 50
    add_line(inv, make_line("L2", 3,  30.00, "ELECTRONICS", False))  # amt 90
    add_line(inv, make_line("L3", 1, 500.00, "MEDICINE", False))  # amt 500
    return inv


# ---------------------------------------------------------------------------
# main.aura  —  scenario driver (port)
# ---------------------------------------------------------------------------

def main():
    graph = sample_graph()
    overrides = sample_overrides()
    exemptions = sample_exemptions()
    invoice = sample_invoice()

    result = compute_invoice(invoice, graph, overrides, exemptions)
    ri = result["rate_info"]
    path = ri["path"]

    # Pick a representative node per level from the path
    country = path[0]
    state = path[1] if len(path) > 1 else country
    city = path[2] if len(path) > 2 else state

    print(f"COUNTRY_CODE={jur_code(country)}")
    print(f"COUNTRY_RATE={fmt_money(jur_rate(country))}")
    print(f"STATE_CODE={jur_code(state)}")
    print(f"STATE_RATE={fmt_money(jur_rate(state))}")
    print(f"CITY_CODE={jur_code(city)}")
    print(f"CITY_RATE={fmt_money(jur_rate(city))}")
    print(f"EFFECTIVE_RATE={fmt_money(ri['effective'])}")
    print(f"EXEMPTIONS_APPLIED={result['exemptions_applied']}")
    print(f"LINE_COUNT={len(result['line_results'])}")
    print(f"SUBTOTAL={fmt_money(result['subtotal'])}")
    print(f"TAX_TOTAL={fmt_money(result['tax_total'])}")
    print(f"GRAND_TOTAL={fmt_money(result['grand_total'])}")
    for i, lr in enumerate(result["line_results"]):
        key = f"LINE_{i}_TAX"
        print(f"{key}={fmt_money(lr['tax'])}")


if __name__ == "__main__":
    main()
