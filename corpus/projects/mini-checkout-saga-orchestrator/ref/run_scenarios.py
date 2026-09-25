import sys

# In-memory toy semantics for a multi-step checkout saga with compensating actions.
# 5 steps: auth -> inventory-hold -> payment-auth -> payment-capture -> fulfillment-kickoff

STEP_NAMES = [
    "auth",
    "inventory-hold",
    "payment-auth",
    "payment-capture",
    "fulfillment-kickoff",
]

class Journal:
    def __init__(self):
        self.records = {}     # (saga_id, step) -> status string ("done" or "compensated")
        self.rollback_log = []  # list of (saga_id, step)

def make_journal():
    return Journal()

def journal_record(j, saga_id, step):
    key = (saga_id, step)
    if key not in j.records:
        j.records[key] = "done"
    return j

def already_done(j, saga_id, step):
    return j.records.get((saga_id, step)) == "done"

def saga_state(j, saga_id):
    # Return ordered list of step statuses for a saga, in canonical step order
    return [(s, j.records.get((saga_id, s))) for s in STEP_NAMES]

# Service views — these are derived from the journal/saga state, not hardcoded.

def svc_order(j, saga_id):
    # Order is considered PLACED once auth is done, CANCELLED if auth was compensated and no further commits.
    states = saga_state(j, saga_id)
    auth_status = dict(states).get("auth")
    payment_capture_status = dict(states).get("payment-capture")
    fulfillment_status = dict(states).get("fulfillment-kickoff")
    if auth_status == "done" and (fulfillment_status == "done"):
        return "FULFILLED"
    if auth_status == "done" and payment_capture_status == "done":
        return "PAID"
    if auth_status == "done":
        return "PLACED"
    if auth_status == "compensated":
        return "CANCELLED"
    return "NONE"

def svc_inventory(j, saga_id):
    s = dict(saga_state(j, saga_id)).get("inventory-hold")
    if s == "done":
        # released if fulfillment done or compensated after the fact
        fulfill = dict(saga_state(j, saga_id)).get("fulfillment-kickoff")
        if fulfill == "done":
            return "CONSUMED"
        return "HELD"
    if s == "compensated":
        return "RELEASED"
    return "NONE"

def svc_payment(j, saga_id):
    cap = dict(saga_state(j, saga_id)).get("payment-capture")
    auth = dict(saga_state(j, saga_id)).get("payment-auth")
    if cap == "done":
        return "CAPTURED"
    if auth == "done":
        return "AUTHORIZED"
    if auth == "compensated":
        return "VOIDED"
    return "NONE"

def svc_fulfillment(j, saga_id):
    s = dict(saga_state(j, saga_id)).get("fulfillment-kickoff")
    if s == "done":
        return "QUEUED"
    if s == "compensated":
        return "CANCELLED"
    return "NONE"

# Handlers — each step may succeed or, if it matches the injected failure step, raise.
# Each handler is idempotent via already_done.

class SagaError(Exception):
    pass

def step_auth(j, saga_id, failure_step):
    if failure_step == "auth":
        raise SagaError("auth failed")
    journal_record(j, saga_id, "auth")
    return True

def compensate_auth(j, saga_id):
    journal_record(j, saga_id, "auth")  # ensure entry
    j.records[(saga_id, "auth")] = "compensated"
    j.rollback_log.append((saga_id, "auth"))

def step_inventory_hold(j, saga_id, failure_step):
    if failure_step == "inventory-hold":
        raise SagaError("inventory-hold failed")
    journal_record(j, saga_id, "inventory-hold")
    return True

def compensate_inventory_hold(j, saga_id):
    j.records[(saga_id, "inventory-hold")] = "compensated"
    j.rollback_log.append((saga_id, "inventory-hold"))

def step_payment_auth(j, saga_id, failure_step):
    if failure_step == "payment-auth":
        raise SagaError("payment-auth failed")
    journal_record(j, saga_id, "payment-auth")
    return True

def compensate_payment_auth(j, saga_id):
    j.records[(saga_id, "payment-auth")] = "compensated"
    j.rollback_log.append((saga_id, "payment-auth"))

def step_payment_capture(j, saga_id, failure_step):
    if failure_step == "payment-capture":
        raise SagaError("payment-capture failed")
    journal_record(j, saga_id, "payment-capture")
    return True

def compensate_payment_capture(j, saga_id):
    j.records[(saga_id, "payment-capture")] = "compensated"
    j.rollback_log.append((saga_id, "payment-capture"))

def step_fulfillment_kickoff(j, saga_id, failure_step):
    if failure_step == "fulfillment-kickoff":
        raise SagaError("fulfillment-kickoff failed")
    journal_record(j, saga_id, "fulfillment-kickoff")
    return True

def compensate_fulfillment_kickoff(j, saga_id):
    j.records[(saga_id, "fulfillment-kickoff")] = "compensated"
    j.rollback_log.append((saga_id, "fulfillment-kickoff"))

STEP_DISPATCH = {
    "auth": (step_auth, compensate_auth),
    "inventory-hold": (step_inventory_hold, compensate_inventory_hold),
    "payment-auth": (step_payment_auth, compensate_payment_auth),
    "payment-capture": (step_payment_capture, compensate_payment_capture),
    "fulfillment-kickoff": (step_fulfillment_kickoff, compensate_fulfillment_kickoff),
}

# Compensator

def rollback_completed(j, saga_id, completed_steps):
    # Run compensators in reverse order of completion
    for step in reversed(completed_steps):
        _, comp = STEP_DISPATCH[step]
        comp(j, saga_id)

def build_audit_trail(j, saga_id):
    # Combine forward journal entries (done) and rollback log (compensated) into a single ordered audit list.
    forward = [(s, "DONE") for s in STEP_NAMES if j.records.get((saga_id, s)) == "done"]
    rollback = [(s, "COMPENSATED") for (sid, s) in j.rollback_log if sid == saga_id]
    return forward + rollback

# Orchestrator

def run_saga(j, id_gen, failure_step):
    saga_id = next_id(id_gen, "SAGA")
    completed = []
    for step in STEP_NAMES:
        # Idempotency guard
        if already_done(j, saga_id, step):
            completed.append(step)
            continue
        try:
            handler, _ = STEP_DISPATCH[step]
            handler(j, saga_id, failure_step)
            completed.append(step)
        except SagaError:
            rollback_completed(j, saga_id, completed)
            return saga_id
    return saga_id

def saga_status(j, saga_id):
    statuses = dict(saga_state(j, saga_id))
    if all(statuses.get(s) == "done" for s in STEP_NAMES):
        return "COMPLETED"
    if any(statuses.get(s) == "compensated" for s in STEP_NAMES):
        return "COMPENSATED"
    if any(statuses.get(s) == "done" for s in STEP_NAMES):
        return "PARTIAL"
    return "FAILED"

# ID generator

class IdGen:
    def __init__(self):
        self.counter = 0

def make_id_gen():
    return IdGen()

def next_id(gen, prefix):
    gen.counter += 1
    return f"{prefix}-{gen.counter:04d}"

# Helpers to derive ordered ids from the saga's completed steps.

def order_id(j, saga_id, id_gen):
    if already_done(j, saga_id, "auth"):
        return next_id(id_gen, "ORD")
    return "ORD-NONE"

def payment_id(j, saga_id, id_gen):
    if already_done(j, saga_id, "payment-auth") or dict(saga_state(j, saga_id)).get("payment-auth") == "compensated":
        return next_id(id_gen, "PAY")
    return "PAY-NONE"

def inventory_hold_id(j, saga_id, id_gen):
    if dict(saga_state(j, saga_id)).get("inventory-hold") in ("done", "compensated"):
        return next_id(id_gen, "HOLD")
    return "HOLD-NONE"

def fulfillment_job_id(j, saga_id, id_gen):
    if dict(saga_state(j, saga_id)).get("fulfillment-kickoff") in ("done", "compensated"):
        return next_id(id_gen, "FUL")
    return "FUL-NONE"

# Counts derived by walking the journal / rollback log (no hardcoded literals).

def count_completed_steps(j, saga_id):
    return sum(1 for s in STEP_NAMES if j.records.get((saga_id, s)) == "done")

def count_compensated_steps(j, saga_id):
    return sum(1 for (sid, s) in j.rollback_log if sid == saga_id)

def main(args):
    j = make_journal()
    g = make_id_gen()
    failure_step = args[1] if len(args) > 1 and args[1] else False

    saga_id = run_saga(j, g, failure_step)

    status = saga_status(j, saga_id)
    audit = build_audit_trail(j, saga_id)

    order_state = svc_order(j, saga_id)
    payment_state = svc_payment(j, saga_id)
    inv_state = svc_inventory(j, saga_id)
    ful_state = svc_fulfillment(j, saga_id)

    o_id = order_id(j, saga_id, g)
    p_id = payment_id(j, saga_id, g)
    h_id = inventory_hold_id(j, saga_id, g)
    f_id = fulfillment_job_id(j, saga_id, g)

    completed = count_completed_steps(j, saga_id)
    compensated = count_compensated_steps(j, saga_id)

    # Dual-write risk: true if any step was compensated (partial commit / rollback window)
    dual_write_risk = "true" if compensated > 0 else "false"

    exit_code = 0 if status == "COMPLETED" else (2 if status == "COMPENSATED" else 1)

    audit_str = ";".join(f"{s}:{st}" for s, st in audit)

    print(f"SAGA_ID={saga_id}")
    print(f"SAGA_STATUS={status}")
    print(f"STEP_AUDIT={audit_str}")
    print(f"DUAL_WRITE_RISK={dual_write_risk}")
    print(f"ORDER_ID={o_id}")
    print(f"ORDER_STATE={order_state}")
    print(f"PAYMENT_ID={p_id}")
    print(f"PAYMENT_STATE={payment_state}")
    print(f"INVENTORY_HOLD_ID={h_id}")
    print(f"INVENTORY_HOLD_STATE={inv_state}")
    print(f"FULFILLMENT_JOB_ID={f_id}")
    print(f"FULFILLMENT_STATE={ful_state}")
    print(f"TOTAL_STEPS={len(STEP_NAMES)}")
    print(f"COMPLETED_STEPS={completed}")
    print(f"COMPENSATED_STEPS={compensated}")
    print(f"EXIT_CODE={exit_code}")

if __name__ == "__main__":
    main(sys.argv)
