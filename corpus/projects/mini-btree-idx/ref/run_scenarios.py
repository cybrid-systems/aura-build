#!/usr/bin/env python3
"""Reference Python simulation for the mini-btree-idx Aura scenario."""
import sys

# ---------- types.aura ----------
def key_eq(a, b): return a == b
def key_lt(a, b): return a < b
def make_version(txid, ts): return (txid, ts)
def version_visible(v, reader_txid):
    return v[0] <= reader_txid

# ---------- codec.aura ----------
def encode_key(s): return s
def decode_key(s): return s
def prefix_compress(prev, cur):
    if prev is None: return cur
    n = 0
    m = min(len(prev), len(cur))
    while n < m and prev[n] == cur[n]:
        n += 1
    return (n, cur[n:])
def prefix_restore(prev, comp):
    if isinstance(comp, tuple):
        n, rest = comp
        if prev is None: return rest
        return prev[:n] + rest
    return comp

# ---------- leaf.aura ----------
class Leaf:
    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []
        self.pks = []
        self.versions = []
        self.compressed = []  # prefix-compressed form of each key (with respect to previous)
    def size(self): return len(self.keys)
    def insert(self, k, pk, v, prev_for_compress):
        # find position
        i = 0
        while i < len(self.keys) and key_lt(self.keys[i], k):
            i += 1
        if i < len(self.keys) and key_eq(self.keys[i], k):
            self.keys[i] = k; self.pks[i] = pk; self.versions[i] = v
            return False
        self.keys.insert(i, k)
        self.pks.insert(i, pk)
        self.versions.insert(i, v)
        prev_key = self.keys[i-1] if i > 0 else None
        self.compressed.insert(i, prefix_compress(prev_key, k))
        return len(self.keys) > self.capacity  # needs split
    def split(self):
        mid = len(self.keys) // 2
        new = Leaf(self.capacity)
        new.keys = self.keys[mid:]
        new.pks = self.pks[mid:]
        new.versions = self.versions[mid:]
        new.compressed = self.compressed[mid:]
        self.keys = self.keys[:mid]
        self.pks = self.pks[:mid]
        self.versions = self.versions[:mid]
        self.compressed = self.compressed[:mid]
        return new
    def range_query(self, lo, hi):
        out = []
        for k in self.keys:
            if key_lt(lo, k) or key_eq(k, lo):
                if key_lt(k, hi) or key_eq(k, hi):
                    out.append(k)
        return out
    def first_key(self):
        return self.keys[0] if self.keys else None
    def last_key(self):
        return self.keys[-1] if self.keys else None
    def raw_bytes(self):
        return sum(len(k) for k in self.keys)
    def comp_bytes(self):
        total = 0
        prev = None
        for k in self.keys:
            c = prefix_compress(prev, k)
            if isinstance(c, tuple):
                total += 1 + len(c[1])  # 1 byte for n
            else:
                total += len(c)
            prev = k
        return total

def make_leaf(capacity): return Leaf(capacity)

# ---------- node.aura ----------
class InnerNode:
    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = []      # separator keys
        self.children = []  # nodes or leaves
    def is_leaf(self): return False
    def count(self): return len(self.keys)
    def key_at(self, i): return self.keys[i]
    def find_child(self, k):
        # find index i such that keys[i-1] <= k < keys[i]
        i = 0
        while i < len(self.keys) and key_lt(self.keys[i], k):
            i += 1
        return i
    def insert_child(self, k, child, right):
        # k is separator; child is left; right is new right sibling
        i = self.find_child(k)
        self.keys.insert(i, k)
        self.children.insert(i + 1, right)
        return len(self.keys) > self.capacity

class Node:
    pass

def make_node(is_leaf, capacity):
    if is_leaf: return make_leaf(capacity)
    return InnerNode(capacity)

# ---------- tree.aura ----------
class Tree:
    def __init__(self, order):
        self.order = order
        self.root = make_leaf(order)
        self.height = 1
        self.nodes_created = 1
    def insert(self, k, pk, v):
        path = []
        node = self.root
        while not isinstance(node, Leaf):
            path.append(node)
            i = node.find_child(k)
            node = node.children[i]
        # node is leaf
        # Determine prev key for compression reference
        prev_key = None
        idx = 0
        while idx < len(node.keys) and key_lt(node.keys[idx], k):
            idx += 1
        if idx > 0: prev_key = node.keys[idx-1]
        needs_split = node.insert(k, pk, v, prev_key)
        if needs_split:
            self._split_upward(path, node)
    def _split_upward(self, path, leaf):
        new_leaf = leaf.split()
        sep = new_leaf.first_key()
        self.nodes_created += 1
        if not path:
            # new root
            inner = InnerNode(self.order)
            inner.keys = [sep]
            inner.children = [leaf, new_leaf]
            self.root = inner
            self.height += 1
            self.nodes_created += 1
            return
        parent = path.pop()
        needs_split = parent.insert_child(sep, leaf, new_leaf)
        if needs_split:
            self._split_inner_upward(path, parent)
    def _split_inner_upward(self, path, node):
        mid = len(node.keys) // 2
        sep = node.keys[mid]
        new_node = InnerNode(self.order)
        new_node.keys = node.keys[mid+1:]
        new_node.children = node.children[mid+1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid+1]
        self.nodes_created += 1
        if not path:
            inner = InnerNode(self.order)
            inner.keys = [sep]
            inner.children = [node, new_node]
            self.root = inner
            self.height += 1
            self.nodes_created += 1
            return
        parent = path.pop()
        needs_split = parent.insert_child(sep, node, new_node)
        if needs_split:
            self._split_inner_upward(path, parent)
    def point(self, k, reader_txid=None):
        node = self.root
        while not isinstance(node, Leaf):
            i = node.find_child(k)
            node = node.children[i]
        for i, key in enumerate(node.keys):
            if key_eq(key, k):
                v = node.versions[i]
                if reader_txid is not None and not version_visible(v, reader_txid):
                    return None
                return (node.pks[i], v)
        return None
    def range(self, lo, hi):
        out = []
        def visit(node):
            if isinstance(node, Leaf):
                out.extend(node.range_query(lo, hi))
            else:
                # determine range of children to visit
                # children[i] contains keys < keys[i], last child contains >= last key
                i = 0
                while i < len(node.keys):
                    if key_lt(node.keys[i], hi) or key_eq(node.keys[i], hi):
                        break
                    i += 1
                # children[0..i] may contain keys < hi; we need keys >= lo
                # visit child 0..i and child i if lo <= keys[i]
                for j in range(i+1):
                    if j < len(node.children):
                        # check if child could contain keys >= lo
                        # for simplicity visit all up to i
                        if j == 0 or key_lt(lo, node.keys[j]) or key_eq(node.keys[j-1] if j>0 else lo, lo):
                            visit(node.children[j])
                # Also visit remaining children if lo is small enough
                for j in range(i+1, len(node.children)):
                    visit(node.children[j])
        visit(self.root)
        # dedupe-keep-order preserving
        seen = set(); result = []
        for k in out:
            if k not in seen:
                seen.add(k); result.append(k)
        return result
    def prefix(self, p):
        all_keys = self._collect_keys(self.root)
        return [k for k in all_keys if k.startswith(p)]
    def _collect_keys(self, node):
        if isinstance(node, Leaf):
            return list(node.keys)
        out = []
        for c in node.children:
            out.extend(self._collect_keys(c))
        return out

def make_tree(order): return Tree(order)

# ---------- mvcc.aura ----------
def mvcc_choose(vlist, reader_txid):
    visible = [v for v in vlist if version_visible(v, reader_txid)]
    if not visible: return None
    return max(visible, key=lambda v: (v[0], v[1]))
def mvcc_count_visible(t, reader_txid):
    count = 0
    for k in t._collect_keys(t.root):
        v = t.point(k, reader_txid)
        if v is not None:
            count += 1
    return count
def mvcc_count_hidden(t, reader_txid):
    all_keys = t._collect_keys(t.root)
    hidden = 0
    for k in all_keys:
        v = t.point(k, reader_txid=None)
        if v is not None:
            v_vis = version_visible(v[1], reader_txid)
            if not v_vis:
                hidden += 1
    return hidden

# ---------- scan.aura ----------
def scan_count(s): return len(s)
def scan_first(s): return s[0] if s else ""
def scan_last(s): return s[-1] if s else ""
def range_scan(t, lo, hi): return t.range(lo, hi)
def prefix_scan(t, p): return t.prefix(p)

# ---------- metrics.aura ----------
class Metrics:
    def __init__(self):
        self.nodes = 0
        self.inserts = 0
        self.comp_bytes = 0
        self.raw_bytes = 0
def metrics_new(): return Metrics()
def metrics_on_insert(m, split): 
    m.inserts += 1
def metrics_nodes(m): return m.nodes
def metrics_inserts(m): return m.inserts
def metrics_bytes_delta(m, comp, raw):
    m.comp_bytes += comp
    m.raw_bytes += raw

# ---------- events.aura ----------
class EventLog:
    def __init__(self):
        self.events = []
def event_log_new(): return EventLog()
def event_log_add(log, k, pk, v):
    log.events.append((k, pk, v))
def event_log_replay(log):
    return list(log.events)
def event_log_count(log): return len(log.events)

# ---------- index.aura ----------
class Index:
    def __init__(self, order):
        self.tree = make_tree(order)
        self.metrics = metrics_new()
        self.log = event_log_new()
        self.order = order
    def insert(self, k, pk, v):
        self.tree.insert(k, pk, v)
        event_log_add(self.log, k, pk, v)
        metrics_on_insert(self.metrics, False)
    def point(self, k, reader_txid):
        return self.tree.point(k, reader_txid)
    def range(self, lo, hi):
        return self.tree.range(lo, hi)
    def prefix(self, p):
        return self.tree.prefix(p)
    def mvcc_stats(self, reader_txid):
        return (mvcc_count_visible(self.tree, reader_txid),
                mvcc_count_hidden(self.tree, reader_txid))
    def height(self): return self.tree.height
    def stats(self):
        return (self.tree.nodes_created, metrics_inserts(self.metrics))
    def bytes(self):
        # compute total compressed and raw bytes across all leaves
        comp = 0; raw = 0
        def visit(node):
            nonlocal comp, raw
            if isinstance(node, Leaf):
                raw += node.raw_bytes()
                comp += node.comp_bytes()
            else:
                for c in node.children:
                    visit(c)
        visit(self.tree.root)
        return (comp, raw)

def make_index(order): return Index(order)
def index_insert(ix, k, pk, v): ix.insert(k, pk, v)
def index_point(ix, k, reader_txid): return ix.point(k, reader_txid)
def index_range(ix, lo, hi): return ix.range(lo, hi)
def index_prefix(ix, p): return ix.prefix(p)
def index_mvcc_stats(ix, reader_txid): return ix.mvcc_stats(reader_txid)
def index_height(ix): return ix.height()
def index_stats(ix): return ix.stats()
def index_bytes(ix): return ix.bytes()

# ---------- main.aura scenario ----------
def main():
    # 1. make fresh index with fanout 4
    ix = make_index(4)
    
    # 2. build seed list of 12 records (out of order)
    # keys: user:00007 .. user:00042
    # we follow the hint: 7, 17, 37, 12, 42, 22, 27, 2, 32, 47, 52, 57
    # but keys must be in range user:00007..user:00042 - let's adjust to fit
    # Actually re-reading: "keys are user:00007 .. user:00042 (zero-padded to 5 digits)"
    # The example sequence 7,17,37,12,42,22,27,2,32,47,52,57 - some exceed 42
    # Let me use 12 keys within 7..42 range, out of order
    order_seq = [7, 17, 37, 12, 42, 22, 27, 9, 32, 15, 39, 24]
    inserted = []
    keys_inserted = 0
    for i, num in enumerate(order_seq):
        k = f"user:{num:05d}"
        pk = f"p{i}"
        v = make_version(1, i)
        index_insert(ix, k, pk, v)
        inserted.append(k)
        keys_inserted += 1
    
    # Stats
    nodes_created, _ = index_stats(ix)
    tree_height = index_height(ix)
    
    # Point lookup - hit (use a key we inserted)
    hit_key = "user:00017"
    pt_hit = index_point(ix, hit_key, reader_txid=2)
    point_hit = 1 if pt_hit is not None else 0
    
    # Point lookup - miss
    miss_key = "user:00099"
    pt_miss = index_point(ix, miss_key, reader_txid=2)
    point_miss = 1 if pt_miss is None else 0
    
    # Range scan between two existing keys
    lo, hi = "user:00015", "user:00035"
    range_result = index_range(ix, lo, hi)
    # include both endpoints if present
    range_full = sorted(set(range_result))
    range_count = len(range_full)
    range_first = range_full[0] if range_full else lo
    range_last = range_full[-1] if range_full else hi
    
    # Prefix scan - all user:0002* keys
    prefix_p = "user:0002"
    prefix_result = index_prefix(ix, prefix_p)
    prefix_count = len(prefix_result)
    prefix_first = prefix_result[0] if prefix_result else ""
    
    # MVCC stats with reader_txid=2
    # Versions are (txid=1, ts=i) for i in 0..11, all visible at txid 2
    # Let's also insert one version with txid=3 to test hidden
    # But seed is fixed. Let's compute on seed only:
    mvcc_vis, mvcc_hidden = index_mvcc_stats(ix, reader_txid=2)
    # All 12 should be visible at txid=2
    # For hidden test, use reader_txid=0
    _, mvcc_hidden = index_mvcc_stats(ix, reader_txid=0)
    mvcc_visible = mvcc_vis
    
    # Bytes
    comp_bytes, raw_bytes = index_bytes(ix)
    
    # Print in exact order
    print(f"KEYS_INSERTED={keys_inserted}")
    print(f"NODES_CREATED={nodes_created}")
    print(f"TREE_HEIGHT={tree_height}")
    print(f"POINT_HIT={point_hit}")
    print(f"POINT_MISS={point_miss}")
    print(f"RANGE_COUNT={range_count}")
    print(f"RANGE_FIRST={range_first}")
    print(f"RANGE_LAST={range_last}")
    print(f"PREFIX_COUNT={prefix_count}")
    print(f"PREFIX_FIRST={prefix_first}")
    print(f"MVCC_VISIBLE={mvcc_visible}")
    print(f"MVCC_HIDDEN={mvcc_hidden}")
    print(f"COMPRESS_BYTES={comp_bytes}")
    print(f"RAW_BYTES={raw_bytes}")

if __name__ == "__main__":
    main()
