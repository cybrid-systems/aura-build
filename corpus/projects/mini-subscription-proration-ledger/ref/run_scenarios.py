#!/usr/bin/env python3
"""Reference implementation of the mini-subscription-proration-ledger scenario."""
import sys
from datetime import date, timedelta

# ---------- money.aura ----------
def money_cents(d):
    return int(round(float(d)))

def money_add(a, b):
    return a + b

def money_sub(a, b):
    return a - b

def money_mul(a, n):
    return int(round(a * n))

def money_div(a, n):
    return a // n

def money_zero():
    return 0

# ---------- date.aura ----------
DATE_FMT = "%Y-%m-%d"

def date_day(d):
    return d

def date_from_yyyy_mm_dd(s):
    return datetime.strptime(s, DATE_FMT).date() if False else __import__("datetime").datetime.strptime(s, DATE_FMT).date()

def date_to_yyyy_mm_dd(d):
    return d.strftime(DATE_FMT)

def date_add_days(d, n):
    return d + timedelta(days=n)

def date_diff_days(a, b):
    return (a - b).days

def date_eq(a, b):
    return a == b

def date_lt(a, b):
    return a < b

# ---------- plan.aura ----------
def make_plan(pid, name, monthly_cents):
    return {"id": pid, "name": name, "monthly_cents": monthly_cents}

def plan_id(p):
    return p["id"]

def plan_name(p):
    return p["name"]

def plan_monthly_cents(p):
    return p["monthly_cents"]

def plan_lookup(plans, pid):
    for p in plans:
        if p["id"] == pid:
            return p
    return None

# ---------- account.aura ----------
def make_account(code, atype):
    return {"code": code, "type": atype}

def acct_code(a):
    return a["code"]

def acct_type(a):
    return a["type"]

def account_lookup(accounts, code):
    for a in accounts:
        if a["code"] == code:
            return a
    return None

def coa_default():
    return [
        make_account("AR", "asset"),
        make_account("REV_A", "revenue"),
        make_account("REV_B", "revenue"),
        make_account("CRED", "liability"),
    ]

# ---------- journal.aura ----------
def make_line(ts, acct, dr, cr, memo):
    return {"ts": ts, "acct": acct, "dr": dr, "cr": cr, "memo": memo}

def line_acct(l):
    return l["acct"]

def line_dr(l):
    return l["dr"]

def line_cr(l):
    return l["cr"]

def line_memo(l):
    return l["memo"]

def journal_append(j, l):
    j.append(l)
    return j

def journal_all(j):
    return list(j)

# ---------- proration.aura ----------
def daily_rate_cents(monthly_cents, period_days):
    return monthly_cents // period_days

def prorate_upgrade(old_monthly, new_monthly, days_remaining, period_days):
    diff = new_monthly - old_monthly
    if diff <= 0:
        return 0
    return daily_rate_cents(diff, period_days) * days_remaining

def prorate_credit(monthly_cents, unused_days, period_days):
    return daily_rate_cents(monthly_cents, period_days) * unused_days

# ---------- subscription.aura ----------
def make_sub(sid, plan_id, started_on, period_days):
    return {"id": sid, "plan_id": plan_id, "started_on": started_on, "period_days": period_days}

def sub_id(s):
    return s["id"]

def sub_plan_id(s):
    return s["plan_id"]

def sub_started_on(s):
    return s["started_on"]

def sub_days_remaining(s, on, period_days):
    used = (on - s["started_on"]).days
    return max(0, period_days - used)

def sub_days_used(s, on):
    return (on - s["started_on"]).days

def sub_change_plan(s, new_plan_id, on):
    s["plan_id"] = new_plan_id
    return s

# ---------- ledger.aura ----------
def make_ledger():
    return {"lines": []}

def ledger_add_line(lg, line):
    lg["lines"].append(line)

def ledger_lines(lg):
    return list(lg["lines"])

def ledger_balance(lg, account_code):
    bal = 0
    for l in lg["lines"]:
        if l["acct"] == account_code:
            bal += l["dr"] - l["cr"]
    return bal

def ledger_total_debits(lg):
    return sum(l["dr"] for l in lg["lines"])

def ledger_total_credits(lg):
    return sum(l["cr"] for l in lg["lines"])

def ledger_balanced(lg):
    return ledger_total_debits(lg) == ledger_total_credits(lg)

# ---------- posting.aura ----------
def post_charge(lg, accounts, ts, sub, amount_cents, memo):
    plan_id = sub["plan_id"]
    if plan_id == "basic":
        rev = "REV_A"
    elif plan_id == "pro":
        rev = "REV_B"
    else:
        rev = "REV_A"
    ledger_add_line(lg, make_line(ts, "AR", amount_cents, 0, memo))
    ledger_add_line(lg, make_line(ts, rev, 0, amount_cents, memo))

def post_upgrade(lg, accounts, ts, sub, old_plan, new_plan, days_remaining, period_days):
    delta = prorate_upgrade(old_plan["monthly_cents"], new_plan["monthly_cents"], days_remaining, period_days)
    if delta <= 0:
        return delta
    memo = f"upgrade {old_plan['id']}->{new_plan['id']} day{ts}"
    ledger_add_line(lg, make_line(ts, "AR", delta, 0, memo))
    ledger_add_line(lg, make_line(ts, "REV_A", 0, delta, memo))
    ledger_add_line(lg, make_line(ts, "REV_B", delta, 0, memo))
    return delta

def post_credit(lg, accounts, ts, sub, amount_cents, memo):
    ledger_add_line(lg, make_line(ts, "AR", 0, amount_cents, memo))
    ledger_add_line(lg, make_line(ts, "CRED", amount_cents, 0, memo))

def post_daily_accrual(lg, accounts, ts, sub, day_idx, period_days):
    plan_id = sub["plan_id"]
    monthly = 4900 if plan_id == "basic" else 9900
    rev = "REV_A" if plan_id == "basic" else "REV_B"
    amount = daily_rate_cents(monthly, period_days)
    ledger_add_line(lg, make_line(ts, "AR", amount, 0, f"daily-{plan_id}"))
    ledger_add_line(lg, make_line(ts, rev, 0, amount, f"daily-{plan_id}"))

# ---------- scenario.aura ----------
def build_catalog():
    return [
        make_plan("basic", "Basic", 4900),
        make_plan("pro", "Pro", 9900),
    ]

def build_accounts():
    return coa_default()

def scenario_date_anchor():
    return date(2025, 3, 1)

def run_scenario():
    plans = build_catalog()
    accounts = build_accounts()
    anchor = scenario_date_anchor()
    period_days = 30

    sub1 = make_sub("sub-1", "basic", anchor, period_days)
    sub2 = make_sub("sub-2", "pro", anchor, period_days)
    subs = [sub1, sub2]

    lg = make_ledger()

    # Day 1: initial charge 1/30 of monthly
    ts1 = date_to_yyyy_mm_dd(anchor)
    daily_basic = daily_rate_cents(4900, period_days)
    daily_pro = daily_rate_cents(9900, period_days)
    post_charge(lg, accounts, ts1, sub1, daily_basic, "initial charge basic")
    post_charge(lg, accounts, ts1, sub2, daily_pro, "initial charge pro")

    # Day 10: sub-1 upgrades basic->pro; 20 days remaining
    upgrade_day = date_add_days(anchor, 9)
    ts10 = date_to_yyyy_mm_dd(upgrade_day)
    days_remaining = sub_days_remaining(sub1, upgrade_day, period_days)
    old_plan = plan_lookup(plans, "basic")
    new_plan = plan_lookup(plans, "pro")
    post_upgrade(lg, accounts, ts10, sub1, old_plan, new_plan, days_remaining, period_days)
    sub_change_plan(sub1, "pro", upgrade_day)

    # Day 12: goodwill credit of 1500 to sub-2
    credit_day = date_add_days(anchor, 11)
    ts12 = date_to_yyyy_mm_dd(credit_day)
    post_credit(lg, accounts, ts12, sub2, 1500, "goodwill credit sub-2")

    # Days 2..30 daily accruals (29 days for each sub)
    for d in range(2, 31):
        day = date_add_days(anchor, d - 1)
        ts = date_to_yyyy_mm_dd(day)
        post_daily_accrual(lg, accounts, ts, sub1, d, period_days)
        post_daily_accrual(lg, accounts, ts, sub2, d, period_days)

    return lg, accounts, subs

# ---------- report.aura ----------
def report_summarize(lg, accounts, subs):
    return {
        "sub_count": len(subs),
        "journal_lines": len(lg["lines"]),
        "total_debits": ledger_total_debits(lg),
        "total_credits": ledger_total_credits(lg),
        "ar_balance": ledger_balance(lg, "AR"),
        "rev_a_balance": ledger_balance(lg, "REV_A"),
        "rev_b_balance": ledger_balance(lg, "REV_B"),
        "cred_balance": ledger_balance(lg, "CRED"),
        "balanced": ledger_balanced(lg),
    }

def report_key_count(subs):
    return len(subs)

def report_line_count(lg):
    return len(lg["lines"])

def report_flag_balanced(lg):
    return ledger_balanced(lg)

def report_ar_balance(lg, accounts):
    return ledger_balance(lg, "AR")

# ---------- print.aura ----------
def print_row(key, value):
    print(f"{key}={value}")

def print_result(summary):
    print_row("SUB_COUNT", summary["sub_count"])
    print_row("PLAN_A_MONTHLY_CENTS", 4900)
    print_row("PLAN_B_MONTHLY_CENTS", 9900)
    print_row("PERIOD_DAYS", 30)
    print_row("JOURNAL_LINES", summary["journal_lines"])
    print_row("TOTAL_DEBITS_CENTS", summary["total_debits"])
    print_row("TOTAL_CREDITS_CENTS", summary["total_credits"])
    print_row("ACCT_AR_BALANCE_CENTS", summary["ar_balance"])
    print_row("ACCT_REV_PLAN_A_BALANCE_CENTS", summary["rev_a_balance"])
    print_row("ACCT_REV_PLAN_B_BALANCE_CENTS", summary["rev_b_balance"])
    print_row("ACCT_CREDIT_BALANCE_CENTS", summary["cred_balance"])
    print_row("LEDGER_BALANCED", "true" if summary["balanced"] else "false")

# ---------- main.aura ----------
def main():
    lg, accounts, subs = run_scenario()
    summary = report_summarize(lg, accounts, subs)
    print_result(summary)

if __name__ == "__main__":
    main()
