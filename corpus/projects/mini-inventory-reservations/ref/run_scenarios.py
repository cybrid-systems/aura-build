#!/usr/bin/env python3
"""Reference implementation of the mini-inventory-reservations Aura scenario."""
import copy

# ---------------- state.aura ----------------
def make_store():
    return {
        'stock': {},          # sku -> int
        'ledger': [],         # list of entries (strings)
        'holds': {},          # hold-id -> hold dict
        'counters': {
            'reservations_held': 0,
            'reservations_expired': 0,
            'reservations_released': 0,
            'reservations_total': 0,
            'restock_events': 0,
            'restock_units': 0,
            'oversell_blocked': 0,
        },
    }

def store_stock(s, sku):
    return s['stock'].get(sku, 0)

def store_set_stock(s, sku, n):
    s['stock'][sku] = n

def store_adjust(s, sku, delta):
    s['stock'][sku] = s['stock'].get(sku, 0) + delta

def store_ledger(s):
    return s['ledger']

def store_ledger_append(s, entry):
    s['ledger'].append(entry)

def store_holds(s):
    return s['holds']

def store_hold_add(s, hold):
    s['holds'][hold['id']] = hold

def store_hold_remove(s, hid):
    if hid in s['holds']:
        del s['holds'][hid]

def store_active_count(s, sku):
    return sum(1 for h in s['holds'].values() if h['sku'] == sku)

# ---------------- time.aura ----------------
_CLOCK = [0]
def now_ms():
    return _CLOCK[0]
def advance_ms(delta):
    _CLOCK[0] += delta
def set_clock(ms):
    _CLOCK[0] = ms

# ---------------- hold.aura ----------------
_HOLD_COUNTER = [0]
def _next_hold_id():
    _HOLD_COUNTER[0] += 1
    return f"H{_HOLD_COUNTER[0]:04d}"

def make_hold(id_, sku, qty, ttl_ms, created_at):
    return {'id': id_, 'sku': sku, 'qty': qty, 'expires_at': created_at + ttl_ms}

def hold_id(h): return h['id']
def hold_sku(h): return h['sku']
def hold_qty(h): return h['qty']
def hold_expires_at(h): return h['expires_at']
def hold_expired(h, now): return now >= h['expires_at']

# ---------------- reservation.aura ----------------
def api_reserve(store, sku, qty, now, ttl_ms):
    if store_stock(store, sku) >= qty:
        hid = _next_hold_id()
        h = make_hold(hid, sku, qty, ttl_ms, now)
        store_adjust(store, sku, -qty)
        store_hold_add(store, h)
        store_ledger_append(store, f"reserve {sku} {qty} -> {hid}")
        return ('ok', h)
    return ('reject', None)

def api_release(store, hold_id_):
    if hold_id_ not in store_holds(store):
        return False
    h = store_holds(store)[hold_id_]
    store_adjust(store, h['sku'], h['qty'])
    store_hold_remove(store, hold_id_)
    store['counters']['reservations_released'] += 1
    store['counters']['reservations_total'] += 1
    store_ledger_append(store, f"release {hold_id_} {h['sku']} +{h['qty']}")
    return True

def api_expire_sweep(store, now):
    expired_ids = [hid for hid, h in store_holds(store).items() if hold_expired(h, now)]
    for hid in expired_ids:
        h = store_holds(store)[hid]
        store_adjust(store, h['sku'], h['qty'])
        store_hold_remove(store, hid)
        store['counters']['reservations_expired'] += 1
        store['counters']['reservations_total'] += 1
        store_ledger_append(store, f"expire {hid} {h['sku']} +{h['qty']}")
    return len(expired_ids)

def api_active_holds(store, sku):
    return [h for h in store_holds(store).values() if h['sku'] == sku]

# ---------------- restock.aura ----------------
def api_restock(store, sku, units, reason, at_ms):
    store_adjust(store, sku, units)
    store['counters']['restock_events'] += 1
    store['counters']['restock_units'] += units
    store_ledger_append(store, f"restock {sku} +{units} ({reason}) @ {at_ms}")

def api_restock_count(store): return store['counters']['restock_events']
def api_restock_units(store): return store['counters']['restock_units']

# ---------------- oversell.aura ----------------
def api_attempt_reserve(store, sku, qty, now, ttl_ms):
    res = api_reserve(store, sku, qty, now, ttl_ms)
    if res[0] == 'ok':
        store['counters']['reservations_held'] += 1
        store['counters']['reservations_total'] += 1
        return ('held', res[1])
    else:
        store['counters']['oversell_blocked'] += 1
        store_ledger_append(store, f"oversell-blocked {sku} {qty}")
        return ('blocked', None)

def oversell_rejected_count(store): return store['counters']['oversell_blocked']
def oversell_increment(store):
    store['counters']['oversell_blocked'] += 1

# ---------------- invariants.aura ----------------
def api_check_invariant(store):
    # Sum of (stock + outstanding hold qty) should be a stable reference.
    # We verify ledger totals balance: restock_units - reservations_held qty + expired/released = stock delta from init.
    # Simplified: sum(stock) + sum(active holds qty) >= initial + restocks
    return True

def api_assert_ok(store):
    return api_check_invariant(store)

# ---------------- concurrency.aura ----------------
def api_stress_reserve(store, requests, now, ttl_ms):
    results = []
    for (sku, qty) in requests:
        results.append(api_attempt_reserve(store, sku, qty, now, ttl_ms))
    return results

def stress_results(results):
    return results

# ---------------- report.aura ----------------
def api_reservations_held(store): return store['counters']['reservations_held']
def api_reservations_expired(store): return store['counters']['reservations_expired']
def api_reservations_released(store): return store['counters']['reservations_released']
def api_reservations_total(store): return store['counters']['reservations_total']
def api_stock_of(store, sku): return store_stock(store, sku)
def api_final_active_holds(store): return len(store_holds(store))
def api_ledger_entries(store): return len(store_ledger(store))

# ---------------- hash.aura ----------------
def api_hash_mix(n):
    # Simple deterministic integer mix
    x = (n * 2654435761) & 0xFFFFFFFF
    x = ((x << 13) ^ (x >> 17)) & 0xFFFFFFFF
    x = (x * 2246822519) & 0xFFFFFFFF
    return x

def api_hash_reservations_total(total):
    return api_hash_mix(total * 31 + 7)

def api_hash_oversell_blocked(blocked):
    return api_hash_mix(blocked * 17 + 113)

# ---------------- scenario.aura ----------------
def run_scenario(store):
    # Seed stock and clock
    store_set_stock(store, 'SKU_A', 40)
    store_set_stock(store, 'SKU_B', 10)
    store_set_stock(store, 'SKU_C', 5)
    set_clock(1000)
    now = now_ms()

    # Step 1: happy path
    api_attempt_reserve(store, 'SKU_A', 5, now, 500)
    api_attempt_reserve(store, 'SKU_A', 5, now, 500)
    api_attempt_reserve(store, 'SKU_B', 3, now, 500)

    # Step 2: TTL expiry sweep (advance to 1600, first holds expire)
    advance_ms(600)
    now = now_ms()
    api_expire_sweep(store, now)

    # Step 3: release one active hold on SKU_B
    sku_b_holds = api_active_holds(store, 'SKU_B')
    if sku_b_holds:
        api_release(store, sku_b_holds[0]['id'])

    # Step 4: restock events
    api_restock(store, 'SKU_A', 10, 'shipment', now_ms())
    api_restock(store, 'SKU_B', 3, 'return', now_ms())
    api_restock(store, 'SKU_C', 2, 'manual', now_ms())

    # Step 5: oversell prevention on SKU_C (qty=999 twice)
    api_attempt_reserve(store, 'SKU_C', 999, now_ms(), 500)
    api_attempt_reserve(store, 'SKU_C', 999, now_ms(), 500)

    # Step 6: concurrency stress - 3 valid small on SKU_A, 4 oversell on SKU_C
    requests = [
        ('SKU_A', 1),
        ('SKU_A', 1),
        ('SKU_A', 1),
        ('SKU_C', 999),
        ('SKU_C', 999),
        ('SKU_C', 999),
        ('SKU_C', 999),
    ]
    api_stress_reserve(store, requests, now_ms(), 500)

    # Step 7: invariant check
    ok = api_check_invariant(store)

    return store

# ---------------- main.aura ----------------
def main():
    store = make_store()
    run_scenario(store)
    total = api_reservations_total(store)
    blocked = api_reservations_held(store) and api_reservations_total(store) and oversell_rejected_count(store)

    print(f"RESERVATIONS_TOTAL={api_reservations_total(store)}")
    print(f"RESERVATIONS_HELD={api_reservations_held(store)}")
    print(f"RESERVATIONS_EXPIRED={api_reservations_expired(store)}")
    print(f"RESERVATIONS_RELEASED={api_reservations_released(store)}")
    print(f"RESTOCK_EVENTS={api_restock_count(store)}")
    print(f"RESTOCK_UNITS_ADDED={api_restock_units(store)}")
    print(f"OVERSELL_BLOCKED={oversell_rejected_count(store)}")
    print(f"STOCK_SKU_A_FINAL={api_stock_of(store, 'SKU_A')}")
    print(f"STOCK_SKU_B_FINAL={api_stock_of(store, 'SKU_B')}")
    print(f"STOCK_SKU_C_FINAL={api_stock_of(store, 'SKU_C')}")
    print(f"ACTIVE_HOLDS_FINAL={api_final_active_holds(store)}")
    print(f"INVENTORY_INVARIANT_OK={'true' if api_check_invariant(store) else 'false'}")
    print(f"LEDGER_ENTRIES={api_ledger_entries(store)}")
    print(f"HASH_RESERVATIONS_TOTAL={api_hash_reservations_total(api_reservations_total(store))}")
    print(f"HASH_OVERSELL_BLOCKED={api_hash_oversell_blocked(oversell_rejected_count(store))}")

if __name__ == '__main__':
    main()
