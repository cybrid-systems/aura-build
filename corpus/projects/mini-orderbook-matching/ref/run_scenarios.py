#!/usr/bin/env python3
"""Mini-Orderbook Matching Engine - Python reference implementation.

Emulates the Aura multi-file project with a single in-memory toy matching
engine: price-time priority on the book, marketable orders cross the spread
generating trades, partial fills rest the remainder, cancels by order id.
"""
import sys

# ----------------------------- event ----------------------------------------

def make_event(etype, side, price, qty, eid):
    return {"type": etype, "side": side, "price": price, "qty": qty, "id": eid}

def event_type(e):   return e["type"]
def event_side(e):   return e["side"]
def event_price(e):  return e["price"]
def event_qty(e):    return e["qty"]
def event_id(e):     return e["id"]

# ----------------------------- book -----------------------------------------

def make_book(ticker):
    # buyers/sellers as association lists: key=price -> [(id, qty, ts), ...]
    return {"ticker": ticker, "buyers": [], "sellers": [], "seq": 0}

def book_ticker(b):    return b["ticker"]
def empty_book(b):
    return not b["buyers"] and not b["sellers"]
def book_buyers(b):    return b["buyers"]
def book_sellers(b):   return b["sellers"]

# ----------------------------- book_ops -------------------------------------

def _alist_insert(alist, price, entry):
    # sorted desc by price for buyers, asc for sellers handled by caller
    out = []
    placed = False
    for k, lst in alist:
        if not placed and (
            (price < k)  # caller decides by passing function
        ):
            pass
        out.append((k, lst))
    return out

def _rest_at(alist, price, ascending):
    """Insert (id, qty, seq) into price level; merge qty if id already present."""
    out = []
    placed = False
    for k, lst in alist:
        if k == price:
            lst = lst + [None]
            out.append((k, lst))
            placed = True
        else:
            out.append((k, lst))
    if not placed:
        # find insertion position
        out = []
        inserted = False
        for k, lst in alist:
            if not inserted and ((ascending and price < k) or (not ascending and price > k)):
                out.append((price, [None]))
                inserted = True
            out.append((k, lst))
        if not inserted:
            out.append((price, [None]))
    return out

def add_resting(book, side, price, qty, oid):
    """Add or augment a resting order. If same id exists at same price, add qty.
    Returns book."""
    book = dict(book)
    if side == "BUY":
        asc = True  # highest price first? for buyers we sort DESC (highest bid first)
        alist = book["buyers"]
        # use custom insertion: descending by price
        new = []
        placed = False
        for k, lst in alist:
            if not placed and price > k:
                # insert before
                new.append((price, [(oid, qty, book["seq"])]))
                placed = True
            elif not placed and price == k:
                # merge: find entry with same id
                merged = False
                nl = []
                for entry in lst:
                    if entry[0] == oid:
                        nl.append((oid, entry[1] + qty, book["seq"]))
                        merged = True
                    else:
                        nl.append(entry)
                if not merged:
                    nl.append((oid, qty, book["seq"]))
                new.append((k, nl))
                placed = True
            else:
                new.append((k, lst))
        if not placed:
            new.append((price, [(oid, qty, book["seq"])]))
        book["buyers"] = new
    else:
        alist = book["sellers"]
        new = []
        placed = False
        for k, lst in alist:
            if not placed and price < k:
                new.append((price, [(oid, qty, book["seq"])]))
                placed = True
            elif not placed and price == k:
                merged = False
                nl = []
                for entry in lst:
                    if entry[0] == oid:
                        nl.append((oid, entry[1] + qty, book["seq"]))
                        merged = True
                    else:
                        nl.append(entry)
                if not merged:
                    nl.append((oid, qty, book["seq"]))
                new.append((k, nl))
                placed = True
            else:
                new.append((k, lst))
        if not placed:
            new.append((price, [(oid, qty, book["seq"])]))
        book["sellers"] = new
    book["seq"] += 1
    return book

def _best_price(book, side):
    if side == "BUY":
        return max((k for k, _ in book["buyers"]), default=None)
    else:
        return min((k for k, _ in book["sellers"]), default=None)

def top_bid(book):
    p = _best_price(book, "BUY")
    if p is None:
        return (None, 0)
    lst = [l for k, l in book["buyers"] if k == p][0]
    return (p, sum(e[1] for e in lst))

def top_ask(book):
    p = _best_price(book, "SELL")
    if p is None:
        return (None, 0)
    lst = [l for k, l in book["sellers"] if k == p][0]
    return (p, sum(e[1] for e in lst))

def best_bid(book):
    p, q = top_bid(book)
    return {"price": p, "qty": q}

def best_ask(book):
    p, q = top_ask(book)
    return {"price": p, "qty": q}

# ----------------------------- idmap ----------------------------------------

def make_idmap():
    return set()

def idmap_register(m, oid): m.add(oid); return m
def idmap_remove(m, oid):
    m.discard(oid); return m
def idmap_has(m, oid): return oid in m
def idmap_count(m): return len(m)

# ----------------------------- queue ----------------------------------------

def make_q(): return []

def enqueue(q, e):
    q.append(e); return q

def dequeue(q):
    if not q: return (q, False)
    e = q.pop(0)
    return (q, e)

def queue_size(q): return len(q)

# ----------------------------- trade ----------------------------------------

def make_trade(taker_id, maker_id, price, qty):
    return {"taker": taker_id, "maker": maker_id, "price": price, "qty": qty}

def trade_price(t): return t["price"]
def trade_qty(t):   return t["qty"]
def trade_notional(t): return t["price"] * t["qty"]

# ----------------------------- match ----------------------------------------

def match_order(book, idmap, trade_tape, incoming):
    """Classic price-time priority: marketable order crosses spread.

    Returns (new_book, new_idmap, new_trade_tape, filled_qty, open_qty).
    open_qty>0 means remainder rests on book (incoming becomes a maker).
    """
    book = {k: (list(v) if isinstance(v, list) else v) for k, v in book.items()}
    trade_tape = list(trade_tape)
    side = event_side(incoming)
    price = event_price(incoming)
    qty_left = event_qty(incoming)
    oid = event_id(incoming)
    filled = 0

    # opposing side list and ordering
    if side == "BUY":
        opp_asc = True  # sellers sorted asc; we want best (lowest) first
        opp = book["sellers"]
    else:
        opp_asc = False  # buyers sorted desc; we want best (highest) first
        opp = book["buyers"]

    # Walk through opposing price levels, matching while marketable
    new_opp = []
    i = 0
    while qty_left > 0 and i < len(opp):
        level_price, lst = opp[i]
        marketable = (side == "BUY" and price >= level_price) or \
                      (side == "SELL" and price <= level_price)
        if not marketable:
            break
        # match FIFO within this level
        new_lst = list(lst)
        while qty_left > 0 and new_lst:
            entry = new_lst[0]
            mid, mqty, mts = entry
            fill = min(qty_left, mqty)
            trade_tape.append(make_trade(oid, mid, level_price, fill))
            filled += fill
            qty_left -= fill
            if fill == mqty:
                new_lst.pop(0)
                idmap.discard(mid)
            else:
                new_lst[0] = (mid, mqty - fill, mts)
        new_opp.append((level_price, new_lst))
        if new_lst:
            # level still has qty; remainder of incoming (if any) wouldn't cross deeper
            break
        i += 1

    # append untouched tail
    while i < len(opp):
        new_opp.append(opp[i])
        i += 1

    if side == "BUY":
        book["sellers"] = new_opp
    else:
        book["buyers"] = new_opp

    open_qty = qty_left
    if open_qty > 0:
        book = add_resting(book, side, price, open_qty, oid)
        idmap.add(oid)

    return (book, idmap, trade_tape, filled, open_qty)

# ----------------------------- cancel ---------------------------------------

def cancel_order(book, idmap, oid):
    """Remove an order by id from whatever side it's resting on. Returns (book, idmap, cancelled?, found?).
    We also support scenario where the id is not on the book (already filled or never existed)."""
    book = {k: (list(v) if isinstance(v, list) else v) for k, v in book.items()}
    found = False
    for side_key in ("buyers", "sellers"):
        alist = book[side_key]
        new = []
        for k, lst in alist:
            nl = [e for e in lst if e[0] != oid]
            if len(nl) != len(lst):
                found = True
            new.append((k, nl))
        # drop empty levels
        new = [(k, l) for k, l in new if l]
        book[side_key] = new
    if found:
        idmap.discard(oid)
    return (book, idmap, found)

# ----------------------------- tape_io / tape_out ---------------------------

def parse_line(line):
    parts = line.strip().split()
    if not parts:
        return None
    etype = parts[0]
    if etype == "NEW":
        return make_event("NEW", parts[1], int(parts[2]), int(parts[3]), parts[4])
    if etype == "CANCEL":
        return make_event("CANCEL", None, None, None, parts[1])
    return None

def build_tape(lines):
    return [parse_line(l) for l in lines if parse_line(l)]

def trade_to_line(t):
    return f"TRADE {t['price']} {t['qty']} {t['maker']}->{t['taker']}"

def render_trades(trades):
    return "\n".join(trade_to_line(t) for t in trades)

# ----------------------------- stats ----------------------------------------

def total_volume(trades):
    return sum(t["qty"] for t in trades)

def total_notional(trades):
    return sum(t["price"] * t["qty"] for t in trades)

def vwap(trades):
    n = total_notional(trades)
    v = total_volume(trades)
    return n / v if v else 0

# ----------------------------- book_view ------------------------------------

def format_top_level(book):
    bp, bq = top_bid(book)
    ap, aq = top_ask(book)
    bs = f"{bp}x{bq}" if bp is not None else "----"
    as_ = f"{ap}x{aq}" if ap is not None else "----"
    return f"{bs}  |  {as_}"

# ----------------------------- counters -------------------------------------

def make_counters():
    return {"NEW": 0, "CANCEL": 0, "FILLED": 0, "RESTING": 0}

def bump_new(c):     c["NEW"] += 1;     return c
def bump_cancel(c):  c["CANCEL"] += 1;  return c
def bump_filled(c):  c["FILLED"] += 1;  return c
def bump_resting(c): c["RESTING"] += 1; return c

def counter_value(c, key): return c.get(key, 0)

# ----------------------------- engine ---------------------------------------

def run_engine(ticker, events):
    book = make_book(ticker)
    idmap = make_idmap()
    trade_tape = []
    counters = make_counters()
    for ev in events:
        if ev is None:
            continue
        et = event_type(ev)
        if et == "NEW":
            counters = bump_new(counters)
            book, idmap, trade_tape, filled, open_qty = match_order(book, idmap, trade_tape, ev)
            if filled > 0:
                counters = bump_filled(counters)
            if open_qty > 0:
                counters = bump_resting(counters)
        elif et == "CANCEL":
            counters = bump_cancel(counters)
            book, idmap, _found = cancel_order(book, idmap, event_id(ev))
    return (book, idmap, trade_tape, counters)

# ----------------------------- scenario -------------------------------------

def scenario_events():
    """Deterministic tape: prices chosen so marketable crosses happen.

    Sequence narrative:
      1. SELL 50x4  id=A   -> rests at ask 50
      2. BUY  49x2  id=B   -> rests at bid 49
      3. BUY  50x3  id=C   -> marketable vs A; trades 2 (C fully filled, A 2 left),
                              then C trades 1 more with the next maker, but no other
                              maker exists, so C rests remaining 0? With qty 3 and only
                              A having 4, C fills 3 completely, A has 1 left.
      4. SELL 50x2  id=D   -> marketable vs C? C is filled; marketable vs existing bid side
                              BUY at 49x2 (B). BUY at 49 is < 50, not marketable, so D rests.
                              Actually we have after step 3: ask 50x1 (A partial), bid 49x2 (B).
      5. BUY  50x2  id=E   -> trades 1 with A (A removed), then 1 against D (newly resting at 50)?
                              D is at 50, marketable. E fully filled (2 trades).
      6. CANCEL B
      7. SELL 48x1 id=F   -> marketable vs remaining bid? After step 6, no bids (B cancelled).
                              Best bid is none; F rests at 48.
      8. BUY  48x1 id=G   -> trades with F at 48.

    Final book: no bids, no asks (everything fully matched).
    Final counters: NEW=8, CANCEL=1, FILLED varies, RESTING varies.
    Trades: 4 trades totalling 7 shares.
    """
    return [
        "NEW SELL 50 4 A",
        "NEW BUY  49 2 B",
        "NEW BUY  50 3 C",
        "NEW SELL 50 2 D",
        "NEW BUY  50 2 E",
        "CANCEL B",
        "NEW SELL 48 1 F",
        "NEW BUY  48 1 G",
    ]

# ----------------------------- main ------------------------------------------

def main():
    ticker = "AURA"
    raw_events = scenario_events()
    events = build_tape(raw_events)

    book, idmap, trade_tape, counters = run_engine(ticker, events)

    bb = best_bid(book)
    ba = best_ask(book)

    out = []
    out.append(f"TICKER={ticker}")
    out.append(f"EVENTS={len(events)}")
    out.append(f"ORDERS_NEW={counter_value(counters, 'NEW')}")
    out.append(f"ORDERS_CANCELLED={counter_value(counters, 'CANCEL')}")
    open_ids = idmap_count(idmap)
    out.append(f"ORDERS_OPEN_RESTING={open_ids}")
    # fully filled = NEW - RESTING  (orders that didn't rest at all)
    out.append(f"ORDERS_FULLY_FILLED={counter_value(counters, 'NEW') - counter_value(counters, 'RESTING')}")
    out.append(f"TRADES={len(trade_tape)}")
    vol = total_volume(trade_tape)
    notional = total_notional(trade_tape)
    out.append(f"TRADE_VOLUME={vol}")
    out.append(f"TRADE_NOTIONAL={notional}")
    out.append(f"VWAP={vwap(trade_tape)}")
    out.append(f"BEST_BID_PRICE={bb['price'] if bb['price'] is not None else ''}")
    out.append(f"BEST_BID_QTY={bb['qty']}")
    out.append(f"BEST_ASK_PRICE={ba['price'] if ba['price'] is not None else ''}")
    out.append(f"BEST_ASK_QTY={ba['qty']}")
    out.append(f"TOP_LEVEL={format_top_level(book)}")

    sys.stdout.write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
