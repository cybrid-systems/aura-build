import time
import random
import math

# ---------- toy "Aura" runtime: plain lists/alists, no records ----------
TICK = [0]
def now_tick():
    TICK[0] += 1
    return TICK[0]

def round2(n):
    # truncate (no banker's rounding): floor to 2 decimals
    if n >= 0:
        return math.floor(n * 100) / 100
    else:
        return -math.floor(-n * 100) / 100

def pad_right(s, n):
    s = str(s)
    if len(s) >= n:
        return s
    return s + " " * (n - len(s))

# ---------- market-clock ----------
def trading_day():
    return True

def slot_count(horizon, slot):
    return horizon // slot

# ---------- venue-registry ----------
VENUES = [
    ("NYSE",  0.0003, 1),
    ("ARCA",  0.0002, 2),
    ("IEX",   0.0009, 1),
    ("BATS",  0.0002, 2),
    ("DARK1", 0.0001, 3),
]

def venue_list():
    return [v[0] for v in VENUES]

def venue_fee(v):
    for name, fee, lat in VENUES:
        if name == v:
            return fee
    return 0.0

def venue_latency(v):
    for name, fee, lat in VENUES:
        if name == v:
            return lat
    return 0

# ---------- order-types ----------
def make_parent(id_, side, qty, px, tif):
    return [("id", id_), ("side", side), ("qty", qty), ("px", px), ("tif", tif), ("parent", True)]

def is_parent(o):
    if not isinstance(o, list):
        return False
    for k, v in o:
        if k == "parent" and v is True:
            return True
    return False

def parent_qty(o):
    for k, v in o:
        if k == "qty":
            return v
    return 0

def parent_side(o):
    for k, v in o:
        if k == "side":
            return v
    return ""

# ---------- accounts ----------
ACCOUNTS = [
    ("ACC-A", 0.50),
    ("ACC-B", 0.30),
    ("ACC-C", 0.20),
]

def account_list():
    return ACCOUNTS

def account_acct(a):
    return a[0]

def account_share(a):
    return a[1]

# ---------- slicers ----------
def _new_child_id_seq(parent_id, n):
    base = parent_id
    seq = []
    for i in range(1, n + 1):
        seq.append(f"{base}-C{i:04d}")
    return seq

def _make_children(parent, qtys):
    base_id = dict(parent).get("id", "P")
    ids = _new_child_id_seq(base_id, len(qtys))
    side = dict(parent).get("side", "BUY")
    px = dict(parent).get("px", 0.0)
    tif = dict(parent).get("tif", "DAY")
    out = []
    for cid, q in zip(ids, qtys):
        out.append([("id", cid), ("side", side), ("qty", q), ("px", px), ("tif", tif), ("parent", False)])
    return out

def slice_pov(parent, mkt_volumed, children):
    # pad mkt_volumed with 1s to length children
    mv = list(mkt_volumed)
    while len(mv) < children:
        mv.append(1)
    total = sum(mv[:children])
    pqty = parent_qty(parent)
    raw = [pqty * (v / total) for v in mv[:children]]
    # distribute integer remainder so qty sum equals pqty
    floors = [int(math.floor(x)) for x in raw]
    rem = pqty - sum(floors)
    # give +1 to the largest fractional parts
    fracs = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]), reverse=True)
    for i in range(rem):
        floors[fracs[i]] += 1
    return _make_children(parent, floors)

def slice_twap(parent, horizon_secs, slot_secs, children):
    pqty = parent_qty(parent)
    base = pqty // children
    qtys = [base] * children
    rem = pqty - sum(qtys)
    for i in range(rem):
        qtys[i] += 1
    return _make_children(parent, qtys)

def slice_vwap(parent, vwap_buckets, children):
    # equal-weighted (toy); treat buckets as weights
    b = list(vwap_buckets)
    while len(b) < children:
        b.append(1)
    total = sum(b[:children])
    pqty = parent_qty(parent)
    raw = [pqty * (w / total) for w in b[:children]]
    floors = [int(math.floor(x)) for x in raw]
    rem = pqty - sum(floors)
    fracs = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]), reverse=True)
    for i in range(rem):
        floors[fracs[i]] += 1
    return _make_children(parent, floors)

def slice_liquidity(parent, venues, children, urgency):
    # sizes biased to higher urgency -> larger first children
    pqty = parent_qty(parent)
    weights = [(urgency ** i) for i in range(children)]
    total = sum(weights)
    raw = [pqty * (w / total) for w in weights]
    floors = [int(math.floor(x)) for x in raw]
    rem = pqty - sum(floors)
    fracs = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]), reverse=True)
    for i in range(rem):
        floors[fracs[i]] += 1
    return _make_children(parent, floors)

# ---------- router ----------
def route(children, venues):
    out = []
    for i, c in enumerate(children):
        v = venues[i % len(venues)]
        out.append((c, v))
    return out

def route_one(child, venue):
    return (child, venue)

# ---------- fill-sim ----------
def simulate_fills(routed, mid_px, volatility):
    rng = random.Random(7)
    fills = []
    for child, venue in routed:
        qty = dict(child).get("qty", 0)
        if qty <= 0:
            continue
        # partial fill probability tied to latency (lower = better)
        lat = venue_latency(venue)
        fill_ratio = max(0.0, 1.0 - 0.15 * lat + rng.uniform(-volatility, volatility))
        fill_ratio = min(1.0, fill_ratio)
        filled = int(math.floor(qty * fill_ratio))
        if filled <= 0:
            continue
        # px drift
        drift = rng.uniform(-volatility, volatility)
        px = round2(mid_px * (1.0 + drift))
        fills.append((dict(child).get("id"), venue, filled, px))
    return fills

def aggregate_fills(fills):
    total_qty = sum(f[2] for f in fills)
    if total_qty == 0:
        return (0, 0.0, 0)
    notional = sum(f[2] * f[3] for f in fills)
    avg_px = notional / total_qty
    return (total_qty, round2(avg_px), len(fills))

# ---------- risk-monitor ----------
def completion_pct(parent, fills):
    pqty = parent_qty(parent)
    if pqty == 0:
        return 0.0
    filled = sum(f[2] for f in fills)
    return 100.0 * filled / pqty

def risk_breached(parent, fills, threshold):
    return completion_pct(parent, fills) < threshold

# ---------- allocators ----------
def allocate_fifo(accounts, total_filled):
    # FIFO: first account gets filled up to its share*total (toy: just split by share)
    remaining = total_filled
    out = []
    for i, a in enumerate(accounts):
        if i == len(accounts) - 1:
            q = remaining
        else:
            q = int(math.floor(total_filled * account_share(a)))
            q = min(q, remaining)
        out.append((account_acct(a), q))
        remaining -= q
    return out

def allocate_pro_rata(accounts, total_filled):
    raw = [total_filled * account_share(a) for a in accounts]
    floors = [int(math.floor(x)) for x in raw]
    rem = total_filled - sum(floors)
    fracs = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]), reverse=True)
    for i in range(rem):
        floors[fracs[i]] += 1
    return [(account_acct(accounts[i]), floors[i]) for i in range(len(accounts))]

def allocate_filled_qty(accounts, per_account_caps, total_filled):
    out = []
    for i, a in enumerate(accounts):
        cap = per_account_caps[i] if i < len(per_account_caps) else total_filled
        q = min(cap, total_filled)
        out.append((account_acct(a), q))
    return out

# ---------- main scenario ----------
def main():
    # Build parent
    parent = make_parent("P-0001", "BUY", 10000, 50.00, "DAY")

    # Choose strategy: liquidity-seeking with high urgency
    strategy = "LIQSEEK"
    venues = venue_list()
    urgency = 2.0
    children_n = 5
    children = slice_liquidity(parent, venues, children_n, urgency)

    # Route
    routed = route(children, venues)

    # Simulate fills at mid=50.00, vol=0.01
    fills = simulate_fills(routed, 50.00, 0.01)

    # Aggregate
    total_filled, avg_px, num_fills = aggregate_fills(fills)

    # Risk
    cpct = completion_pct(parent, fills)
    breached = risk_breached(parent, fills, 50.0)

    # Allocation: pro-rata
    rule = "PRO-RATA"
    allocs = allocate_pro_rata(ACCOUNTS, total_filled)
    alloc_sum = sum(q for _, q in allocs)
    checksum = "OK" if alloc_sum == total_filled else "FAIL"

    venues_used = sorted(set(f[1] for f in fills))

    # Print KEY=value lines (exactly the 16 keys in order)
    lines = [
        ("PARENT_ID",         dict(parent).get("id")),
        ("PARENT_SIDE",       dict(parent).get("side")),
        ("PARENT_QTY",        parent_qty(parent)),
        ("STRATEGY_CHOSEN",   strategy),
        ("NUM_CHILDREN",      len(children)),
        ("TOTAL_CHILD_QTY",   sum(dict(c).get("qty", 0) for c in children)),
        ("FILLED_CHILD_QTY",  total_filled),
        ("COMPLETION_PCT",    round2(cpct)),
        ("VENUES_USED",       ",".join(venues_used)),
        ("AVG_FILL_PX",       avg_px),
        ("NUM_FILLS",         num_fills),
        ("RISK_BREACHED",     "TRUE" if breached else "FALSE"),
        ("ALLOC_RULE",        rule),
        ("ALLOC_ACCOUNTS",    ",".join(a for a, _ in allocs)),
        ("ALLOC_TOTAL_FILLED", alloc_sum),
        ("ALLOC_CHECKSUM",    checksum),
    ]
    for k, v in lines:
        print(f"{k}={v}")

if __name__ == "__main__":
    main()
