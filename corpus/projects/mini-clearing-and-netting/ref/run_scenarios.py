"""
Python reference implementation of the Aura "Mini Clearing and Netting Engine".
This re-implements the GOAL semantics in a single self-contained Python script
using only stdlib, mirroring the behavior described in GOAL.md.
"""
import math
from collections import defaultdict

# -------------------- types.aura --------------------
class Trade:
    _counter = 0
    def __init__(self, tid, ccy, payer, payee, amount, value_date):
        self.id = tid if tid is not None else f"T{Trade._counter}"
        Trade._counter += 1
        self.ccy = ccy
        self.payer = payer
        self.payee = payee
        self.amount = float(amount)
        self.value_date = value_date

def trade_id(t): return t.id
def trade_ccy(t): return t.ccy
def trade_payer(t): return t.payer
def trade_payee(t): return t.payee
def trade_amount(t): return t.amount
def trade_value_date(t): return t.value_date
def trade_is_trade(x): return isinstance(x, Trade)

# -------------------- registry.aura --------------------
_REGISTRY = []

def reset_registry():
    global _REGISTRY
    _REGISTRY = []

def register_trade(t):
    _REGISTRY.append(t)

def all_trades():
    return list(_REGISTRY)

def trades_for_date(vd):
    return [t for t in _REGISTRY if t.value_date == vd]

def party_list():
    s = set()
    for t in _REGISTRY:
        s.add(t.payer); s.add(t.payee)
    return sorted(s)

# -------------------- calendar.aura --------------------
def parse_date(s): return s  # ISO string passthrough
def format_date(d): return d
def value_date_is(x): return isinstance(x, str)
def choose_value_date(trades, today):
    if not trades:
        return today
    # Return earliest distinct value date present in the book
    return min({t.value_date for t in trades})

# -------------------- currency.aura --------------------
def normalize_ccy(c): return c.upper()
def same_ccy(a, b): return normalize_ccy(a) == normalize_ccy(b)
def amount_plus(a, b): return float(a) + float(b)
def amount_minus(a, b): return float(a) - float(b)
def sum_amounts(lst): return float(sum(lst))

# -------------------- mta.aura --------------------
_MTA = {}

def set_mta(ccy, amt):
    _MTA[normalize_ccy(ccy)] = float(amt)

def get_mta(ccy):
    return _MTA.get(normalize_ccy(ccy), 0.0)

def below_mta(amount, ccy):
    return float(amount) < get_mta(ccy)

# -------------------- paythrough.aura --------------------
_HIERARCHY = {}        # party -> tier (e.g. CCP=0, CM=1, Client=2)
_PARENT = {}           # party -> parent (CCP roots parties)
_DEPTH = 0

def set_paythrough(hier):
    """hierarchy: list of (party, tier) pairs; depth is max tier+1."""
    global _DEPTH, _HIERARCHY, _PARENT
    _HIERARCHY = {p: tier for (p, tier) in hier}
    _PARENT = {}
    # Parent = next-lower tier party (alphabetically nearest)
    by_tier = defaultdict(list)
    for p, t in _HIERARCHY.items():
        by_tier[t].append(p)
    for p, t in _HIERARCHY.items():
        parents = []
        for tt in range(t - 1, -1, -1):
            parents.extend(by_tier.get(tt, []))
        if parents:
            _PARENT[p] = sorted(parents)[0]
    _DEPTH = (max(_HIERARCHY.values()) + 1) if _HIERARCHY else 0

def paythrough_chain(party):
    out = []
    cur = party
    seen = set()
    while cur is not None and cur not in seen:
        seen.add(cur); out.append(cur); cur = _PARENT.get(cur)
    return out

def effective_counterparty(party):
    """Top-most ancestor (CCP if any)."""
    chain = paythrough_chain(party)
    return chain[-1] if chain else party

def tier_depth():
    return _DEPTH

# -------------------- novation.aura --------------------
_NOVATION_POLICY = 'off'
_NOVATION_APPLIED = False

def set_novation_policy(mode):
    global _NOVATION_POLICY
    if mode in ('off', 'ccp'):
        _NOVATION_POLICY = mode

def novation_policy():
    return _NOVATION_POLICY

def apply_novation(vd, ccy):
    """Replace payer/payee on trades in date/ccy with their effective counterparty."""
    global _NOVATION_APPLIED
    applied = 0
    if _NOVATION_POLICY != 'ccp':
        _NOVATION_APPLIED = False
        return applied
    for t in _REGISTRY:
        if t.value_date == vd and same_ccy(t.ccy, ccy):
            new_payer = effective_counterparty(t.payer)
            new_payee = effective_counterparty(t.payee)
            if new_payer != t.payer or new_payee != t.payee:
                t.payer, t.payee = new_payer, new_payee
                applied += 1
    _NOVATION_APPLIED = applied > 0
    return applied

# -------------------- bilateral.aura --------------------
def gross_exposure(vd, ccy):
    return sum(t.amount for t in _REGISTRY
               if t.value_date == vd and same_ccy(t.ccy, ccy))

def _bilateral_map(vd, ccy):
    m = defaultdict(float)
    for t in _REGISTRY:
        if t.value_date == vd and same_ccy(t.ccy, ccy):
            a, b = sorted([t.payer, t.payee])
            m[(a, b)] += t.amount
    return m

def exposure_between(a, b, vd, ccy):
    key = tuple(sorted([a, b]))
    return _bilateral_map(vd, ccy).get(key, 0.0)

def all_bilateral_pairs(vd, ccy):
    return sorted(_bilateral_map(vd, ccy).items())

# -------------------- mts.aura --------------------
_MTA_FILTERED = 0

def mta_filtered_pairs(vd, ccy):
    return _MTA_FILTERED

def apply_mta_filter(vd, ccy):
    """Drop net legs whose absolute value is below MTA. Re-register filtered."""
    global _MTA_FILTERED
    keep = []
    filtered = 0
    mta = get_mta(ccy)
    for t in _REGISTRY:
        if t.value_date == vd and same_ccy(t.ccy, ccy):
            if abs(t.amount) < mta:
                filtered += 1
                continue
        keep.append(t)
    _MTA_FILTERED = filtered
    # Mutate registry in place
    _REGISTRY.clear()
    _REGISTRY.extend(keep)
    return filtered

# -------------------- netting.aura --------------------
def _net_map(vd, ccy):
    """Sum raw trade amounts per party (incoming - outgoing)."""
    net = defaultdict(float)
    for t in _REGISTRY:
        if t.value_date == vd and same_ccy(t.ccy, ccy):
            net[t.payee] += t.amount
            net[t.payer] -= t.amount
    return dict(net)

def net_obligations(vd, ccy):
    m = _net_map(vd, ccy)
    return sum(abs(v) for v in m.values()) / 2.0  # per spec "NET_OBLIGATIONS"

def net_position(party, vd, ccy):
    return _net_map(vd, ccy).get(party, 0.0)

def zero_sum(net_map):
    return math.isclose(sum(net_map.values()), 0.0, abs_tol=1e-6)

def settlement_instructions(vd, ccy):
    """Greedy: pair biggest debtor with biggest creditor."""
    inst = []
    net = {k: v for k, v in _net_map(vd, ccy).items() if not math.isclose(v, 0, abs_tol=1e-9)}
    def take_pos():
        return max(((k, v) for k, v in net.items() if v > 0), key=lambda x: x[1], default=(None, 0))
    def take_neg():
        return min(((k, v) for k, v in net.items() if v < 0), key=lambda x: x[1], default=(None, 0))
    while True:
        d_name, d_amt = take_neg()
        c_name, c_amt = take_pos()
        if d_name is None or c_name is None:
            break
        pay = min(-d_amt, c_amt)
        inst.append((d_name, c_name, pay))
        net[d_name] += pay
        net[c_name] -= pay
        if math.isclose(net[d_name], 0, abs_tol=1e-9): del net[d_name]
        if math.isclose(net[c_name], 0, abs_tol=1e-9): del net[c_name]
    return inst

# -------------------- settlement.aura --------------------
class Instruction:
    def __init__(self, payer, payee, amount):
        self.payer = payer
        self.payee = payee
        self.amount = float(amount)
def build_instructions(vd, ccy):
    return [Instruction(p, q, a) for (p, q, a) in settlement_instructions(vd, ccy)]
def instruction_payer(i): return i.payer
def instruction_payee(i): return i.payee
def instruction_amount(i): return i.amount
def instructions_total_out(instrs):
    return sum(i.amount for i in instrs)

# -------------------- efficiency.aura --------------------
_CLEARED = 0
_UNCLEARED = 0

def set_cleared(c, u):
    global _CLEARED, _UNCLEARED
    _CLEARED, _UNCLEARED = c, u

def efficiency_ratio(gross, net):
    if gross <= 0: return 0.0
    return round(1.0 - (net / gross), 4)

def largest_single_payment(instrs):
    if not instrs: return 0.0
    return max(i.amount for i in instrs)

def cleared_count(): return _CLEARED
def uncleared_count(): return _UNCLEARED

# -------------------- report.aura --------------------
_REPORT_BIC = "REGBIC01"

def report_bic(): return _REPORT_BIC

def regulator_report(vd, ccy):
    g = gross_exposure(vd, ccy)
    n = net_obligations(vd, ccy)
    return {"gross": g, "net": n, "efficiency": efficiency_ratio(g, n)}

def report_lines(vd, ccy):
    return ["GROSS=" + str(regulator_report(vd, ccy)["gross"]),
            "NET=" + str(regulator_report(vd, ccy)["net"])]

# -------------------- compliance.aura --------------------
def check_consistency(vd, ccy):
    if not zero_sum_ok(vd, ccy): return 'FAIL'
    if not efficiency_bounds_ok(vd, ccy): return 'FAIL'
    if not mtas_applied_ok(vd, ccy): return 'FAIL'
    return 'PASS'

def zero_sum_ok(vd, ccy):
    return zero_sum(_net_map(vd, ccy))

def efficiency_bounds_ok(vd, ccy):
    g = gross_exposure(vd, ccy); n = net_obligations(vd, ccy)
    if g < 0 or n < 0: return False
    if n - g > 1e-6: return False
    return True

def mtas_applied_ok(vd, ccy):
    mta = get_mta(ccy)
    return all(abs(t.amount) >= mta - 1e-9
               for t in _REGISTRY
               if t.value_date == vd and same_ccy(t.ccy, ccy))

# -------------------- scenario.aura --------------------
def party_hierarchy():
    # CCP root, two clearing members, four clients -> tiers 0,1,1,2,2,2,2
    return [("CCP1", 0), ("CM_A", 1), ("CM_B", 1),
            ("CLI_A1", 2), ("CLI_A2", 2),
            ("CLI_B1", 2), ("CLI_B2", 2)]

def scenario_ccy(): return "USD"

def scenario_value_date(): return "2025-03-17"

def scenario_trades():
    # Raw bilateral trades (pre-novation): clients trade through CMs
    return [
        Trade("T01", "USD", "CLI_A1", "CLI_B1", 12000, "2025-03-17"),
        Trade("T02", "USD", "CLI_A1", "CLI_B2",  8000, "2025-03-17"),
        Trade("T03", "USD", "CLI_A2", "CLI_B1",  5500, "2025-03-17"),
        Trade("T04", "USD", "CLI_A2", "CLI_B2",  3000, "2025-03-17"),  # below MTA -> filtered
        Trade("T05", "USD", "CM_A",  "CM_B",   15000, "2025-03-17"),
        Trade("T06", "USD", "CLI_A1", "CLI_A2", 4500, "2025-03-17"),  # same CM
        Trade("T07", "USD", "CLI_B1", "CLI_B2", 6500, "2025-03-17"),  # same CM
        Trade("T08", "USD", "CLI_A1", "CCP1",  9000, "2025-03-17"),
    ]

def seed_scenario():
    reset_registry()
    for t in scenario_trades():
        register_trade(t)

# -------------------- main.aura (run) --------------------
def run():
    seed_scenario()
    ccy = scenario_ccy()
    set_mta(ccy, 1000)
    set_paythrough(party_hierarchy())
    set_novation_policy('ccp')

    today = "2025-03-17"
    vd = choose_value_date(all_trades(), today)

    novation_applied_n = apply_novation(vd, ccy)
    apply_mta_filter(vd, ccy)

    gross = gross_exposure(vd, ccy)
    net = net_obligations(vd, ccy)
    eff = efficiency_ratio(gross, net)

    instrs = build_instructions(vd, ccy)

    parties = party_list()
    cps = {effective_counterparty(p) for p in parties}
    c_count = len(cps)
    u_count = len(parties) - c_count

    # Track cleared/uncleared relative to CCP presence after novation
    has_ccp = any(p.upper() == 'CCP1' for p in parties)
    set_cleared(c_count if has_ccp else 0,
                u_count if has_ccp else len(parties))

    print("VALUE_DATE=" + format_date(vd))
    print("TRADE_COUNT=" + str(len(trades_for_date(vd))))
    print("GROSS_OBLIGATIONS=" + str(int(round(gross))))
    print("NET_OBLIGATIONS=" + str(int(round(net))))
    print("NETTING_EFFICIENCY=" + str(eff))
    print("COUNTERPARTY_COUNT=" + str(len(parties)))
    print("CLEARED_COUNT=" + str(cleared_count()))
    print("UNCLEARED_COUNT=" + str(uncleared_count()))
    print("MTA_FILTERED_COUNT=" + str(mta_filtered_pairs(vd, ccy)))
    print("SETTLEMENT_INSTRUCTION_COUNT=" + str(len(instrs)))
    print("LARGEST_SINGLE_NET_PAYMENT=" + str(int(round(largest_single_payment(instrs)))))
    print("NOVATION_APPLIED=" + str(novation_applied_n))
    print("PAY_THROUGH_TIER_DEPTH=" + str(tier_depth()))
    print("REPORT_BIC=" + report_bic())
    print("COMPLIANCE_CHECK=" + check_consistency(vd, ccy))

if __name__ == "__main__":
    run()
