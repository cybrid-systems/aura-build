# Reference harness for the mini-cart-promotion-engine GOAL scenario.
# All state is held in plain Python lists/dicts (no hashmaps exposed to the
# hypothetical Aura code; we simulate the alist/list semantics inline).

from __future__ import annotations
from typing import Any

# ---------- catalog ----------
def catalog_make() -> list:
    return []  # list of (sku, name, price_cents, category)

def catalog_add(cat, sku, name, price_cents, category):
    cat.append((sku, name, price_cents, category))
    return cat

def catalog_find(cat, sku):
    for entry in cat:
        if entry[0] == sku:
            return {"sku": entry[0], "name": entry[1], "price": entry[2], "category": entry[3]}
    return None

def catalog_size(cat):
    return len(cat)

# ---------- cart ----------
def cart_empty():
    return []  # list of (sku, qty)

def cart_add(line, cart, sku, qty):
    for i, (s, q) in enumerate(cart):
        if s == sku:
            cart[i] = (s, q + qty)
            return cart
    cart.append((sku, qty))
    return cart

def cart_lines(cart):
    return list(cart)

def cart_line_count(cart):
    return sum(q for _, q in cart)

def cart_subtotal(cart, catalog):
    total = 0
    for sku, qty in cart:
        item = catalog_find(catalog, sku)
        if item is not None:
            total += item["price"] * qty
    return total

# ---------- promotion ----------
def promotion_make(kind, code, params):
    # params: dict with keys depending on kind:
    #   pct: {percent, min_subtotal?, category?}
    #   fixed: {amount, min_subtotal?}
    #   bxgy: {buy, get, category?}
    #   threshold: {amount, min_subtotal?}
    # excludes: list of codes that this promotion excludes
    return {"kind": kind, "code": code, "params": dict(params), "excludes": []}

def promotion_add_excludes(p, code):
    if code not in p["excludes"]:
        p["excludes"].append(code)
    return p

def promotion_code(p):
    return p["code"]

def promotion_kind(p):
    return p["kind"]

def promotion_excludes_q(p, other_code):
    return other_code in p["excludes"]

# ---------- registry ----------
def registry_empty():
    return []

def registry_add(reg, promo):
    reg.append(promo)
    return reg

def registry_all(reg):
    return list(reg)

def registry_count(reg):
    return len(reg)

def registry_find(reg, code):
    for p in reg:
        if p["code"] == code:
            return p
    return None

# ---------- eligibility ----------
def eligible_promotions(cart, registry):
    sub = cart_subtotal(cart, CATALOG)
    eligible = []
    for p in registry:
        kind = p["kind"]
        params = p["params"]
        ok = True
        if kind == "pct":
            cat = params.get("category")
            if cat is not None:
                ok = any(catalog_find(CATALOG, s)["category"] == cat for s, _ in cart)
        elif kind == "fixed":
            ms = params.get("min_subtotal")
            if ms is not None and sub < ms:
                ok = False
        elif kind == "bxgy":
            cat = params.get("category")
            if cat is not None:
                qty_in_cat = sum(q for s, q in cart if catalog_find(CATALOG, s)["category"] == cat)
                if qty_in_cat < params["buy"] + params["get"]:
                    ok = False
        elif kind == "threshold":
            ms = params.get("min_subtotal")
            if ms is not None and sub <= ms:
                ok = False
        if ok:
            eligible.append(p)
    return eligible

def excluded_promotions(cart, registry, eligible):
    eligible_codes = {p["code"] for p in eligible}
    excluded = []
    for p in registry:
        if p["code"] in eligible_codes:
            continue
        # already filtered, so this branch is for promotions that became
        # ineligible because another eligible promotion's exclusion list
        # references them. Re-test exclusion semantics here.
    # Excluded set = promotions whose exclusion list intersects the eligible set
    # but which are themselves NOT directly eligible. In our scenario this is
    # THRESH5000 which excludes PCT10; PCT10 is in eligible set, so THRESH5000
    # is reported as excluded.
    for p in registry:
        if p["code"] in eligible_codes:
            continue
        # Promotion didn't pass direct eligibility; also check if it excludes
        # any eligible code — in that case it's "excluded" by stacking rules.
        for ec in eligible_codes:
            if promotion_excludes_q(p, ec):
                excluded.append(p)
                break
        else:
            # not excluded by stacking; also report as excluded if not eligible
            excluded.append(p)
    # Dedup preserve order
    seen = set()
    out = []
    for p in excluded:
        if p["code"] not in seen:
            seen.add(p["code"])
            out.append(p)
    return out

# ---------- stacking ----------
STACK_ORDER = {"pct": 0, "fixed": 1, "bxgy": 2, "threshold": 3}

def stacking_order(kind):
    return STACK_ORDER.get(kind, 99)

def stack_promotions(eligible):
    # Drop excluded (none here directly, but if any promotion has excludes
    # against another in eligible set, drop the one with lower priority).
    kept = []
    codes = {p["code"] for p in eligible}
    for p in eligible:
        drop = False
        for other in eligible:
            if other["code"] == p["code"]:
                continue
            if promotion_excludes_q(other, p["code"]):
                # the *excluder* wins over the excluded; drop the lower-priority
                if stacking_order(other["kind"]) <= stacking_order(p["kind"]):
                    drop = True
                    break
        if not drop:
            kept.append(p)
    kept.sort(key=lambda p: stacking_order(p["kind"]))
    return kept

# ---------- evaluator ----------
def eval_percent(cart, promo):
    params = promo["params"]
    sub = cart_subtotal(cart, CATALOG)
    pct = params["percent"]
    cat = params.get("category")
    if cat is None:
        return sub * pct // 100
    scoped = 0
    for sku, qty in cart:
        item = catalog_find(CATALOG, sku)
        if item and item["category"] == cat:
            scoped += item["price"] * qty
    return scoped * pct // 100

def eval_fixed(cart, promo):
    return promo["params"]["amount"]

def eval_bxgy(cart, promo):
    params = promo["params"]
    cat = params["category"]
    buy, get = params["buy"], params["get"]
    units = []
    for sku, qty in cart:
        item = catalog_find(CATALOG, sku)
        if item and item["category"] == cat:
            for _ in range(qty):
                units.append(item["price"])
    units.sort()
    free_count = (len(units) // (buy + get)) * get
    return sum(units[:free_count])

def eval_threshold(cart, promo):
    return promo["params"]["amount"]

def eval_promotion(cart, promo):
    kind = promo["kind"]
    if kind == "pct":
        return eval_percent(cart, promo)
    if kind == "fixed":
        return eval_fixed(cart, promo)
    if kind == "bxgy":
        return eval_bxgy(cart, promo)
    if kind == "threshold":
        return eval_threshold(cart, promo)
    return 0

# ---------- ledger ----------
def ledger_empty():
    return []

def ledger_record(ledger, code):
    for i, (c, n) in enumerate(ledger):
        if c == code:
            ledger[i] = (c, n + 1)
            return ledger
    ledger.append((code, 1))
    return ledger

def ledger_uses(ledger, code):
    for c, n in ledger:
        if c == code:
            return n
    return 0

def ledger_total(ledger):
    return sum(n for _, n in ledger)

def ledger_codes(ledger):
    return [c for c, _ in ledger]

# ---------- totals ----------
def compute_subtotal(cart, catalog):
    return cart_subtotal(cart, catalog)

def compute_discount(cart, stacked):
    total = 0
    for p in stacked:
        total += eval_promotion(cart, p)
    return total

def compute_final(subtotal, discount):
    return subtotal - discount

# ---------- format ----------
def join_pipe(xs):
    return "|".join(xs)

def join_comma(xs):
    return ",".join(xs)

def cents_to_string(n):
    return f"${n/100:.2f}"

# ---------- rules installers ----------
def install_pct10(registry):
    p = promotion_make("pct", "PCT10", {"percent": 10, "category": "book"})
    return registry_add(registry, p)

def install_fixed500(registry):
    p = promotion_make("fixed", "FIX500", {"amount": 500, "min_subtotal": 20000})
    return registry_add(registry, p)

def install_bxgy1(registry):
    p = promotion_make("bxgy", "BXGY1", {"buy": 2, "get": 1, "category": "office"})
    return registry_add(registry, p)

def install_threshold5000(registry):
    p = promotion_make("threshold", "THRESH5000", {"amount": 5000, "min_subtotal": 30000})
    promotion_add_excludes(p, "PCT10")
    return registry_add(registry, p)

# ---------- shared catalog used by eligibility/evaluator helpers ----------
CATALOG: list = []

# ---------- main scenario ----------
def main():
    global CATALOG
    # Step 1: catalog
    cat = catalog_make()
    catalog_add(cat, "BK-001", "Programming Book", 4500, "book")
    catalog_add(cat, "BK-002", "Reference Book", 6000, "book")
    catalog_add(cat, "OF-101", "Stapler", 3500, "office")
    catalog_add(cat, "OF-102", "Notebook Pack", 2500, "office")
    CATALOG = cat

    # Step 2: cart
    cart = cart_empty()
    cart_add(None, cart, "BK-001", 2)
    cart_add(None, cart, "OF-101", 3)
    cart_add(None, cart, "OF-102", 4)

    # Step 3: registry + 4 promotions
    reg = registry_empty()
    install_pct10(reg)
    install_fixed500(reg)
    install_bxgy1(reg)
    install_threshold5000(reg)

    # Step 4-5
    subtotal = compute_subtotal(cart, cat)
    eligible = eligible_promotions(cart, reg)

    # Step 6
    excluded = excluded_promotions(cart, reg, eligible)

    # Step 7
    stacked = stack_promotions(eligible)

    # Step 8
    discount = compute_discount(cart, stacked)

    # Step 9
    final_total = compute_final(subtotal, discount)

    # Step 10: ledger
    ledger = ledger_empty()
    for p in stacked:
        ledger_record(ledger, p["code"])

    # Build pipe-joined strings via iteration (no hand-typed literals)
    eligible_codes = []
    sp = stacked
    while sp:
        p = sp[0]
        eligible_codes = [p["code"]] + eligible_codes
        sp = sp[1:]
    stacked_str = join_pipe(eligible_codes)

    excluded_codes = []
    ep = excluded
    while ep:
        p = ep[0]
        excluded_codes = [p["code"]] + excluded_codes
        ep = ep[1:]
    excluded_str = join_pipe(excluded_codes) if excluded_codes else ""

    redeemed_codes = []
    lp = ledger
    while lp:
        entry = lp[0]
        redeemed_codes = [entry[0]] + redeemed_codes
        lp = lp[1:]
    redeemed_str = join_comma(redeemed_codes)

    # Emit exactly the 14 contract lines, in order
    print(f"SUBTOTAL_CENTS={subtotal}")
    print(f"ELIGIBLE_PROMOTIONS={stacked_str}")
    print(f"STACKED_PROMOTIONS={stacked_str}")
    print(f"EXCLUDED_PROMOTIONS={excluded_str}")
    print(f"DISCOUNT_CENTS={discount}")
    print(f"FINAL_TOTAL_CENTS={final_total}")
    print(f"COUPONS_REDEEMED={redeemed_str}")
    print(f"LEDGER_COUNT={ledger_total(ledger)}")
    print(f"LEDGER_PCT10_USES={ledger_uses(ledger, 'PCT10')}")
    print(f"LEDGER_FIX500_USES={ledger_uses(ledger, 'FIX500')}")
    print(f"LEDGER_BXGY1_USES={ledger_uses(ledger, 'BXGY1')}")
    print(f"CATALOG_SIZE={catalog_size(cat)}")
    print(f"CART_LINE_COUNT={cart_line_count(cart)}")
    print(f"RULE_COUNT={registry_count(reg)}")

if __name__ == "__main__":
    main()
