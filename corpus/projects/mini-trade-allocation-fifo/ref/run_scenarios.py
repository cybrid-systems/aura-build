#!/usr/bin/env python3
"""Reference implementation of mini-trade-allocation-fifo Aura scenario."""
from collections import deque

# ---------- util ----------
_TICK = [0]
def now_tick():
    return _TICK[0]

def round2(n):
    return round(n + 0.0, 2)

def fmt_money(n):
    return f"{round2(n):.2f}"

# ---------- lot ----------
def make_lot(client, qty, cost, basis_date):
    return {'client': client, 'qty': qty, 'cost': cost, 'date': basis_date, 'id': None}

def lot_qty(l): return l['qty']
def lot_cost(l): return l['cost']
def lot_client(l): return l['client']
def lot_date(l): return l['date']

def lot_decrease(l, qty):
    l['qty'] = l['qty'] - qty

def lot_set_qty(l, qty):
    l['qty'] = qty

def lots_by_client(lots, client):
    return [l for l in lots if l['client'] == client]

def lots_total_qty(lots):
    return sum(l['qty'] for l in lots)

# ---------- block ----------
def make_block(id_, instr, side, qty, price, ts):
    return {'id': id_, 'instr': instr, 'side': side, 'qty': qty, 'price': price, 'ts': ts}

def block_qty(b): return b['qty']
def block_price(b): return b['price']
def block_side(b): return b['side']
def block_instr(b): return b['instr']
def block_ts(b): return b['ts']
def block_id(b): return b['id']

# ---------- ledger ----------
def make_ledger():
    return {'lots': [], 'blocks': [], 'ticks': 0, 'reassignments': [], 'activity': []}

def ledger_add_lot(led, lot):
    if lot['id'] is None:
        lot['id'] = f"L{len(led['lots'])+1:03d}"
    led['lots'].append(lot)

def ledger_add_block(led, blk):
    led['blocks'].append(blk)
    led['activity'].append(blk)

def ledger_lots(led): return led['lots']
def ledger_blocks(led): return led['blocks']
def ledger_ticks(led): return led['ticks']

def ledger_tick(led):
    return led['ticks']

def ledger_bump(led):
    led['ticks'] += 1

# ---------- policy ----------
def policy_name(p): return p

def _ordered_lots(lots, policy, side):
    if side == 'BUY':
        # Buying creates a new lot scenario - but we consume existing lots.
        # For buys we don't allocate from existing lots in the standard sense.
        return []
    # For SELL, consume lots in policy order
    if policy == 'FIFO':
        return sorted(lots, key=lambda l: (l['date'], id(l)))
    elif policy == 'LIFO':
        return sorted(lots, key=lambda l: (-l['date'], id(l)))
    elif policy == 'HIFO':
        return sorted(lots, key=lambda l: -l['cost'])
    return list(lots)

def allocate(led, block, policy):
    side = block['side']
    qty = block['qty']
    price = block['price']
    ts = block['ts']
    instr = block['instr']
    fills = []
    if side == 'BUY':
        return fills
    # SELL: consume existing lots greedily
    candidates = [l for l in led['lots'] if l['qty'] > 0 and l.get('instr', 'ACME') == instr]
    ordered = _ordered_lots(candidates, policy, side)
    remaining = qty
    for lot in ordered:
        if remaining <= 0:
            break
        take = min(lot['qty'], remaining)
        cost_basis = lot['cost']
        realized = (price - cost_basis) * take
        fills.append({
            'client': lot['client'],
            'lot_id': lot['id'],
            'qty': take,
            'price': price,
            'cost_basis': cost_basis,
            'realized': realized,
            'instr': instr,
            'ts': ts,
        })
        lot_decrease(lot, take)
        remaining -= take
    return fills

# ---------- pnl ----------
def realized_pnl(fills):
    return sum(f['realized'] for f in fills)

def flag_wash(fill, ledger):
    # Wash if same client has opposite-side activity within 30 ticks
    target_side = 'BUY' if fill['side_marker'] == 'SELL' else 'SELL' if fill.get('side_marker') else 'BUY'
    # fill doesn't carry side directly; infer from context via the block that produced it
    # We'll store side on the fill at allocation time - patch here
    return fill.get('wash', False)

def wash_flags(fills, ledger):
    # For each fill, check if same client has opposite block within 30 ticks
    for f in fills:
        is_wash = False
        for blk in ledger['blocks']:
            if blk['ts'] == f['ts'] and blk['instr'] == f['instr']:
                continue
            if blk['instr'] != f['instr']:
                continue
            # opposite side
            opp = 'BUY' if f.get('side') == 'SELL' else 'SELL'
            if blk['side'] != opp:
                continue
            # same client block? Only flag if block is for this client - blocks are generic
            # The spec says "same-client opposite-side block" but blocks aren't tagged client.
            # Use heuristic: flag if any same-instr opposite block within 30 ticks
            if abs(blk['ts'] - f['ts']) <= 30:
                is_wash = True
                break
        f['wash'] = is_wash
    return [f['wash'] for f in fills]

# ---------- reassign ----------
def reassign_ledger(led, from_client, to_client, lots):
    moved = 0
    for l in led['lots']:
        if l['client'] == from_client and l['qty'] > 0:
            l['client'] = to_client
            moved += 1
    led['reassignments'].append({'from': from_client, 'to': to_client, 'count': moved, 'tick': led['ticks']})
    return moved

# ---------- report ----------
def count_open_lots(led):
    return sum(1 for l in led['lots'] if l['qty'] > 0)

def count_fills(fills):
    return len(fills)

def total_pnl(fills):
    return sum(f['realized'] for f in fills)

def count_wash(flags):
    return sum(1 for f in flags if f)

def count_reassigned(ledger):
    return sum(r['count'] for r in ledger['reassignments'])

def ledger_ticks_fn(led):
    return led['ticks']

def summarize(led, blocks, fills_fifo, fills_lifo, fills_hifo,
              pnl_fifo, pnl_lifo, pnl_hifo, wash):
    # We'll compute per-policy fills again to keep side marker on fills
    pass

# ---------- main scenario ----------
def run():
    # Reset tick
    _TICK[0] = 0

    led = make_ledger()

    # Build lots on ACME for 4 clients, mixed cost bases and dates
    # client, qty, cost, date
    lots_data = [
        ('C1', 100, 10.0, 1),
        ('C2',  80, 12.0, 2),
        ('C3',  60, 15.0, 3),
        ('C4',  50,  8.0, 4),
        ('C1',  50, 20.0, 5),
    ]
    for c, q, p, d in lots_data:
        lot = make_lot(c, q, p, d)
        lot['instr'] = 'ACME'
        ledger_add_lot(led, lot)

    # Add 3 blocks: buy, sell, sell
    blocks = [
        make_block('B1', 'ACME', 'BUY',  50, 18.0, 10),
        make_block('B2', 'ACME', 'SELL', 90, 22.0, 20),
        make_block('B3', 'ACME', 'SELL', 60, 19.0, 25),
    ]
    for b in blocks:
        ledger_add_block(led, b)

    INSTRUMENT = 'ACME'
    CLIENTS = 4

    # For each block run allocate under each policy
    # We need separate ledger snapshots per policy so consumption doesn't cross-contaminate.
    # Build three ledgers: one per policy run.
    def fresh_ledger():
        nl = make_ledger()
        for c, q, p, d in lots_data:
            l = make_lot(c, q, p, d)
            l['instr'] = 'ACME'
            ledger_add_lot(nl, l)
        for b in blocks:
            ledger_add_block(nl, b)
        return nl

    fills_fifo_all, fills_lifo_all, fills_hifo_all = [], [], []

    for policy_name_str, bucket in [('FIFO', fills_fifo_all), ('LIFO', fills_lifo_all), ('HIFO', fills_hifo_all)]:
        nled = fresh_ledger()
        for b in blocks:
            if b['side'] == 'SELL':
                fs = allocate(nled, b, policy_name_str)
                for f in fs:
                    f['side'] = 'SELL'
                    f['instr'] = 'ACME'
                bucket.extend(fs)
            ledger_bump(nled)

    # Tag wash flags using a shared ledger that has all blocks
    wash_f_fifo = wash_flags(fills_fifo_all, led)
    wash_f_lifo = wash_flags(fills_lifo_all, led)
    wash_f_hifo = wash_flags(fills_hifo_all, led)

    # Reassignment: move C1 remaining lots to C2
    # Compute remaining C1 lots from the original ledger (untouched by allocation since
    # we used snapshots). Actually original ledger has all lots intact since we never
    # allocated against it. So remaining C1 lots = all C1 lots.
    remaining_c1 = [l for l in led['lots'] if l['client'] == 'C1']
    reassign_ledger(led, 'C1', 'C2', remaining_c1)

    LOTS_OPEN = count_open_lots(led)
    BLOCKS_N = len(blocks)
    ALLOC_FIFO_FILLS = count_fills(fills_fifo_all)
    ALLOC_LIFO_FILLS = count_fills(fills_lifo_all)
    ALLOC_HIFO_FILLS = count_fills(fills_hifo_all)
    PNL_FIFO = round2(realized_pnl(fills_fifo_all))
    PNL_LIFO = round2(realized_pnl(fills_lifo_all))
    PNL_HIFO = round2(realized_pnl(fills_hifo_all))
    WASH_FLAGS = count_wash(wash_f_fifo) + count_wash(wash_f_lifo) + count_wash(wash_f_hifo)
    REASSIGNED = count_reassigned(led)
    LEDGER_TICKS = ledger_ticks_fn(led)
    RUN_ID = "mini-trade-allocation-fifo-001"

    print(f"INSTRUMENT={INSTRUMENT}")
    print(f"CLIENTS={CLIENTS}")
    print(f"LOTS_OPEN={LOTS_OPEN}")
    print(f"BLOCKS={BLOCKS_N}")
    print(f"ALLOC_FIFO_FILLS={ALLOC_FIFO_FILLS}")
    print(f"ALLOC_LIFO_FILLS={ALLOC_LIFO_FILLS}")
    print(f"ALLOC_HIFO_FILLS={ALLOC_HIFO_FILLS}")
    print(f"PNL_FIFO={PNL_FIFO}")
    print(f"PNL_LIFO={PNL_LIFO}")
    print(f"PNL_HIFO={PNL_HIFO}")
    print(f"WASH_FLAGS={WASH_FLAGS}")
    print(f"REASSIGNED={REASSIGNED}")
    print(f"LEDGER_TICKS={LEDGER_TICKS}")
    print(f"RUN_ID={RUN_ID}")

if __name__ == '__main__':
    run()
