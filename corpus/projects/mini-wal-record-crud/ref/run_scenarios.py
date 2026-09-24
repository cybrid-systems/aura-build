#!/usr/bin/env python3
"""Reference Python implementation for the mini-wal-record-crud Aura project.

Single-file, stdlib only. Toy in-memory semantics matching the Aura GOAL.
"""

# ---------------------------------------------------------------------------
# wal-types
# ---------------------------------------------------------------------------

WAL_VERSION = 1

def make_tag(name, ttype):
    return ("tag", name, ttype)

def tag_is(t):
    return isinstance(t, tuple) and len(t) == 3 and t[0] == "tag"

def tag_name(t):
    return t[1]

def tag_type(t):
    return t[2]

def make_record(sid, fields):
    return ("record", sid, fields)

def record_schema_id(r):
    return r[1]

def record_fields(r):
    return r[2]

# ---------------------------------------------------------------------------
# wal-defaults
# ---------------------------------------------------------------------------

KNOWN_TYPES = ("int", "str", "bool")

DEFAULT_VALUES = {
    "int": 0,
    "str": "",
    "bool": False,
}

def default_value(t):
    return DEFAULT_VALUES[t]

def known_types():
    return KNOWN_TYPES

# ---------------------------------------------------------------------------
# wal-schema
# ---------------------------------------------------------------------------

_SCHEMAS = {}        # id -> {"fields": [tags...], "types": {name: type}}
_SCHEMA_ORDER = []   # insertion order of schema ids

def define_schema(sid, fields):
    type_map = {}
    for tg in fields:
        type_map[tag_name(tg)] = tag_type(tg)
    _SCHEMAS[sid] = {"fields": list(fields), "types": type_map}
    if sid not in _SCHEMA_ORDER:
        _SCHEMA_ORDER.append(sid)
    return len(_SCHEMA_ORDER)

def schema_exists(sid):
    return sid in _SCHEMAS

def schema_fields(sid):
    return list(_SCHEMAS[sid]["fields"])

def schema_type(sid, tagname):
    return _SCHEMAS[sid]["types"][tagname]

def all_schemas():
    return list(_SCHEMA_ORDER)

def latest_schema_id():
    return max(_SCHEMA_ORDER)

# ---------------------------------------------------------------------------
# wal-encode / wal-decode / wal-bytes
# ---------------------------------------------------------------------------

def encode_value(v, t):
    if t == "int":
        return ("int", int(v))
    if t == "bool":
        return ("bool", bool(v))
    if t == "str":
        return ("str", str(v))
    raise ValueError(f"unknown type {t}")

def decode_value(v, t):
    kind, payload = v
    return payload

def encode_field(f):
    # f is a (tag . value) pair: (("tag", name, ttype), value)
    tg, val = f
    return ("field", tag_name(tg), encode_value(val, tag_type(tg)))

def decode_field(tok):
    _, name, ev = tok
    ttype = ev[0]
    val = ev[1]
    return (make_tag(name, ttype), val)

def encode_record(r):
    sid = record_schema_id(r)
    fields = record_fields(r)
    return ("rec", sid, [encode_field(f) for f in fields])

def decode_record(s):
    _, sid, efields = s
    fields = [decode_field(ef) for ef in efields]
    return make_record(sid, fields)

def encoded_length(s):
    # toy: 1 byte per tuple element
    n = 0
    def walk(x):
        nonlocal n
        if isinstance(x, tuple):
            n += 1
            for el in x:
                walk(el)
        else:
            n += 1
    walk(s)
    return n

def join_encoded(xs):
    out = []
    for x in xs:
        out.extend(x)
    return tuple(out)

def payload_bytes(store):
    total = 0
    for r in store:
        total += encoded_length(encode_record(r))
    return total

# ---------------------------------------------------------------------------
# wal-migrate
# ---------------------------------------------------------------------------

def forward_fill(r, from_id, to_id):
    if not schema_exists(to_id):
        return r
    to_fields = schema_fields(to_id)
    have = {tag_name(tg): val for tg, val in record_fields(r)}
    new_fields = []
    for tg in to_fields:
        nm = tag_name(tg)
        if nm in have:
            new_fields.append((tg, have[nm]))
        else:
            new_fields.append((tg, default_value(tag_type(tg))))
    return make_record(to_id, new_fields)

def backward_strip(r, from_id, to_id):
    if not schema_exists(to_id):
        return r
    to_field_names = {tag_name(tg) for tg in schema_fields(to_id)}
    new_fields = []
    for tg, val in record_fields(r):
        if tag_name(tg) in to_field_names:
            new_fields.append((tg, val))
    return make_record(to_id, new_fields)

def migrate_record(r, from_id, to_id):
    if from_id == to_id:
        return r
    # forward or backward: pick by which has the fields present
    if from_id < to_id:
        return forward_fill(r, from_id, to_id)
    return backward_strip(r, from_id, to_id)

# ---------------------------------------------------------------------------
# wal-store
# ---------------------------------------------------------------------------

_STORE = []

def store_clear():
    _STORE.clear()

def store_append(r):
    _STORE.append(r)
    return len(_STORE)

def store_all():
    return list(_STORE)

def store_count():
    return len(_STORE)

def store_nth(i):
    return _STORE[i]

# ---------------------------------------------------------------------------
# wal-main-helpers / stats
# ---------------------------------------------------------------------------

def setup_schemas():
    define_schema(1, [make_tag("id", "int"), make_tag("name", "str")])
    define_schema(2, [make_tag("id", "int"), make_tag("name", "str"),
                      make_tag("email", "str")])
    define_schema(3, [make_tag("id", "int"), make_tag("name", "str"),
                      make_tag("email", "str"), make_tag("phone", "str"),
                      make_tag("age", "int")])
    return len(all_schemas())

def build_sample_records():
    # 6 records covering schema ids 1, 2, 3 (twice each, last has future field)
    return [
        make_record(1, [
            (make_tag("id", "int"), 1),
            (make_tag("name", "str"), "alice"),
        ]),
        make_record(1, [
            (make_tag("id", "int"), 2),
            (make_tag("name", "str"), "bob"),
        ]),
        make_record(2, [
            (make_tag("id", "int"), 3),
            (make_tag("name", "str"), "carol"),
            (make_tag("email", "str"), "c@x"),
        ]),
        make_record(2, [
            (make_tag("id", "int"), 4),
            (make_tag("name", "str"), "dave"),
            (make_tag("email", "str"), "d@x"),
        ]),
        make_record(3, [
            (make_tag("id", "int"), 5),
            (make_tag("name", "str"), "erin"),
            (make_tag("email", "str"), "e@x"),
            (make_tag("phone", "str"), "555"),
            (make_tag("age", "int"), 30),
        ]),
        make_record(2, [
            (make_tag("id", "int"), 6),
            (make_tag("name", "str"), "frank"),
            (make_tag("email", "str"), "f@x"),
            (make_tag("phone", "str"), "999"),  # future column for sid=2
        ]),
    ]

def records_equal(a, b):
    return a == b

def run_roundtrip(encoded):
    for s in encoded:
        r = decode_record(s)
        s2 = encode_record(r)
        if not records_equal(s, s2):
            return False
    return True

def count_migrations(store, latest):
    fwd = 0
    bwd = 0
    for r in store:
        rid = record_schema_id(r)
        if rid < latest:
            migrate_record(r, rid, latest)
            fwd += 1
        elif rid > latest:
            migrate_record(r, rid, 1)  # backward to oldest
            bwd += 1
    return fwd, bwd

def collect_stats(store):
    if not store:
        return {}
    oldest = min(record_schema_id(r) for r in store)
    newest = max(record_schema_id(r) for r in store)
    last = store[-1]
    last_fields = record_fields(last)
    last_tag = tag_name(last_fields[-1][0]) if last_fields else ""
    return {
        "oldest_schema": oldest,
        "newest_schema": newest,
        "latest_record_tag": last_tag,
    }

def format_stats(d):
    return d

# stats
def stat_new():
    return []

def stat_set(alist, k, v):
    for i, (kk, vv) in enumerate(alist):
        if kk == k:
            alist[i] = (k, v)
            return alist
    alist.append((k, v))
    return alist

def stat_get(alist, k):
    for kk, vv in alist:
        if kk == k:
            return vv
    return None

def stat_keys(alist):
    return [k for k, _ in alist]

# ---------------------------------------------------------------------------
# main orchestration
# ---------------------------------------------------------------------------

def main():
    store_clear()
    wv = WAL_VERSION

    schemas_defined = setup_schemas()
    records = build_sample_records()

    encoded = []
    for r in records:
        encoded.append(encode_record(r))
    records_encoded = len(encoded)

    store_clear()
    for s in encoded:
        rec = decode_record(s)
        store_append(rec)
    records_decoded = store_count()

    round_trip_ok = run_roundtrip(encoded)

    latest = latest_schema_id()
    fwd, bwd = count_migrations(store_all(), latest)
    forward_migrations = fwd
    backward_migrations = bwd

    stats = collect_stats(store_all())
    oldest_schema = stats["oldest_schema"]
    newest_schema = stats["newest_schema"]
    latest_record_tag = stats["latest_record_tag"]
    total_bytes = payload_bytes(store_all())

    print(f"WAL_VERSION={wv}")
    print(f"SCHEMAS_DEFINED={schemas_defined}")
    print(f"RECORDS_ENCODED={records_encoded}")
    print(f"RECORDS_DECODED={records_decoded}")
    print(f"FORWARD_MIGRATIONS={forward_migrations}")
    print(f"BACKWARD_MIGRATIONS={backward_migrations}")
    print(f"ROUND_TRIP_OK={'true' if round_trip_ok else 'false'}")
    print(f"OLDEST_SCHEMA={oldest_schema}")
    print(f"NEWEST_SCHEMA={newest_schema}")
    print(f"LATEST_RECORD_TAG={latest_record_tag}")
    print(f"TOTAL_BYTES={total_bytes}")

if __name__ == "__main__":
    main()
