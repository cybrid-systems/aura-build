#!/usr/bin/env python3
"""
Mini Invoice Dunning Runner — Python reference implementation.

Toy in-memory semantics for the GOAL scenario. Computes every KEY=value
line by walking the seeded portfolio through the aging → notice → fee →
promise → writeoff → audit pipeline, exactly as main.aura would.
"""

import sys
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# data.aura — seed portfolio
# ---------------------------------------------------------------------------

def seed_portfolio():
    """
    Returns (invoices, today, ptps_seed).
    Mix of statuses: open, paid, disputed. Today is a fixed reference day.
    """
    today = date(2025, 3, 15)

    # (id, customer, amount_cents, due_day, status, age_days_relative_to_today)
    raw = [
        # current (not yet due)
        ("INV-001", "Acme Corp",      50000,  date(2025, 3, 20), "open",    -5),
        ("INV-002", "Beta LLC",       12000,  date(2025, 3, 18), "open",    -3),
        # 1-30
        ("INV-101", "Gamma Inc",      75000,  date(2025, 3, 1),  "open",    14),
        ("INV-102", "Delta Co",       33000,  date(2025, 2, 25), "open",    18),
        ("INV-103", "Epsilon Ltd",    22000,  date(2025, 2, 20), "open",    23),
        # 31-60
        ("INV-201", "Zeta Holdings",  180000, date(2025, 1, 25), "open",    49),
        ("INV-202", "Eta Group",      65000,  date(2025, 1, 20), "open",    54),
        # 61-90
        ("INV-301", "Theta SA",       95000,  date(2025, 1, 1),  "open",    73),
        ("INV-302", "Iota Partners",  41000,  date(2025, 12, 25),"open",    80),
        # 90+
        ("INV-401", "Kappa Industries",240000, date(2024, 11, 20),"open",   115),
        ("INV-402", "Lambda Bros",    88000,  date(2024, 10, 30),"open",   136),
        # paid / disputed (excluded from open balance + bucket totals)
        ("INV-501", "Mu Corp",        15000,  date(2025, 2, 10), "paid",    33),
        ("INV-502", "Nu Services",    27000,  date(2025, 1, 15), "disputed",55),
    ]
    invoices = []
    for (iid, cust, amt, due, status, age) in raw:
        # store as plain dicts (the Aura alist analogue)
        invoices.append({
            "id": iid, "customer": cust, "amount": amt,
            "due": due, "status": status, "age": age,
        })

    # Promise-to-pay seed: (customer, invoice_id, promised_by_day_offset)
    ptps_seed = [
        ("Gamma Inc",     "INV-101", 7),    # honored (due in 7 days from today)
        ("Delta Co",      "INV-102", -2),   # broken (already past)
        ("Theta SA",      "INV-301", 14),   # honored
        ("Kappa Industries","INV-401", -30),# broken
        ("Beta LLC",      "INV-002", 3),    # honored
    ]

    return invoices, today, ptps_seed


def api_portfolio_data():
    return seed_portfolio()


# ---------------------------------------------------------------------------
# invoice.aura — invoice records
# ---------------------------------------------------------------------------

def api_invoice_make(iid, cust, amount, due_day, status):
    return {"id": iid, "customer": cust, "amount": amount,
            "due": due_day, "status": status, "age": None}


def _invoice_attr(inv, name):
    return inv.get(name)


def api_invoice_id(inv):         return _invoice_attr(inv, "id")
def api_invoice_customer(inv):   return _invoice_attr(inv, "customer")
def api_invoice_amount(inv):     return _invoice_attr(inv, "amount")
def api_invoice_due_day(inv):    return _invoice_attr(inv, "due")
def api_invoice_status(inv):     return _invoice_attr(inv, "status")
def api_invoice_age_days(inv, today):
    if inv.get("age") is not None:
        return inv["age"]
    return (today - inv["due"]).days


def api_invoice_set_status(inv, s):
    inv["status"] = s
    return inv


# ---------------------------------------------------------------------------
# aging.aura — bucketing
# ---------------------------------------------------------------------------

def api_bucket_classify(days):
    if days <= 0:        return "current"
    if days <= 30:       return "1-30"
    if days <= 60:       return "31-60"
    if days <= 90:       return "61-90"
    return "90+"


def api_aging_bucketize(invoices, today):
    buckets = {"current": [], "1-30": [], "31-60": [],
               "61-90": [], "90+": []}
    for inv in invoices:
        if api_invoice_status(inv) != "open":
            continue
        days = api_invoice_age_days(inv, today)
        b = api_bucket_classify(days)
        buckets[b].append(inv)
    return buckets


# ---------------------------------------------------------------------------
# fee.aura — tiered late fees
# ---------------------------------------------------------------------------

def api_fee_rate(days_past_due):
    if days_past_due <= 0:   return 0
    if days_past_due <= 30:  return 100     # 1.00% in cents-per-100
    if days_past_due <= 60:  return 200
    if days_past_due <= 90:  return 350
    return 500                                # cap at 5%


def api_fee_applicable(inv, today):
    if api_invoice_status(inv) != "open":
        return False
    days = api_invoice_age_days(inv, today)
    return days > 0 and api_fee_rate(days) > 0


def api_fee_compute(inv, today):
    days = api_invoice_age_days(inv, today)
    rate = api_fee_rate(days)
    # fee in cents = amount_cents * rate / 10000  (rate is basis points / 100)
    fee = (api_invoice_amount(inv) * rate) // 10000
    return fee


# ---------------------------------------------------------------------------
# promise.aura — promises to pay
# ---------------------------------------------------------------------------

def api_promise_make(cust, invoice_id, by_day):
    return {"customer": cust, "invoice_id": invoice_id,
            "promised_by_offset": by_day}


def api_promise_valid(p, today):
    return p.get("invoice_id") is not None


def api_promise_honored(p, today):
    # honored if promised_by_offset >= 0  (future promise still good)
    return p.get("promised_by_offset", -1) >= 0


def api_promise_add(ptps, p):
    ptps.append(p)
    return ptps


def api_promise_find(ptps, invoice_id):
    for p in ptps:
        if p["invoice_id"] == invoice_id:
            return p
    return None


# ---------------------------------------------------------------------------
# notice.aura — stage-based cadence
# ---------------------------------------------------------------------------

def api_notice_stage(inv, ptps, today):
    """
    Returns one of: 'reminder | 'firm | 'final | 'none
    'reminder  — any open invoice with age >= 1
    'firm      — age >= 30 OR honored promise exists for it
    'final     — age >= 60
    'none      — paid/disputed or current (age <= 0)
    """
    if api_invoice_status(inv) != "open":
        return "none"
    days = api_invoice_age_days(inv, today)
    if days <= 0:
        return "none"
    if days >= 60:
        return "final"
    if days >= 30:
        return "firm"
    if api_promise_find(ptps, api_invoice_id(inv)) is not None:
        return "firm"
    return "reminder"


def api_notice_template(stage, inv):
    return f"[{stage.upper()}] To {api_invoice_customer(inv)} re {api_invoice_id(inv)}"


def api_notice_send(state, stage, inv):
    if stage == "none":
        return
    state.setdefault("counters", {})[stage] = \
        state["counters"].get(stage, 0) + 1


def api_notice_counters(state):
    return dict(state.get("counters", {}))


# ---------------------------------------------------------------------------
# writeoff.aura
# ---------------------------------------------------------------------------

def api_writeoff_eligible(inv, today):
    if api_invoice_status(inv) != "open":
        return False
    return api_invoice_age_days(inv, today) > 90


def api_writeoff_amount(inv):
    return api_invoice_amount(inv)


def api_writeoff_record(state, inv):
    state["writeoffs_cents"] = state.get("writeoffs_cents", 0) \
        + api_writeoff_amount(inv)
    api_invoice_set_status(inv, "written_off")


# ---------------------------------------------------------------------------
# audit.aura
# ---------------------------------------------------------------------------

def api_audit_log(state, msg):
    state.setdefault("audit", []).append(msg)


def api_audit_entries(state):
    return list(state.get("audit", []))


def api_audit_format(e):
    return str(e)


# ---------------------------------------------------------------------------
# state.aura
# ---------------------------------------------------------------------------

def api_state_make():
    return {"counters": {}, "audit": [], "writeoffs_cents": 0}


def api_state_get(state, key):
    return state.get(key)


def api_state_set(state, key, val):
    state[key] = val
    return state


def api_state_add(state, key, val):
    state[key] = state.get(key, 0) + val
    return state


# ---------------------------------------------------------------------------
# runner.aura
# ---------------------------------------------------------------------------

def api_run_dunning(portfolio, ptps, today):
    state = api_state_make()
    buckets = api_aging_bucketize(portfolio, today)

    # walk every open invoice through the cadence
    for inv in portfolio:
        if api_invoice_status(inv) != "open":
            continue
        stage = api_notice_stage(inv, ptps, today)
        api_notice_send(state, stage, inv)
        api_audit_log(state, f"NOTICE stage={stage} id={api_invoice_id(inv)}")

        if stage in ("firm", "final") and api_fee_applicable(inv, today):
            fee = api_fee_compute(inv, today)
            api_state_add(state, "late_fees_cents", fee)
            api_audit_log(state, f"LATE_FEE id={api_invoice_id(inv)} cents={fee}")

        if stage == "final" and api_writeoff_eligible(inv, today):
            api_writeoff_record(state, inv)
            api_audit_log(state, f"WRITEOFF id={api_invoice_id(inv)} "
                                  f"cents={api_writeoff_amount(inv)}")

    # promises: each PTP evaluated against the today counter
    for p in ptps:
        if api_promise_valid(p, today):
            if api_promise_honored(p, today):
                api_state_add(state, "promises_honored", 1)
                api_audit_log(state, f"PTP_HONORED id={p['invoice_id']}")
            else:
                api_state_add(state, "promises_broken", 1)
                api_audit_log(state, f"PTP_BROKEN id={p['invoice_id']}")

    return state, buckets


# ---------------------------------------------------------------------------
# report.aura
# ---------------------------------------------------------------------------

def api_report_summary(state, buckets):
    counters = api_notice_counters(state)
    return {
        "portfolio_invoices":      sum(len(v) for v in buckets.values()),
        "portfolio_open_balance":  sum(api_invoice_amount(i)
                                       for v in buckets.values() for i in v),
        "bucket_current":          len(buckets["current"]),
        "bucket_1_30":             len(buckets["1-30"]),
        "bucket_31_60":            len(buckets["31-60"]),
        "bucket_61_90":            len(buckets["61-90"]),
        "bucket_90_plus":          len(buckets["90+"]),
        "reminders_sent":          counters.get("reminder", 0),
        "firm_notices_sent":       counters.get("firm", 0),
        "final_notices_sent":      counters.get("final", 0),
        "promises_honored":        state.get("promises_honored", 0),
        "promises_broken":         state.get("promises_broken", 0),
        "late_fees_collected":     state.get("late_fees_cents", 0),
        "writeoffs":               state.get("writeoffs_cents", 0),
        "audit_entries":           len(api_audit_entries(state)),
    }


# ---------------------------------------------------------------------------
# main.aura — orchestrate + print KEY=value lines in canonical order
# ---------------------------------------------------------------------------

def main():
    invoices, today, ptps_seed = api_portfolio_data()

    ptps = []
    for (cust, iid, by_day) in ptps_seed:
        api_promise_add(ptps,
                        api_promise_make(cust, iid, by_day))

    state, buckets = api_run_dunning(invoices, ptps, today)
    summary = api_report_summary(state, buckets)

    out = [
        f"PORTFOLIO_INVOICES={summary['portfolio_invoices']}",
        f"PORTFOLIO_OPEN_BALANCE={summary['portfolio_open_balance']}",
        f"BUCKET_CURRENT={summary['bucket_current']}",
        f"BUCKET_1_30={summary['bucket_1_30']}",
        f"BUCKET_31_60={summary['bucket_31_60']}",
        f"BUCKET_61_90={summary['bucket_61_90']}",
        f"BUCKET_90_PLUS={summary['bucket_90_plus']}",
        f"REMINDERS_SENT={summary['reminders_sent']}",
        f"FIRM_NOTICES_SENT={summary['firm_notices_sent']}",
        f"FINAL_NOTICES_SENT={summary['final_notices_sent']}",
        f"PROMISES_HONORED={summary['promises_honored']}",
        f"PROMISES_BROKEN={summary['promises_broken']}",
        f"LATE_FEES_COLLECTED={summary['late_fees_collected']}",
        f"WRITEOFFS={summary['writeoffs']}",
        f"AUDIT_ENTRIES={summary['audit_entries']}",
        "RUN_OK=#t",
    ]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
