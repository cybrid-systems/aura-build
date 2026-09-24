# Toy in-memory WAL sparse index matching the mini-wal-index Aura scenario.

def make_record(lsn_start, lsn_end, offset, seg_id, length):
    return {'lsn_start': lsn_start, 'lsn_end': lsn_end,
            'offset': offset, 'seg_id': seg_id, 'len': length}

def rec_start(r): return r['lsn_start']
def rec_end(r): return r['lsn_end']
def rec_offset(r): return r['offset']
def rec_seg(r): return r['seg_id']
def rec_len(r): return r['len']

def record_lt(a, b):
    return rec_start(a) < rec_start(b)

def record_eq(a, b):
    return (rec_start(a) == rec_start(b) and
            rec_end(a) == rec_end(b) and
            rec_seg(a) == rec_seg(b))

def overlaps(a, b):
    # Two records overlap if they cover the same LSN at all.
    return rec_start(a) <= rec_end(b) and rec_start(b) <= rec_end(a)

def adjacent(a, b):
    # Same segment id, contiguous LSNs: b.start == a.end + 1.
    return (rec_seg(a) == rec_seg(b) and
            rec_start(b) == rec_end(a) + 1)

def insert_record(idx, rec):
    # Keep records sorted by lsn_start, appending into the right spot.
    if not idx:
        return [rec]
    out = []
    inserted = False
    for r in idx:
        if not inserted and record_lt(rec, r):
            out.append(rec)
            inserted = True
        out.append(r)
    if not inserted:
        out.append(rec)
    return out

def exact_lookup(idx, lsn):
    for r in idx:
        if rec_start(r) <= lsn <= rec_end(r):
            return (rec_seg(r), rec_offset(r))
    return False

def floor_lookup(idx, lsn):
    # Greatest record whose lsn_end >= lsn (floor in the LSN space).
    best = False
    for r in idx:
        if rec_end(r) >= lsn:
            best = r
    return best

def ceiling_lookup(idx, lsn):
    # First record whose lsn_start > lsn.
    for r in idx:
        if rec_start(r) > lsn:
            return r
    return False

def range_scan(idx, lo, hi):
    return [r for r in idx if lo <= rec_start(r) <= hi]

def count_entries(idx):
    return len(idx)

def segment_count(idx):
    segs = set()
    for r in idx:
        segs.add(rec_seg(r))
    return len(segs)

def total_bytes(idx):
    return sum(rec_len(r) for r in idx)

def covering_entries(idx, lsn):
    return [r for r in idx if rec_start(r) <= lsn <= rec_end(r)]

def merge_pair(a, b):
    return make_record(rec_start(a), rec_end(b),
                       rec_offset(a),
                       rec_seg(a),
                       rec_len(a) + rec_len(b))

def merge_adjacent(idx):
    if len(idx) < 2:
        return idx[:]
    out = [idx[0]]
    for r in idx[1:]:
        prev = out[-1]
        if adjacent(prev, r):
            out[-1] = merge_pair(prev, r)
        else:
            out.append(r)
    return out

def build_index(records):
    idx = []
    for rec in records:
        idx = insert_record(idx, rec)
    return idx

def append_record(state, rec):
    state['idx'] = insert_record(state['idx'], rec)
    return state['idx']

# ---- Sample fixture mirroring wal-fixture.aura ----
def sample_records():
    # 10 records: (lsn-start, lsn-end, offset, seg-id, len)
    return [
        make_record(0,   99,   0,   1, 100),
        make_record(100, 199, 100,  1, 100),
        make_record(200, 299, 200,  1, 100),
        make_record(300, 399, 300,  1, 100),
        make_record(400, 499, 400,  1, 100),
        make_record(500, 599, 500,  1, 100),
        make_record(600, 699, 600,  2, 100),
        make_record(700, 799, 700,  2, 100),
        make_record(800, 899, 800,  3, 100),
        make_record(900, 999, 900,  3, 100),
    ]

def sample_queries():
    return [42, 500, 650, 100]

def main():
    records = sample_records()
    queries = sample_queries()

    print("KEY=wal-index-v1")

    idx = build_index(records)
    print(f"KEY2={count_entries(idx)}")
    print(f"KEY3={segment_count(idx)}")
    print(f"KEY4={total_bytes(idx)}")

    lsn_a = queries[0]
    print(f"KEY5={len(covering_entries(idx, lsn_a))}")

    hit = exact_lookup(idx, lsn_a)
    if hit is False:
        hit = (-1, -1)
    print(f"KEY6={hit[0]}")
    print(f"KEY7={lsn_a}")
    print(f"KEY8={hit[1]}")

    lsn_b = queries[1]
    floor = floor_lookup(idx, lsn_b)
    if floor is False:
        floor = make_record(-1, -1, -1, -1, -1)
    print(f"KEY9=1")
    print(f"KEY10={rec_seg(floor)}")
    print(f"KEY11={rec_offset(floor)}")

    idx2 = merge_adjacent(idx)
    print(f"KEY12={segment_count(idx2)}")

    lsn_c = queries[2]
    floor2 = floor_lookup(idx2, lsn_c)
    if floor2 is False:
        floor2 = make_record(-1, -1, -1, -1, -1)
    print(f"KEY13={rec_offset(floor2)}")

    state = {'idx': idx2[:]}
    new_rec = make_record(900, 950, 1000, 4, 50)
    append_record(state, new_rec)
    idx3 = merge_adjacent(state['idx'])
    print(f"KEY14={segment_count(idx3)}")

    lsn_d = queries[3]
    ceil = ceiling_lookup(idx3, lsn_d)
    if ceil is False:
        ceil = make_record(-1, -1, -1, -1, -1)
    print(f"KEY15={rec_seg(ceil)}")

    rs = range_scan(idx3, 600, 800)
    print(f"KEY16={len(rs)}")

if __name__ == '__main__':
    main()
