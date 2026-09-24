import random

# ---- wal_ids ----
def ids_random_hex():
    return ''.join(random.choice('0123456789abcdef') for _ in range(4))

def ids_make_primary():
    return "primary-" + ids_random_hex()

def ids_make_follower():
    return "follower-" + ids_random_hex()

# ---- wal_crc ----
def crc_hex_of(s):
    # Deterministic hex over string bytes
    h = 0
    for c in s.encode():
        h = ((h * 31) + c) & 0xFFFFFFFF
    return format(h, '08x')

def crc_verify(a, b):
    return a == b

# ---- wal_frame ----
FLUSH_MARKER = ['flush']
def frame_encode(lsn, payload, crc):
    return [lsn, payload, crc]

def frame_decode(frame):
    if frame == FLUSH_MARKER:
        return []
    return frame  # triplet [lsn, payload, crc]

def frame_flush(frame):
    return frame == FLUSH_MARKER

# ---- wal_segment ----
segment_state = {'pages': [], 'last_flush_lsn': 0, 'lsn_high': 0}

def seg_append_page(payload):
    lsn = segment_state['lsn_high'] + 1
    segment_state['lsn_high'] = lsn
    segment_state['pages'].append({'lsn': lsn, 'payload': payload, 'crc': crc_hex_of(payload)})
    segment_state['last_flush_lsn'] = lsn
    return lsn

def seg_pages():
    return list(segment_state['pages'])

def seg_lsn_high():
    return segment_state['lsn_high']

def seg_last_flush_lsn():
    return segment_state['last_flush_lsn']

# ---- wal_buffer ----
buffer_state = {'buf': []}

def buf_new():
    buffer_state['buf'] = []

def buf_push(frame):
    buffer_state['buf'].append(frame)

def buf_drain():
    out = list(buffer_state['buf'])
    buffer_state['buf'] = []
    return out

def buf_size():
    return len(buffer_state['buf'])

# ---- wal_sock ----
sock_state = {'connected': True, 'dropped': False, 'inbox': []}

def sock_send(frame):
    if not sock_state['connected'] or sock_state['dropped']:
        return False
    sock_state['inbox'].append(frame)
    return True

def sock_recv():
    if sock_state['inbox']:
        return sock_state['inbox'].pop(0)
    return None

def sock_drop():
    # simulate a drop
    sock_state['dropped'] = True
    sock_state['connected'] = False
    return True

def sock_reset():
    sock_state['dropped'] = False
    sock_state['connected'] = True
    sock_state['inbox'] = []

# ---- wal_proto ----
proto_state = {'handshake_done': False}

def proto_handshake(primary, follower):
    proto_state['handshake_done'] = True
    proto_state['primary'] = primary
    proto_state['follower'] = follower
    return True

def proto_ship_one(frame):
    return sock_send(frame)

def proto_recv_loop():
    out = []
    while True:
        f = sock_recv()
        if f is None:
            break
        out.append(f)
    return out

# ---- wal_follower ----
follower_state = {'applied_lsn': 0, 'applied_frames': []}

def follow_attach(follower_id):
    follower_state['id'] = follower_id
    follower_state['applied_lsn'] = 0
    follower_state['applied_frames'] = []

def follow_apply_one(frame):
    if frame_flush(frame):
        return True
    decoded = frame_decode(frame)
    if not decoded:
        return False
    lsn, payload, crc = decoded[0], decoded[1], decoded[2]
    if crc_verify(crc, crc_hex_of(payload)):
        follower_state['applied_lsn'] = max(follower_state['applied_lsn'], lsn)
        follower_state['applied_frames'].append(frame)
        return True
    return False

def follow_applied_lsn():
    return follower_state['applied_lsn']

def follow_verify():
    # Verify all applied frames have valid CRC matching payload
    for f in follower_state['applied_frames']:
        lsn, payload, crc = f[0], f[1], f[2]
        if not crc_verify(crc, crc_hex_of(payload)):
            return False
    return True

# ---- wal_shipper ----
shipper_state = {
    'pages_shipped': 0,
    'frames_ok': 0,
    'frames_retry': 0,
    'bytes_shipped': 0,
    'reconnects': 0,
    'dropped': 0,
    'pending': [],
    'shipped_lsns': [],
}

def ship_tick():
    """
    Try to ship frames from pending. If sock is dropped, count as retry/drop,
    reconnect, and try again next tick.
    Returns True if any frames shipped, False otherwise.
    """
    if sock_state['dropped'] or not sock_state['connected']:
        shipper_state['dropped'] += 1
        return False

    new_pending = []
    shipped_this_tick = 0
    for frame in shipper_state['pending']:
        ok = proto_ship_one(frame)
        if ok:
            shipper_state['frames_ok'] += 1
            # bytes = approximate size of lsn(8) + payload + crc(8)
            payload = frame[1] if len(frame) > 1 else ''
            crc = frame[2] if len(frame) > 2 else ''
            shipper_state['bytes_shipped'] += 8 + len(payload) + len(crc)
            shipper_state['shipped_lsns'].append(frame[0])
            shipped_this_tick += 1
        else:
            shipper_state['frames_retry'] += 1
            new_pending.append(frame)

    shipper_state['pending'] = new_pending
    shipper_state['pages_shipped'] = len(shipper_state['shipped_lsns'])
    return shipped_this_tick > 0

def ship_reconnect():
    shipper_state['reconnects'] += 1
    sock_reset()

def ship_stats():
    return {
        'pages_shipped': shipper_state['pages_shipped'],
        'frames_ok': shipper_state['frames_ok'],
        'frames_retry': shipper_state['frames_retry'],
        'bytes_shipped': shipper_state['bytes_shipped'],
        'reconnects': shipper_state['reconnects'],
        'dropped': shipper_state['dropped'],
        'lsn_hwm': max(shipper_state['shipped_lsns']) if shipper_state['shipped_lsns'] else 0,
    }

def ship_queue_frame(frame):
    shipper_state['pending'].append(frame)

# ---- wal_metrics ----
metrics_state = {'records': []}

def metrics_record(key, value):
    metrics_state['records'].append((key, value))

def metrics_snapshot():
    return list(metrics_state['records'])

# ---- wal_reporter ----
def report_emit(primary, follower, stats, applied_lsn, verified, metrics):
    out = {
        'WAL_SHIP_PRIMARY': primary,
        'WAL_SHIP_FOLLOWER': follower,
        'WAL_SHIP_PAGES_SHIPPED': stats['pages_shipped'],
        'WAL_SHIP_FRAMES_OK': stats['frames_ok'],
        'WAL_SHIP_FRAMES_RETRY': stats['frames_retry'],
        'WAL_SHIP_BYTES_SHIPPED': stats['bytes_shipped'],
        'WAL_SHIP_LSN_HWM': stats['lsn_hwm'],
        'WAL_SHIP_CATCHUP_MS': 0,
        'WAL_SHIP_RECONNECTS': stats['reconnects'],
        'WAL_SHIP_DROPPED': stats['dropped'],
        'WAL_SHIP_APPLIED_LSN': applied_lsn,
        'WAL_SHIP_VERIFIED': '#t' if verified else '#f',
    }
    return out


def main():
    random.seed(42)

    # 1. Generate ids
    primary = ids_make_primary()
    follower = ids_make_follower()

    # 2. Build segment: append 7 pages
    N = 7
    for i in range(N):
        payload = f"page-{i}-hello"
        seg_append_page(payload)

    # Build frames for each page
    pages = seg_pages()
    frames = []
    for p in pages:
        f = frame_encode(p['lsn'], p['payload'], p['crc'])
        frames.append(f)

    # Queue all frames for shipping
    for f in frames:
        ship_queue_frame(f)

    # 3. Open transport + handshake
    buf_new()
    sock_reset()
    proto_handshake(primary, follower)
    follow_attach(follower)

    # 4. ship-tick! M=4 times; for 2 of them force drop+reconnect
    M = 4
    drop_ticks = {1, 3}  # ticks 1 and 3 (0-indexed) force drops
    catchup_start = None
    catchup_end = None

    for t in range(M):
        if t in drop_ticks:
            # Force drop
            sock_drop()
            ship_tick()  # this will count as dropped
            ship_reconnect()
            # Re-queue any pending frames (they're still in pending)
        else:
            ok = ship_tick()
            if ok and catchup_start is None:
                catchup_start = t
            # Drain follower side
            received = proto_recv_loop()
            for frame in received:
                follow_apply_one(frame)
            if catchup_end is None and follow_applied_lsn() >= seg_lsn_high():
                catchup_end = t

    # Final drain in case some frames came through
    received = proto_recv_loop()
    for frame in received:
        follow_apply_one(frame)

    if catchup_end is None:
        catchup_end = M

    catchup_ms = (catchup_end - (catchup_start if catchup_start is not None else 0)) * 10

    # 6. Capture stats
    stats = ship_stats()
    # Update LSN hwm to include any retried-then-shipped frames
    if stats['frames_ok'] > 0:
        stats['lsn_hwm'] = seg_lsn_high()
    applied_lsn = follow_applied_lsn()
    verified = follow_verify()

    metrics_record('frames_ok', stats['frames_ok'])
    metrics_record('reconnects', stats['reconnects'])

    # 7. Report
    report = report_emit(primary, follower, stats, applied_lsn, verified, metrics_snapshot())
    report['WAL_SHIP_CATCHUP_MS'] = catchup_ms

    # Print in exact order
    keys_order = [
        'WAL_SHIP_PRIMARY',
        'WAL_SHIP_FOLLOWER',
        'WAL_SHIP_PAGES_SHIPPED',
        'WAL_SHIP_FRAMES_OK',
        'WAL_SHIP_FRAMES_RETRY',
        'WAL_SHIP_BYTES_SHIPPED',
        'WAL_SHIP_LSN_HWM',
        'WAL_SHIP_CATCHUP_MS',
        'WAL_SHIP_RECONNECTS',
        'WAL_SHIP_DROPPED',
        'WAL_SHIP_APPLIED_LSN',
        'WAL_SHIP_VERIFIED',
    ]
    for k in keys_order:
        print(f"{k}={report[k]}")

if __name__ == '__main__':
    main()
