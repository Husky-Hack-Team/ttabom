"""Replay the Verified Contact Payment check over the HuskyHack v2 events.

For every "Payment Initiated" event, run engine.evaluate() on that row plus the
member's earlier rows, then score it against the Member Key (via oracle.py only).

Outputs (analysis/out/):
  decisions.csv       one row per initiated payment: our check vs what happened
  member_summary.csv  one row per member
  metrics.json        headline numbers, sensitivity, and callouts
  walkthroughs.md     the anchor cases plus one miss and one false positive

Run: analysis/.venv/bin/python analysis/replay.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

import config
import engine
import oracle
import overlay

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
INTERVENTION_EVENTS = {
    "Warning Displayed",
    "Confirmation Requested",
    "Payment Held",
    "Employee Outreach",
    "Employee Escalation",
    "Account Restricted",
}
MONEY_MOVED_STATUSES = {"Completed"}


def load_events():
    e = pd.read_csv(overlay.EVENTS_CSV, dtype=str, keep_default_na=False)
    e["_seq"] = e["event_sequence"].astype(int)
    return e.sort_values(["synthetic_member_id", "_seq"]).drop(columns="_seq")


def actual_outcomes(events):
    """What really happened to each payment, from its own later rows (scoring only)."""
    out = {}
    for pid, rows in events[events.payment_id != ""].groupby("payment_id", sort=False):
        rows = rows.sort_values("event_sequence", key=lambda s: s.astype(int))
        final = rows.payment_status.iloc[-1]
        intervened = rows[rows.event_type.isin(INTERVENTION_EVENTS)]
        out[pid] = {
            "actual_final_status": final,
            "actual_money_moved": final in MONEY_MOVED_STATUSES,
            "actual_intervened": len(intervened) > 0,
            "actual_first_intervention_ts": intervened.event_timestamp.iloc[0] if len(intervened) else "",
            "actual_member_response": ";".join(x for x in rows.member_response.unique() if x and x != "Not Asked"),
        }
    return out


def run_engine(events, ov, stated):
    by_member = {m: g.to_dict("records") for m, g in events.groupby("synthetic_member_id", sort=False)}
    decisions = {}
    for m, rows in by_member.items():
        for row in rows:
            if row["event_type"] != "Payment Initiated":
                continue
            ctx = dict(ov[m], stated=stated.get(row["payment_id"]))
            decisions[row["payment_id"]] = (row, engine.evaluate(row, rows, ctx))
    return decisions


def minutes_between(a, b):
    if not a or not b:
        return None
    return round((engine.parse_ts(b) - engine.parse_ts(a)).total_seconds() / 60)


def score(decisions, key, actual, cancel_rate):
    scams = oracle.scam_payment_ids(key)
    rows = []
    for pid, (ev, d) in decisions.items():
        m = ev["synthetic_member_id"]
        k = key[m]
        is_scam = pid in scams
        sim = oracle.simulate(d, k, is_scam, cancel_rate)
        amount = float(ev["amount"] or 0)
        a = actual.get(pid, {})
        asked = d["contact_asked"] or {}
        rows.append(
            {
                "payment_id": pid,
                "synthetic_member_id": m,
                "event_timestamp": ev["event_timestamp"],
                "channel": ev["channel"],
                "payment_rail": ev["payment_rail"],
                "amount": amount,
                "recipient_id": ev["recipient_id"],
                "recipient_status": ev["recipient_status"],
                "is_scam_payment": is_scam,
                "member_group": member_group(k),
                "decision": d["decision"],
                "hold_window": d["hold_window"] or "",
                "contact_asked": f"{asked.get('name') or 'member'} via {asked['channel']} {asked.get('masked', '')}".strip()
                if asked
                else "",
                "reasons": " | ".join(d["reasons"]),
                "signals_used": ";".join(d["signals_used"]),
                "simulated_answer": sim["simulated_answer"],
                "paused_before_money_moved": d["decision"] != "PASS",
                "friction_minutes": sim["friction_minutes"],
                "stop_probability": sim["stop_probability"],
                "expected_dollars_stopped": round(amount * sim["stop_probability"], 2) if is_scam else 0.0,
                "send_anyway_expected": round(1 - sim["stop_probability"], 2)
                if is_scam and d["decision"] == "MISMATCH_PAUSE"
                else 0.0,
                **{k2: a.get(k2, "") for k2 in ("actual_final_status", "actual_money_moved", "actual_intervened", "actual_member_response")},
                "actual_first_intervention_ts": a.get("actual_first_intervention_ts", ""),
            }
        )
    return pd.DataFrame(rows)


def member_group(k):
    if k["anchor_persona"]:
        return "anchor"
    if k["is_legitimate_lookalike"] == "Yes":
        return "lookalike"
    if k["scenario_type"] == "Normal Activity":
        return "routine"
    return "scam"


def summarize_members(df, key):
    out = []
    for m, k in key.items():
        g = df[df.synthetic_member_id == m]
        s = g[g.is_scam_payment]
        flagged = g[g.decision != "PASS"]
        first_ours = s[s.paused_before_money_moved].event_timestamp.min() if len(s) else ""
        if len(s) and s[s.paused_before_money_moved].empty:
            first_ours = ""
        first_ours = first_ours if isinstance(first_ours, str) else ""
        # earliest by real time, not string order
        if len(s[s.paused_before_money_moved]):
            first_ours = min(s[s.paused_before_money_moved].event_timestamp, key=engine.parse_ts)
        out.append(
            {
                "synthetic_member_id": m,
                "anchor_persona": k["anchor_persona"],
                "member_group": member_group(k),
                "scenario_type": k["scenario_type"],
                "scenario_subtype": k["scenario_subtype"],
                "payments_initiated": len(g),
                "scam_payments": len(s),
                "scam_payments_paused": int(s.paused_before_money_moved.sum()),
                "scam_dollars_attempted": round(s.amount.sum(), 2),
                "scam_dollars_paused": round(s[s.paused_before_money_moved].amount.sum(), 2),
                "expected_dollars_stopped": round(s.expected_dollars_stopped.sum(), 2),
                "key_dollars_attempted": float(k["dollars_attempted"] or 0),
                "key_dollars_sent": float(k["dollars_sent"] or 0),
                "key_dollars_prevented": float(k["dollars_prevented"] or 0),
                "key_journey_outcome": k["journey_outcome"],
                "incident_start": k["incident_start"],
                "key_first_intervention": k["first_intervention"],
                "our_first_intervention": first_ours,
                "key_minutes_to_intervention": minutes_between(k["incident_start"], k["first_intervention"]),
                "our_minutes_to_intervention": minutes_between(k["incident_start"], first_ours),
                "payments_flagged": len(flagged),
                "non_scam_payments_flagged": int((~flagged.is_scam_payment).sum()),
                "friction_minutes": int(g.friction_minutes.sum()),
                "non_scam_friction_minutes": int(g[~g.is_scam_payment].friction_minutes.sum()),
                "decisions": ";".join(f"{d}:{n}" for d, n in flagged.decision.value_counts().items()),
            }
        )
    return pd.DataFrame(out)


def metrics(df, ms, key, by_rate):
    scam = df[df.is_scam_payment]
    legit = df[~df.is_scam_payment]
    look = ms[ms.member_group == "lookalike"]
    routine = ms[ms.member_group == "routine"]
    key_attempted = sum(float(k["dollars_attempted"] or 0) for k in key.values())
    key_sent = sum(float(k["dollars_sent"] or 0) for k in key.values())
    key_prevented = sum(float(k["dollars_prevented"] or 0) for k in key.values())
    t_ours = ms.our_minutes_to_intervention.dropna()
    t_key = ms.key_minutes_to_intervention.dropna()
    return {
        "disclaimer": config.DISCLAIMER,
        "payments_initiated": len(df),
        "decisions": df.decision.value_counts().to_dict(),
        "scam": {
            "payments": len(scam),
            "members": int((ms.scam_payments > 0).sum()),
            "payments_paused_before_money_moved": int(scam.paused_before_money_moved.sum()),
            "payments_passed": int((~scam.paused_before_money_moved).sum()),
            "dollars_attempted": round(scam.amount.sum(), 2),
            "dollars_paused_before_money_moved": round(scam[scam.paused_before_money_moved].amount.sum(), 2),
            "expected_dollars_stopped": round(scam.expected_dollars_stopped.sum(), 2),
            "expected_dollars_stopped_by_cancel_rate": by_rate,
            # Paused for a person (employee review, outreach, branch teller) but no stop credited.
            "dollars_paused_for_employee_not_credited": round(
                scam[scam.decision.isin(["EMPLOYEE_REVIEW_HOLD", "EMPLOYEE_OUTREACH", "BRANCH_EMPLOYEE_PROMPT"])].amount.sum(), 2
            ),
            "dollars_confirmed_by_member_and_sent": round(scam[scam.decision == "NEW_PAYEE_CONFIRM"].amount.sum(), 2),
            "decisions": scam.decision.value_counts().to_dict(),
        },
        "key": {
            "dollars_attempted": round(key_attempted, 2),
            "dollars_sent": round(key_sent, 2),
            "dollars_prevented": round(key_prevented, 2),
            "reconciles_with_replay": bool(abs(key_attempted - scam.amount.sum()) < 0.01),
        },
        "time_to_intervention_minutes": {
            "members_with_ours": int(len(t_ours)),
            "median_ours": float(t_ours.median()) if len(t_ours) else None,
            "members_with_key": int(len(t_key)),
            "median_key": float(t_key.median()) if len(t_key) else None,
            "scam_members_key_never_intervened": int(((ms.scam_payments > 0) & (ms.key_first_intervention == "")).sum()),
        },
        "lookalikes": {
            "members": len(look),
            "members_flagged": int((look.payments_flagged > 0).sum()),
            "payments_flagged": int(look.payments_flagged.sum()),
            "friction_minutes": int(look.friction_minutes.sum()),
            "friction_minutes_per_member": round(look.friction_minutes.mean(), 1),
            "decisions": legit[legit.member_group == "lookalike"].query("decision != 'PASS'").decision.value_counts().to_dict(),
        },
        "routine": {
            "members": len(routine),
            "members_flagged": int((routine.payments_flagged > 0).sum()),
            "payments_flagged": int(routine.payments_flagged.sum()),
            "friction_minutes": int(routine.friction_minutes.sum()),
        },
        "non_scam_payments": {
            "total": len(legit),
            "flagged": int((legit.decision != "PASS").sum()),
            "friction_minutes": int(legit.friction_minutes.sum()),
        },
        "assumptions": {
            "cancel_rate_after_not_mine": config.CANCEL_RATE_AFTER_NOT_MINE,
            "ato_stop_rate": config.ATO_STOP_RATE,
            "employee_stop_rate": config.EMPLOYEE_STOP_RATE,
            "confirm_stop_rate": config.CONFIRM_STOP_RATE,
            "friction_minutes": config.FRICTION_MINUTES,
        },
    }


def pick_callouts(df):
    scam = df[df.is_scam_payment]
    # Miss: the biggest scam payment where the member's own confirmation lets the money go.
    pool = scam[scam.decision == "NEW_PAYEE_CONFIRM"]
    miss = (pool if len(pool) else scam[scam.stop_probability == 0]).sort_values("amount", ascending=False).iloc[0]
    passed = scam[~scam.paused_before_money_moved]
    fp_pool = df[(~df.is_scam_payment) & (df.member_group == "lookalike") & (df.decision != "PASS")]
    fp = fp_pool.sort_values(["friction_minutes", "amount"], ascending=False).iloc[0]
    return miss, fp, passed


def card(r):
    return (
        f"| | |\n|---|---|\n"
        f"| Payment | {r.payment_id} · {r.payment_rail} · ${r.amount:,.2f} · {r.channel} · {r.event_timestamp} |\n"
        f"| Recipient | {r.recipient_id or '(cash)'} ({r.recipient_status}) |\n"
        f"| Our decision | **{r.decision}** ({r.hold_window or 'no pause'}) |\n"
        f"| Asked | {r.contact_asked or 'nobody'} → {r.simulated_answer or 'n/a'} |\n"
        f"| Friction added | {r.friction_minutes} min |\n"
        f"| Signals | {r.signals_used.replace(';', ', ')} |\n"
        f"| What actually happened | {r.actual_final_status}"
        f"{' after ' + r.actual_member_response if r.actual_member_response else ''}"
        f"{' (Sound intervened)' if r.actual_intervened else ' (no intervention)'} |\n"
    )


def reasons_md(r):
    return "\n".join(f"- {x}" for x in r.reasons.split(" | "))


def walkthroughs(df, ms, miss, fp, passed):
    get = lambda pid: df[df.payment_id == pid].iloc[0]
    linda, m1037 = get("P1001-003"), get("P1037-002")
    lm = ms[ms.synthetic_member_id == "M1001"].iloc[0]
    parts = [
        "# Replay walkthroughs",
        f"> {config.DISCLAIMER}",
        "",
        "Each card shows our check, computed only from what Sound could see at the moment the payment was "
        "started, next to what the synthetic data says actually happened.",
        "",
        "## 1. Linda (M1001), P1001-003: $8,500 wire in a branch",
        card(linda),
        "What the check says:",
        reasons_md(linda),
        "",
        "Tommy's screen shows the amount, the bank, and the masked account, and two buttons: "
        "\"Yes, it's my account\" or \"No, it's not mine\". Tommy can't approve or cancel. "
        "Tommy answers \"No, it's not mine.\" Linda still decides. If Linda cancels, the wire never leaves. "
        "If Linda chooses \"Send anyway\", that's logged, the wire goes, and a recall request opens at once.",
        "",
        f"Time to intervention: the key's first intervention came {lm.key_minutes_to_intervention} min after the "
        f"incident started. Ours is at initiation, {lm.our_minutes_to_intervention} min after. In the data, "
        "Linda overrode a generic hold and lost $8,500. "
        f"At a {config.CANCEL_RATE_AFTER_NOT_MINE:.0%} cancel rate after \"not mine\", the replay expects "
        f"${linda.expected_dollars_stopped:,.2f} of this wire to be stopped.",
        "",
        "## 2. M1037, P1037-002: $1,188.37 P2P to a family member's new account",
        card(m1037),
        "What the check says:",
        reasons_md(m1037),
        "",
        f"The family member answers \"Yes, it's my account\" and the payment is submitted. Friction added: "
        f"{m1037.friction_minutes} min, the time for one contact answer. This is a legitimate look-alike, "
        "and it goes through within minutes.",
        "",
        "## 3. A miss",
        card(miss),
        "What the check says:",
        reasons_md(miss),
        "",
        "Why it's a miss: the member is the one being deceived and taps \"confirm\" for a payee they believe in. "
        "The check paused the payment, but nothing independent contradicted the member's story, so the replay "
        "credits no stop. A confirmation screen can't beat a scam the member believes. These journeys need "
        "pattern-aware human outreach (the Starter Kit's suggestion), which this check doesn't model.",
        "",
        f"Scam payments that passed with no pause at all: {len(passed)}.",
        "",
        "## 4. A false positive",
        card(fp),
        "What the check says:",
        reasons_md(fp),
        "",
        f"Why it's a false positive: this is a legitimate member. The check adds {fp.friction_minutes} min of "
        "employee review to a real payment. That cost is the price of escalating a first wire in years "
        "or an unusually large one. The pilot tracks it as look-alike friction minutes.",
        "",
    ]
    return "\n".join(parts)


def main(cancel_rate=config.CANCEL_RATE_AFTER_NOT_MINE):
    events = load_events()
    key = oracle.load_key(overlay.KEY_CSV)
    if not (overlay.OUT / "stated_recipient.csv").exists():
        overlay.build()
    ov, stated = overlay.load()
    decisions = run_engine(events, ov, stated)
    actual = actual_outcomes(events)
    df = score(decisions, key, actual, cancel_rate)
    by_rate = {
        str(r): round(float(score(decisions, key, actual, r).query("is_scam_payment").expected_dollars_stopped.sum()), 2)
        for r in config.CANCEL_RATE_SENSITIVITY
    }
    ms = summarize_members(df, key)
    met = metrics(df, ms, key, by_rate)
    miss, fp, passed = pick_callouts(df)
    met["callouts"] = {
        "miss": {"payment_id": miss.payment_id, "member": miss.synthetic_member_id, "decision": miss.decision, "amount": float(miss.amount)},
        "false_positive": {"payment_id": fp.payment_id, "member": fp.synthetic_member_id, "decision": fp.decision, "friction_minutes": int(fp.friction_minutes)},
        "scam_payments_passed": passed.payment_id.tolist(),
    }

    OUT.mkdir(exist_ok=True)
    df.insert(0, "disclaimer", config.DISCLAIMER)
    df.to_csv(OUT / "decisions.csv", index=False)
    ms.insert(0, "disclaimer", config.DISCLAIMER)
    ms.to_csv(OUT / "member_summary.csv", index=False)
    (OUT / "metrics.json").write_text(json.dumps(met, indent=2, default=float) + "\n")
    (OUT / "walkthroughs.md").write_text(walkthroughs(df, ms, miss, fp, passed))
    return met


def print_summary(m):
    s, k, lk, rt = m["scam"], m["key"], m["lookalikes"], m["routine"]
    t = m["time_to_intervention_minutes"]
    print(m["disclaimer"])
    print(f"Payments initiated: {m['payments_initiated']}  decisions: {m['decisions']}")
    print(
        f"Scam payments: {s['payments']} ({s['members']} members). Paused before money moved: "
        f"{s['payments_paused_before_money_moved']}; passed: {s['payments_passed']}"
    )
    print(
        f"Scam dollars attempted ${s['dollars_attempted']:,.2f} (key ${k['dollars_attempted']:,.2f}, reconciles: {k['reconciles_with_replay']})"
    )
    print(f"  paused before money moved: ${s['dollars_paused_before_money_moved']:,.2f}")
    print(f"  expected stopped: ${s['expected_dollars_stopped']:,.2f}  by cancel rate {s['expected_dollars_stopped_by_cancel_rate']}")
    print(f"  paused for an employee, stop not credited: ${s['dollars_paused_for_employee_not_credited']:,.2f}; member confirmed and sent: ${s['dollars_confirmed_by_member_and_sent']:,.2f}")
    print(f"  key: sent ${k['dollars_sent']:,.2f}, prevented ${k['dollars_prevented']:,.2f}")
    print(f"Median minutes incident→intervention: ours {t['median_ours']} ({t['members_with_ours']} members), key {t['median_key']} ({t['members_with_key']} members)")
    print(f"Look-alikes: {lk['members_flagged']}/{lk['members']} flagged, {lk['payments_flagged']} payments, {lk['friction_minutes']} friction min ({lk['decisions']})")
    print(f"Routine: {rt['members_flagged']}/{rt['members']} members flagged, {rt['payments_flagged']} payments, {rt['friction_minutes']} friction min")
    print(f"Callouts: miss {m['callouts']['miss']}, false positive {m['callouts']['false_positive']}")


if __name__ == "__main__":
    sys.exit(print_summary(main()))
