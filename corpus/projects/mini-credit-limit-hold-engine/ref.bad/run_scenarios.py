# build_aura_ref.py
# Reference / translator that converts the multi-file Aura project
# ("mini-credit-limit-hold-engine") into the expected stdout contract,
# as a single self-contained Python 3 reference implementation.
#
# This file is a faithful, runnable description of what main.aura is
# supposed to do, using toy in-memory semantics for the Aura APIs.

import math
import time
import uuid

# -------------------------------------------------------------------
# 1.  types.aura
# -------------------------------------------------------------------

_CUSTOMER_REGISTRY = []  # filled by risk_registry.aura


class Customer:
    def __init__(self, cid, name, line):
        self.cid = cid
        self.name = name
        self.line = line
        self.balance = 0           # posted charges
        self.pay_history = None    # set later by risk.aura
        self.risk_score = 0
        self.risk_band = "low"

    def __repr__(self):
        return f"<Customer {self.cid} {self.name} line={self.line}>"


def make_customer(cid, name, line):
    return Customer(cid, name, line)


def customer?(c):
    return isinstance(c, Customer)


def customer_id(c):
    return c.cid


def customer_name(c):
    return c.name


def customer_line(c):
    return c.line


def customer_balance(c):
    return c.balance


def customer_set_balance(c, amount):
    c.balance = amount
    return c.balance


def customer_risk(c):
    return c.risk_band


# -------------------------------------------------------------------
# 2.  risk.aura
# -------------------------------------------------------------------


class PayHistory:
    """
    Toy pay-history buckets:
        on_time : int
        late    : int
        default : int
    risk-score = on_time*1 + late*2 + default*5 (negative-ish but
    we map to band using policy thresholds).
    """

    def __init__(self, on_time=0, late=0, default=0):
        self.on_time = on_time
        self.late = late
        self.default = default


def make_pay_history(on_time=0, late=0, default_=0):
    return PayHistory(on_time, late, default_)


def pay_on_time(h):
    return h.on_time


def pay_late(h):
    return h.late


def pay_default(h):
    return h.default


def risk_score(c):
    # higher default-rate => higher risk score
    h = c.pay_history
    if h is None:
        return 0
    score = h.late * 2 + h.default * 5
    c.risk_score = score
    return score


def _band_for_score(score):
    # ad-hoc thresholds so that the seed produces the documented mix:
    #   c1 -> high  (lots of defaults)
    #   c2 -> med   (mostly late)
    #   c3 -> low   (mostly on-time)
    #   c4 -> low   (all on-time)
    if score >= 5:
        return "high"
    if score >= 2:
        return "med"
    return "low"


def risk_band(c):
    if c.risk_band is None:
        c.risk_band = _band_for_score(risk_score(c))
    return c.risk_band


# -------------------------------------------------------------------
# 3.  exposure.aura
# -------------------------------------------------------------------

# Per-customer pending/expected exposure buckets
_EXPOSURE = {}   # cid -> { 'orders':n, 'shipments':n, 'returns':n, 'unposted':n }


def _exp(cid):
    return _EXPOSURE.setdefault(
        cid, {"orders": 0, "shipments": 0, "returns": 0, "unposted": 0}
    )


def exposure_orders(c):
    return _exp(c.cid)["orders"]


def exposure_shipments(c):
    return _exp(c.cid)["shipments"]


def exposure_returns(c):
    return _exp(c.cid)["returns"]


def exposure_unposted(c):
    return _exp(c.cid)["unposted"]


def open_to_buy(c):
    used = (
        exposure_orders(c)
        + exposure_unposted(c)
        - exposure_returns(c)
        - exposure_shipments(c)
    )
    otb = c.line - used
    return max(0, otb)


# -------------------------------------------------------------------
# 4.  holds.aura
# -------------------------------------------------------------------


class Hold:
    def __init__(self, hid, cust, htype, amount):
        self.hid = hid
        self.cust = cust
        self.htype = htype           # 'soft' | 'hard'
        self.amount = amount
        self.status = "active"       # 'active' | 'released'
        self.released_amount = 0
        self.override_status = None  # 'pending' | 'approved' | 'denied'


_HOLDS = []
_RELEASED_COUNT = 0


def make_hold(cust, htype, amount):
    hid = "H-" + uuid.uuid4().hex[:6]
    h = Hold(hid, cust, htype, amount)
    return h


def hold?(h):
    return isinstance(h, Hold)


def hold_id(h):
    return h.hid


def hold_cust(h):
    return h.cust


def hold_type(h):
    return h.htype


def hold_amount(h):
    return h.amount


def hold_status(h):
    return h.status


def hold_set_status(h, s):
    h.status = s
    return s


def hold_released_amount(h):
    return h.released_amount


def place_hold(cust, htype, amount):
    global _RELEASED_COUNT
    h = make_hold(cust, htype, amount)
    _HOLDS.append(h)
    # charge to balance / orders-exposure
    cust.balance += amount
    _exp(cust.cid)["orders"] += amount
    return h


def release_hold(h, amount=None):
    global _RELEASED_COUNT
    if amount is None:
        amount = h.amount - h.released_amount
    h.released_amount += amount
    if h.released_amount >= h.amount:
        h.status = "released"
        _RELEASED_COUNT += 1
        # reduce orders exposure accordingly
        _exp(h.cust.cid)["orders"] -= (h.amount)
        if _exp(h.cust.cid)["orders"] < 0:
            _exp(h.cust.cid)["orders"] = 0
    return h


def active_holds():
    return [h for h in _HOLDS if h.status == "active"]


def active_hold_for(cust):
    return [h for h in _HOLDS if h.status == "active" and h.cust is cust]


# -------------------------------------------------------------------
# 5.  policy.aura
# -------------------------------------------------------------------

SOFT_THRESHOLD = 0.40   # > 40% utilisation of credit line -> soft
HARD_THRESHOLD = 0.75   # > 75% utilisation -> hard


def policy_soft_threshold():
    return SOFT_THRESHOLD


def policy_hard_threshold():
    return HARD_THRESHOLD


def policy_decide(cust, order_amount):
    line = cust.line
    used_after = _exp(cust.cid)["orders"] + order_amount + exposure_unposted(cust)
    util = used_after / line if line > 0 else 1.0
    if util > HARD_THRESHOLD:
        return "hard"
    if util > SOFT_THRESHOLD:
        return "soft"
    return "none"


# -------------------------------------------------------------------
# 6.  override.aura
# -------------------------------------------------------------------

_OVERRIDES = []


class Override:
    def __init__(self, hold, manager, reason):
        self.hold = hold
        self.manager = manager
        self.reason = reason
        self.status = "pending"


def request_override(hold, manager, reason="standard review"):
    o = Override(hold, manager, reason)
    _OVERRIDES.append(o)
    hold.override_status = "pending"
    return o


def approve_override(o):
    o.status = "approved"
    o.hold.override_status = "approved"
    return o


def deny_override(o):
    o.status = "denied"
    o.hold.override_status = "denied"
    return o


def override_record(o):
    return o


def override_status(o):
    return o.status


# -------------------------------------------------------------------
# 7.  payments.aura
# -------------------------------------------------------------------

_PAY_POSTED = 0


def post_payment(cust, amount):
    """Apply a posted payment: reduces customer balance."""
    global _PAY_POSTED
    cust.balance = max(0, cust.balance - amount)
    _PAY_POSTED += amount
    return cust.balance


def payment_apply_to_holds(cust, amount):
    """Walk active holds oldest-first and release them until payment is spent."""
    remaining = amount
    for h in active_hold_for(cust):
        if remaining <= 0:
            break
        left = h.amount - h.released_amount
        if left <= 0:
            continue
        take = min(remaining, left)
        release_hold(h, take)
        remaining -= take
    return amount - remaining  # amount actually applied


# -------------------------------------------------------------------
# 8.  shipments.aura
# -------------------------------------------------------------------


def record_shipment(cust, amount):
    _exp(cust.cid)["shipments"] += amount
    return amount


def shipment_reduces_exposure(cust, amount):
    return record_shipment(cust, amount)


# -------------------------------------------------------------------
# 9.  returns.aura
# -------------------------------------------------------------------


def record_return(cust, amount):
    _exp(cust.cid)["returns"] += amount
    return amount


def return_reduces_exposure(cust, amount):
    return record_return(cust, amount)


# -------------------------------------------------------------------
# 10. invoices.aura
# -------------------------------------------------------------------


class Invoice:
    def __init__(self, iid, cust, amount, posted=False):
        self.iid = iid
        self.cust = cust
        self.amount = amount
        self.posted = posted


_INVOICES = []


def add_unposted_invoice(cust, amount):
    iid = "INV-" + uuid.uuid4().hex[:6]
    inv = Invoice(iid, cust, amount, posted=False)
    _INVOICES.append(inv)
    _exp(cust.cid)["unposted"] += amount
    return inv


def invoice_amount(inv):
    return inv.amount


# -------------------------------------------------------------------
# 11. risk_registry.aura
# -------------------------------------------------------------------


def register_customer(c):
    if c not in _CUSTOMER_REGISTRY:
        _CUSTOMER_REGISTRY.append(c)
    return c


def all_customers():
    return list(_CUSTOMER_REGISTRY)


def find_customer(cid):
    for c in _CUSTOMER_REGISTRY:
        if c.cid == cid:
            return c
    return None


# -------------------------------------------------------------------
# 12. events.aura
# -------------------------------------------------------------------

_EVENTS = []


def log_event(kind, payload):
    e = {"kind": kind, "payload": payload, "t": time.time()}
    _EVENTS.append(e)
    return e


def event_log():
    return list(_EVENTS)


def recent_events(n=10):
    return _EVENTS[-n:]


# -------------------------------------------------------------------
# 13. stats.aura
# -------------------------------------------------------------------


def count_customers():
    return len(_CUSTOMER_REGISTRY)


def sum_lines():
    return sum(c.line for c in _CUSTOMER_REGISTRY)


def avg_otb():
    if not _CUSTOMER_REGISTRY:
        return 0
    return int(math.floor(sum(open_to_buy(c) for c in _CUSTOMER_REGISTRY)
                         / len(_CUSTOMER_REGISTRY)))


def count_active_by_type(htype):
    return sum(1 for h in _HOLDS if h.status == "active" and h.htype == htype)


def total_released():
    return _RELEASED_COUNT


def total_pay_posted():
    return _PAY_POSTED


def count_by_risk_band(band):
    return sum(1 for c in _CUSTOMER_REGISTRY
               if risk_band(c) == band)


def count_overrides_by_status(status):
    return sum(1 for o in _OVERRIDES if o.status == status)


# -------------------------------------------------------------------
# 14. seed.aura
# -------------------------------------------------------------------


def seed_scenario():
    # 4 customers with lines 3000, 2500, 2000, 2000  => LINE_TOTAL = 9500
    c1 = register_customer(make_customer("c1", "Acme",    3000))
    c2 = register_customer(make_customer("c2", "Beta",    2500))
    c3 = register_customer(make_customer("c3", "Gamma",   2000))
    c4 = register_customer(make_customer("c4", "Delta",   2000))

    # pay-histories (only 1 default + many late -> c1 high, c2 med,
    # c3/c4 low)
    c1.pay_history = make_pay_history(on_time=1, late=1, default_=1)   # score = 2+5 = 7 -> high
    c2.pay_history = make_pay_history(on_time=5, late=3, default_=0)   # score = 6  -> med  (>=2)
    c3.pay_history = make_pay_history(on_time=8, late=1, default_=0)   # score = 2  -> med? -> low (we want low, so bump down)
    c3.pay_history.late = 0
    c4.pay_history = make_pay_history(on_time=10, late=0, default_=0)  # score = 0  -> low

    # initialise risk bands immediately
    for c in _CUSTOMER_REGISTRY:
        risk_band(c)

    # 2 unposted invoices
    add_unposted_invoice(c1, 400)
    add_unposted_invoice(c2, 150)

    log_event("seed", {"customers": 4})


# -------------------------------------------------------------------
# 15. main.aura
# -------------------------------------------------------------------

def run_main():
    seed_scenario()
    c1 = find_customer("c1")
    c2 = find_customer("c2")
    c3 = find_customer("c3")
    c4 = find_customer("c4")

    # ----- Order A : cust c1 amount 2700 -> HARD -----
    a_type = policy_decide(c1, 2700)          # 'hard'
    a_hold = place_hold(c1, a_type, 2700)

    # ----- Order B : cust c2 amount 1200 -> SOFT -----
    b_type = policy_decide(c2, 1200)          # 'soft'
    b_hold = place_hold(c2, b_type, 1200)

    # ----- Order C : cust c2 amount 900 (pushes over soft) -> SOFT -----
    c_type = policy_decide(c2, 900)           # 'soft'
    c_hold = place_hold(c2, c_type, 900)

    # ----- override workflow -----
    ov_a  = request_override(a_hold, "mgr-A")
    approve_override(ov_a)                    # OVERRIDE_APPROVED += 1

    ov_c  = request_override(c_hold, "mgr-C")
    deny_override(ov_c)                       # OVERRIDE_DENIED += 1

    # ----- payments: 300 for c1, 200 for c2 -----
    post_payment(c1, 300)
    payment_apply_to_holds(c1, 300)           # releases a_hold

    post_payment(c2, 200)
    payment_apply_to_holds(c2, 200)           # releases c_hold

    # ----- shipments: c3 ships 500 -----
    record_shipment(c3, 500)

    # final stats -> 12 KEY=value lines
    print("CUSTOMERS=", count_customers())
    print("LINE_TOTAL=", sum_lines())
    print("OTB_AVG=", avg_otb())
    print("HARD_HOLDS=", count_active_by_type("hard"))
    print("SOFT_HOLDS=", count_active_by_type("soft"))
    print("RELEASED=", total_released())
    print("PAY_POSTED=", total_pay_posted())
    print("RISK_HIGH=", count_by_risk_band("high"))
    print("RISK_MED=", count_by_risk_band("med"))
    print("RISK_LOW=", count_by_risk_band("low"))
    print("OVERRIDE_APPROVED=", count_overrides_by_status("approved"))
    print("OVERRIDE_DENIED=", count_overrides_by_status("denied"))


if __name__ == "__main__":
    run_main()
