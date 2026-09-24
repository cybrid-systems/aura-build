"""
Toy in-memory copy-on-write WAL store.

Implements the semantics of the Aura mini-wal-copy-on-write project as a single
self-contained Python script. Runs the scenario described in GOAL.md and prints
the KEY=value contract.
"""

import sys
from collections import OrderedDict


# ---------------------------------------------------------------------------
# codec.aura
# ---------------------------------------------------------------------------
def encode_entry(key, value):
    return (key, value)


def decode_entry(cell):
    return cell


def kv_pair(x):
    return isinstance(x, tuple) and len(x) == 2


# ---------------------------------------------------------------------------
# keydir.aura
# ---------------------------------------------------------------------------
class KeyDir:
    def __init__(self):
        self._m = OrderedDict()

    def put(self, key, offset):
        self._m[key] = offset
        return self

    def get(self, key):
        return self._m.get(key)

    def snapshot(self):
        kd = KeyDir()
        kd._m = OrderedDict(self._m)
        return kd

    def entries(self):
        return list(self._m.items())


def make_keydir():
    return KeyDir()


def keydir_put(kd, key, offset):
    return kd.put(key, offset)


def keydir_get(kd, key):
    return kd.get(key)


def keydir_snapshot(kd):
    return kd.snapshot()


def keydir_entries(kd):
    return kd.entries()


# ---------------------------------------------------------------------------
# segment.aura
# ---------------------------------------------------------------------------
class Segment:
    def __init__(self, sid, entries):
        self._id = sid
        # entries: list of (key, value)
        self._entries = list(entries)

    @property
    def id(self):
        return self._id

    @property
    def entries(self):
        return self._entries

    def size(self):
        return len(self._entries)


def make_segment(sid, entries):
    return Segment(sid, entries)


def segment_id(seg):
    return seg.id


def segment_entries(seg):
    return seg.entries


def segment_size(seg):
    return seg.size()


# ---------------------------------------------------------------------------
# delta.aura
# ---------------------------------------------------------------------------
class Delta:
    def __init__(self, puts, deletes):
        self._puts = dict(puts)      # key -> value
        self._deletes = set(deletes) # set of keys

    def puts(self):
        return self._puts

    def deletes(self):
        return self._deletes

    def apply_to(self, seg):
        # Merge delta onto base segment entries, returning a NEW segment.
        new_entries = []
        seen = set()
        for k, v in seg.entries:
            if k in self._deletes:
                continue
            if k in self._puts:
                new_entries.append((k, self._puts[k]))
                seen.add(k)
            else:
                new_entries.append((k, v))
                seen.add(k)
        for k, v in self._puts.items():
            if k not in seen:
                new_entries.append((k, v))
        return Segment(seg.id + ":cow", new_entries)

    def empty(self):
        return len(self._puts) == 0 and len(self._deletes) == 0


def make_delta(puts, deletes):
    return Delta(puts, deletes)


def delta_apply_to(delta, seg):
    return delta.apply_to(seg)


def delta_puts(delta):
    return delta.puts()


def delta_deletes(delta):
    return delta.deletes()


def empty_delta(delta):
    return delta.empty()


# ---------------------------------------------------------------------------
# root.aura
# ---------------------------------------------------------------------------
class Root:
    def __init__(self, rid, parent_id, segment_id):
        self._id = rid
        self._parent = parent_id
        self._segment = segment_id

    @property
    def id(self):
        return self._id

    @property
    def parent(self):
        return self._parent

    @property
    def segment(self):
        return self._segment


def make_root(rid, parent_id, segment_id):
    return Root(rid, parent_id, segment_id)


def root_id(r):
    return r.id


def root_parent(r):
    return r.parent


def root_segment(r):
    return r.segment


def root_eq(a, b):
    return a.id == b.id


# ---------------------------------------------------------------------------
# snapshot.aura
# ---------------------------------------------------------------------------
class Snapshot:
    def __init__(self, root_id_, segments):
        self._root_id = root_id_
        # segments is an ordered list (oldest -> newest) that forms the chain
        # ending at the snapshot's root segment.
        self._segments = list(segments)

    def get(self, key):
        # Look from newest to oldest segment.
        for seg in reversed(self._segments):
            for k, v in seg.entries:
                if k == key:
                    return v
        return None

    def keys(self):
        # Union of keys, last-write-wins via reversed iteration.
        result = OrderedDict()
        for seg in reversed(self._segments):
            for k, v in seg.entries:
                result[k] = v
        return list(result.keys())

    def root_id(self_):
        return self_._root_id

    def segment_count(self):
        return len(self._segments)


def make_snapshot(root_id_, segments):
    return Snapshot(root_id_, segments)


def snapshot_get(snap, key):
    return snap.get(key)


def snapshot_keys(snap):
    return snap.keys()


def snapshot_root_id(snap):
    return snap.root_id()


def snapshot_segment_count(snap):
    return snap.segment_count()


# ---------------------------------------------------------------------------
# history.aura
# ---------------------------------------------------------------------------
class History:
    def __init__(self):
        self._roots = []

    def record(self, root_id_):
        self._roots.append(root_id_)
        return self

    def list(self):
        return list(self._roots)

    def length(self):
        return len(self._roots)

    def at(self, idx):
        return self._roots[idx]


def history_record(hist, root_id_):
    return hist.record(root_id_)


def history_list(hist):
    return hist.list()


def history_len(hist):
    return hist.length()


def history_at(hist, idx):
    return hist.at(idx)


# ---------------------------------------------------------------------------
# metrics.aura
# ---------------------------------------------------------------------------
class Metrics:
    def __init__(self):
        self._m = {}

    def inc(self, k, by=1):
        self._m[k] = self._m.get(k, 0) + by
        return self

    def get(self, k):
        return self._m.get(k, 0)

    def snapshot(self):
        return dict(self._m)


def make_metrics():
    return Metrics()


def metrics_inc(m, k):
    return m.inc(k)


def metrics_get(m, k):
    return m.get(k)


def metrics_snapshot(m):
    return m.snapshot()


# ---------------------------------------------------------------------------
# gc.aura
# ---------------------------------------------------------------------------
def gc_reclaimable_segments(wal, keep_roots):
    keep = set(keep_roots)
    live = set()
    for r in wal.roots:
        if r.id in keep:
            live.add(r.segment)
            # Also keep all ancestors in the chain that the wal retains.
    # All segment ids that are reachable via the wal itself:
    for seg in wal.segments:
        live.add(seg.id)
    # Collect all segment ids that exist anywhere:
    all_segs = set()
    for r in wal.roots:
        all_segs.add(r.segment)
    # A segment is reclaimable if it is not referenced by any keep root and
    # not part of the live chain reachable from a keep root.
    # In our model we keep it simple: segments referenced by R0/R1 (non-kept)
    # are reclaimable.
    keep_root_set = set(r.id for r in wal.roots if r.id in keep)
    referenced_by_kept = set()
    for r in wal.roots:
        if r.id in keep_root_set:
            referenced_by_kept.add(r.segment)
    referenced_by_dropped = set()
    for r in wal.roots:
        if r.id not in keep_root_set:
            referenced_by_dropped.add(r.segment)
    # Reclaimable = referenced by dropped roots that aren't also referenced
    # by kept roots.
    reclaimable = referenced_by_dropped - referenced_by_kept
    return reclaimable


def plan_gc(wal, keep_roots):
    return gc_reclaimable_segments(wal, keep_roots)


def run_gc(wal, keep_roots):
    reclaimable = gc_reclaimable_segments(wal, keep_roots)
    count = 0
    # Remove from wal.segments
    new_segs = []
    for s in wal.segments:
        if s.id in reclaimable:
            count += 1
        else:
            new_segs.append(s)
    wal.segments = new_segs
    # Drop roots that aren't kept AND whose segment is gone.
    new_roots = []
    for r in wal.roots:
        if r.id in set(keep_roots) or r.segment not in reclaimable:
            new_roots.append(r)
    wal.roots = new_roots
    wal.gc_count += 1
    wal.gc_reclaimed += count
    return count


# ---------------------------------------------------------------------------
# cow.aura
# ---------------------------------------------------------------------------
def cow_merge(base_seg, delta):
    if empty_delta(delta):
        return base_seg
    return delta_apply_to(delta, base_seg)


def cow_fork(wal, at_root):
    # Returns a new wal handle sharing all segments/roots (independent object).
    return wal.fork(at_root)


def cow_readable_at(wal, root_id_):
    return root_id_ in set(r.id for r in wal.roots)


# ---------------------------------------------------------------------------
# wal.aura
# ---------------------------------------------------------------------------
class WAL:
    def __init__(self):
        self._segments = []   # list of Segment
        self._active = []     # pending entries for next commit
        self._roots = []      # list of Root (chronological)
        self._roots_by_id = {}
        self._seg_counter = 0
        self._root_counter = 0
        self._history = History()
        self.gc_count = 0
        self.gc_reclaimed = 0

    # --- accessors ---
    @property
    def segments(self):
        return self._segments

    @property
    def roots(self):
        return self._roots

    def active(self):
        return list(self._active)

    def append(self, key, value):
        self._active.append((key, value))
        return self

    def commit(self):
        # Flush active buffer into an immutable segment, create a new root.
        self._seg_counter += 1
        sid = "seg-%d" % self._seg_counter
        seg = Segment(sid, self._active)
        self._segments.append(seg)
        # New root
        self._root_counter += 1
        rid = "R%d" % self._root_counter
        parent = self._roots[-1].id if self._roots else None
        root = Root(rid, parent, seg.id)
        self._roots.append(root)
        self._roots_by_id[rid] = root
        self._history.record(rid)
        self._active = []
        return root

    def root(self):
        # Latest registered root (could be promoted).
        return self._roots[-1] if self._roots else None

    def fork(self, at_root_id):
        # Produce an independent handle sharing the segment store.
        new_wal = WAL()
        new_wal._segments = list(self._segments)
        new_wal._roots = list(self._roots)
        new_wal._roots_by_id = dict(self._roots_by_id)
        new_wal._seg_counter = self._seg_counter
        new_wal._root_counter = self._root_counter
        new_wal._history = self._history
        return new_wal

    def promote(self, root):
        # Register an additional root (e.g. R3) so it appears in roots list
        # and becomes the latest.
        self._roots.append(root)
        self._roots_by_id[root.id] = root
        return root

    def _segments_up_to(self, root_id_):
        """Return segments leading up to (and including) the given root,
        in chronological order."""
        # Find the root and walk back via parent links to the oldest.
        target = self._roots_by_id.get(root_id_)
        if target is None:
            return []
        # Build chain of root ids from earliest ancestor to target.
        chain_ids = []
        cur = target
        while cur is not None:
            chain_ids.append(cur.id)
            cur = self._roots_by_id.get(cur.parent) if cur.parent else None
        chain_ids.reverse()
        # Map each root to its segment.
        seg_ids = []
        for rid in chain_ids:
            r = self._roots_by_id[rid]
            seg_ids.append(r.segment)
        # Return segments in chain order.
        segs = []
        for sid in seg_ids:
            for s in self._segments:
                if s.id == sid:
                    segs.append(s)
                    break
        return segs

    def read_at(self, root_id_, key):
        segs = self._segments_up_to(root_id_)
        for seg in reversed(segs):
            for k, v in seg.entries:
                if k == key:
                    return v
        return None

    def keys_at(self, root_id_):
        segs = self._segments_up_to(root_id_)
        result = OrderedDict()
        for seg in reversed(segs):
            for k, v in seg.entries:
                result[k] = v
        return list(result.keys())

    def gc(self, keep_roots):
        return run_gc(self, keep_roots)


def make_wal():
    return WAL()


def wal_append(wal, key, value):
    return wal.append(key, value)


def wal_commit(wal):
    return wal.commit()


def wal_active(wal):
    return wal.active()


def wal_segments(wal):
    return wal.segments


def wal_root(wal):
    return wal.root()


def wal_roots(wal):
    return wal.roots


def wal_fork(wal, root_id_):
    return wal.fork(root_id_)


def wal_read_at(wal, root_id_, key):
    return wal.read_at(root_id_, key)


def wal_keys_at(wal, root_id_):
    return wal.keys_at(root_id_)


def wal_gc(wal, keep_roots):
    return wal.gc(keep_roots)


def wal_promote(wal, root):
    return wal.promote(root)


# ---------------------------------------------------------------------------
# report.aura
# ---------------------------------------------------------------------------
def format_kv_list(alist):
    return ", ".join("%s=%s" % (k, v) for k, v in alist)


def kvline(key, value):
    return "%s=%s" % (key, value)


def print_stats(stats):
    for k, v in stats:
        sys.stdout.write("%s=%s\n" % (k, v))


# ---------------------------------------------------------------------------
# main.aura -- scenario
# ---------------------------------------------------------------------------
def main():
    # 1. Bootstrap
    W = make_wal()

    # 2. Commit 0
    wal_append(W, "alpha", 1)
    wal_append(W, "beta", "beta-v0")
    wal_append(W, "gamma", "g0")
    R0 = wal_commit(W)

    # 3. Fork at R0
    F = wal_fork(W, R0.id)  # independent handle, not mutated

    # 4. Commit 1
    wal_append(W, "alpha", 42)
    wal_append(W, "beta", "beta-v1")
    wal_append(W, "delta", "d1")
    R1 = wal_commit(W)

    # 5. Commit 2
    wal_append(W, "alpha", 200)
    wal_append(W, "beta", "beta-stable")
    R2 = wal_commit(W)

    # 6. Root promotion: build R3 manually from R2's segment.
    latest_seg_id = R2.segment
    R3 = make_root("R3", R2.id, latest_seg_id)
    wal_promote(W, R3)

    # 7. Snapshot reads
    # Build segments for each root by walking wal segments matching root chains.
    # For each R0, R1, R2 we build a snapshot from the wal itself.
    def segments_for_root(root_id_):
        return W._segments_up_to(root_id_)

    snap0 = make_snapshot(R0.id, segments_for_root(R0.id))
    snap1 = make_snapshot(R1.id, segments_for_root(R1.id))
    snap2 = make_snapshot(R2.id, segments_for_root(R2.id))

    snap0_keys = snapshot_keys(snap0)
    snap1_keys = snapshot_keys(snap1)
    snap2_keys = snapshot_keys(snap2)

    # 8. GC pass -- keep R2 and R3, reclaim segments referenced only by R0/R1
    gc_reclaimed = wal_gc(W, [R2.id, R3.id])

    # 9. Forked-root readability check (re-read alpha at R1)
    read_at_R1_alpha = wal_read_at(W, R1.id, "alpha")

    # 10. History
    hist_list = history_list(W._history)
    history_str = ",".join(hist_list)

    # ---- KEY=value contract ----
    segments_count = len(wal_segments(W))
    commits_count = len(wal_roots(W))  # R0, R1, R2, R3
    latest_root_id = wal_root(W).id
    key_alpha_after_commit2 = wal_read_at(W, R2.id, "alpha")
    key_beta_after_commit2 = wal_read_at(W, R2.id, "beta")
    key_new_after_commit1 = wal_read_at(W, R1.id, "delta")

    lines = [
        ("SEGMENTS", segments_count),
        ("COMMITS", commits_count),
        ("LATEST_ROOT", latest_root_id),
        ("SNAP0_KEYS", len(snap0_keys)),
        ("SNAP1_KEYS", len(snap1_keys)),
        ("SNAP2_KEYS", len(snap2_keys)),
        ("KEY_ALPHA_AFTER_COMMIT2", key_alpha_after_commit2),
        ("KEY_BETA_AFTER_COMMIT2", key_beta_after_commit2),
        ("KEY_NEW_AFTER_COMMIT1", key_new_after_commit1),
        ("GC_COUNT", W.gc_count),
        ("GC_RECLAIMED", gc_reclaimed),
        ("READ_FROM_FORKED_ROOT", read_at_R1_alpha),
        ("ROOT_HISTORY", history_str),
    ]

    for k, v in lines:
        sys.stdout.write("%s=%s\n" % (k, v))


if __name__ == "__main__":
    main()
