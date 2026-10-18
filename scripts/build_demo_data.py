"""Build frontend/app/data/demo.json for the one-page demo.

Reads only the HuskyHack files and the documented overlay:
  data/raw/HuskyHack_Synthetic_Events_v2.csv
  data/raw/HuskyHack_Member_Key_v2.csv
  data/overlay/contacts_overlay.csv, recipients_overlay.csv,
  stated_recipient.csv, member_channels.csv
and data/overlay/recipient_numbers.csv, which it creates if missing
(synthetic routing and account numbers, seed 2026).

Standard library only. Never hand-edit demo.json; rerun this instead:
  python3 scripts/build_demo_data.py
"""

import csv
import json
import random
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OVERLAY = ROOT / "data" / "overlay"
OUT = ROOT / "frontend" / "app" / "data" / "demo.json"
NUMBERS = OVERLAY / "recipient_numbers.csv"
SEED = 2026

SCAM = {"member": "M1001", "payment": "P1001-003"}
LOOKALIKE = {"member": "M1037", "payment": "P1037-002"}
HOLD_HOURS = 4
CONTACT_MIN_ON_FILE_DAYS = 7
DISCLAIMER = "Synthetic data only. Not a measure of real fraud rates."
SOURCE_NOTE = (
    "Synthetic data from the HuskyHack 2026 starter kit. Names, banks and account numbers "
    "come from our documented overlay on top of the dataset's recipient IDs."
)


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aba_check_digit(first8):
    weights = (3, 7, 1, 3, 7, 1, 3, 7)
    total = sum(int(d) * w for d, w in zip(first8, weights))
    return str((10 - total % 10) % 10)


def ensure_recipient_numbers():
    """Synthetic 9-digit routing (valid ABA checksum) and an account number ending in the masked last 4."""
    if NUMBERS.exists():
        return
    rng = random.Random(SEED)
    routing_by_bank = {}
    rows = []
    for r in sorted(read(OVERLAY / "recipients_overlay.csv"), key=lambda r: r["recipient_id"]):
        bank = r["bank"]
        if bank not in routing_by_bank:
            first8 = f"{rng.randint(1, 12):02d}" + f"{rng.randint(0, 999999):06d}"
            routing_by_bank[bank] = first8 + aba_check_digit(first8)
        last4 = r["account_masked"][-4:]
        account = f"{rng.randint(1000, 999999):06d}{last4}"
        rows.append(
            {
                "recipient_id": r["recipient_id"],
                "synthetic_member_id": r["synthetic_member_id"],
                "bank": bank,
                "routing_number": routing_by_bank[bank],
                "account_number": account,
                "account_masked": r["account_masked"],
            }
        )
    with open(NUMBERS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def ts(value):
    return datetime.strptime(value, "%m/%d/%Y %H:%M")


def clock(dt):
    return dt.strftime("%I:%M %p").lstrip("0")


def day(dt):
    return dt.strftime("%b %d, %Y").replace(" 0", " ")


def money(value):
    return round(float(value), 2)


def payment_rows(events, member, payment):
    return [e for e in events if e["synthetic_member_id"] == member and e["payment_id"] == payment]


def initiated(events, member, payment):
    return next(e for e in payment_rows(events, member, payment) if e["event_type"] == "Payment Initiated")


def recipient_added(events, member, recipient):
    return next(
        (e for e in events if e["synthetic_member_id"] == member and e["event_type"] == "Recipient Added" and e["recipient_id"] == recipient),
        None,
    )


def account(numbers, recipients, rid):
    n, r = numbers[rid], recipients[rid]
    return {
        "recipient_id": rid,
        "bank": r["bank"],
        "account_masked": r["account_masked"],
        "routing_number": n["routing_number"],
        "account_number": n["account_number"],
        "owner_contact_id": r["owner_contact_id"] or None,
    }


def contact_block(c, numbers, recipients, events, at):
    accounts = [a for a in c["accounts"].split(";") if a]
    verified = []
    for rid in accounts:
        a = account(numbers, recipients, rid)
        # The data's own recipient age, from the last completed payment to it before the payment under test.
        paid = [
            e for e in events
            if e["recipient_id"] == rid and e["event_type"] == "Payment Completed" and ts(e["event_timestamp"]) <= at
        ]
        if paid:
            a["age_days"] = int(paid[-1]["recipient_age_days"])
            a["last_paid_label"] = day(ts(paid[-1]["event_timestamp"]))
        verified.append(a)
    added = date.fromisoformat(c["phone_added_at"])
    return {
        "contact_id": c["contact_id"],
        "name": c["name"],
        "relationship": c["relationship"],
        "phone_masked": c["phone_masked"],
        "phone_on_file_since": c["phone_added_at"],
        "phone_on_file_since_label": added.strftime("%b %Y"),
        "phone_on_file_days": (at.date() - added).days,
        "phone_eligible": (at.date() - added).days >= CONTACT_MIN_ON_FILE_DAYS,
        "verified_accounts": verified,
    }


def payment_block(e, recipients, numbers, events):
    at = ts(e["event_timestamp"])
    added = recipient_added(events, e["synthetic_member_id"], e["recipient_id"])
    return {
        "payment_id": e["payment_id"],
        "rail": e["payment_rail"],
        "amount": money(e["amount"]),
        "channel": e["channel"],
        "timestamp": at.isoformat(),
        "date_label": day(at),
        "time_label": clock(at),
        "recipient": account(numbers, recipients, e["recipient_id"]),
        "recipient_status": e["recipient_status"],
        "recipient_age_days": int(e["recipient_age_days"]),
        "recipient_added_label": clock(ts(added["event_timestamp"])) if added else None,
        "days_since_last_same_rail": int(e["days_since_last_same_rail"]),
        "years_since_last_same_rail": int(e["days_since_last_same_rail"]) // 365,
        "amount_vs_member_baseline": e["amount_vs_member_baseline"],
        "amount_to_baseline_ratio": float(e["amount_to_baseline_ratio"]),
        # Balance is reported after completed transactions only, so on the
        # initiation row it is still the balance before this payment.
        "balance_before": money(e["available_balance_after"]),
        "profile_change_recent": e["profile_change_recent"],
        "password_reset_recent": e["password_reset_recent"],
    }


def timeline(events, member, payment, extra_types=()):
    """What actually happened, from the payment's own rows (shown as 'Without our check')."""
    out = []
    for e in events:
        if e["synthetic_member_id"] != member:
            continue
        if e["payment_id"] != payment and e["event_type"] not in extra_types:
            continue
        at = ts(e["event_timestamp"])
        out.append(
            {
                "event_type": e["event_type"],
                "date_label": day(at),
                "time_label": clock(at),
                "member_response": e["member_response"] if e["member_response"] not in ("", "Not Asked") else None,
                "payment_status": e["payment_status"],
                "note": e["event_note"] or None,
            }
        )
    return out


def main():
    ensure_recipient_numbers()
    events = read(RAW / "HuskyHack_Synthetic_Events_v2.csv")
    events.sort(key=lambda e: (e["synthetic_member_id"], int(e["event_sequence"])))
    key = {r["synthetic_member_id"]: r for r in read(RAW / "HuskyHack_Member_Key_v2.csv")}
    contacts = read(OVERLAY / "contacts_overlay.csv")
    recipients = {r["recipient_id"]: r for r in read(OVERLAY / "recipients_overlay.csv")}
    stated = {r["payment_id"]: r for r in read(OVERLAY / "stated_recipient.csv")}
    channels = {r["synthetic_member_id"]: r for r in read(OVERLAY / "member_channels.csv")}
    numbers = {r["recipient_id"]: r for r in read(NUMBERS)}

    def story(ids, persona_name=None):
        e = initiated(events, ids["member"], ids["payment"])
        at = ts(e["event_timestamp"])
        s = stated[ids["payment"]]
        c = next(c for c in contacts if c["contact_id"] == s["contact_id"])
        k = key[ids["member"]]
        return {
            "member_id": ids["member"],
            "member_name": persona_name or k["anchor_persona"] or ids["member"],
            "member_phone_masked": channels[ids["member"]]["phone_masked"],
            "stated_recipient": s["stated_type"],
            "payment": payment_block(e, recipients, numbers, events),
            "contact": contact_block(c, numbers, recipients, events, at),
            "key": {
                "scenario_type": k["scenario_type"],
                "scenario_subtype": k["scenario_subtype"],
                "is_legitimate_lookalike": k["is_legitimate_lookalike"] == "Yes",
                "journey_outcome": k["journey_outcome"],
                "journey_summary": k["journey_summary"],
                "dollars_attempted": money(k["dollars_attempted"]),
                "dollars_sent": money(k["dollars_sent"]),
                "dollars_prevented": money(k["dollars_prevented"]),
                "dollars_recovered": money(k["dollars_recovered"]),
            },
        }

    scam = story(SCAM)
    scam["without_check"] = timeline(events, SCAM["member"], SCAM["payment"])
    scam["hold_hours"] = HOLD_HOURS
    scam["case_number"] = "CASE-" + SCAM["payment"].removeprefix("P")
    scam["caller_account_owner"] = None if not recipients[scam["payment"]["recipient"]["recipient_id"]]["owner_contact_id"] else "contact"

    look = story(LOOKALIKE)
    rows = payment_rows(events, LOOKALIKE["member"], LOOKALIKE["payment"])
    start = ts(rows[0]["event_timestamp"])
    done = next(ts(r["event_timestamp"]) for r in rows if r["payment_status"] == "Completed")
    look["actual"] = {
        "timeline": timeline(events, LOOKALIKE["member"], LOOKALIKE["payment"]),
        "minutes_to_complete": int((done - start).total_seconds() // 60),
        "completed_label": clock(done),
    }

    demo = {
        "generated_by": "scripts/build_demo_data.py",
        "source_note": SOURCE_NOTE,
        "disclaimer": DISCLAIMER,
        "scam": scam,
        "lookalike": look,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(demo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
