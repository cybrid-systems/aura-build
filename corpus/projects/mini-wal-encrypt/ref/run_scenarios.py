"""
Python reference implementation of the mini-wal-encrypt Aura scenario.

Implements toy in-memory semantics matching the Aura modules described in GOAL.md:
  - keys.aura: versioned keyring with rotation
  - cipher.aura: reversible XOR "encryption" with truncated tag
  - wal.aura:   segmented write-ahead log
  - tamper.aura: tamper primitives
  - compact.aura: rekey / lag
  - stats.aura: active-key range

Each Aura list of "bytes" is represented here as a Python list of ints 0..255.
Cells (cons pairs) are represented as Python tuples (head, tail) — same shape
as Aura cons cells.  Alists are lists of (key . value) tuples.

run_scenarios.py is self-contained (stdlib only) and prints the 13 required
KEY=value lines in the exact order specified by the GOAL stdout contract.
"""

from copy import deepcopy


# ---------- keys.aura ----------------------------------------------------

def api_keys_make_init(n_versions: int = 2):
    """
    Build an initial keyring with `n_versions` versions.
    Each version's "bytes" are 32 ints 0..255 derived deterministically from v.
    Returned shape matches Aura: alist of (version . bytes-list).
    """
    alist = []
    for v in range(1, n_versions + 1):
        key_bytes = []
        for i in range(32):
            # deterministic per-version key material
            key_bytes.append((v * 131 + i * 17 + 5) % 256)
        alist.append((v, key_bytes))
    return alist


def api_keys_current(keys):
    """Return the current (max) version number in the keyring."""
    if not keys:
        return 0
    return max(v for v, _ in keys)


def api_keys_rotate(keys):
    """
    Append a new version one above the current max.
    Returns a NEW alist; old one is untouched.
    """
    new_v = api_keys_current(keys) + 1
    key_bytes = []
    for i in range(32):
        key_bytes.append((new_v * 131 + i * 17 + 5) % 256)
    new_keys = list(keys) + [(new_v, key_bytes)]
    return new_keys


def api_keys_version_bytes(keys, v):
    """Lookup helper: bytes for a given version (or None if missing)."""
    for kv, kb in keys:
        if kv == v:
            return kb
    return None


# ---------- cipher.aura --------------------------------------------------

def _xor_with_key(payload, key_bytes):
    """Reversible XOR of payload bytes with a repeating key."""
    if not key_bytes:
        return list(payload)
    out = []
    for i, b in enumerate(payload):
        out.append(b ^ key_bytes[i % len(key_bytes)])
    return out


def api_cipher_seal(key_bytes, payload):
    """
    Seal payload under key_bytes.
    Returns a cons cell: (header . body) where:
      header = (key-version . tag)
      body   = list of ciphertext bytes
    """
    body = _xor_with_key(payload, key_bytes)
    tag = sum(body) % 1000000
    header = (None, tag)  # key-version injected by wal layer
    return (header, body)


def api_cipher_tag(ct):
    """Return the truncated tag (hash stand-in) from a ciphertext cell."""
    header, _body = ct
    _, tag = header
    return tag


def api_cipher_open(key_bytes, ct):
    """
    Open ciphertext cell with key_bytes.
    Returns plaintext bytes on success, or False if tag doesn't match.
    """
    header, body = ct
    _, tag = header
    expected = sum(body) % 1000000
    if expected != tag:
        return False
    return _xor_with_key(body, key_bytes)


# ---------- wal.aura -----------------------------------------------------

# Segment shape (Aura):
#   seg = (header . entries)
#   header = (key-version . segment-index . tag)
#   entries = list of (lsn . ciphertext-cell)


def api_wal_new(keys):
    """Empty wal: list of segments, starting lsn = 1, current key v = first."""
    if keys:
        current_v = keys[0][0]
    else:
        current_v = 1
    return {
        "segs": [],          # list of segments
        "next_lsn": 1,
        "current_v": current_v,
    }


def _new_segment(seg_idx, key_version):
    """Fresh empty segment with header (no tag yet)."""
    return ({"kv": key_version, "seg_idx": seg_idx, "tag": None}, [])


def _seal_segment(seg, key_bytes):
    """
    Compute/refresh the segment's aggregate tag from its ciphertext bodies.
    This makes per-segment verification possible.
    """
    header, entries = seg
    total = 0
    for _lsn, ct in entries:
        _, body = ct
        total += sum(body)
    new_header = {"kv": header["kv"],
                  "seg_idx": header["seg_idx"],
                  "tag": total % 1000000}
    return (new_header, entries)


def api_wal_append(wal, key_version, payload_bytes, seg_capacity: int = 15):
    """
    Append one record.  Auto-rotates into a new segment once the current
    segment hits `seg_capacity` records.
    Returns a NEW wal (deep-copied).
    """
    new_wal = deepcopy(wal)

    # Determine target segment (create one if needed / if last is full)
    if not new_wal["segs"]:
        seg_idx = 0
        new_wal["segs"].append(_new_segment(seg_idx, key_version))
    else:
        last_seg = new_wal["segs"][-1]
        _, last_entries = last_seg
        if len(last_entries) >= seg_capacity:
            seg_idx = len(new_wal["segs"])
            new_wal["segs"].append(_new_segment(seg_idx, key_version))
        # else: append into the existing last segment

    # Seal the record
    key_bytes = [(key_version * 131 + i * 17 + 5) % 256 for i in range(32)]
    ct = api_cipher_seal(key_bytes, payload_bytes)
    header, _body = ct
    # Stamp the key-version into the cell header for traceability
    ct = (("kv", key_version), _body)

    # Append to (now current) last segment
    target = new_wal["segs"][-1]
    theader, tentries = target
    lsn = new_wal["next_lsn"]
    new_entries = tentries + [(lsn, ct)]
    # Re-seal the segment so its tag reflects all current bodies
    new_seg = _seal_segment((theader, new_entries),
                            [(key_version * 131 + i * 17 + 5) % 256
                             for i in range(32)])
    new_wal["segs"][-1] = new_seg
    new_wal["next_lsn"] = lsn + 1
    new_wal["current_v"] = key_version
    return new_wal


def api_wal_segs(wal):
    return len(wal["segs"])


def api_wal_records(wal):
    return sum(len(entries) for _, entries in wal["segs"])


def api_wal_lsn_range(wal):
    """Return (min_lsn . max_lsn) as a cons cell tuple."""
    all_lsns = [lsn for _, entries in wal["segs"] for lsn, _ in entries]
    if not all_lsns:
        return (0, 0)
    return (min(all_lsns), max(all_lsns))


def api_wal_seal_version(wal, seg_idx):
    """Return the key version used to seal segment `seg_idx`."""
    header, _ = wal["segs"][seg_idx]
    return header["kv"]


def api_wal_verify(wal, keys):
    """
    Re-derive each segment's tag and report indices whose stored tag
    doesn't match.  Returns a list of tampered segment indices.
    """
    tampered = []
    for i, seg in enumerate(wal["segs"]):
        header, entries = seg
        # Recompute tag from ciphertext bodies
        total = 0
        for _lsn, ct in entries:
            _, body = ct
            total += sum(body)
        recomputed = total % 1000000
        if recomputed != header["tag"]:
            tampered.append(i)
    return tampered


# ---------- tamper.aura --------------------------------------------------

def api_tamper_flip_bit(wal, seg_idx, byte_offset: int = 0):
    """
    Flip a bit in one ciphertext body of segment `seg_idx`.
    Returns a NEW wal.
    """
    new_wal = deepcopy(wal)
    header, entries = new_wal["segs"][seg_idx]
    if not entries:
        return new_wal
    lsn, ct = entries[0]
    cheader, body = ct
    if not body:
        return new_wal
    target = byte_offset % len(body)
    body = list(body)
    body[target] = body[target] ^ 0xFF
    new_ct = (cheader, body)
    new_entries = list(entries)
    new_entries[0] = (lsn, new_ct)
    # Segment tag is intentionally NOT updated — that's what makes it tamper
    new_seg = (header, new_entries)
    new_wal["segs"][seg_idx] = new_seg
    return new_wal


def api_tamper_key_version(wal, seg_idx, new_v):
    """Rewrite a segment header's key-version field. Returns a NEW wal."""
    new_wal = deepcopy(wal)
    header, entries = new_wal["segs"][seg_idx]
    new_header = {"kv": new_v, "seg_idx": header["seg_idx"], "tag": header["tag"]}
    new_wal["segs"][seg_idx] = (new_header, entries)
    return new_wal


# ---------- compact.aura -------------------------------------------------

def api_compact_rekey(wal, keys, threshold: int):
    """
    Re-encrypt the oldest `threshold` segments under the current key version.
    Returns (new_wal . new_keys . stats) where:
      stats = (rekeyed-segments . reencrypted-records)
    """
    new_wal = deepcopy(wal)
    current_v = api_keys_current(keys)
    current_key_bytes = api_keys_version_bytes(keys, current_v)
    n_to_rekey = min(threshold, len(new_wal["segs"]))

    rekeyed_segs = 0
    reencrypted_recs = 0

    for i in range(n_to_rekey):
        seg = new_wal["segs"][i]
        header, entries = seg
        if header["kv"] == current_v:
            continue  # already under current key
        new_entries = []
        for lsn, ct in entries:
            cheader, body = ct
            # Decrypt under old key, re-seal under current key
            old_v = header["kv"]
            old_key_bytes = api_keys_version_bytes(keys, old_v)
            plaintext = _xor_with_key(body, old_key_bytes)
            new_ct = api_cipher_seal(current_key_bytes, plaintext)
            cheader2, _body2 = new_ct
            new_ct = (("kv", current_v), _body2)
            new_entries.append((lsn, new_ct))
            reencrypted_recs += 1
        # Rebuild segment under current key with refreshed tag
        new_header = {"kv": current_v,
                      "seg_idx": header["seg_idx"],
                      "tag": None}
        new_seg = _seal_segment((new_header, new_entries), current_key_bytes)
        new_wal["segs"][i] = new_seg
        rekeyed_segs += 1

    stats = (rekeyed_segs, reencrypted_recs)
    return (new_wal, keys, stats)


def api_compact_lag(old_wal, new_wal):
    """Segments dropped between old and new wal."""
    return api_wal_segs(old_wal) - api_wal_segs(new_wal)


# ---------- stats.aura ---------------------------------------------------

def api_stats_active_key_range(wal):
    """
    Return (min-seg-with-current . max-seg-with-current) — i.e., the range
    of segment indices that are sealed under the current key version.
    """
    current_v = wal["current_v"]
    hits = [i for i, seg in enumerate(wal["segs"])
            if seg[0]["kv"] == current_v]
    if not hits:
        return (None, None)
    return (min(hits), max(hits))


# ---------- main.aura scenario ------------------------------------------

def run_scenario():
    # 1. Initial keyring (2 versions)
    keys = api_keys_make_init(2)

    # 2. Empty wal
    wal = api_wal_new(keys)

    # 3. Append 120 records, splitting into 8 segments of 15 records each.
    #    Rotation policy:
    #      seg 0   -> v1
    #      seg 1,2 -> v1
    #      rotate -> v2 for seg 3
    #      seg 4,5 -> v2
    #      rotate -> v3 for seg 6
    #      rotate -> v4 for seg 7
    #    Total rotations: 3.

    seg_capacity = 15
    total_records = 120
    total_segs_planned = 8
    records_per_seg = total_records // total_segs_planned  # 15

    # Plan per-segment key versions following the rotation policy.
    # We rotate AT segment boundaries before sealing that segment.
    seg_versions = []
    current_v = api_keys_current(keys)
    rotation_count = 0

    # seg 0: v1 (current), seg 1,2: v1 (no rotation), seg 3: rotate to v2
    seg_versions.append(current_v)            # seg 0
    seg_versions.append(current_v)            # seg 1
    seg_versions.append(current_v)            # seg 2
    # rotate -> v2
    keys = api_keys_rotate(keys); current_v = api_keys_current(keys); rotation_count += 1
    seg_versions.append(current_v)            # seg 3
    seg_versions.append(current_v)            # seg 4
    seg_versions.append(current_v)            # seg 5
    # rotate -> v3
    keys = api_keys_rotate(keys); current_v = api_keys_current(keys); rotation_count += 1
    seg_versions.append(current_v)            # seg 6
    # rotate -> v4
    keys = api_keys_rotate(keys); current_v = api_keys_current(keys); rotation_count += 1
    seg_versions.append(current_v)            # seg 7

    assert len(seg_versions) == total_segs_planned

    # Append records
    lsn_counter = 1
    for seg_i in range(total_segs_planned):
        kv = seg_versions[seg_i]
        for _ in range(records_per_seg):
            payload = [(lsn_counter * 7 + k) % 256 for k in range(15)]
            wal = api_wal_append(wal, kv, payload, seg_capacity=seg_capacity)
            lsn_counter += 1

    # 4. Verify integrity — should be clean
    tampered_before = api_wal_verify(wal, keys)

    # 5. Tamper two distinct segments, then re-verify
    wal = api_tamper_flip_bit(wal, 1, byte_offset=2)
    wal = api_tamper_flip_bit(wal, 5, byte_offset=4)
    tampered_after = api_wal_verify(wal, keys)

    # 6. Compaction/rekey: force oldest 2 segments (sealed with v1)
    #    to be re-encrypted under the current key version.
    #    Current key version at this point is v4 (last rotation).
    rekey_threshold = 2
    new_wal, new_keys, stats = api_compact_rekey(wal, keys, rekey_threshold)
    rekeyed_segs, reencrypted_recs = stats

    # 7. Re-verify after re-key (post-rekey wal) — should be clean
    tampered_post_rekey = api_wal_verify(new_wal, new_keys)

    # 8. Active-key range under the post-rekey current version (v4)
    min_active, max_active = api_stats_active_key_range(new_wal)

    # 9. Lag: no segments dropped
    lag = api_compact_lag(wal, new_wal)

    # 10. Gather all KEY=value lines (must follow exact order in expect list)
    wal_segs            = api_wal_segs(new_wal)
    wal_records         = api_wal_records(new_wal)
    wal_key_current     = api_keys_current(new_keys)
    wal_rotations       = rotation_count
    wal_rekeyed         = rekeyed_segs
    wal_reencrypted     = reencrypted_recs
    wal_verified        = len(tampered_post_rekey)  # 0 if clean
    wal_tamper_detected = len(tampered_after)        # 2
    lsn_first, lsn_last = api_wal_lsn_range(new_wal)
    wal_active_key_seg_min = min_active
    wal_active_key_seg_max = max_active
    wal_lag_segs        = lag

    # Print in EXACT order
    print(f"WAL_SEGS={wal_segs}")
    print(f"WAL_RECORDS={wal_records}")
    print(f"WAL_KEY_CURRENT={wal_key_current}")
    print(f"WAL_ROTATIONS={wal_rotations}")
    print(f"WAL_REKEYED={wal_rekeyed}")
    print(f"WAL_REENCRYPTED={wal_reencrypted}")
    print(f"WAL_VERIFIED={wal_verified}")
    print(f"WAL_TAMPER_DETECTED={wal_tamper_detected}")
    print(f"WAL_LSN_FIRST={lsn_first}")
    print(f"WAL_LSN_LAST={lsn_last}")
    print(f"WAL_ACTIVE_KEY_SEG_MIN={wal_active_key_seg_min}")
    print(f"WAL_ACTIVE_KEY_SEG_MAX={wal_active_key_seg_max}")
    print(f"WAL_LAG_SEGS={wal_lag_segs}")


if __name__ == "__main__":
    run_scenario()
