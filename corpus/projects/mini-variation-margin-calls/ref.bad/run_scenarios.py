# Toy reference implementation for the "mini-variation-margin-calls" Aura scenario.
# Single-file Python (stdlib only) that mirrors the semantics described in GOAL.md.

import math
from collections import defaultdict


# ----------------------------- state.aura -----------------------------

_csas = {}            # cp_id -> csa dict
_trades = []          # list of trade dicts
_calls = {}           # call_id -> call dict
_deliveries = []      # list of (call_id, amount) deliveries
_interest_ledger = defaultdict(int)  # call_id -> accrued interest (integer)
_call_counter = [0]   # mutable counter


def api_reset():
    _csas.clear()
    _trades.clear()
    _calls.clear()
    _deliveries.clear()
    _interest_ledger.clear()
    _call_counter[0] = 0


def api_next_call_id():
    _call_counter[0] += 1
    return f"CALL-{_call_counter[0]:04d}"


# ----------------------------- types.aura -----------------------------

def make_csa(cid, threshold, mta, rounding, ccy, dispute_hours, rate_bps):
    return {
        "id": cid, "threshold": threshold, "mta": mta,
        "rounding": rounding, "ccy": ccy,
        "dispute_hours": dispute_hours, "rate_bps": rate_bps,
    }


def _csa_field(name):
    def getter(c):
        return c[name]
    return getter


csa_id = _csa_field("id")
csa_threshold = _csa_field("threshold")
csa_mta = _csa_field("mta")
csa_rounding = _csa_field("rounding")
csa_ccy = _csa_field("ccy")
csa_dispute_hours = _csa_field("dispute_hours")
csa_rate_bps = _csa_field("rate_bps")


def make_trade(cp_id, notional, direction, mv):
    return {"cp": cp_id, "notional": notional, "dir": direction, "mv": mv}


trade_cp = _csa_field("cp")
trade_notional = _csa_field("notional")
trade_dir = _csa_field("dir")
trade_mv = _csa_field("mv")


def make_call(cid, cp_id, amount, issued_at, status):
    return {"id": cid, "cp": cp_id, "amount": amount,
            "issued_at": issued_at, "status": status}


call_id = _csa_field("id")
call_cp = _csa_field("cp")
call_amount = _csa_field("amount")


def call_status(c):
    return c["status"]


# ----------------------------- portfolio.aura -----------------------------

def api_portfolio_add_cp(cp):
    _csas[cp["id"]] = cp


def api_portfolio_add_trade(t):
    _trades.append(t)


def api_portfolio_mtm(cp_id):
    total = 0
    for t in _trades:
        if t["cp"] == cp_id:
            # direction: +1 for long (asset value owed to us),
            # -1 for short. MtM in absolute terms (we always sum exposure
            # owed to the CCP/clearing perspective). Use raw mv.
            total += t["mv"]
    return total


def api_portfolio_total_mtm():
    return sum(api_portfolio_mtm(cp) for cp in _csas)


def api_portfolio_counterparties():
    return list(_csas.keys())


def api_portfolio_trade_count():
    return len(_trades)


def api_portfolio_trades_for(cp_id):
    return [t for t in _trades if t["cp"] == cp_id]


# ----------------------------- rounding.aura -----------------------------

def api_round_up(amount, rounding):
    if rounding <= 0:
        return amount
    return ((amount + rounding - 1) // rounding) * rounding


def api_round_nearest(amount, rounding):
    if rounding <= 0:
        return amount
    return round(amount / rounding) * rounding


# ----------------------------- threshold.aura -----------------------------

def api_call_required(mtm, threshold, mta):
    return mtm >= threshold + mta


def api_call_amount(mtm, threshold, mta, rounding):
    # Exposure above threshold; only call if above MTA; round up to rounding.
    exposure = mtm - threshold
    if exposure < mta:
        return 0
    return api_round_up(exposure, rounding)


# ----------------------------- dispute.aura -----------------------------

def api_open_dispute(call_id):
    c = _calls.get(call_id)
    if c is None:
        return False
    if c["status"] == "open":
        c["status"] = "disputed"
        return True
    return False


def api_dispute_count():
    return sum(1 for c in _calls.values() if c["status"] == "disputed")


def api_expired_disputes(now_hours):
    # Auto-confirm (mark 'expired') any disputed call whose dispute window
    # elapsed since issuance.
    count = 0
    for c in _calls.values():
        if c["status"] == "disputed":
            window = _csas[c["cp"]]["dispute_hours"]
            if now_hours - c["issued_at"] >= window:
                c["status"] = "expired"
                count += 1
    return count


def api_call_status(call_id):
    c = _calls.get(call_id)
    if c is None:
        return None
    return c["status"]


# ----------------------------- settlement.aura -----------------------------

def _outstanding_amount(call):
    delivered = sum(a for (cid, a) in _deliveries if cid == call["id"])
    return max(call["amount"] - delivered, 0)


def api_deliver(call_id, amount):
    c = _calls.get(call_id)
    if c is None:
        return False
    _deliveries.append((call_id, amount))
    return True


def api_mark_settled(call_id):
    c = _calls.get(call_id)
    if c is None:
        return False
    # If not fully delivered, top it up implicitly
    outstanding = _outstanding_amount(c)
    if outstanding > 0:
        _deliveries.append((call_id, outstanding))
    c["status"] = "settled"
    return True


def api_call_outstanding(call_id):
    c = _calls.get(call_id)
    if c is None:
        return 0
    return _outstanding_amount(c)


def api_total_delivered():
    return sum(a for (_, a) in _deliveries)


def api_total_outstanding():
    return sum(_outstanding_amount(c) for c in _calls.values())


def api_settled_calls():
    return sum(1 for c in _calls.values() if c["status"] == "settled")


def api_open_calls():
    # open = anything not settled (open, disputed, expired)
    return sum(1 for c in _calls.values() if c["status"] != "settled")


# ----------------------------- interest.aura -----------------------------

def api_accrue_on_call(call_id, days):
    c = _calls.get(call_id)
    if c is None:
        return 0
    csa = _csas[c["cp"]]
    outstanding = _outstanding_amount(c)
    rate = csa["rate_bps"]
    # interest = outstanding * rate_bps * days / 10000  (floor)
    interest = (outstanding * rate * days) // 10000
    _interest_ledger[call_id] += interest
    return interest


def api_total_interest():
    return sum(_interest_ledger.values())


def api_interest_for_call(call_id):
    return _interest_ledger.get(call_id, 0)


# ----------------------------- reporting.aura -----------------------------

def api_top_exposure():
    if not _csas:
        return None
    best_cp = None
    best_mtm = -math.inf
    for cp in _csas:
        m = api_portfolio_mtm(cp)
        if m > best_mtm:
            best_mtm = m
            best_cp = cp
    return (best_cp, best_mtm)


def api_summary():
    return {
        "mtm": api_portfolio_total_mtm(),
        "calls": len(_calls),
        "outstanding": api_total_outstanding(),
        "interest": api_total_interest(),
    }


# ----------------------------- scenario driver -----------------------------

def main():
    api_reset()

    # 1. Three counterparties
    api_portfolio_add_cp(make_csa("CP-A", 1_000_000, 100_000, 50_000, "USD", 24, 50))
    api_portfolio_add_cp(make_csa("CP-B", 500_000, 50_000, 10_000, "EUR", 48, 75))
    api_portfolio_add_cp(make_csa("CP-C", 0, 0, 1_000, "GBP", 12, 100))

    # 2. Six trades
    api_portfolio_add_trade(make_trade("CP-A", 10_000_000, "long", 1_250_000))
    api_portfolio_add_trade(make_trade("CP-A", 5_000_000, "short", -400_000))

    api_portfolio_add_trade(make_trade("CP-B", 8_000_000, "long", 720_000))
    api_portfolio_add_trade(make_trade("CP-B", 3_000_000, "long", 180_000))

    api_portfolio_add_trade(make_trade("CP-C", 2_000_000, "short", -95_000))
    api_portfolio_add_trade(make_trade("CP-C", 1_500_000, "long", 60_000))

    # 3. Decide & issue calls
    issued = []
    now = 0
    for cp_id in api_portfolio_counterparties():
        csa = _csas[cp_id]
        mtm = api_portfolio_mtm(cp_id)
        if api_call_required(mtm, csa["threshold"], csa["mta"]):
            amt = api_call_amount(mtm, csa["threshold"], csa["mta"], csa["rounding"])
            cid = api_next_call_id()
            _calls[cid] = make_call(cid, cp_id, amt, now, "open")
            issued.append(cid)

    # 4. Open disputes on 2 of the issued calls
    api_open_dispute(issued[0])
    api_open_dispute(issued[1])

    # 5. Settle one fully, one partially
    api_mark_settled(issued[2])  # full
    api_deliver(issued[0], _calls[issued[0]]["amount"] // 2)  # half

    # 6. Advance clock: 48h -> elapses 1 disputed call (CP-B with 48h window)
    api_expired_disputes(48)

    # 7. Accrue 3 days interest on the still-open partially-settled call
    api_accrue_on_call(issued[0], 3)

    # 8. Final aggregates
    portfolio_mtm = api_portfolio_total_mtm()
    counterparty_count = len(api_portfolio_counterparties())
    trade_count = api_portfolio_trade_count()
    calls_issued = len(_calls)
    total_called = sum(c["amount"] for c in _calls.values())
    total_delivered = api_total_delivered()
    total_outstanding = api_total_outstanding()
    disputed_count = api_dispute_count()
    expired_disputes = sum(1 for c in _calls.values() if c["status"] == "expired")
    interest_accrued = api_total_interest()
    top_cp, top_val = api_top_exposure()
    settled_calls = api_settled_calls()
    open_calls = api_open_calls()
    # round trip calls: calls whose full amount was delivered (settled + any
    # fully-paid but not yet marked settled) -- in our scenario only the one
    # we explicitly marked settled, plus any whose outstanding is 0.
    round_trip_calls = sum(
        1 for c in _calls.values()
        if _outstanding_amount(c) == 0 and c["status"] == "settled"
    )
    final_outstanding = api_total_outstanding()

    print(f"portfolio_mtm={portfolio_mtm}")
    print(f"counterparty_count={counterparty_count}")
    print(f"trade_count={trade_count}")
    print(f"calls_issued={calls_issued}")
    print(f"total_called={total_called}")
    print(f"total_delivered={total_delivered}")
    print(f"total_outstanding={total_outstanding}")
    print(f"disputed_count={disputed_count}")
    print(f"expired_disputes={expired_disputes}")
    print(f"interest_accrued={interest_accrued}")
    print(f"top_exposure_cp={top_cp}")
    print(f"top_exposure_value={top_val}")
    print(f"settled_calls={settled_calls}")
    print(f"open_calls={open_calls}")
    print(f"round_trip_calls={round_trip_calls}")
    print(f"final_outstanding={final_outstanding}")


if __name__ == "__main__":
    main()
