"""Build the synthetic overlay the events file doesn't carry (seed 2026).

The Verified Contact Payment check needs records Sound would hold but the
HuskyHack events don't include: members' saved contacts and their phones, which
bank each recipient account is at, the member's own phone/email history, and
what the member says a payment is for. This script makes them up, deterministically.

Outputs (data/overlay/):
  contacts_overlay.csv    saved contacts per member, with verified accounts
  stated_recipient.csv    simulated member input for New-recipient and cash payments
  recipients_overlay.csv  bank and masked account per recipient
  member_channels.csv     the member's own phone/email and the masked value after a change

Every assumption is written up in data/overlay/README.md.

Run: analysis/.venv/bin/python analysis/overlay.py
"""

import csv
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import oracle
from engine import parse_ts

SEED = 2026
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "overlay"
EVENTS_CSV = RAW / "HuskyHack_Synthetic_Events_v2.csv"
KEY_CSV = RAW / "HuskyHack_Member_Key_v2.csv"
WINDOW_START = date(2026, 8, 31)

FAMILY_RELATIONSHIPS = ("grandson", "child", "grandchild", "sibling", "niece or nephew", "cousin")  # "grandson" is Tommy only
OTHER_RELATIONSHIPS = ("friend", "neighbor", "roommate", "coworker")
FIRST_NAMES = (
    "Ava", "Ben", "Carmen", "Dev", "Elena", "Felix", "Grace", "Hiro", "Isla", "Jamal",
    "Keiko", "Luis", "Maya", "Nadia", "Omar", "Priya", "Quinn", "Rosa", "Sam", "Tara",
    "Uma", "Victor", "Wen", "Yusuf", "Zoe", "Aaron", "Bea", "Caleb", "Dana", "Eli",
)
EXTERNAL_BANKS = ("Cascade Federal Bank", "Evergreen National", "Pinecrest Credit Union", "Harbor Trust Bank", "Summit Online Bank")
SOUND_SHARE_OF_KNOWN_ACCOUNTS = 0.3

# Demo anchors (resolution 6).
LINDA = "M1001"
TOMMY = {
    "contact_id": "C1001-1",
    "name": "Tommy",
    "relationship": "grandson",
    "phone_masked": "(•••) •••-4417",
    "phone_added_at": (date(2026, 10, 20) - timedelta(days=240)).isoformat(),  # 240 days on file at P1001-003
}
LINDA_WIRE_RECIPIENT = "R1001-11"
LINDA_WIRE_ACCOUNT = "••••8723"
# One family-story member whose contact phone changed 3 days before their first
# scam payment, so the replay exercises the "call a number you already know" fallback.
RECENT_PHONE_FIXTURE_DAYS = 3


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def masked_phone(rng):
    return f"(•••) •••-{rng.randint(0, 9999):04d}"


def masked_account(rng):
    return f"••••{rng.randint(0, 9999):04d}"


def build():
    rng = random.Random(SEED)
    events = read_csv(EVENTS_CSV)
    key = oracle.load_key(KEY_CSV)
    scams = oracle.scam_payment_ids(key)
    members = sorted({e["synthetic_member_id"] for e in events})
    initiated = [e for e in events if e["event_type"] == "Payment Initiated"]

    # Recipients: first-seen status says whether the account predates the window.
    first_seen = {}
    for e in initiated:
        rid = e["recipient_id"]
        if rid and rid not in first_seen:
            first_seen[rid] = e
    pay_counts = defaultdict(Counter)
    for e in initiated:
        if e["recipient_id"] and e["payment_rail"] == "P2P":
            pay_counts[e["synthetic_member_id"]][e["recipient_id"]] += 1

    recipients = {}
    for rid, e in sorted(first_seen.items()):
        known = e["recipient_status"] == "Existing" and int(e["recipient_age_days"] or 0) >= 30
        bank = "Sound" if known and rng.random() < SOUND_SHARE_OF_KNOWN_ACCOUNTS else rng.choice(EXTERNAL_BANKS)
        recipients[rid] = {
            "synthetic_member_id": e["synthetic_member_id"],
            "recipient_id": rid,
            "bank": bank,
            "account_masked": masked_account(rng),
            "predates_window": "Yes" if known else "No",
            "owner_contact_id": "",
        }
    recipients[LINDA_WIRE_RECIPIENT].update(bank="Cascade Federal Bank", account_masked=LINDA_WIRE_ACCOUNT)

    first_scam_ts = {}
    for e in initiated:
        if e["payment_id"] in scams and e["synthetic_member_id"] not in first_scam_ts:
            first_scam_ts[e["synthetic_member_id"]] = parse_ts(e["event_timestamp"])
    family_scam_members = [
        m for m in members if key[m]["scenario_type"] == "Family Emergency" and not key[m]["anchor_persona"]
    ]
    recent_phone_member = family_scam_members[0] if family_scam_members else None

    contacts, channels = [], []
    used_names = set()
    for m in members:
        n = rng.choice((0, 1, 1, 2))
        need_family = oracle.needs_family_contact(key[m])
        if need_family:
            n = max(n, 1)
        # Verified-account candidates: P2P recipients that predate the window, most paid first.
        known_accounts = [
            rid for rid, _ in pay_counts[m].most_common() if recipients.get(rid, {}).get("predates_window") == "Yes"
        ]
        for i in range(n):
            cid = f"C{m[1:]}-{i + 1}"
            if m == LINDA and i == 0:
                c = dict(TOMMY)
            else:
                family = (i == 0 and need_family) or rng.random() < 0.6
                name = rng.choice([x for x in FIRST_NAMES if (m, x) not in used_names])
                c = {
                    "contact_id": cid,
                    "name": name,
                    "relationship": rng.choice(FAMILY_RELATIONSHIPS[1:] if family else OTHER_RELATIONSHIPS),
                    "phone_masked": masked_phone(rng),
                    "phone_added_at": (WINDOW_START - timedelta(days=rng.randint(30, 2000))).isoformat(),
                }
                if m == recent_phone_member and i == 0:
                    c["phone_added_at"] = (
                        first_scam_ts[m].date() - timedelta(days=RECENT_PHONE_FIXTURE_DAYS)
                    ).isoformat()
            used_names.add((m, c["name"]))
            accounts = known_accounts[i : i + 1]
            for rid in accounts:
                recipients[rid]["owner_contact_id"] = c["contact_id"]
            c.update(synthetic_member_id=m, accounts=";".join(accounts))
            contacts.append(c)

        channels.append(
            {
                "synthetic_member_id": m,
                "phone_masked": masked_phone(rng),
                "phone_added_at": (WINDOW_START - timedelta(days=rng.randint(200, 3000))).isoformat(),
                "phone_masked_after_change": masked_phone(rng),
                "email_masked": f"{chr(rng.randint(97, 122))}•••@{rng.choice(('mail.example', 'inbox.example', 'post.example'))}",
                "email_added_at": (WINDOW_START - timedelta(days=rng.randint(200, 3000))).isoformat(),
                "email_masked_after_change": f"{chr(rng.randint(97, 122))}•••@{rng.choice(('fastmail.example', 'webmail.example'))}",
            }
        )

    family_contact = {}
    for c in contacts:
        if c["relationship"] in FAMILY_RELATIONSHIPS and c["synthetic_member_id"] not in family_contact:
            family_contact[c["synthetic_member_id"]] = c["contact_id"]

    stated = []
    for e in initiated:
        if e["recipient_status"] != "New" and e["payment_rail"] != "Cash":
            continue
        m = e["synthetic_member_id"]
        stype = oracle.stated_recipient_type(key[m], e["payment_id"] in scams)
        stated.append(
            {
                "payment_id": e["payment_id"],
                "synthetic_member_id": m,
                "recipient_id": e["recipient_id"],
                "stated_type": stype,
                "contact_id": family_contact.get(m, "") if stype == "saved_contact" else "",
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUT / "contacts_overlay.csv",
        contacts,
        ["synthetic_member_id", "contact_id", "name", "relationship", "phone_masked", "phone_added_at", "accounts"],
    )
    write_csv(
        OUT / "stated_recipient.csv",
        stated,
        ["payment_id", "synthetic_member_id", "recipient_id", "stated_type", "contact_id"],
    )
    write_csv(
        OUT / "recipients_overlay.csv",
        list(recipients.values()),
        ["synthetic_member_id", "recipient_id", "bank", "account_masked", "predates_window", "owner_contact_id"],
    )
    write_csv(OUT / "member_channels.csv", channels, list(channels[0]))
    return {
        "contacts": len(contacts),
        "stated": Counter(s["stated_type"] for s in stated),
        "recipients": len(recipients),
        "recent_phone_member": recent_phone_member,
    }


def load(member_id=None, overlay_dir=OUT):
    """Overlay as engine ctx pieces, keyed by member: {member: {contacts, recipients, member_channels}}."""
    out = defaultdict(lambda: {"contacts": {}, "recipients": {}, "member_channels": {}})
    for c in read_csv(overlay_dir / "contacts_overlay.csv"):
        c = dict(c, accounts=[a for a in c["accounts"].split(";") if a])
        out[c["synthetic_member_id"]]["contacts"][c["contact_id"]] = c
    for r in read_csv(overlay_dir / "recipients_overlay.csv"):
        out[r["synthetic_member_id"]]["recipients"][r["recipient_id"]] = r
    for ch in read_csv(overlay_dir / "member_channels.csv"):
        out[ch["synthetic_member_id"]]["member_channels"] = {
            "phone": {"masked": ch["phone_masked"], "added_at": ch["phone_added_at"], "masked_after_change": ch["phone_masked_after_change"]},
            "email": {"masked": ch["email_masked"], "added_at": ch["email_added_at"], "masked_after_change": ch["email_masked_after_change"]},
        }
    stated = {s["payment_id"]: {"type": s["stated_type"], "contact_id": s["contact_id"]} for s in read_csv(overlay_dir / "stated_recipient.csv")}
    return out, stated


if __name__ == "__main__":
    print(build())
