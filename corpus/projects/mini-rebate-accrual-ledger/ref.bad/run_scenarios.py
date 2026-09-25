```python run_scenarios.py
#!/usr/bin/env python3
"""
Mini-rebate-accrual-ledger reference implementation in Python 3.

This is a toy in-memory re-implementation of the Aura GOAL.md scenario:
a rebate accrual engine with retroactive true-ups, dispute holdbacks,
paid-in-advance vs arrears reconciliation, and a subledger.

It mirrors the 14-module Aura project using only stdlib + lists/alists/dicts.
The semantics are simplified but structurally aligned with the spec:
- util          -> kv alist helpers + sum/round2
- hierarchy     -> customer tree + aggregate-attribute
- tiers         -> tier table + qualification/rate/bonus
- sales         -> event log + total-volume + growth-vs-prior
- promotions    -> promo predicate + amount
- retro         -> retro window/qualify/bonus-rate
- disputes      -> open-dispute + holdback + release
- accruals      -> volume/growth/promo accruals + gross + semantic-mode
- trueups       -> trueup-due? + post-trueup + advance-vs-accrued
- subledger     -> init/debit/credit/balance/lines
- seed-*        -> small seed datasets
- main          -> orchestrates and prints the 12 KEY=value lines

Only data structures used: lists, dicts, numbers, strings, tuples.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

# ---------------------------------------------------------------------------
# lib/util.aura  --  alist-backed KV helpers + sum / round2
# ---------------------------------------------------------------------------

ROUND_NDIGITS = 2


def make_kv() -> list:
    """Return an empty association list."""
    return []


def kv_put(kv: list, key: str, value: Any) -> list:
    """Set key=value, replacing any prior binding. Returns the (mutated) kv."""
    out = []
    replaced = False
    for k, v in kv:
        if k == key:
            out.append((k, value))
            replaced = True
        else:
            out.append((k, v))
    if not replaced:
        out.append((key, value))
    return out


def kv_get(kv: list, key: str, default: Any = None) -> Any:
    for k, v in kv:
        if k == key:
            return v
    return default


def kv_keys(kv: list) -> list:
    return [k for k, _ in kv]


def sum_vals(values: list) -> float:
    total = 0.0
    for v in values:
        total += float(v)
    return total


def round2(x: float) -> float:
    return round(float(x), ROUND_NDIGITS)


# ---------------------------------------------------------------------------
# lib/hierarchy.aura  --  customer tree built from (cust-id . parent) pairs
# ---------------------------------------------------------------------------


def build_hierarchy(customers: list) -> dict:
    """
    Input: list of (cust_id, parent_id_or_None, attrs_dict) tuples.
    Output: dict with:
        'roots'   -> list of root cust_ids
        'children'-> dict cust_id -> list of child cust_ids
        'descendants' -> dict cust_id -> list of all descendants (BFS)
        'attrs'   -> dict cust_id -> attrs_dict
        'all'     -> list of cust_ids in insertion order
    """
    children: dict = {}
    attrs: dict = {}
    all_ids: list = []
    parent_of: dict = {}

    for cust_id, parent_id, attr in customers:
        all_ids.append(cust_id)
        attrs[cust_id] = dict(attr) if attr else {}
        parent_of[cust_id] = parent_id
        children.setdefault(cust_id, [])
        children.setdefault(parent_id, []).append(cust_id) if parent_id else None

    # Fix: build children cleanly without leaking None key.
    children = {}
    for cust_id in all_ids:
        children[cust_id] = []
    for cust_id, parent_id, _ in customers:
        if parent_id is not None:
            children.setdefault(parent_id, []).append(cust_id)
        else:
            children.setdefault(cust_id, [])

    roots = [c for c, p, _ in customers if p is None]

    descendants: dict = {}

    def _desc(node: str) -> list:
        if node in descendants:
            return descendants[node]
        out = []
        for ch in children.get(node, []):
            out.append(ch)
            out.extend(_desc(ch))
        descendants[node] = out
        return out

    for c in all_ids:
        _desc(c)

    return {
        "roots": roots,
        "children": children,
        "descendants": descendants,
        "attrs": attrs,
        "all": all_ids,
    }


def descendants_of(hier: dict, cust_id: str) -> list:
    return list(hier["descendants"].get(cust_id, []))


def aggregate_attribute(hier: dict, cust_id: str, attr: str) -> float:
    """Sum `attr` across cust_id + all descendants (0.0 if missing)."""
    total = 0.0
    ids = [cust_id] + descendants_of(hier, cust_id)
    for cid in ids:
        a = hier["attrs"].get(cid, {})
        v = a.get(attr, 0)
        try:
            total += float(v)
        except (TypeError, ValueError):
            pass
    return total


# ---------------------------------------------------------------------------
# lib/tiers.aura  --  tier table
# ---------------------------------------------------------------------------


def make_tier_table(rows: list) -> list:
    """
    rows: list of dicts with keys
        'program', 'tier_name', 'min_volume', 'rebate_rate', 'bonus'
    Sorted ascending by min_volume; returned as list-of-dicts.
    """
    return sorted(rows, key=lambda r: float(r["min_volume"]))


def tier_qualifies(tiers: list, program: str, volume: float) -> bool:
    """True if volume meets the lowest min_volume threshold for that program."""
    relevant = [t for t in tiers if t["program"] == program]
    if not relevant:
        return False
    return volume >= float(min(t["min_volume"] for t in relevant))


def tier_rebate_rate(tiers: list, program: str, volume: float) -> float:
    """Return the highest qualifying rebate rate for (program, volume)."""
    applicable = [
        t for t in tiers
        if t["program"] == program and volume >= float(t["min_volume"])
    ]
    if not applicable:
        return 0.0
    return float(max(t["rebate_rate"] for t in applicable))


def tier_bonus(tiers: list, program: str, volume: float) -> float:
    """Return the bonus of the highest qualifying tier (0 if none)."""
    applicable = [
        t for t in tiers
        if t["program"] == program and volume >= float(t["min_volume"])
    ]
    if not applicable:
        return 0.0
    # Highest qualifying tier = the one with largest min_volume.
    best = max(applicable, key=lambda t: float(t["min_volume"]))
    return float(best.get("bonus", 0.0))


# ---------------------------------------------------------------------------
# lib/sales.aura  --  event log + aggregates
# ---------------------------------------------------------------------------


def record_sale(events: list, event: dict) -> list:
    """Append a sale event to the global event log."""
    out = list(events)
    out.append(dict(event))
    return out


def events_in_period(events: list, cust_id: str, period: str) -> list:
    """Return events for cust_id matching the given period tag."""
    return [e for e in events if e.get("cust_id") == cust_id and e.get("period") == period]


def total_volume(events: list, cust_id: str, period: str | None = None) -> float:
    """Sum of event amounts for cust_id (optionally filtered by period)."""
    total = 0.0
    for e in events:
        if e.get("cust_id") != cust_id:
            continue
        if period is not None and e.get("period") != period:
            continue
        total += float(e.get("amount", 0))
    return total


def growth_vs_prior(events: list, cust_id: str, current_period: str, prior_period: str) -> float:
    """current_volume - prior_volume (negative if shrinking)."""
    cur = total_volume(events, cust_id, current_period)
    pri = total_volume(events, cust_id, prior_period)
    return cur - pri


# ---------------------------------------------------------------------------
# lib/promotions.aura
# ---------------------------------------------------------------------------


def make_promo(spec: dict) -> dict:
    """Just a normalized copy; keeps the spec as-is for downstream use."""
    return dict(spec)


def promo_applies(promo: dict, event: dict) -> bool:
    """Predicate: does this promo apply to this event?"""
    if promo.get("program") != event.get("program"):
        return False
    if promo.get("min_amount") is not None:
        if float(event.get("amount", 0)) < float(promo["min_amount"]):
            return False
    only = promo.get("only_period")
    if only is not None and event.get("period") != only:
        return False
    return True


def promo_amount(promo: dict, event: dict) -> float:
    """Flat or rate-based promo payout for one event."""
    amt = float(event.get("amount", 0))
    if "flat" in promo:
        return float(promo["flat"])
    if "rate" in promo:
        return amt * float(promo["rate"])
    return 0.0


# ---------------------------------------------------------------------------
# lib/retro.aura
# ---------------------------------------------------------------------------


def retro_window(spec: dict) -> dict:
    """spec has {'lookback_periods': int, 'qualifying_periods': [str,...]}."""
    return dict(spec)


def retro_qualify(win: dict, event: dict, current_period: str) -> bool:
    """An event qualifies for retro if its period is in the lookback set
    AND predates current_period."""
    qual = win.get("qualifying_periods", []) or []
    if event.get("period") not in qual:
        return False
    # Simple ordering: 'YYYY-QN' sorts lexicographically.
    if str(event.get("period")) >= str(current_period):
        return False
    return True


def retro_bonus_rate(win: dict, event: dict) -> float:
    """Bonus rate scales linearly with lookback depth (toy model)."""
    qual = win.get("qualifying_periods", []) or []
    if event.get("period") not in qual:
        return 0.0
    base = float(win.get("base_rate", 0.0))
    depth = qual.index(event["period"])  # earlier = larger depth
    return base * (1.0 + 0.25 * depth)


# ---------------------------------------------------------------------------
# lib/disputes.aura
# ---------------------------------------------------------------------------


def open_dispute(disputes: list, cust_id: str, amount: float, reason: str = "") -> list:
    out = list(disputes)
    out.append({"cust_id": cust_id, "amount": float(amount), "reason": reason, "status": "open"})
    return out


def dispute_holdback(disputes: list, cust_id: str) -> float:
    """Sum of open dispute amounts for a customer."""
    total = 0.0
    for d in disputes:
        if d.get("cust_id") == cust_id and d.get("status") == "open":
            total += float(d.get("amount", 0))
    return total


def release_dispute(disputes: list, cust_id: str) -> list:
    out = []
    for d in disputes:
        if d.get("cust_id") == cust_id and d.get("status") == "open":
            d = dict(d)
            d["status"] = "released"
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# lib/accruals.aura
# ---------------------------------------------------------------------------


SEMANTIC_MODES = ("advance", "arrears")


def semantic_mode(mode: str) -> str:
    return mode if mode in SEMANTIC_MODES else "arrears"


def accrue_volume_rebate(
    volume: float, rate: float, bonus: float, mode: str
) -> float:
    """Gross volume rebate: volume*rate + flat bonus."""
    return volume * rate + bonus


def accrue_growth_rebate(
    growth: float, rate: float, cap: float | None = None
) -> float:
    """Growth rebate: max(0, growth) * rate, optionally capped."""
    base = max(0.0, float(growth)) * float(rate)
    if cap is not None:
        base = min(base, float(cap))
    return base


def accrue_promo_rebate(events: list, promos: list, cust_id: str, program: str) -> float:
    """Sum of promo_amount across events/promos where promo_applies is true."""
    total = 0.0
    for e in events:
        if e.get("cust_id") != cust_id or e.get("program") != program:
            continue
        for p in promos:
            if p.get("program") != program:
                continue
            if promo_applies(p, e):
                total += promo_amount(p, e)
    return total


def gross_accrued(per_program: dict) -> float:
    """Sum of all program-level accruals."""
    return float(sum(float(v) for v in per_program.values()))


# ---------------------------------------------------------------------------
# lib/trueups.aura
# ---------------------------------------------------------------------------


def trueup_due(cadence: dict, period: str, last_trueup_period: str | None) -> bool:
    """A true-up is due if cadence['every'] periods have elapsed since last post."""
    every = int(cadence.get("every", 1))
    if last_trueup_period is None:
        return True
    # Toy: 'YYYY-QN' style ordering; we just compare lexicographically.
    return last_trueup_period < period and _period_index(period) - _period_index(last_trueup_period) >= every


def _period_index(p: str) -> int:
    """Toy period -> integer: split 'YYYY-QN' into integer."""
    try:
        y, q = p.split("-Q")
        return int(y) * 4 + int(q)
    except Exception:
        return 0


def post_trueup(subledger: list, program: str, amount: float, period: str) -> list:
    """Post a true-up as a debit (net payable movement)."""
    return subledger_debit(subledger, program, amount, memo=f"trueup:{period}")


def advance_vs_accrued(
    paid_in_advance: float, accrued: float
) -> float:
    """Positive => advance exceeded accrual (over-paid, recoverable).
       Negative => arrears (under-paid, additional owed)."""
    return float(paid_in_advance) - float(accrued)


# ---------------------------------------------------------------------------
# lib/subledger.aura
# ---------------------------------------------------------------------------


def subledger_init() -> list:
    """Subledger is an alist of (program -> {debits, credits, lines})."""
    return []


def _ensure_program(ledger: list, program: str) -> list:
    if any(p == program for p, _ in ledger):
        return ledger
    return ledger + [(program, {"debits": 0.0, "credits": 0.0, "lines": []})]


def subledger_debit(ledger: list, program: str, amount: float, memo: str = "") -> list:
    ledger = _ensure_program(ledger, program)
    out = []
    for p, state in ledger:
        if p == program:
            state = dict(state)
            state["debits"] = float(state.get("debits", 0.0)) + float(amount)
            state["lines"] = list(state.get("lines", []))
            state["lines"].append({"side": "debit", "amount": float(amount), "memo": memo})
        out.append((p, state))
    return out


def subledger_credit(ledger: list, program: str, amount: float, memo: str = "") -> list:
    ledger = _ensure_program(ledger, program)
    out = []
    for p, state in ledger:
        if p == program:
            state = dict(state)
            state["credits"] = float(state.get("credits", 0.0)) + float(amount)
            state["lines"] = list(state.get("lines", []))
            state["lines"].append({"side": "credit", "amount": float(amount), "memo": memo})
        out.append((p, state))
    return out


def subledger_balance(ledger: list, program: str | None = None) -> float:
    total = 0.0
    for p, state in ledger:
        if program is not None and p != program:
            continue
        total += float(state.get("debits", 0.0)) - float(state.get("credits", 0.0))
    return total


def subledger_lines(ledger: list, program: str | None = None) -> list:
    out = []
    for p, state in ledger:
        if program is not None and p != program:
            continue
        out.extend([(p, ln) for ln in state.get("lines", [])])
    return out


# ---------------------------------------------------------------------------
# seed/seed-customers.aura
# ---------------------------------------------------------------------------


def seed_customers() -> list:
    """
    Return [(cust_id, parent_id_or_None, attrs_dict)].
    3 roots, each with one child, plus an orphan leaf.
    """
    return [
        ("C001", None,  {"region": "NA",  "channel": "retail",  "tier_hint": "gold"}),
        ("C002", "C001", {"region": "NA",  "channel": "retail"}),
        ("C003", None,  {"region": "EMEA", "channel": "wholesale"}),
        ("C004", "C003", {"region": "EMEA", "channel": "wholesale"}),
        ("C005", None,  {"region": "APAC", "channel": "retail"}),
    ]


# ---------------------------------------------------------------------------
# seed/seed-programs.aura
# ---------------------------------------------------------------------------


def seed_programs() -> list:
    return [
        {"program": "VOL",  "name": "Volume Rebate",     "type": "volume"},
        {"program": "GROW", "name": "Growth Rebate",     "type": "growth"},
        {"program": "PROMO","name": "Promo Rebate",      "type": "promo"},
    ]


def seed_tiers() -> list:
    """
    Each row defines a rebate tier for a program.
    rebate_rate is applied to qualifying volume; bonus is a flat add-on.
    """
    return [
        {"program": "VOL",  "tier_name": "VOL-bronze", "min_volume":     0, "rebate_rate": 0.010, "bonus":    0.0},
        {"program": "VOL",  "tier_name": "VOL-silver", "min_volume": 10000, "rebate_rate": 0.015, "bonus":   50.0},
        {"program": "VOL",  "tier_name": "VOL-gold",   "min_volume": 25000, "rebate_rate": 0.020, "bonus":  200.0},

        {"program": "GROW", "tier_name": "GR-bronze",  "min_volume":     0, "rebate_rate": 0.000, "bonus":    0.0},
        {"program": "GROW", "tier_name": "GR-silver",  "min_volume":  1000, "rebate_rate": 0.050, "bonus":    0.0},
        {"program": "GROW", "tier_name": "GR-gold",    "min_volume":  5000, "rebate_rate": 0.080, "bonus":  100.0},
    ]


def seed_promotions() -> list:
    return [
        {"program": "PROMO", "name": "Q4-bonus",  "flat": 25.0,  "min_amount": 500.0,  "only_period": "2024-Q4"},
        {"program": "PROMO", "name": "Spring-5pct","rate": 0.05,  "min_amount": 100.0},
    ]


# ---------------------------------------------------------------------------
# seed/seed-events.aura
# ---------------------------------------------------------------------------


def seed_sales_events() -> list:
    """
    Hand-crafted but non-trivial mix across 4 quarters and 5 customers,
    touching all 3 programs (PROMO events use program='PROMO').
    """
    return [
        # ---- 2024-Q3 (prior period) ----
        {"event_id": "E01", "cust_id": "C001", "program": "VOL",   "amount":  6000.0, "period": "2024-Q3"},
        {"event_id": "E02", "cust_id": "C002", "program": "VOL",   "amount":  2500.0, "period": "2024-Q3"},
        {"event_id": "E03", "cust_id": "C003", "program": "VOL",   "amount":  9000.0, "period": "2024-Q3"},
        {"event_id": "E04", "cust_id": "C004", "program": "VOL",   "amount":  1500.0, "period": "2024-Q3"},
        {"event_id": "E05", "cust_id": "C005", "program": "VOL",   "amount":  3000.0, "period": "2024-Q3"},

        # ---- 2024-Q3 GROW baseline ----
        {"event_id": "E06", "cust_id": "C001", "program": "GROW",  "amount":  1000.0, "period": "2024-Q3"},
        {"event_id": "E07", "cust_id": "C003", "program": "GROW",  "amount":  2000.0, "period": "2024-Q3"},
        {"event_id": "E08", "cust_id": "C005", "program": "GROW",  "amount":   500.0, "period": "2024-Q3"},

        # ---- 2024-Q4 (current period) ----
        {"event_id": "E10", "cust_id": "C001", "program": "VOL",   "amount": 12000.0, "period": "2024-Q4"},
        {"event_id": "E11", "cust_id": "C002", "program": "VOL",   "amount":  4500.0, "period": "2024-Q4"},
        {"event_id": "E12", "cust_id": "C003", "program": "VOL",   "amount": 18000.0, "period": "2024-Q4"},
        {"event_id": "E13", "cust_id": "C004", "program": "VOL",   "amount":  3500.0, "period": "2024-Q4"},
        {"event_id": "E14", "cust_id": "C005", "program": "VOL",   "amount":  7000.0, "period": "2024-Q4"},

        # GROW events (current period)
        {"event_id": "E20", "cust_id": "C001", "program": "GROW",  "amount":  3000.0, "period": "2024-Q4"},
        {"event_id": "E21", "cust_id": "C003", "program": "GROW",  "amount":  8000.0, "period": "2024-Q4"},
        {"event_id": "E22", "cust_id": "C005", "program": "GROW",  "amount":  1500.0, "period": "2024-Q4"},

        # PROMO events
        {"event_id": "E30", "cust_id": "C001", "program": "PROMO", "amount":  800.0,  "period": "2024-Q4"},
        {"event_id": "E31", "cust_id": "C002", "program": "PROMO", "amount":  300.0,  "period": "2024-Q4"},
        {"event_id": "E32", "cust_id": "C003", "program": "PROMO", "amount": 1500.0,  "period": "2024-Q4"},
        {"event_id": "E33", "cust_id": "C004", "program": "PROMO", "amount":   50.0,  "period": "2024-Q4"},  # too small
        {"event_id": "E34", "cust_id": "C005", "program": "PROMO", "amount":  400.0,  "period": "2024-Q4"},
    ]


def seed_disputes() -> list:
    return [
        {"cust_id": "C002", "amount":  75.0, "reason": "short-shipment", "status": "open"},
        {"cust_id": "C004", "amount": 120.0, "reason": "pricing claim",  "status": "open"},
    ]


# ---------------------------------------------------------------------------
# seed/seed-config.aura
# ---------------------------------------------------------------------------


def seed_retro_window() -> dict:
    return {
        "lookback_periods": 4,
        "qualifying_periods": ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"],
        "base_rate": 0.005,
    }


def seed_trueup_cadence() -> dict:
    return {"every": 1, "unit": "quarter"}


def seed_semantic_modes() -> dict:
    """Maps program -> 'advance' or 'arrears'."""
    return {
        "VOL":   "advance",   # Paid in advance based on forecast
        "GROW":  "arrears",   # Paid after growth is realized
        "PROMO": "advance",
    }


# ---------------------------------------------------------------------------
# main.aura  --  orchestration + printing the 12 KEY=value lines
# ---------------------------------------------------------------------------

ENGINE_VERSION = "1.0.0"
CURRENT_PERIOD = "2024-Q4"
PRIOR_PERIOD = "2024-Q3"
GROWTH_CAP = 10000.0   # per-program cap on growth rebate (toy)


def _safe_round(x: float) -> float:
    """Round to 2dp without drifting on whole numbers."""
    return float(round(float(x) + 1e-9, 2))


def run_scenario() -> dict:
    """Execute the full engine pipeline. Returns a dict of the 12 outputs."""

    # Step 1: util + state KV
    state = make_kv()
    state = kv_put(state, "engine_version", ENGINE_VERSION)
    state = kv_put(state, "current_period", CURRENT_PERIOD)
